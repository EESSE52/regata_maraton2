# database_maraton.py
# Versión completa con todas las funciones necesarias para los reportes PDF/PNG

import sqlite3
import os
import datetime
from utils_maraton import resource_path

DB_FILENAME = "regatas_maraton.db"
DB_PATH = resource_path(DB_FILENAME)

def conectar_db():
    """Establece una conexión a la base de datos."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise e

def inicializar_db():
    """Crea todas las tablas necesarias si no existen."""
    conn = None 
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_evento TEXT NOT NULL UNIQUE, fecha TEXT, lugar TEXT, notas TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS clubes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_club TEXT NOT NULL UNIQUE, abreviatura TEXT, ciudad TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS participantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, apellido TEXT NOT NULL, rut_o_id TEXT UNIQUE, fecha_nacimiento TEXT, genero TEXT CHECK(genero IN ('Masculino', 'Femenino')), club_id INTEGER, FOREIGN KEY (club_id) REFERENCES clubes (id) ON DELETE SET NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_categoria TEXT NOT NULL, codigo_categoria TEXT UNIQUE, edad_min INTEGER DEFAULT 0, edad_max INTEGER DEFAULT 99, genero TEXT, tipo_embarcacion TEXT, distancia_km REAL, numero_vueltas INTEGER)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS inscripciones (id INTEGER PRIMARY KEY AUTOINCREMENT, evento_id INTEGER NOT NULL, categoria_id INTEGER NOT NULL, participante1_id INTEGER NOT NULL, participante2_id INTEGER, participante3_id INTEGER, participante4_id INTEGER, numero_competidor INTEGER, tiempo_final TEXT, tiempo_vueltas TEXT, lugar_final INTEGER, estado TEXT DEFAULT 'Inscrito' CHECK(estado IN ('Inscrito', 'DNS', 'DNF', 'DSQ', 'Finalizado')), FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE, FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE CASCADE, FOREIGN KEY (participante1_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante2_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante3_id) REFERENCES participantes (id) ON DELETE CASCADE, FOREIGN KEY (participante4_id) REFERENCES participantes (id) ON DELETE CASCADE, UNIQUE (evento_id, categoria_id, numero_competidor))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sponsors (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_sponsor TEXT NOT NULL, logo_path TEXT, evento_id INTEGER NOT NULL, FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE)""")

        conn.commit()
    except sqlite3.Error as e:
        raise e
    finally:
        if conn: conn.close()

# --- FUNCIONES DE SOPORTE PARA OBTENER INFO ---
def obtener_info_evento(evento_id):
    conn = conectar_db()
    if not conn: return None
    try: 
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eventos WHERE id=?", (evento_id,))
        return cursor.fetchone() 
    except sqlite3.Error as e: 
        print(f"Error al obtener info del evento: {e}")
        return None
    finally: 
        conn.close()

def obtener_info_categoria(categoria_id):
    conn = conectar_db()
    if not conn: return None
    try: 
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categorias WHERE id=?", (categoria_id,))
        return cursor.fetchone()
    except sqlite3.Error as e: 
        print(f"Error al obtener info de la categoría: {e}")
        return None
    finally: 
        conn.close()

def obtener_info_participante(participante_id):
    conn = conectar_db()
    if not conn: return None
    try: 
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM participantes WHERE id=?", (participante_id,))
        return cursor.fetchone()
    except sqlite3.Error as e: 
        print(f"Error al obtener info del participante: {e}")
        return None
    finally: 
        conn.close()

# --- FUNCIONES DE BÚSQUEDA Y CREACIÓN PARA IMPORTACIÓN ---
def buscar_o_crear_club(nombre_club):
    if not nombre_club or not nombre_club.strip(): return None
    nombre_club_limpio = nombre_club.strip()
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clubes WHERE nombre_club = ?", (nombre_club_limpio,))
        resultado = cursor.fetchone()
        if resultado: return resultado[0]
        else:
            cursor.execute("INSERT INTO clubes (nombre_club) VALUES (?)", (nombre_club_limpio,))
            conn.commit()
            return cursor.lastrowid
    finally:
        if conn: conn.close()

def buscar_o_crear_participante(datos_participante):
    rut_id = datos_participante.get('rut_o_id')
    if not rut_id or not rut_id.strip(): raise ValueError("El RUT/ID es obligatorio para la importación.")
    rut_id_limpio = rut_id.strip()
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM participantes WHERE rut_o_id = ?", (rut_id_limpio,))
        resultado = cursor.fetchone()
        if resultado: return resultado[0]
        else:
            club_id = buscar_o_crear_club(datos_participante.get('club'))
            sql = "INSERT INTO participantes (nombre, apellido, rut_o_id, fecha_nacimiento, genero, club_id) VALUES (?, ?, ?, ?, ?, ?)"
            nombre_completo = datos_participante.get('nombre_completo', '').strip().split(' ')
            nombre = nombre_completo[0]
            apellido = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''
            params = (nombre, apellido, rut_id_limpio, datos_participante.get('fecha_nacimiento'), datos_participante.get('genero'), club_id)
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    finally:
        if conn: conn.close()

def obtener_categoria_por_codigo(codigo_categoria):
    if not codigo_categoria or not codigo_categoria.strip(): return None
    codigo_limpio = codigo_categoria.strip().upper()
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categorias WHERE codigo_categoria = ?", (codigo_limpio,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA EVENTOS ---
def obtener_eventos():
    conn = conectar_db()
    if not conn: return []
    try: 
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_evento, fecha, lugar FROM eventos ORDER BY fecha DESC")
        return cursor.fetchall()
    except sqlite3.Error as e: 
        print(f"Error al obtener eventos: {e}")
        return []
    finally: 
        conn.close()

def agregar_o_actualizar_evento(datos, evento_id=None):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        if evento_id: 
            sql = "UPDATE eventos SET nombre_evento=?, fecha=?, lugar=?, notas=? WHERE id=?"
            params = (datos['nombre_evento'], datos['fecha'], datos['lugar'], datos['notas'], evento_id)
            mensaje = "Evento actualizado."
        else: 
            sql = "INSERT INTO eventos (nombre_evento, fecha, lugar, notas) VALUES (?, ?, ?, ?)"
            params = (datos['nombre_evento'], datos['fecha'], datos['lugar'], datos['notas'])
            mensaje = "Evento agregado."
        cursor.execute(sql, params)
        if not evento_id: evento_id = cursor.lastrowid
        conn.commit()
        return evento_id, mensaje
    except sqlite3.IntegrityError: 
        return None, "Error: El nombre del evento ya existe."
    finally:
        if conn: conn.close()

def eliminar_evento(evento_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM eventos WHERE id=?", (evento_id,))
        conn.commit()
        return True, "Evento eliminado."
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA CLUBES ---
def obtener_clubes():
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_club, abreviatura, ciudad FROM clubes ORDER BY nombre_club")
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def agregar_o_actualizar_club(nombre, abreviatura, ciudad, club_id=None):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        if club_id: 
            cursor.execute("UPDATE clubes SET nombre_club=?, abreviatura=?, ciudad=? WHERE id=?", 
                          (nombre, abreviatura, ciudad, club_id))
            mensaje = "Club actualizado."
        else: 
            cursor.execute("INSERT INTO clubes (nombre_club, abreviatura, ciudad) VALUES (?, ?, ?)", 
                          (nombre, abreviatura, ciudad))
            club_id = cursor.lastrowid
            mensaje = "Club agregado."
        conn.commit()
        return club_id, mensaje
    except sqlite3.IntegrityError: 
        return None, "Error: El nombre del club ya existe."
    finally:
        if conn: conn.close()

def eliminar_club(club_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clubes WHERE id=?", (club_id,))
        conn.commit()
        return True, "Club eliminado."
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA PARTICIPANTES ---
def obtener_participantes_con_club():
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.nombre, p.apellido, p.rut_o_id, p.fecha_nacimiento, p.genero, c.nombre_club 
            FROM participantes p 
            LEFT JOIN clubes c ON p.club_id = c.id 
            ORDER BY p.apellido, p.nombre
        """)
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def agregar_o_actualizar_participante(datos, participante_id=None):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        if participante_id: 
            sql = "UPDATE participantes SET nombre=?, apellido=?, rut_o_id=?, fecha_nacimiento=?, genero=?, club_id=? WHERE id=?"
            params = (datos['nombre'], datos['apellido'], datos['rut_o_id'], datos['fecha_nacimiento'], 
                     datos['genero'], datos['club_id'], participante_id)
            mensaje = "Participante actualizado."
        else: 
            sql = "INSERT INTO participantes (nombre, apellido, rut_o_id, fecha_nacimiento, genero, club_id) VALUES (?, ?, ?, ?, ?, ?)"
            params = (datos['nombre'], datos['apellido'], datos['rut_o_id'], datos['fecha_nacimiento'], 
                     datos['genero'], datos['club_id'])
            mensaje = "Participante agregado."
        cursor.execute(sql, params)
        if not participante_id: participante_id = cursor.lastrowid
        conn.commit()
        return participante_id, mensaje
    except sqlite3.IntegrityError: 
        return None, "Error: El RUT o ID del participante ya existe."
    finally:
        if conn: conn.close()

def eliminar_participante(participante_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM participantes WHERE id=?", (participante_id,))
        conn.commit()
        return True, "Participante eliminado."
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA CATEGORÍAS ---
def obtener_categorias():
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre_categoria, codigo_categoria, edad_min, edad_max, genero, 
                   tipo_embarcacion, distancia_km, numero_vueltas 
            FROM categorias 
            ORDER BY nombre_categoria
        """)
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def agregar_o_actualizar_categoria(datos, categoria_id=None):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        if categoria_id: 
            sql = """UPDATE categorias SET nombre_categoria=?, codigo_categoria=?, edad_min=?, edad_max=?, 
                    genero=?, tipo_embarcacion=?, distancia_km=?, numero_vueltas=? WHERE id=?"""
            params = (datos['nombre_categoria'], datos['codigo_categoria'], datos['edad_min'], 
                     datos['edad_max'], datos['genero'], datos['tipo_embarcacion'], 
                     datos['distancia_km'], datos['numero_vueltas'], categoria_id)
            mensaje = "Categoría actualizada."
        else: 
            sql = """INSERT INTO categorias (nombre_categoria, codigo_categoria, edad_min, edad_max, 
                    genero, tipo_embarcacion, distancia_km, numero_vueltas) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (datos['nombre_categoria'], datos['codigo_categoria'], datos['edad_min'], 
                     datos['edad_max'], datos['genero'], datos['tipo_embarcacion'], 
                     datos['distancia_km'], datos['numero_vueltas'])
            mensaje = "Categoría agregada."
        cursor.execute(sql, params)
        if not categoria_id: categoria_id = cursor.lastrowid
        conn.commit()
        return categoria_id, mensaje
    except sqlite3.IntegrityError: 
        return None, "Error: El código de la categoría ya existe."
    finally:
        if conn: conn.close()

def eliminar_categoria(categoria_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categorias WHERE id=?", (categoria_id,))
        conn.commit()
        return True, "Categoría eliminada."
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA INSCRIPCIONES ---
def inscribir_embarcacion(datos):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    sql = """INSERT INTO inscripciones 
            (evento_id, categoria_id, participante1_id, participante2_id, 
             participante3_id, participante4_id, numero_competidor) 
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
    params = (datos['evento_id'], datos['categoria_id'], datos['participante1_id'], 
             datos.get('participante2_id'), datos.get('participante3_id'), 
             datos.get('participante4_id'), datos['numero_competidor'])
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid, "Inscripción guardada."
    except sqlite3.IntegrityError: 
        return None, "Error: El número de competidor ya está en uso en esta categoría/evento."
    finally:
        if conn: conn.close()

def obtener_inscripciones_por_categoria(evento_id, categoria_id):
    conn = conectar_db()
    if not conn: return []
    sql = """
        SELECT 
            i.id, 
            i.numero_competidor,
            p1.apellido || ', ' || p1.nombre, p1.fecha_nacimiento, c1.nombre_club,
            p2.apellido || ', ' || p2.nombre, p2.fecha_nacimiento, c2.nombre_club,
            p3.apellido || ', ' || p3.nombre, p3.fecha_nacimiento, c3.nombre_club,
            p4.apellido || ', ' || p4.nombre, p4.fecha_nacimiento, c4.nombre_club,
            i.lugar_final, 
            i.tiempo_final, 
            i.estado
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
            i.lugar_final ASC, 
            i.tiempo_final ASC, 
            i.numero_competidor ASC
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id, categoria_id))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener inscripciones: {e}")
        return []
    finally:
        if conn: conn.close()

def eliminar_inscripcion(inscripcion_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inscripciones WHERE id=?", (inscripcion_id,))
        conn.commit()
        return True, "Inscripción eliminada."
    finally:
        if conn: conn.close()

def actualizar_resultado_inscripcion(inscripcion_id, tiempo_final, estado, tiempos_vueltas_json=None):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    sql = "UPDATE inscripciones SET tiempo_final = ?, estado = ?, tiempo_vueltas = ? WHERE id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (tiempo_final, estado, tiempos_vueltas_json, inscripcion_id))
        conn.commit()
        return True, "Resultado actualizado."
    finally:
        if conn: conn.close()

def recalcular_posiciones_categoria(evento_id, categoria_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM inscripciones 
            WHERE evento_id = ? AND categoria_id = ? 
            AND estado = 'Finalizado' AND tiempo_final IS NOT NULL AND tiempo_final != '' 
            ORDER BY tiempo_final ASC
        """, (evento_id, categoria_id))
        finalizados = cursor.fetchall()
        for i, (insc_id,) in enumerate(finalizados):
            lugar = i + 1
            cursor.execute("UPDATE inscripciones SET lugar_final = ? WHERE id = ?", (lugar, insc_id))
        cursor.execute("""
            UPDATE inscripciones SET lugar_final = NULL 
            WHERE evento_id = ? AND categoria_id = ? AND estado != 'Finalizado'
        """, (evento_id, categoria_id))
        conn.commit()
        return True, "Posiciones recalculadas."
    finally:
        if conn: conn.close()

# --- FUNCIONES DE PUNTUACIÓN Y RANKING ---
def calcular_puntuacion_clubes(evento_id, sistema_puntuacion):
    conn = conectar_db()
    if not conn: return []
    sql = """
        SELECT c.nombre_club, i.lugar_final 
        FROM inscripciones i 
        JOIN participantes p1 ON i.participante1_id = p1.id 
        JOIN clubes c ON p1.club_id = c.id 
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IS NOT NULL
    """
    puntuacion_por_club = {}
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()
        for nombre_club, lugar in resultados:
            puntos = sistema_puntuacion.get(lugar, 0)
            if nombre_club not in puntuacion_por_club: 
                puntuacion_por_club[nombre_club] = 0
            puntuacion_por_club[nombre_club] += puntos
        return sorted(puntuacion_por_club.items(), key=lambda item: item[1], reverse=True)
    finally:
        if conn: conn.close()

def calcular_ranking_medallas(evento_id):
    conn = conectar_db()
    if not conn: return []
    sql = """
        SELECT c.nombre_club, i.lugar_final 
        FROM inscripciones i 
        JOIN participantes p1 ON i.participante1_id = p1.id 
        JOIN clubes c ON p1.club_id = c.id 
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IN (1, 2, 3)
    """
    medallas_por_club = {}
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()
        for nombre_club, lugar in resultados:
            if nombre_club not in medallas_por_club: 
                medallas_por_club[nombre_club] = {'oro': 0, 'plata': 0, 'bronce': 0}
            if lugar == 1: 
                medallas_por_club[nombre_club]['oro'] += 1
            elif lugar == 2: 
                medallas_por_club[nombre_club]['plata'] += 1
            elif lugar == 3: 
                medallas_por_club[nombre_club]['bronce'] += 1
        
        lista_medallero = []
        for nombre, medallas in medallas_por_club.items(): 
            lista_medallero.append((nombre, medallas['oro'], medallas['plata'], medallas['bronce']))
        lista_medallero.sort(key=lambda item: (item[1], item[2], item[3]), reverse=True)
        return lista_medallero
    finally:
        if conn: conn.close()

# --- FUNCIONES PARA REPORTES ---
def obtener_evento_por_id(evento_id):
    """Obtiene información básica de un evento para reportes"""
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_evento FROM eventos WHERE id = ?", (evento_id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def obtener_categoria_por_id(categoria_id):
    """Obtiene información básica de una categoría para reportes"""
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_categoria, codigo_categoria FROM categorias WHERE id = ?", (categoria_id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def obtener_participantes_por_categoria(evento_id, categoria_id):
    """Obtiene participantes para listados de partida"""
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.nombre, p.apellido, c.nombre_club, i.numero_competidor
            FROM inscripciones i
            JOIN participantes p ON i.participante1_id = p.id
            LEFT JOIN clubes c ON p.club_id = c.id
            WHERE i.evento_id = ? AND i.categoria_id = ?
            ORDER BY i.numero_competidor
        """, (evento_id, categoria_id))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def obtener_resultados_por_categoria(evento_id, categoria_id):
    """Obtiene resultados finales por categoría"""
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.nombre, p.apellido, c.nombre_club, i.lugar_final, i.tiempo_final
            FROM inscripciones i
            JOIN participantes p ON i.participante1_id = p.id
            LEFT JOIN clubes c ON p.club_id = c.id
            WHERE i.evento_id = ? AND i.categoria_id = ? AND i.estado = 'Finalizado'
            ORDER BY i.lugar_final
        """, (evento_id, categoria_id))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def calcular_ranking_individual_puntos(evento_id, sistema_puntuacion):
    """Calcula ranking individual por puntos"""
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nombre, p.apellido, c.nombre_club, i.lugar_final
            FROM inscripciones i
            JOIN participantes p ON i.participante1_id = p.id
            LEFT JOIN clubes c ON p.club_id = c.id
            WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IS NOT NULL
            ORDER BY i.lugar_final
        """, (evento_id,))
        
        ranking = []
        for nombre, apellido, club, posicion in cursor.fetchall():
            puntos = sistema_puntuacion.get(posicion, 0)
            ranking.append((nombre, apellido, club, puntos))
        
        return sorted(ranking, key=lambda x: x[3], reverse=True)
    finally:
        if conn: conn.close()

def calcular_ranking_individual_medallas(evento_id):
    """Calcula ranking individual por medallas"""
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.nombre, p.apellido, c.nombre_club,
                SUM(CASE WHEN i.lugar_final = 1 THEN 1 ELSE 0 END) as oro,
                SUM(CASE WHEN i.lugar_final = 2 THEN 1 ELSE 0 END) as plata,
                SUM(CASE WHEN i.lugar_final = 3 THEN 1 ELSE 0 END) as bronce
            FROM inscripciones i
            JOIN participantes p ON i.participante1_id = p.id
            LEFT JOIN clubes c ON p.club_id = c.id
            WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IN (1, 2, 3)
            GROUP BY p.id
            ORDER BY oro DESC, plata DESC, bronce DESC
        """, (evento_id,))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

# --- FUNCIONES DE UTILIDAD ---
def obtener_siguiente_numero_competidor(evento_id, categoria_id):
    conn = conectar_db()
    if not conn: return 1
    sql = "SELECT MAX(numero_competidor) FROM inscripciones WHERE evento_id = ? AND categoria_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id, categoria_id))
        resultado = cursor.fetchone()
        return (resultado[0] or 0) + 1
    finally:
        if conn: conn.close()

def obtener_inscripciones_para_exportar(evento_id):
    conn = conectar_db()
    if not conn: return []
    sql = """
        SELECT 
            cat.codigo_categoria, i.numero_competidor,
            p1.nombre || ' ' || p1.apellido, p1.rut_o_id, p1.fecha_nacimiento, p1.genero, c1.nombre_club,
            p2.nombre || ' ' || p2.apellido, p2.rut_o_id, p2.fecha_nacimiento, p2.genero, c2.nombre_club,
            p3.nombre || ' ' || p3.apellido, p3.rut_o_id, p3.fecha_nacimiento, p3.genero, c3.nombre_club,
            p4.nombre || ' ' || p4.apellido, p4.rut_o_id, p4.fecha_nacimiento, p4.genero, c4.nombre_club
        FROM inscripciones i
        JOIN categorias cat ON i.categoria_id = cat.id
        JOIN participantes p1 ON i.participante1_id = p1.id 
        LEFT JOIN clubes c1 ON p1.club_id = c1.id
        LEFT JOIN participantes p2 ON i.participante2_id = p2.id 
        LEFT JOIN clubes c2 ON p2.club_id = c2.id
        LEFT JOIN participantes p3 ON i.participante3_id = p3.id 
        LEFT JOIN clubes c3 ON p3.club_id = c3.id
        LEFT JOIN participantes p4 ON i.participante4_id = p4.id 
        LEFT JOIN clubes c4 ON p4.club_id = c4.id
        WHERE i.evento_id = ? 
        ORDER BY cat.id, i.numero_competidor
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

# --- FUNCIONES CRUD PARA PATROCINADORES ---
def agregar_sponsor(nombre, logo_path, evento_id):
    conn = conectar_db()
    if not conn: return None, "No se pudo conectar a la base de datos."
    sql = "INSERT INTO sponsors (nombre_sponsor, logo_path, evento_id) VALUES (?, ?, ?)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (nombre, logo_path, evento_id))
        conn.commit()
        return cursor.lastrowid, "Patrocinador agregado."
    finally:
        if conn: conn.close()

def obtener_sponsors_por_evento(evento_id):
    conn = conectar_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre_sponsor, logo_path 
            FROM sponsors 
            WHERE evento_id = ? 
            ORDER BY nombre_sponsor
        """, (evento_id,))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def eliminar_sponsor(sponsor_id):
    conn = conectar_db()
    if not conn: return False, "No se pudo conectar a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
        conn.commit()
        return True, "Patrocinador eliminado."
    finally:
        if conn: conn.close()
        
# Añade estas funciones a tu database_maraton.py existente

def verificar_numero_competidor(evento_id, categoria_id, numero_competidor, excluir_inscripcion_id=None):
    """Verifica si un número de competidor ya está en uso en una categoría"""
    conn = conectar_db()
    if not conn: return True  # Por defecto asumir que está en uso si hay error
    
    try:
        cursor = conn.cursor()
        if excluir_inscripcion_id:
            cursor.execute("""
                SELECT id FROM inscripciones 
                WHERE evento_id=? AND categoria_id=? AND numero_competidor=? AND id!=?
            """, (evento_id, categoria_id, numero_competidor, excluir_inscripcion_id))
        else:
            cursor.execute("""
                SELECT id FROM inscripciones 
                WHERE evento_id=? AND categoria_id=? AND numero_competidor=?
            """, (evento_id, categoria_id, numero_competidor))
        
        return cursor.fetchone() is not None
    finally:
        conn.close()

def actualizar_numero_competidor(inscripcion_id, nuevo_numero):
    """Actualiza el número de competidor de una inscripción"""
    conn = conectar_db()
    if not conn: return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inscripciones 
            SET numero_competidor=? 
            WHERE id=?
        """, (nuevo_numero, inscripcion_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()