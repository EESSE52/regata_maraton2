# generador_pdf_reportes.py
# Módulo para crear reportes en PDF y PNG con el mismo formato visual
# Versión completa con todas las funciones de generación

import datetime
import os
import base64
from PySide6.QtGui import QTextDocument, QImage, QPainter
from PySide6.QtCore import QUrl, QSize, QBuffer
import database_maraton as db
import ranking_individual as ranking_ind
from utils_maraton import resource_path

def image_to_base64(path):
    """Convierte una imagen en una cadena base64 para embeberla en HTML."""
    if not path or not os.path.exists(path): return ""
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        ext = os.path.splitext(path)[1].lower()
        mime_type = f"image/{ext[1:]}" if ext in ['.png', '.jpg', '.jpeg', '.gif'] else "image/png"
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error convirtiendo imagen a base64: {e}")
        return ""

def crear_documento_base(titulo_reporte, nombre_evento, fecha_evento, logo_path):
    """Crea la cabecera y el estilo base para todos los reportes."""
    logo_src = image_to_base64(logo_path)
    
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset='UTF-8'>
    <style>
        body {{ font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; font-size: 9pt; }}
        @page {{ margin: 2.5cm; }}
        .main-content {{ margin: 0 auto; max-width: 18cm; }}
        .header-container {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #3949ab; padding-bottom: 10px; margin-bottom: 20px; }}
        .logo {{ max-width: 20px; max-height: 20px; }}
        .event-details {{ text-align: right; }}
        .event-details h1 {{ margin: 0; font-size: 18pt; color: #3949ab; }}
        .event-details h2 {{ margin: 0; font-size: 12pt; font-weight: normal; color: #333; }}
        .report-title {{ text-align: center; font-size: 14pt; font-weight: bold; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; page-break-inside: auto; }}
        tr {{ page-break-inside: avoid; page-break-after: auto; }}
        th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; vertical-align: top; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .center {{ text-align: center; }}
        .rank {{ width: 5%; font-weight: bold; font-size: 11pt; text-align: center; vertical-align: middle; }}
        .lane {{ width: 5%; text-align: center; vertical-align: middle; }}
        .boat {{ width: 50%; }}
        .time {{ width: 15%; text-align: center; vertical-align: middle; }}
        .boat-details p {{ margin: 0; padding: 0; line-height: 1.2; }}
        .boat-details .club {{ font-weight: bold; font-size: 10pt; }}
        .boat-details .participant {{ font-size: 9pt; }}
        .footer {{ text-align: center; font-size: 8pt; color: #888; border-top: 1px solid #ccc; padding-top: 5px; margin-top: 30px; page-break-inside: avoid; }}
        .sponsors-title {{ text-align: center; font-size: 10pt; color: #555; margin-bottom: 10px; }}
        .sponsors-container {{ display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 20px; padding: 10px 0; margin-bottom: 10px; }}
        .sponsor-logo {{ max-height: 25px; max-width: 100px; object-fit: contain; }}
    </style>
    </head><body>
    <div class="main-content">
        <div class="header-container">
            <div><img src="{logo_src}" class="logo" alt="Logo"></div>
            <div class="event-details"><h1>{nombre_evento}</h1><h2>{fecha_evento}</h2></div>
        </div>
        <div class="report-title">{titulo_reporte}</div>
    """
    return html

def finalizar_documento_html(html, sponsor_logo_paths):
    """Añade el pie de página con patrocinadores y cierra las etiquetas HTML."""
    fecha_generacion = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    sponsors_html = ""
    if sponsor_logo_paths:
        sponsors_html += "<div class='sponsors-title'>Auspician:</div><div class='sponsors-container'>"
        for sp_logo_path in sponsor_logo_paths:
            sp_logo_src = image_to_base64(sp_logo_path)
            if sp_logo_src:
                sponsors_html += f'<img src="{sp_logo_src}" class="sponsor-logo">'
        sponsors_html += "</div>"

    html += f"""
            <div class="footer">
                {sponsors_html}
                <div class="footer-text">Reporte generado el {fecha_generacion} por Gestor de Regatas.</div>
            </div>
        </div> 
    </body></html>"""
    return html

def format_participant(nombre_completo, fecha_nac):
    if not nombre_completo or nombre_completo.strip() == ',': return ""
    try:
        ano_nac = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").year
        return f'<p class="participant">{nombre_completo} ({ano_nac})</p>'
    except (ValueError, TypeError):
        return f'<p class="participant">{nombre_completo}</p>'

def document_to_png(doc, output_path=None):
    """
    Convierte un QTextDocument a imagen PNG.
    Si se proporciona output_path, guarda la imagen en ese archivo.
    Retorna los bytes de la imagen PNG si output_path es None.
    """
    # Configurar el tamaño del documento para renderizado
    margin = 50  # margen en píxeles
    doc_width = int(doc.size().width()) + 2 * margin
    doc_height = int(doc.size().height()) + 2 * margin
    
    # Crear imagen con fondo blanco
    image = QImage(QSize(doc_width, doc_height), QImage.Format_ARGB32)
    image.fill(0xFFFFFFFF)  # fondo blanco
    
    # Renderizar el documento en la imagen
    painter = QPainter(image)
    painter.translate(margin, margin)
    doc.drawContents(painter)
    painter.end()
    
    if output_path:
        image.save(output_path, "PNG")
        return True
    else:
        # Retornar los bytes de la imagen
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        image.save(buffer, "PNG")
        return buffer.data()

def generar_reporte_como_png(doc, output_path):
    """Guarda un QTextDocument como archivo PNG."""
    return document_to_png(doc, output_path)

def crear_start_list(evento_id, categoria_id, logo_path, sponsor_logo_paths):
    """Genera el Listado de Partida con el formato: Nº, Nombre, Año Nac., Club."""
    evento_info = db.obtener_info_evento(evento_id)
    categoria_info = db.obtener_info_categoria(categoria_id)
    if not evento_info or not categoria_info: return None, None
    nombre_evento, fecha_evento, nombre_categoria = evento_info[1], evento_info[2], categoria_info[1]
    
    html = crear_documento_base(f"Listado de Partida - {nombre_categoria}", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class="center" style="width:10%;">Nº</th><th style="width:40%;">Nombre Participante</th><th class="center" style="width:15%;">Año Nac.</th><th style="width:35%;">Club</th></tr></thead><tbody>"""
    
    inscripciones = db.obtener_inscripciones_por_categoria(evento_id, categoria_id)
    for insc in inscripciones:
        numero = insc[1]
        
        # Procesar Participante 1
        nombre_p1 = insc[2]
        try: ano_p1 = datetime.datetime.strptime(insc[3], "%Y-%m-%d").year if insc[3] else ""
        except (ValueError, TypeError): ano_p1 = ""
        club_p1 = insc[4] or ""
        html += f"""<tr><td class="center" rowspan="1">{numero}</td><td>{nombre_p1}</td><td class="center">{ano_p1}</td><td>{club_p1}</td></tr>"""
        
        # Procesar Participantes 2, 3 y 4 en filas adicionales si existen
        if insc[5] and insc[5].strip() != ',':
            nombre_p2 = insc[5]
            try: ano_p2 = datetime.datetime.strptime(insc[6], "%Y-%m-%d").year if insc[6] else ""
            except (ValueError, TypeError): ano_p2 = ""
            club_p2 = insc[7] or ""
            html += f"""<tr><td></td><td>{nombre_p2}</td><td class="center">{ano_p2}</td><td>{club_p2}</td></tr>"""
            
        if insc[8] and insc[8].strip() != ',':
            nombre_p3 = insc[8]
            try: ano_p3 = datetime.datetime.strptime(insc[9], "%Y-%m-%d").year if insc[9] else ""
            except (ValueError, TypeError): ano_p3 = ""
            club_p3 = insc[10] or ""
            html += f"""<tr><td></td><td>{nombre_p3}</td><td class="center">{ano_p3}</td><td>{club_p3}</td></tr>"""

        if insc[11] and insc[11].strip() != ',':
            nombre_p4 = insc[11]
            try: ano_p4 = datetime.datetime.strptime(insc[12], "%Y-%m-%d").year if insc[12] else ""
            except (ValueError, TypeError): ano_p4 = ""
            club_p4 = insc[13] or ""
            html += f"""<tr><td></td><td>{nombre_p4}</td><td class="center">{ano_p4}</td><td>{club_p4}</td></tr>"""

    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_resultados_categoria(evento_id, categoria_id, logo_path, sponsor_logo_paths):
    """Genera los Resultados Finales con el formato: Lugar, Nº, Embarcación (con Club y Participantes), Tiempo, Estado."""
    evento_info = db.obtener_info_evento(evento_id)
    categoria_info = db.obtener_info_categoria(categoria_id)
    if not evento_info or not categoria_info: return None, None
    nombre_evento, fecha_evento, nombre_categoria = evento_info[1], evento_info[2], categoria_info[1]
    
    html = crear_documento_base(f"Resultados Finales - {nombre_categoria}", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class="rank">Lugar</th><th class="lane">Nº</th><th class="boat">Embarcación</th><th class="time">Tiempo Final</th><th class="time">Estado</th></tr></thead><tbody>"""
    
    inscripciones = db.obtener_inscripciones_por_categoria(evento_id, categoria_id)
    for insc in inscripciones:
        lugar = str(insc[14]) if insc[14] else "-"
        numero = insc[1]
        tiempo = insc[15] or "-"
        estado = insc[16] or "Inscrito"
        
        boat_html = f'<div class="boat-details"><p class="club">{insc[4] or "S/C"}</p>'
        boat_html += format_participant(insc[2], insc[3])
        if insc[5] and insc[5].strip() != ',': boat_html += format_participant(insc[5], insc[6])
        if insc[8] and insc[8].strip() != ',': boat_html += format_participant(insc[8], insc[9])
        if insc[11] and insc[11].strip() != ',': boat_html += format_participant(insc[11], insc[12])
        boat_html += '</div>'

        html += f"""<tr><td class="rank">{lugar}</td><td class="lane">{numero}</td><td class="boat">{boat_html}</td><td class="time">{tiempo}</td><td class="time">{estado}</td></tr>"""
    
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_puntuacion_general(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el documento para la puntuación general y el medallero."""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Clasificación General por Clubes", nombre_evento, fecha_evento, logo_path)

    html += "<h3>Ranking por Puntos</h3><table><thead><tr><th class='center'>Lugar</th><th>Club</th><th class='center'>Puntuación Total</th></tr></thead><tbody>"
    puntuacion = db.calcular_puntuacion_clubes(evento_id, sistema_puntuacion)
    for i, (club, puntos) in enumerate(puntuacion):
        html += f"""<tr><td class="center">{i+1}</td><td>{club}</td><td class="center">{puntos}</td></tr>"""
    html += "</tbody></table><br><br>"

    html += "<h3>Ranking por Medallas (Medallero)</h3><table><thead><tr><th class='center'>Lugar</th><th>Club</th><th class='center'>🥇 Oro</th><th class='center'>🥈 Plata</th><th class='center'>🥉 Bronce</th></tr></thead><tbody>"
    medallero = db.calcular_ranking_medallas(evento_id)
    for i, (club, oro, plata, bronce) in enumerate(medallero):
        html += f"""<tr><td class="center">{i+1}</td><td>{club}</td><td class="center">{oro}</td><td class="center">{plata}</td><td class="center">{bronce}</td></tr>"""
    
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_resultados_completos(evento_id, logo_path, sponsor_logo_paths):
    """Genera un reporte con los resultados de todas las categorías."""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Resultados Completos del Evento", nombre_evento, fecha_evento, logo_path)
    
    categorias = db.obtener_categorias()
    for cat_id, nombre_categoria, *_ in categorias:
        inscripciones = db.obtener_inscripciones_por_categoria(evento_id, cat_id)
        if not inscripciones: continue

        html += f"<h3 style='page-break-before: always;'>Resultados - {nombre_categoria}</h3>"
        html += """<table><thead><tr><th class="rank">Lugar</th><th class="lane">Nº</th><th class="boat">Embarcación</th><th class="time">Tiempo Final</th><th class="time">Estado</th></tr></thead><tbody>"""
        
        for insc in inscripciones:
            lugar = str(insc[14]) if insc[14] else "-"
            numero = insc[1]
            tiempo = insc[15] or "-"
            estado = insc[16] or "Inscrito"
            boat_html = f'<div class="boat-details"><p class="club">{insc[4] or "S/C"}</p>'
            boat_html += format_participant(insc[2], insc[3])
            if insc[5] and insc[5].strip() != ',': boat_html += format_participant(insc[5], insc[6])
            if insc[8] and insc[8].strip() != ',': boat_html += format_participant(insc[8], insc[9])
            if insc[11] and insc[11].strip() != ',': boat_html += format_participant(insc[11], insc[12])
            boat_html += '</div>'
            html += f"""<tr><td class="rank">{lugar}</td><td class="lane">{numero}</td><td class="boat">{boat_html}</td><td class="time">{tiempo}</td><td class="time">{estado}</td></tr>"""
        html += "</tbody></table>"

    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_ranking_deportistas_puntos(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el ranking individual de deportistas por puntos."""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Ranking Individual por Puntos", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class='center'>Lugar</th><th>Deportista</th><th>Club</th><th class='center'>Puntos</th></tr></thead><tbody>"""
    
    ranking = ranking_ind.calcular_puntuacion_deportistas(evento_id, sistema_puntuacion)
    for i, data in enumerate(ranking):
        html += f"""<tr><td class="center">{i+1}</td><td>{data['nombre']}</td><td>{data['club']}</td><td class="center">{data['puntos']}</td></tr>"""
    
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_ranking_deportistas_medallas(evento_id, logo_path, sponsor_logo_paths):
    """Genera el ranking individual de deportistas por medallas."""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Ranking Individual por Medallas", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class='center'>Lugar</th><th>Deportista</th><th>Club</th><th class='center'>🥇</th><th class='center'>🥈</th><th class='center'>🥉</th></tr></thead><tbody>"""
    
    medallero = ranking_ind.calcular_ranking_medallas_deportistas(evento_id)
    for i, data in enumerate(medallero):
        html += f"""<tr><td class="center">{i+1}</td><td>{data['nombre']}</td><td>{data['club']}</td><td class="center">{data['oro']}</td><td class="center">{data['plata']}</td><td class="center">{data['bronce']}</td></tr>"""
    
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument()
    doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes