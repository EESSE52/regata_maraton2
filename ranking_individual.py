# ranking_individual.py
# Módulo dedicado para calcular los rankings individuales de deportistas.

import sqlite3
import database_maraton as db

def calcular_puntuacion_deportistas(evento_id, sistema_puntuacion):
    """Calcula la puntuación total para cada deportista en un evento dado."""
    conn = db.conectar_db()
    if not conn: return []
    
    sql = """
        SELECT i.lugar_final, i.participante1_id, i.participante2_id, i.participante3_id, i.participante4_id
        FROM inscripciones i
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IS NOT NULL
    """
    
    puntuacion_por_deportista = {}
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()
        
        for lugar, p1_id, p2_id, p3_id, p4_id in resultados:
            puntos = sistema_puntuacion.get(lugar, 0)
            if puntos == 0: continue
            
            participantes_en_bote = [p_id for p_id in [p1_id, p2_id, p3_id, p4_id] if p_id is not None]
            
            for p_id in participantes_en_bote:
                if p_id not in puntuacion_por_deportista:
                    cursor.execute("SELECT p.apellido || ', ' || p.nombre, c.nombre_club FROM participantes p LEFT JOIN clubes c ON p.club_id = c.id WHERE p.id = ?", (p_id,))
                    info = cursor.fetchone()
                    if info:
                        puntuacion_por_deportista[p_id] = {'nombre': info[0], 'club': info[1], 'puntos': 0}
                
                if p_id in puntuacion_por_deportista:
                    puntuacion_por_deportista[p_id]['puntos'] += puntos

        lista_ranking = list(puntuacion_por_deportista.values())
        lista_ranking.sort(key=lambda item: item['puntos'], reverse=True)
        return lista_ranking

    except sqlite3.Error as e:
        print(f"Error al calcular la puntuación por deportistas: {e}")
        return []
    finally:
        if conn: conn.close()

def calcular_ranking_medallas_deportistas(evento_id):
    """Calcula el medallero para cada deportista en un evento."""
    conn = db.conectar_db()
    if not conn: return []

    sql = """
        SELECT i.lugar_final, i.participante1_id, i.participante2_id, i.participante3_id, i.participante4_id
        FROM inscripciones i
        WHERE i.evento_id = ? AND i.estado = 'Finalizado' AND i.lugar_final IN (1, 2, 3)
    """
    
    medallas_por_deportista = {}
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (evento_id,))
        resultados = cursor.fetchall()

        for lugar, p1_id, p2_id, p3_id, p4_id in resultados:
            participantes_en_bote = [p_id for p_id in [p1_id, p2_id, p3_id, p4_id] if p_id is not None]
            
            for p_id in participantes_en_bote:
                if p_id not in medallas_por_deportista:
                    cursor.execute("SELECT p.apellido || ', ' || p.nombre, c.nombre_club FROM participantes p LEFT JOIN clubes c ON p.club_id = c.id WHERE p.id = ?", (p_id,))
                    info = cursor.fetchone()
                    if info:
                        medallas_por_deportista[p_id] = {'nombre': info[0], 'club': info[1], 'oro': 0, 'plata': 0, 'bronce': 0}

                if p_id in medallas_por_deportista:
                    if lugar == 1: medallas_por_deportista[p_id]['oro'] += 1
                    elif lugar == 2: medallas_por_deportista[p_id]['plata'] += 1
                    elif lugar == 3: medallas_por_deportista[p_id]['bronce'] += 1
        
        lista_medallero = list(medallas_por_deportista.values())
        lista_medallero.sort(key=lambda item: (item['oro'], item['plata'], item['bronce']), reverse=True)
        return lista_medallero

    except sqlite3.Error as e:
        print(f"Error al calcular el ranking de medallas de deportistas: {e}")
        return []
    finally:
        if conn: conn.close()