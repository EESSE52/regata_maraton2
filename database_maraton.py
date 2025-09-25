# database_maraton.py
# CORREGIDO: Las funciones de reportes ahora devuelven el logo_path del club.

import sqlite3
import os
import datetime
from contextlib import contextmanager
from utils_maraton import resource_path

DB_FILENAME = "regatas_maraton.db"
DB_PATH = resource_path(DB_FILENAME)

@contextmanager
def conectar_db():
    """Establece una conexión a la base de datos como un context manager."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise e
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def inicializar_db():
    """Crea todas las tablas necesarias si no existen y realiza migraciones."""
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_evento TEXT NOT NULL UNIQUE, fecha TEXT, lugar TEXT, notas TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS clubes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_club TEXT NOT NULL UNIQUE, abreviatura TEXT, ciudad TEXT, logo_path TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS participantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, apellido TEXT NOT NULL, rut_o_id TEXT UNIQUE, fecha_nacimiento TEXT, genero TEXT CHECK(genero IN ('Masculino', 'Femenino')), club_id INTEGER, FOREIGN KEY (club_id) REFERENCES clubes (id) ON DELETE SET NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_categoria TEXT NOT NULL, codigo_categoria TEXT UNIQUE, edad_min INTEGER DEFAULT 0, edad_max INTEGER DEFAULT 99, genero TEXT, tipo_embarcacion TEXT, distancia_km REAL, numero_vueltas INTEGER)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS inscripciones (id INTEGER PRIMARY KEY AUTOINCREMENT, evento_id INTEGER NOT NULL, categoria_id INTEGER NOT NULL, participante1_id INTEGER NOT NULL, participante2_id INTEGER, participante3_id INTEGER, participante4_id INTEGER, numero_competidor INTEGER, tiempo_final TEXT, tiempo_vueltas TEXT, lugar_final INTEGER, estado TEXT DEFAULT 'Inscrito' CHECK(estado IN ('Inscrito', 'DNS', 'DNF', 'DSQ', 'Finalizado')), FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE, FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE CASCADE, FOREIGN KEY (participante1_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante2_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante3_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante4_id) REFERENCES participantes (id) ON DELETE CASCADE, UNIQUE (evento_id, categoria_id, numero_competidor))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_sponsor TEXT NOT NULL, logo_path TEXT, evento_id INTEGER NOT NULL, FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS evento_categorias_estado (evento_id INTEGER NOT NULL, categoria_id INTEGER NOT NULL, es_valida INTEGER NOT NULL DEFAULT 1, PRIMARY KEY (evento_id, categoria_id), FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE, FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE CASCADE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS programa_pruebas (id INTEGER PRIMARY KEY AUTOINCREMENT, evento_id INTEGER NOT NULL, categoria_id INTEGER NOT NULL, orden INTEGER NOT NULL, hora_inicio TEXT, UNIQUE (evento_id, categoria_id), FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE, FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE CASCADE)""")

        cursor.execute("PRAGMA table_info(clubes)")
        columnas = [info[1] for info in cursor.fetchall()]
        if 'logo_path' not in columnas:
            print("[INFO] Migración: Añadiendo columna 'logo_path' a la tabla 'clubes'.")
            cursor.execute("ALTER TABLE clubes ADD COLUMN logo_path TEXT")
        
        conn.commit()

def obtener_info_evento(evento_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eventos WHERE id=?", (evento_id,))
        return cursor.fetchone()

def obtener_info_categoria(categoria_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categorias WHERE id=?", (categoria_id,))
        return cursor.fetchone()

def obtener_info_participante(participante_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM participantes WHERE id=?", (participante_id,))
        return cursor.fetchone()

def buscar_o_crear_club(nombre_club):
    if not nombre_club or not nombre_club.strip(): return None
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clubes WHERE nombre_club = ?", (nombre_club.strip(),))
        res = cursor.fetchone()
        if res: return res[0]
        cursor.execute("INSERT INTO clubes (nombre_club) VALUES (?)", (nombre_club.strip(),))
        conn.commit()
        return cursor.lastrowid

def buscar_o_crear_participante(datos_participante):
    rut_id = datos_participante.get('rut_o_id')
    if not rut_id or not rut_id.strip(): raise ValueError("El RUT/ID es obligatorio.")
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM participantes WHERE rut_o_id = ?", (rut_id.strip(),))
        res = cursor.fetchone()
        if res: return res[0]
        club_id = buscar_o_crear_club(datos_participante.get('club'))
        nombre_completo = datos_participante.get('nombre_completo', '').strip().split(' ')
        nombre = nombre_completo[0]
        apellido = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''
        params = (nombre, apellido, rut_id.strip(), datos_participante.get('fecha_nacimiento'), datos_participante.get('genero'), club_id)
        cursor.execute("INSERT INTO participantes (nombre, apellido, rut_o_id, fecha_nacimiento, genero, club_id) VALUES (?, ?, ?, ?, ?, ?)", params)
        conn.commit()
        return cursor.lastrowid

def obtener_categoria_por_codigo(codigo_categoria):
    if not codigo_categoria or not codigo_categoria.strip(): return None
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categorias WHERE codigo_categoria = ?", (codigo_categoria.strip().upper(),))
        res = cursor.fetchone()
        return res[0] if res else None

def obtener_eventos():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_evento, fecha, lugar FROM eventos ORDER BY fecha DESC")
        return cursor.fetchall()

def agregar_o_actualizar_evento(datos, evento_id=None):
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            if evento_id:
                sql, params = "UPDATE eventos SET nombre_evento=?, fecha=?, lugar=?, notas=? WHERE id=?", (datos['nombre_evento'], datos['fecha'], datos['lugar'], datos['notas'], evento_id)
            else:
                sql, params = "INSERT INTO eventos (nombre_evento, fecha, lugar, notas) VALUES (?, ?, ?, ?)", (datos['nombre_evento'], datos['fecha'], datos['lugar'], datos['notas'])
            cursor.execute(sql, params)
            if not evento_id: evento_id = cursor.lastrowid
            conn.commit()
            return evento_id, "Evento guardado."
    except sqlite3.IntegrityError: return None, "Error: El nombre del evento ya existe."

def eliminar_evento(evento_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM eventos WHERE id=?", (evento_id,))
        conn.commit()
        return True, "Evento eliminado."

def obtener_clubes():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_club, abreviatura, ciudad, logo_path FROM clubes ORDER BY nombre_club")
        return cursor.fetchall()

def agregar_o_actualizar_club(nombre, abreviatura, ciudad, logo_path=None, club_id=None):
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            if club_id:
                cursor.execute("UPDATE clubes SET nombre_club=?, abreviatura=?, ciudad=?, logo_path=? WHERE id=?", (nombre, abreviatura, ciudad, logo_path, club_id))
            else:
                cursor.execute("INSERT INTO clubes (nombre_club, abreviatura, ciudad, logo_path) VALUES (?, ?, ?, ?)", (nombre, abreviatura, ciudad, logo_path))
            conn.commit()
            return True, "Club guardado."
    except sqlite3.IntegrityError: return False, "Error: El nombre del club ya existe."

def eliminar_club(club_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clubes WHERE id=?", (club_id,))
        conn.commit()
        return True, "Club eliminado."

def obtener_participantes_con_club():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT p.id, p.nombre, p.apellido, p.rut_o_id, p.fecha_nacimiento, p.genero, c.nombre_club FROM participantes p LEFT JOIN clubes c ON p.club_id = c.id ORDER BY p.apellido, p.nombre")
        return cursor.fetchall()

def agregar_o_actualizar_participante(datos, participante_id=None):
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            params = (datos['nombre'], datos['apellido'], datos['rut_o_id'], datos['fecha_nacimiento'], datos['genero'], datos['club_id'])
            if participante_id:
                cursor.execute("UPDATE participantes SET nombre=?, apellido=?, rut_o_id=?, fecha_nacimiento=?, genero=?, club_id=? WHERE id=?", params + (participante_id,))
            else:
                cursor.execute("INSERT INTO participantes (nombre, apellido, rut_o_id, fecha_nacimiento, genero, club_id) VALUES (?, ?, ?, ?, ?, ?)", params)
            conn.commit()
            return True, "Participante guardado."
    except sqlite3.IntegrityError: return False, "Error: El RUT o ID del participante ya existe."

def eliminar_participante(participante_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM participantes WHERE id=?", (participante_id,))
        conn.commit()
        return True, "Participante eliminado."

def obtener_categorias():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_categoria, codigo_categoria, edad_min, edad_max, genero, tipo_embarcacion, distancia_km, numero_vueltas FROM categorias ORDER BY nombre_categoria")
        return cursor.fetchall()

def agregar_o_actualizar_categoria(datos, categoria_id=None):
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            params = (datos['nombre_categoria'], datos['codigo_categoria'], datos['edad_min'], datos['edad_max'], datos['genero'], datos['tipo_embarcacion'], datos['distancia_km'], datos['numero_vueltas'])
            if categoria_id:
                cursor.execute("UPDATE categorias SET nombre_categoria=?, codigo_categoria=?, edad_min=?, edad_max=?, genero=?, tipo_embarcacion=?, distancia_km=?, numero_vueltas=? WHERE id=?", params + (categoria_id,))
            else:
                cursor.execute("INSERT INTO categorias (nombre_categoria, codigo_categoria, edad_min, edad_max, genero, tipo_embarcacion, distancia_km, numero_vueltas) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", params)
            conn.commit()
            return True, "Categoría guardada."
    except sqlite3.IntegrityError: return False, "Error: El código de la categoría ya existe."

def eliminar_categoria(categoria_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categorias WHERE id=?", (categoria_id,))
        conn.commit()
        return True, "Categoría eliminada."

def inscribir_embarcacion(datos):
    sql = "INSERT INTO inscripciones (evento_id, categoria_id, participante1_id, participante2_id, participante3_id, participante4_id, numero_competidor) VALUES (?, ?, ?, ?, ?, ?, ?)"
    params = (datos['evento_id'], datos['categoria_id'], datos['participante1_id'], datos.get('participante2_id'), datos.get('participante3_id'), datos.get('participante4_id'), datos['numero_competidor'])
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid, "Inscripción guardada."
    except sqlite3.IntegrityError: return None, "Error: El número de competidor ya está en uso."

def obtener_inscripciones_por_categoria(evento_id, categoria_id):
    sql = """
        SELECT 
            i.id, i.numero_competidor,
            p1.apellido || ', ' || p1.nombre, p1.fecha_nacimiento, c1.nombre_club, c1.logo_path,
            p2.apellido || ', ' || p2.nombre, p2.fecha_nacimiento, c2.nombre_club, c2.logo_path,
            p3.apellido || ', ' || p3.nombre, p3.fecha_nacimiento, c3.nombre_club, c3.logo_path,
            p4.apellido || ', ' || p4.nombre, p4.fecha_nacimiento, c4.nombre_club, c4.logo_path,
            i.lugar_final, i.tiempo_final, i.estado, i.tiempo_vueltas
        FROM inscripciones i
        JOIN participantes p1 ON i.participante1_id = p1.id
        LEFT JOIN clubes c1 ON p1.club_id = c1.id
        LEFT JOIN participantes p2 ON i.participante2_id = p2.id
        LEFT JOIN clubes c2 ON p2.club_id = c2.id
        LEFT JOIN participantes p3 ON i.participante3_id = p3.id
        LEFT JOIN clubes c3 ON p3.club_id = c3.id
        LEFT JOIN participantes p4 ON i.participante4_id = p4.id
        LEFT JOIN clubes c4 ON p4.club_id = c4.id
        WHERE i.evento_id = ? AND i.categoria_id = ?
        ORDER BY 
            CASE WHEN i.lugar_final IS NULL THEN 1 ELSE 0 END,
            i.lugar_final ASC, i.tiempo_final ASC, i.numero_competidor ASC
    """
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id, categoria_id))
        return cursor.fetchall()

def eliminar_inscripcion(inscripcion_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inscripciones WHERE id=?", (inscripcion_id,))
        conn.commit()
        return True, "Inscripción eliminada."

def actualizar_resultado_inscripcion(inscripcion_id, tiempo_final, estado, tiempos_vueltas_json=None):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE inscripciones SET tiempo_final = ?, estado = ?, tiempo_vueltas = ? WHERE id = ?", (tiempo_final, estado, tiempos_vueltas_json, inscripcion_id))
        conn.commit()
        return True, "Resultado actualizado."

def recalcular_posiciones_categoria(evento_id, categoria_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM inscripciones WHERE evento_id = ? AND categoria_id = ? AND estado = 'Finalizado' AND tiempo_final IS NOT NULL AND tiempo_final != '' ORDER BY tiempo_final ASC", (evento_id, categoria_id))
        finalizados = cursor.fetchall()
        for i, (insc_id,) in enumerate(finalizados):
            cursor.execute("UPDATE inscripciones SET lugar_final = ? WHERE id = ?", (i + 1, insc_id))
        cursor.execute("UPDATE inscripciones SET lugar_final = NULL WHERE evento_id = ? AND categoria_id = ? AND estado != 'Finalizado'", (evento_id, categoria_id))
        conn.commit()
        return True, "Posiciones recalculadas."

def obtener_estado_categoria(evento_id, categoria_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT es_valida FROM evento_categorias_estado WHERE evento_id = ? AND categoria_id = ?", (evento_id, categoria_id))
        res = cursor.fetchone()
        if res is None:
            cursor.execute("INSERT INTO evento_categorias_estado (evento_id, categoria_id, es_valida) VALUES (?, ?, 1)", (evento_id, categoria_id))
            conn.commit()
            return 1
        return res[0]

def actualizar_estado_categoria(evento_id, categoria_id, es_valida):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO evento_categorias_estado (evento_id, categoria_id, es_valida) VALUES (?, ?, ?)", (evento_id, categoria_id, int(es_valida)))
        conn.commit()

def calcular_puntuacion_clubes(evento_id, sistema_puntuacion):
    sql = """
        SELECT c.nombre_club, c.logo_path, i.lugar_final 
        FROM inscripciones i 
        JOIN participantes p1 ON i.participante1_id = p1.id 
        JOIN clubes c ON p1.club_id = c.id 
        JOIN evento_categorias_estado ece ON i.evento_id = ece.evento_id AND i.categoria_id = ece.categoria_id
        WHERE i.evento_id = ? 
          AND i.estado = 'Finalizado' 
          AND i.lugar_final IS NOT NULL
          AND ece.es_valida = 1
    """
    puntuacion_por_club = {}
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()
        for nombre_club, logo_path, lugar in resultados:
            puntos = sistema_puntuacion.get(lugar, 0)
            if nombre_club not in puntuacion_por_club: 
                puntuacion_por_club[nombre_club] = {'puntos': 0, 'logo_path': logo_path}
            puntuacion_por_club[nombre_club]['puntos'] += puntos
        
        lista_ordenada = sorted(puntuacion_por_club.items(), key=lambda item: item[1]['puntos'], reverse=True)
        return [(nombre, data['logo_path'], data['puntos']) for nombre, data in lista_ordenada]

def calcular_ranking_medallas(evento_id):
    sql = """
        SELECT c.nombre_club, c.logo_path, i.lugar_final 
        FROM inscripciones i 
        JOIN participantes p1 ON i.participante1_id = p1.id 
        JOIN clubes c ON p1.club_id = c.id 
        JOIN evento_categorias_estado ece ON i.evento_id = ece.evento_id AND i.categoria_id = ece.categoria_id
        WHERE i.evento_id = ? 
          AND i.estado = 'Finalizado' 
          AND i.lugar_final IN (1, 2, 3)
          AND ece.es_valida = 1
    """
    medallas_por_club = {}
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()
        for nombre_club, logo_path, lugar in resultados:
            if nombre_club not in medallas_por_club: 
                medallas_por_club[nombre_club] = {'oro': 0, 'plata': 0, 'bronce': 0, 'logo_path': logo_path}
            if lugar == 1: medallas_por_club[nombre_club]['oro'] += 1
            elif lugar == 2: medallas_por_club[nombre_club]['plata'] += 1
            elif lugar == 3: medallas_por_club[nombre_club]['bronce'] += 1
        
        lista_medallero = [(nombre, data['logo_path'], data['oro'], data['plata'], data['bronce']) for nombre, data in medallas_por_club.items()]
        lista_medallero.sort(key=lambda item: (item[2], item[3], item[4]), reverse=True)
        return lista_medallero

def obtener_inscripciones_para_exportar(evento_id):
    sql = "SELECT cat.codigo_categoria, i.numero_competidor, p1.nombre || ' ' || p1.apellido, p1.rut_o_id, p1.fecha_nacimiento, p1.genero, c1.nombre_club, p2.nombre || ' ' || p2.apellido, p2.rut_o_id, p2.fecha_nacimiento, p2.genero, c2.nombre_club, p3.nombre || ' ' || p3.apellido, p3.rut_o_id, p3.fecha_nacimiento, p3.genero, c3.nombre_club, p4.nombre || ' ' || p4.apellido, p4.rut_o_id, p4.fecha_nacimiento, p4.genero, c4.nombre_club FROM inscripciones i JOIN categorias cat ON i.categoria_id = cat.id JOIN participantes p1 ON i.participante1_id = p1.id LEFT JOIN clubes c1 ON p1.club_id = c1.id LEFT JOIN participantes p2 ON i.participante2_id = p2.id LEFT JOIN clubes c2 ON p2.club_id = c2.id LEFT JOIN participantes p3 ON i.participante3_id = p3.id LEFT JOIN clubes c3 ON p3.club_id = c3.id LEFT JOIN participantes p4 ON i.participante4_id = p4.id LEFT JOIN clubes c4 ON p4.club_id = c4.id WHERE i.evento_id = ? ORDER BY cat.id, i.numero_competidor"
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        return cursor.fetchall()

def agregar_sponsor(nombre, logo_path, evento_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sponsors (nombre_sponsor, logo_path, evento_id) VALUES (?, ?, ?)", (nombre, logo_path, evento_id))
        conn.commit()
        return cursor.lastrowid, "Patrocinador agregado."

def obtener_sponsors_por_evento(evento_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_sponsor, logo_path FROM sponsors WHERE evento_id = ? ORDER BY nombre_sponsor", (evento_id,))
        return cursor.fetchall()

def eliminar_sponsor(sponsor_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
        conn.commit()
        return True, "Patrocinador eliminado."

def obtener_siguiente_numero_competidor(evento_id, categoria_id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero_competidor) FROM inscripciones WHERE evento_id = ? AND categoria_id = ?", (evento_id, categoria_id))
        res = cursor.fetchone()
        return (res[0] or 0) + 1

def verificar_numero_competidor(evento_id, categoria_id, numero_competidor, excluir_inscripcion_id=None):
    with conectar_db() as conn:
        cursor = conn.cursor()
        if excluir_inscripcion_id:
            cursor.execute("SELECT id FROM inscripciones WHERE evento_id=? AND categoria_id=? AND numero_competidor=? AND id!=?", (evento_id, categoria_id, numero_competidor, excluir_inscripcion_id))
        else:
            cursor.execute("SELECT id FROM inscripciones WHERE evento_id=? AND categoria_id=? AND numero_competidor=?", (evento_id, categoria_id, numero_competidor))
        return cursor.fetchone() is not None

def actualizar_numero_competidor(inscripcion_id, nuevo_numero):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE inscripciones SET numero_competidor=? WHERE id=?", (nuevo_numero, inscripcion_id))
        conn.commit()
        return True

def buscar_deportistas_por_nombre(texto_busqueda):
    sql = """
        SELECT p.id, p.nombre || ' ' || p.apellido, c.nombre_club
        FROM participantes p
        LEFT JOIN clubes c ON p.club_id = c.id
        WHERE p.nombre LIKE ? OR p.apellido LIKE ?
        ORDER BY p.apellido, p.nombre
        LIMIT 50
    """
    param = f"%{texto_busqueda}%"
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (param, param))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al buscar deportistas: {e}")
        return []

def obtener_inscripciones_de_deportista(evento_id, participante_id):
    sql = """
        SELECT 
            i.id,
            cat.nombre_categoria,
            i.numero_competidor,
            p1.id, p1.nombre || ' ' || p1.apellido,
            p2.id, p2.nombre || ' ' || p2.apellido,
            p3.id, p3.nombre || ' ' || p3.apellido,
            p4.id, p4.nombre || ' ' || p4.apellido
        FROM inscripciones i
        JOIN categorias cat ON i.categoria_id = cat.id
        LEFT JOIN participantes p1 ON i.participante1_id = p1.id
        LEFT JOIN participantes p2 ON i.participante2_id = p2.id
        LEFT JOIN participantes p3 ON i.participante3_id = p3.id
        LEFT JOIN participantes p4 ON i.participante4_id = p4.id
        WHERE i.evento_id = ? AND (
            i.participante1_id = ? OR
            i.participante2_id = ? OR
            i.participante3_id = ? OR
            i.participante4_id = ?
        )
    """
    params = (evento_id, participante_id, participante_id, participante_id, participante_id)
    inscripciones_formateadas = []
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            resultados = cursor.fetchall()
            
            for row in resultados:
                insc_id, categoria, num_bote, p1_id, p1_n, p2_id, p2_n, p3_id, p3_n, p4_id, p4_n = row
                companeros = []
                if p1_id != participante_id and p1_n: companeros.append(p1_n)
                if p2_id != participante_id and p2_n: companeros.append(p2_n)
                if p3_id != participante_id and p3_n: companeros.append(p3_n)
                if p4_id != participante_id and p4_n: companeros.append(p4_n)
                
                inscripciones_formateadas.append({'inscripcion_id': insc_id, 'categoria': categoria, 'numero_bote': num_bote, 'companeros': " / ".join(companeros) if companeros else "Bote individual"})
        return inscripciones_formateadas
    except sqlite3.Error as e:
        print(f"Error al obtener inscripciones de deportista: {e}")
        return []

def guardar_programa_pruebas(evento_id, programa):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM programa_pruebas WHERE evento_id = ?", (evento_id,))
        sql = "INSERT INTO programa_pruebas (evento_id, categoria_id, orden, hora_inicio) VALUES (?, ?, ?, ?)"
        cursor.executemany(sql, programa)
        conn.commit()
    return True, "Programa guardado correctamente."

def obtener_programa_pruebas(evento_id):
    sql = """
        SELECT p.categoria_id, c.nombre_categoria, c.codigo_categoria, p.hora_inicio
        FROM programa_pruebas p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.evento_id = ?
        ORDER BY p.orden ASC
    """
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (evento_id,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener el programa de pruebas: {e}")
        return []

def calcular_puntuacion_deportistas(evento_id, sistema_puntuacion):
    sql = """
        SELECT i.lugar_final, i.participante1_id, i.participante2_id, i.participante3_id, i.participante4_id
        FROM inscripciones i
        JOIN evento_categorias_estado ece ON i.evento_id = ece.evento_id AND i.categoria_id = ece.categoria_id
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IS NOT NULL AND ece.es_valida = 1
    """
    puntuacion_por_deportista = {}
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        for lugar, p1_id, p2_id, p3_id, p4_id in cursor.fetchall():
            puntos = sistema_puntuacion.get(lugar, 0)
            if puntos == 0: continue
            for p_id in filter(None, [p1_id, p2_id, p3_id, p4_id]):
                if p_id not in puntuacion_por_deportista:
                    info = cursor.execute("SELECT p.apellido || ', ' || p.nombre, c.nombre_club, c.logo_path FROM participantes p LEFT JOIN clubes c ON p.club_id = c.id WHERE p.id = ?", (p_id,)).fetchone()
                    if info: puntuacion_por_deportista[p_id] = {'nombre': info[0], 'club': info[1], 'logo_path': info[2], 'puntos': 0}
                if p_id in puntuacion_por_deportista:
                    puntuacion_por_deportista[p_id]['puntos'] += puntos
        return sorted(puntuacion_por_deportista.values(), key=lambda item: item['puntos'], reverse=True)

def calcular_ranking_medallas_deportistas(evento_id):
    sql = """
        SELECT i.lugar_final, i.participante1_id, i.participante2_id, i.participante3_id, i.participante4_id
        FROM inscripciones i
        JOIN evento_categorias_estado ece ON i.evento_id = ece.evento_id AND i.categoria_id = ece.categoria_id
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IN (1, 2, 3) AND ece.es_valida = 1
    """
    medallas_por_deportista = {}
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        for lugar, p1_id, p2_id, p3_id, p4_id in cursor.fetchall():
            for p_id in filter(None, [p1_id, p2_id, p3_id, p4_id]):
                if p_id not in medallas_por_deportista:
                    info = cursor.execute("SELECT p.apellido || ', ' || p.nombre, c.nombre_club, c.logo_path FROM participantes p LEFT JOIN clubes c ON p.club_id = c.id WHERE p.id = ?", (p_id,)).fetchone()
                    if info: medallas_por_deportista[p_id] = {'nombre': info[0], 'club': info[1], 'logo_path': info[2], 'oro': 0, 'plata': 0, 'bronce': 0}
                if p_id in medallas_por_deportista:
                    if lugar == 1: medallas_por_deportista[p_id]['oro'] += 1
                    elif lugar == 2: medallas_por_deportista[p_id]['plata'] += 1
                    elif lugar == 3: medallas_por_deportista[p_id]['bronce'] += 1
        return sorted(medallas_por_deportista.values(), key=lambda item: (item['oro'], item['plata'], item['bronce']), reverse=True)