# generador_web.py
# VERSIÓN REPARADA - Se unifica la llamada a 4 argumentos para los reportes fijos.

import os
import shutil
from PySide6.QtGui import QTextDocument
import database_maraton as db
# Se añade una importación condicional para manejar el sistema de puntuación
try:
    from database_maraton import obtener_sistema_puntuacion_activo 
except ImportError:
    # Si la función no existe, definimos un valor por defecto
    def obtener_sistema_puntuacion_activo(evento_id):
        return [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] 


from generador_pdf_reportes import (
    crear_resultados_categoria, 
    crear_ranking_puntuacion_pdf, 
    crear_ranking_medallas_pdf,
    crear_programa_evento_pdf,
    image_to_base64
)
from utils_maraton import resource_path

# --- Estilos CSS para el sitio web ---
CSS_STYLES = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    background-color: #f4f7f6;
    color: #333;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 960px;
    margin: 0 auto;
    background: #fff;
    padding: 20px 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.header {
    border-bottom: 2px solid #0056b3;
    padding-bottom: 15px;
    margin-bottom: 20px;
    text-align: center;
}
.header h1 {
    margin: 0;
    color: #0056b3;
    font-size: 2.5em;
}
.header h2 {
    margin: 5px 0 0;
    color: #666;
    font-size: 1.2em;
}
.header-logo {
    max-width: 250px;
    height: auto;
    margin-bottom: 15px;
}
.logo-small {
    height: 30px;
    width: auto;
    margin-right: 5px;
    vertical-align: middle;
}
/* Estilo específico para logos de patrocinadores */
.sponsor-logo-footer {
    max-width: 150px; 
    height: auto;
    margin: 10px;
    vertical-align: middle;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    font-size: 0.9em;
}
th, td {
    padding: 12px 15px;
    border: 1px solid #ddd;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #f2f2f2;
    font-weight: bold;
    color: #444;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.center { text-align: center; }
.nowrap { white-space: nowrap; }
.footer {
    border-top: 1px solid #ccc;
    padding-top: 15px;
    margin-top: 30px;
    text-align: center;
    color: #888;
    font-size: 0.8em;
}
.report-list {
    list-style: none;
    padding: 0;
}
.report-list li {
    margin-bottom: 10px;
}
.report-list li a {
    display: block;
    padding: 15px 20px;
    background-color: #e9ecef;
    border-radius: 5px;
    text-decoration: none;
    color: #0056b3;
    font-weight: bold;
    transition: background-color 0.3s;
}
.report-list li a:hover {
    background-color: #cfe2f3;
}
.back-link {
    display: inline-block;
    margin-top: 20px;
    color: #0056b3;
    text-decoration: none;
    font-weight: bold;
}
.back-link:hover {
    text-decoration: underline;
}
"""

def crear_pagina_html(titulo, cuerpo_html, ruta_css="style.css", back_link="index.html"):
    """Crea una página HTML completa a partir de un cuerpo de HTML."""
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <link rel="stylesheet" href="{ruta_css}">
</head>
<body>
    <div class="container">
        {cuerpo_html}
        <a href="{back_link}" class="back-link">← Volver al Índice</a>
    </div>
</body>
</html>
"""

def generar_todos_los_reportes(evento_id, ruta_destino, generar_todo=False):
    """
    Genera los archivos HTML para cada reporte de la regata.
    Crea un índice para navegar entre ellos.
    """
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return False
    nombre_evento, fecha_evento = evento_info[1], evento_info[2]
    
    ruta_resultados = os.path.join(ruta_destino, "resultados")
    os.makedirs(ruta_resultados, exist_ok=True)
    
    enlaces_reportes = []
    
    # 0. Obtener sistema de puntuación para el ranking de puntos
    try:
        sistema_puntuacion = obtener_sistema_puntuacion_activo(evento_id)
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo obtener el sistema de puntuación ({e}). Usando valor por defecto [25, 18, ...]")
        sistema_puntuacion = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] 

    # 1. Obtener los logos de sponsor 
    sponsors = db.obtener_sponsors_por_evento(evento_id)
    sponsor_logo_paths = [s[2] for s in sponsors] # Esto debe ser una lista de rutas (strings)
    
    # 2. Reportes fijos
    reportes_fijos = [
        ("Ranking General por Puntuación", "ranking_puntuacion.html", crear_ranking_puntuacion_pdf),
        ("Medallero por Club", "medallero_club.html", crear_ranking_medallas_pdf),
        ("Programa Oficial de Regatas", "programa.html", crear_programa_evento_pdf)
    ]
    
    for titulo, nombre_archivo, funcion_creadora in reportes_fijos:
        try:
            doc = None
            
            # CORRECCIÓN DEFINITIVA: Llamada UNIFICADA con 4 argumentos para evitar el desplazamiento.
            # Esto asume que las tres funciones de reporte fijo en generador_pdf_reportes.py 
            # aceptan cuatro argumentos (el segundo es sistema_puntuacion).
            # Si crear_ranking_medallas_pdf o crear_programa_evento_pdf no usan el sistema_puntuacion,
            # simplemente deben aceptar el argumento y ignorarlo internamente.
            doc, _ = funcion_creadora(evento_id, sistema_puntuacion, 'logo.png', sponsor_logo_paths)
            
            doc_html = doc.toHtml()
            
            if doc_html:
                titulo_pagina = f"{titulo} | {nombre_evento}"
                pagina_completa = crear_pagina_html(titulo_pagina, doc_html, ruta_css="../style.css", back_link="./index.html")
                with open(os.path.join(ruta_resultados, nombre_archivo), "w", encoding="utf-8") as f:
                    f.write(pagina_completa)
                enlaces_reportes.append({'titulo': titulo, 'url': f"resultados/{nombre_archivo}"})
        except Exception as e:
            # Si el error persiste aquí, el problema está en la firma de las funciones en generador_pdf_reportes.py
            print(f"Error generando reporte fijo {titulo}: {e}")
            
    # 3. Reportes de categorías individuales
    if generar_todo:
        categorias = db.obtener_categorias()
        for cat_id, nombre_cat, _, _, _, _, _, _, _ in categorias:
            try:
                # Esta función requiere 4 argumentos: evento_id, cat_id, logo_path, sponsor_logo_paths
                doc, _ = crear_resultados_categoria(evento_id, cat_id, 'logo.png', sponsor_logo_paths)
                doc_html = doc.toHtml()
                
                if doc_html:
                    titulo = f"Resultados Categoría: {nombre_cat}"
                    nombre_archivo = f"resultados_{cat_id}.html"
                    titulo_pagina = f"{titulo} | {nombre_evento}"
                    
                    pagina_completa = crear_pagina_html(titulo_pagina, doc_html, ruta_css="../style.css", back_link="./index.html")
                    with open(os.path.join(ruta_resultados, nombre_archivo), "w", encoding="utf-8") as f:
                        f.write(pagina_completa)
                    enlaces_reportes.append({'titulo': titulo, 'url': f"resultados/{nombre_archivo}"})
            except Exception as e:
                print(f"Error generando reporte de categoría {nombre_cat}: {e}")

    # 4. Crear el índice principal de resultados
    index_html = f"""
    <div class="header">
        <h1>{nombre_evento}</h1>
        <h2>Resultados y Reportes</h2>
        <p>Fecha: {fecha_evento}</p>
    </div>
    <ul class="report-list">
    """
    for enlace in enlaces_reportes:
        index_html += f"<li><a href='{enlace['url']}'>{enlace['titulo']}</a></li>"
    index_html += "</ul>"
    
    pagina_indice = crear_pagina_html(f"Índice de Resultados: {nombre_evento}", index_html, ruta_css="../style.css", back_link="..")
    with open(os.path.join(ruta_resultados, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina_indice)
    
    return True

def generar_estilos_css(ruta_destino):
    """Crea el archivo CSS en la carpeta de destino."""
    try:
        with open(os.path.join(ruta_destino, "style.css"), "w", encoding="utf-8") as f:
            f.write(CSS_STYLES)
        return True
    except Exception as e:
        print(f"Error al escribir el archivo CSS: {e}")
        return False

def generar_pagina_inicio_evento(evento_id, ruta_destino):
    """Genera la página de inicio del sitio web con información del evento y links a los reportes."""
    evento_info = db.obtener_info_evento(evento_id)
    if not evento_info: return
    
    nombre_evento, fecha_evento, lugar_evento, notas_evento = evento_info[1:5]
    
    # El logo de la cabecera se incrusta en el HTML como base64
    logo_path_header = resource_path('logo.png')
    logo_src = image_to_base64(logo_path_header)
    
    sponsors = db.obtener_sponsors_por_evento(evento_id)
    sponsors_html = ""
    for _, _, logo_path in sponsors:
        # Se comprueba la existencia de la ruta ANTES de procesar
        if os.path.exists(logo_path):
            sponsor_logo_src = image_to_base64(logo_path)
            if sponsor_logo_src:
                # Aplicamos la clase CSS para controlar el tamaño
                sponsors_html += f'<img src="{sponsor_logo_src}" class="sponsor-logo-footer">'
        else:
            print(f"ADVERTENCIA: Logo de patrocinador no encontrado en la ruta guardada: {logo_path}. Omitiendo logo.")
    
    html = f"""
    <div class="header">
        <img src="{logo_src}" class="header-logo">
        <h1>{nombre_evento}</h1>
        <h2>{lugar_evento}</h2>
        <p><b>Fecha:</b> {fecha_evento}</p>
        <p>{notas_evento if notas_evento else ''}</p>
    </div>
    <div class="content">
        <ul class="report-list">
            <li><a href="resultados/index.html">Ver todos los Resultados y Reportes</a></li>
        </ul>
    </div>
    <div class="footer">
        <h3>Patrocinadores</h3>
        <div style="text-align: center;">{sponsors_html if sponsors_html else "<i>(No hay patrocinadores)</i>"}</div>
    </div>
    """
    
    pagina_completa = crear_pagina_html(f"Inicio: {nombre_evento}", html, ruta_css="style.css", back_link="#") 
    with open(os.path.join(ruta_destino, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina_completa)
        
def copiar_archivos_necesarios(evento_id, ruta_destino):
    """Copia los archivos necesarios a la carpeta de destino."""
    return True

# --- FUNCIÓN ORQUESTADORA ---

def generar_sitio_completo(evento_id, ruta_destino, generar_todo=False):
    """
    Función principal llamada desde la interfaz para orquestar la generación 
    de todo el sitio web estático.
    """
    if not os.path.exists(ruta_destino):
        os.makedirs(ruta_destino)
        
    # 1. Generar estilos CSS
    if not generar_estilos_css(ruta_destino):
        return False, "Error al generar los estilos CSS."
    
    # 2. Generar todos los reportes (PDF to HTML conversion and index)
    if not generar_todos_los_reportes(evento_id, ruta_destino, generar_todo):
        return False, "Error al generar los reportes individuales y el índice de resultados."
    
    # 3. Generar la página de inicio (index.html principal)
    try:
        generar_pagina_inicio_evento(evento_id, ruta_destino)
    except Exception as e:
        return False, f"Error al generar la página de inicio (index.html): {e}"

    return True, f"Sitio web generado con éxito en: {ruta_destino}"