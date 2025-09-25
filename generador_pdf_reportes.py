# generador_pdf_reportes.py
# CORREGIDO: Todas las funciones de reporte están unificadas a 4 argumentos
# para prevenir el error de desplazamiento de la lista 'sistema_puntuacion'.

import datetime
import os
import base64
from PySide6.QtGui import QTextDocument, QImage, QPainter
from PySide6.QtCore import QUrl, QSize, QBuffer
import database_maraton as db
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
    
    # CORRECCIÓN DE RUTA DE LOGO: Se usa resource_path si se pasa solo 'logo.png'
    # Esta lógica es correcta para garantizar que logo_path es un string.
    if logo_path == 'logo.png':
        ruta_logo_real = resource_path('logo.png')
    else:
        # Añadido chequeo de tipo para atrapar el error si persiste.
        if not isinstance(logo_path, str):
             print(f"ERROR DE TIPO: logo_path es {type(logo_path)}. Se esperaba un string.")
             return "" # Retorna un string vacío si falla, o se lanza la excepción.
        ruta_logo_real = logo_path
        
    logo_src = image_to_base64(ruta_logo_real)
    
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
        .club-logo {{ max-height: 14px; vertical-align: middle; margin-right: 5px; }}
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
    """Convierte un QTextDocument a imagen PNG."""
    margin = 50
    doc_width = int(doc.size().width()) + 2 * margin
    doc_height = int(doc.size().height()) + 2 * margin
    
    image = QImage(QSize(doc_width, doc_height), QImage.Format_ARGB32)
    image.fill(0xFFFFFFFF)
    
    painter = QPainter(image)
    painter.translate(margin, margin)
    doc.drawContents(painter)
    painter.end()
    
    if output_path:
        image.save(output_path, "PNG")
        return True
    else:
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        image.save(buffer, "PNG")
        return buffer.data()

# Se deja como 4 argumentos para consistencia, aunque sistema_puntuacion no se use
def crear_start_list(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el Listado de Partida."""
    # sistema_puntuacion se acepta y se ignora
    evento_info = db.obtener_info_evento(evento_id)
    categoria_info = db.obtener_info_categoria(categoria_id)
    if not evento_info or not categoria_info: return None, None
    nombre_evento, fecha_evento, nombre_categoria = evento_info[1], evento_info[2], categoria_info[1]
    
    html = crear_documento_base(f"Listado de Partida - {nombre_categoria}", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class="center" style="width:10%;">Nº</th><th style="width:40%;">Nombre Participante</th><th class="center" style="width:15%;">Año Nac.</th><th style="width:35%;">Club</th></tr></thead><tbody>"""
    
    inscripciones = db.obtener_inscripciones_por_categoria(evento_id, categoria_id)
    for insc in inscripciones:
        _, numero, p1_n, p1_fn, p1_c, p1_l, p2_n, p2_fn, p2_c, p2_l, p3_n, p3_fn, p3_c, p3_l, p4_n, p4_fn, p4_c, p4_l, *_ = insc
        
        try: ano_p1 = datetime.datetime.strptime(p1_fn, "%Y-%m-%d").year if p1_fn else ""
        except (ValueError, TypeError): ano_p1 = ""
        logo1_b64 = image_to_base64(p1_l); logo1_html = f'<img src="{logo1_b64}" class="club-logo">' if logo1_b64 else ''
        html += f"""<tr><td class="center" rowspan="1">{numero}</td><td>{p1_n}</td><td class="center">{ano_p1}</td><td>{logo1_html}{p1_c or ""}</td></tr>"""
        
        if p2_n and p2_n.strip() != ',':
            try: ano_p2 = datetime.datetime.strptime(p2_fn, "%Y-%m-%d").year if p2_fn else ""
            except (ValueError, TypeError): ano_p2 = ""
            logo2_b64 = image_to_base64(p2_l); logo2_html = f'<img src="{logo2_b64}" class="club-logo">' if logo2_b64 else ''
            html += f"""<tr><td></td><td>{p2_n}</td><td class="center">{ano_p2}</td><td>{logo2_html}{p2_c or ""}</td></tr>"""
        
        if p3_n and p3_n.strip() != ',':
            try: ano_p3 = datetime.datetime.strptime(p3_fn, "%Y-%m-%d").year if p3_fn else ""
            except (ValueError, TypeError): ano_p3 = ""
            logo3_b64 = image_to_base64(p3_l); logo3_html = f'<img src="{logo3_b64}" class="club-logo">' if logo3_b64 else ''
            html += f"""<tr><td></td><td>{p3_n}</td><td class="center">{ano_p3}</td><td>{logo3_html}{p3_c or ""}</td></tr>"""

        if p4_n and p4_n.strip() != ',':
            try: ano_p4 = datetime.datetime.strptime(p4_fn, "%Y-%m-%d").year if p4_fn else ""
            except (ValueError, TypeError): ano_p4 = ""
            logo4_b64 = image_to_base64(p4_l); logo4_html = f'<img src="{logo4_b64}" class="club-logo">' if logo4_b64 else ''
            html += f"""<tr><td></td><td>{p4_n}</td><td class="center">{ano_p4}</td><td>{logo4_html}{p4_c or ""}</td></tr>"""
            
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_resultados_categoria(evento_id, categoria_id, logo_path, sponsor_logo_paths):
    """Genera los Resultados Finales de una categoría."""
    evento_info = db.obtener_info_evento(evento_id)
    categoria_info = db.obtener_info_categoria(categoria_id)
    if not evento_info or not categoria_info: return None, None
    nombre_evento, fecha_evento, nombre_categoria = evento_info[1], evento_info[2], categoria_info[1]
    
    html = crear_documento_base(f"Resultados Finales - {nombre_categoria}", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class="rank">Lugar</th><th class="lane">Nº</th><th class="boat">Embarcación</th><th class="time">Tiempo Final</th><th class="time">Estado</th></tr></thead><tbody>"""
    
    inscripciones = db.obtener_inscripciones_por_categoria(evento_id, categoria_id)
    for insc in inscripciones:
        _, numero, p1_n, p1_fn, p1_c, p1_l, p2_n, p2_fn, p2_c, p2_l, p3_n, p3_fn, p3_c, p3_l, p4_n, p4_fn, p4_c, p4_l, lugar, tiempo, estado, _ = insc

        logo1_b64 = image_to_base64(p1_l)
        logo1_html = f'<img src="{logo1_b64}" class="club-logo">' if logo1_b64 else ''
        
        boat_html = f'<div class="boat-details"><p class="club">{logo1_html}{p1_c or "S/C"}</p>'
        boat_html += format_participant(p1_n, p1_fn)
        if p2_n and p2_n.strip() != ',': boat_html += format_participant(p2_n, p2_fn)
        if p3_n and p3_n.strip() != ',': boat_html += format_participant(p3_n, p3_fn)
        if p4_n and p4_n.strip() != ',': boat_html += format_participant(p4_n, p4_fn)
        boat_html += '</div>'
        
        html += f"""<tr><td class="rank">{lugar or '-'}</td><td class="lane">{numero}</td><td class="boat">{boat_html}</td><td class="time">{tiempo or '-'}</td><td class="time">{estado or 'Inscrito'}</td></tr>"""
    
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes


def crear_ranking_puntuacion_pdf(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el ranking de puntos por club. (4 argumentos, usa sistema_puntuacion)"""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Clasificación General por Puntos", nombre_evento, fecha_evento, logo_path)
    html += "<table><thead><tr><th class='center'>Lugar</th><th>Club</th><th class='center'>Puntuación Total</th></tr></thead><tbody>"
    
    puntuacion = db.calcular_puntuacion_clubes(evento_id, sistema_puntuacion)
    for i, (club, logo, puntos) in enumerate(puntuacion):
        logo_b64 = image_to_base64(logo)
        logo_html = f'<img src="{logo_b64}" class="club-logo">' if logo_b64 else ''
        html += f"""<tr><td class="center">{i+1}</td><td>{logo_html}{club}</td><td class="center">{puntos}</td></tr>"""
        
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes


def crear_ranking_medallas_pdf(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el ranking de medallas por club (Medallero). (4 argumentos, IGNORA sistema_puntuacion)"""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    html = crear_documento_base("Medallero por Club", nombre_evento, fecha_evento, logo_path)
    html += "<table><thead><tr><th class='center'>Lugar</th><th>Club</th><th class='center'>🥇 Oro</th><th class='center'>🥈 Plata</th><th class='center'>🥉 Bronce</th></tr></thead><tbody>"
    
    medallero = db.calcular_ranking_medallas(evento_id)
    for i, (club, logo, oro, plata, bronce) in enumerate(medallero):
        logo_b64 = image_to_base64(logo)
        logo_html = f'<img src="{logo_b64}" class="club-logo">' if logo_b64 else ''
        html += f"""<tr><td class="center">{i+1}</td><td>{logo_html}{club}</td><td class="center">{oro}</td><td class="center">{plata}</td><td class="center">{bronce}</td></tr>"""
        
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes


def crear_resultados_completos(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera un reporte con los resultados de todas las categorías. (4 argumentos, IGNORA sistema_puntuacion)"""
    # sistema_puntuacion se acepta y se ignora
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
            _, numero, p1_n, p1_fn, p1_c, p1_l, p2_n, p2_fn, _, _, p3_n, p3_fn, _, _, p4_n, p4_fn, _, _, lugar, tiempo, estado, _ = insc
            logo1_b64 = image_to_base64(p1_l)
            logo1_html = f'<img src="{logo1_b64}" class="club-logo">' if logo1_b64 else ''
            boat_html = f'<div class="boat-details"><p class="club">{logo1_html}{p1_c or "S/C"}</p>'
            boat_html += format_participant(p1_n, p1_fn)
            if p2_n and p2_n.strip() != ',': boat_html += format_participant(p2_n, p2_fn)
            if p3_n and p3_n.strip() != ',': boat_html += format_participant(p3_n, p3_fn)
            if p4_n and p4_n.strip() != ',': boat_html += format_participant(p4_n, p4_fn)
            boat_html += '</div>'
            html += f"""<tr><td class="rank">{lugar or '-'}</td><td class="lane">{numero}</td><td class="boat">{boat_html}</td><td class="time">{tiempo or '-'}</td><td class="time">{estado or 'Inscrito'}</td></tr>"""
        html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_ranking_deportistas_puntos(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el ranking individual de deportistas por puntos. (4 argumentos, usa sistema_puntuacion)"""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    html = crear_documento_base("Ranking Individual por Puntos", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class='center'>Lugar</th><th>Deportista</th><th>Club</th><th class='center'>Puntos</th></tr></thead><tbody>"""
    ranking = db.calcular_puntuacion_deportistas(evento_id, sistema_puntuacion)
    for i, data in enumerate(ranking):
        logo_b64 = image_to_base64(data.get('logo_path'))
        logo_html = f'<img src="{logo_b64}" class="club-logo">' if logo_b64 else ''
        html += f"""<tr><td class="center">{i+1}</td><td>{data['nombre']}</td><td>{logo_html}{data['club']}</td><td class="center">{data['puntos']}</td></tr>"""
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_ranking_deportistas_medallas(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el ranking individual de deportistas por medallas. (4 argumentos, IGNORA sistema_puntuacion)"""
    # sistema_puntuacion se acepta y se ignora
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    html = crear_documento_base("Ranking Individual por Medallas", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class='center'>Lugar</th><th>Deportista</th><th>Club</th><th class='center'>🥇</th><th class='center'>🥈</th><th class='center'>🥉</th></tr></thead><tbody>"""
    medallero = db.calcular_ranking_medallas_deportistas(evento_id)
    for i, data in enumerate(medallero):
        logo_b64 = image_to_base64(data.get('logo_path'))
        logo_html = f'<img src="{logo_b64}" class="club-logo">' if logo_b64 else ''
        html += f"""<tr><td class="center">{i+1}</td><td>{data['nombre']}</td><td>{logo_html}{data['club']}</td><td class="center">{data['oro']}</td><td class="center">{data['plata']}</td><td class="center">{data['bronce']}</td></tr>"""
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes

def crear_programa_evento_pdf(evento_id, sistema_puntuacion, logo_path, sponsor_logo_paths):
    """Genera el Programa Oficial del Evento con horarios. (4 argumentos, IGNORA sistema_puntuacion)"""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return None, None
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    html = crear_documento_base("Programa Oficial de Regatas", nombre_evento, fecha_evento, logo_path)
    html += """<table><thead><tr><th class="center" style="width:20%;">Hora</th><th style="width:80%;">Categoría</th></tr></thead><tbody>"""
    programa = db.obtener_programa_pruebas(evento_id)
    for cat_id, nombre_cat, codigo_cat, hora in programa:
        html += f"""<tr><td class="center"><b>{hora or 'A definir'}</b></td><td>{nombre_cat} ({codigo_cat})</td></tr>"""
    html += "</tbody></table>"
    html = finalizar_documento_html(html, sponsor_logo_paths)
    doc = QTextDocument(); doc.setHtml(html)
    png_bytes = document_to_png(doc)
    return doc, png_bytes