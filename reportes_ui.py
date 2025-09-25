# reportes_ui.py
# CORREGIDO: Añadida la opción para generar el reporte "Programa Oficial del Evento".

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGroupBox, QComboBox, QFileDialog, QDialog,
    QFormLayout, QDialogButtonBox, QProgressDialog
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QPageSize, QPageLayout, QFont, QImage, QPainter
from PySide6.QtCore import Qt, QMarginsF, QUrl, QStandardPaths, QSize, QRectF
from PySide6.QtGui import QTextDocument, QTextCursor, QTextCharFormat

import database_maraton as db
import generador_pdf_reportes as gen_reportes
import generador_web
from pdf_preview_dialog_ui import PdfPreviewDialog
from utils_maraton import resource_path

LOGO_FILENAME = "logo.png"

class ReportesTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.sistema_puntuacion_actual = {}
        self.logo_path = resource_path(LOGO_FILENAME)

        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(15)

        panel_estado = QGroupBox("Evento Activo")
        panel_estado.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; color: #2a5c7a; }")
        layout_estado = QHBoxLayout(panel_estado)
        
        self.label_evento_activo = QLabel(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        font = QFont(); font.setPointSize(12); font.setBold(True)
        self.label_evento_activo.setFont(font)
        self.label_evento_activo.setStyleSheet("color: #2a5c7a;")
        
        layout_estado.addWidget(self.label_evento_activo)
        layout_principal.addWidget(panel_estado)

        panel_generacion = QGroupBox("Generar Reportes")
        panel_generacion.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; color: #2a5c7a; }")
        layout_generacion = QFormLayout(panel_generacion)
        layout_generacion.setVerticalSpacing(12); layout_generacion.setHorizontalSpacing(15)
        
        self.combo_tipo_reporte = QComboBox()
        self.combo_tipo_reporte.setStyleSheet("QComboBox { min-height: 28px; }")
        # --- OPCIÓN AÑADIDA AL MENÚ ---
        self.combo_tipo_reporte.addItems([
            "Programa Oficial del Evento",
            "Listado de Partida por Categoría", "Resultados Finales por Categoría",
            "Resultados Completos del Evento", "Clasificación General por Clubes",
            "Ranking Individual por Puntos", "Ranking Individual por Medallas"
        ])
        
        self.combo_categorias = QComboBox()
        self.combo_categorias.setPlaceholderText("Selecciona una categoría...")
        self.combo_categorias.setStyleSheet("QComboBox { min-height: 28px; }")
        
        botones_reporte_layout = QHBoxLayout(); botones_reporte_layout.setSpacing(15)
        
        self.btn_generar_pdf = QPushButton("Previsualizar y Guardar PDF")
        self.btn_exportar_png = QPushButton("Exportar como Imagen (PNG)")
        self.btn_generar_todos = QPushButton("Generar Todos los Reportes (PDF)")
        self.btn_generar_web = QPushButton("🌐 Generar Sitio Web Completo")

        estilo_boton = """
        QPushButton { font-weight: bold; padding: 8px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4ca1d9, stop:1 #2a7bb9); color: white; border: 1px solid #1a6da9; border-radius: 5px; min-width: 200px; }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5cb1e9, stop:1 #3a8bc9); }
        QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a7bb9, stop:1 #4ca1d9); }
        """
        self.btn_generar_pdf.setStyleSheet(estilo_boton)
        self.btn_exportar_png.setStyleSheet(estilo_boton)
        self.btn_generar_todos.setStyleSheet(estilo_boton)
        self.btn_generar_web.setStyleSheet(estilo_boton)

        botones_reporte_layout.addWidget(self.btn_generar_pdf); botones_reporte_layout.addWidget(self.btn_exportar_png)
        botones_reporte_layout.addWidget(self.btn_generar_todos); botones_reporte_layout.addWidget(self.btn_generar_web)

        layout_generacion.addRow("Tipo de Reporte:", self.combo_tipo_reporte)
        layout_generacion.addRow("Categoría (si aplica):", self.combo_categorias)
        layout_generacion.addRow(botones_reporte_layout)
        
        layout_principal.addWidget(panel_generacion); layout_principal.addStretch()

        self.combo_tipo_reporte.currentIndexChanged.connect(self.actualizar_visibilidad_combo_categorias)
        self.btn_generar_pdf.clicked.connect(self.generar_reporte_pdf)
        self.btn_exportar_png.clicked.connect(self.exportar_reporte_png)
        self.btn_generar_todos.clicked.connect(self.generar_todos_los_reportes)
        self.btn_generar_web.clicked.connect(self.generar_sitio_web)

        self.actualizar_visibilidad_combo_categorias()

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        self.label_evento_activo.setText(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        self.cargar_combo_categorias()

    def actualizar_sistema_puntuacion(self, sistema_puntuacion):
        self.sistema_puntuacion_actual = sistema_puntuacion
        print("[REPORTES] Sistema de puntuación actualizado.")

    def cargar_combo_categorias(self):
        self.combo_categorias.clear()
        self.combo_categorias.addItem("Selecciona una categoría...", None)
        if self.id_evento_activo is not None:
            categorias = db.obtener_categorias()
            for cat_id, nombre, codigo, *_ in categorias:
                self.combo_categorias.addItem(f"{nombre} ({codigo})", cat_id)

    def actualizar_visibilidad_combo_categorias(self):
        tipo_reporte = self.combo_tipo_reporte.currentText()
        label_categoria = self.layout().itemAt(1).widget().layout().labelForField(self.combo_categorias)
        # La visibilidad ahora depende de si la palabra "Categoría" está en el texto
        visibile = "Categoría" in tipo_reporte
        self.combo_categorias.setVisible(visibile)
        if label_categoria: label_categoria.setVisible(visibile)

    def _generar_logica_reporte(self):
        if self.id_evento_activo is None:
            QMessageBox.warning(self, "Sin Evento", "Primero selecciona un evento activo."); return None, None
        
        tipo_reporte = self.combo_tipo_reporte.currentText()
        documento, nombre_archivo_sugerido = None, "reporte.pdf"
        sponsors = db.obtener_sponsors_por_evento(self.id_evento_activo)
        sponsor_logo_paths = [s[2] for s in sponsors if s[2]]

        if "Programa Oficial" in tipo_reporte:
            documento, _ = gen_reportes.crear_programa_evento(self.id_evento_activo, self.logo_path, sponsor_logo_paths)
            nombre_archivo_sugerido = "Programa_Oficial_Evento.pdf"
        elif "Categoría" in tipo_reporte:
            categoria_id = self.combo_categorias.currentData()
            if categoria_id is None: QMessageBox.warning(self, "Sin Categoría", "Selecciona una categoría para este tipo de reporte."); return None, None
            nombre_cat_limpio = self.combo_categorias.currentText().replace(" ", "_").replace("(", "").replace(")", "")
            if "Listado de Partida" in tipo_reporte:
                documento, _ = gen_reportes.crear_start_list(self.id_evento_activo, categoria_id, self.logo_path, sponsor_logo_paths)
                nombre_archivo_sugerido = f"StartList_{nombre_cat_limpio}.pdf"
            elif "Resultados Finales" in tipo_reporte:
                documento, _ = gen_reportes.crear_resultados_categoria(self.id_evento_activo, categoria_id, self.logo_path, sponsor_logo_paths)
                nombre_archivo_sugerido = f"Resultados_{nombre_cat_limpio}.pdf"
        elif "Resultados Completos" in tipo_reporte:
            documento, _ = gen_reportes.crear_resultados_completos(self.id_evento_activo, self.logo_path, sponsor_logo_paths)
            nombre_archivo_sugerido = "Resultados_Completos_Evento.pdf"
        elif "Clasificación General" in tipo_reporte or "Ranking Individual" in tipo_reporte:
            if not self.sistema_puntuacion_actual: QMessageBox.warning(self, "Sin Puntuación", "Calcula la puntuación en la pestaña 'Puntuación' primero."); return None, None
            if "Clasificación General" in tipo_reporte:
                documento, _ = gen_reportes.crear_ranking_puntuacion_pdf(self.id_evento_activo, self.sistema_puntuacion_actual, self.logo_path, sponsor_logo_paths)
                nombre_archivo_sugerido = "Clasificacion_General_Clubes.pdf"
            elif "Puntos" in tipo_reporte:
                documento, _ = gen_reportes.crear_ranking_deportistas_puntos(self.id_evento_activo, self.sistema_puntuacion_actual, self.logo_path, sponsor_logo_paths)
                nombre_archivo_sugerido = "Ranking_Individual_Puntos.pdf"
            elif "Medallas" in tipo_reporte:
                documento, _ = gen_reportes.crear_ranking_deportistas_medallas(self.id_evento_activo, self.logo_path, sponsor_logo_paths)
                nombre_archivo_sugerido = "Ranking_Individual_Medallas.pdf"
        
        return documento, nombre_archivo_sugerido

    # (El resto de las funciones: generar_reporte_pdf, _guardar_documento_pdf, exportar_reporte_png, etc. no cambian)
    def generar_reporte_pdf(self):
        documento, nombre_archivo_sugerido = self._generar_logica_reporte()
        if not documento: return
        preview_dialog = PdfPreviewDialog(documento, self)
        if preview_dialog.exec() == QDialog.Accepted:
            directorio = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            ruta_sugerida = os.path.join(directorio, nombre_archivo_sugerido)
            filePath, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte PDF", ruta_sugerida, "Archivos PDF (*.pdf)")
            if filePath: self._guardar_documento_pdf(documento, filePath); QMessageBox.information(self, "Éxito", f"Reporte PDF guardado en:\n{filePath}")

    def _guardar_documento_pdf(self, documento, filePath):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat); printer.setOutputFileName(filePath)
        printer.setPageSize(QPageSize(QPageSize.A4)); printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
        documento.print_(printer)

    def exportar_reporte_png(self):
        documento, nombre_archivo_sugerido = self._generar_logica_reporte()
        if not documento: return
        dialog = QDialog(self); dialog.setWindowTitle("Seleccionar Resolución para TV")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Seleccione la resolución de salida:"))
        resoluciones = {"HD Ready (1280x720)": (1280, 720), "Full HD (1920x1080)": (1920, 1080), "4K UHD (3840x2160)": (3840, 2160)}
        combo_resoluciones = QComboBox(); combo_resoluciones.addItems(resoluciones.keys())
        layout.addWidget(combo_resoluciones)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        if dialog.exec() != QDialog.Accepted: return
        width, height = list(resoluciones.values())[combo_resoluciones.currentIndex()]
        image = QImage(QSize(width, height), QImage.Format_ARGB32); image.fill(Qt.white)
        painter = QPainter(image); documento.drawContents(painter, QRectF(0, 0, width, height)); painter.end()
        nombre_png = nombre_archivo_sugerido.replace('.pdf', f'_{width}x{height}.png')
        directorio = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        ruta_sugerida = os.path.join(directorio, nombre_png)
        filePath, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte como Imagen PNG", ruta_sugerida, "Imágenes PNG (*.png)")
        if filePath and image.save(filePath, "PNG", 100):
            QMessageBox.information(self, "Exportación Exitosa", f"Imagen PNG guardada en:\n{filePath}")
        elif filePath:
            QMessageBox.critical(self, "Error de Exportación", "No se pudo guardar el archivo PNG.")

    def generar_todos_los_reportes(self):
        if self.id_evento_activo is None: QMessageBox.warning(self, "Sin Evento", "Primero selecciona un evento activo."); return
        sponsors, sponsor_logo_paths = db.obtener_sponsors_por_evento(self.id_evento_activo), [s[2] for s in db.obtener_sponsors_por_evento(self.id_evento_activo) if s[2]]
        categorias = db.obtener_categorias()
        if not categorias: QMessageBox.warning(self, "Sin Categorías", "No hay categorías definidas."); return
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Guardar Reportes", QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation))
        if not directorio: return
        num_pasos = len(categorias) * 2 + 5 # Aumentamos en 1 por el nuevo reporte
        progress = QProgressDialog("Generando reportes...", "Cancelar", 0, num_pasos, self)
        progress.setWindowTitle("Generación Masiva de Reportes"); progress.setWindowModality(Qt.WindowModal)
        
        paso_actual = 0
        # Generar Programa Oficial
        progress.setLabelText("Generando Programa Oficial..."); progress.setValue(paso_actual)
        doc, _ = gen_reportes.crear_programa_evento(self.id_evento_activo, self.logo_path, sponsor_logo_paths)
        if doc: self._guardar_documento_pdf(doc, os.path.join(directorio, "Programa_Oficial_Evento.pdf"))
        paso_actual += 1

        for i, (cat_id, nombre, codigo, *_) in enumerate(categorias):
            if progress.wasCanceled(): break
            nombre_cat_limpio = f"{nombre}_{codigo}".replace(" ", "_").replace("(", "").replace(")", "")
            progress.setLabelText(f"Generando listado: {nombre}..."); progress.setValue(paso_actual); paso_actual +=1
            doc, _ = gen_reportes.crear_start_list(self.id_evento_activo, cat_id, self.logo_path, sponsor_logo_paths)
            if doc: self._guardar_documento_pdf(doc, os.path.join(directorio, f"StartList_{nombre_cat_limpio}.pdf"))
            
            progress.setLabelText(f"Generando resultados: {nombre}..."); progress.setValue(paso_actual); paso_actual += 1
            doc, _ = gen_reportes.crear_resultados_categoria(self.id_evento_activo, cat_id, self.logo_path, sponsor_logo_paths)
            if doc: self._guardar_documento_pdf(doc, os.path.join(directorio, f"Resultados_{nombre_cat_limpio}.pdf"))
        
        if not progress.wasCanceled():
            reportes_globales = [
                ("Resultados Completos Evento", gen_reportes.crear_resultados_completos, (self.id_evento_activo, self.logo_path, sponsor_logo_paths)),
                ("Clasificacion General Clubes", gen_reportes.crear_puntuacion_general, (self.id_evento_activo, self.sistema_puntuacion_actual, self.logo_path, sponsor_logo_paths)),
                ("Ranking Individual Puntos", gen_reportes.crear_ranking_deportistas_puntos, (self.id_evento_activo, self.sistema_puntuacion_actual, self.logo_path, sponsor_logo_paths)),
                ("Ranking Individual Medallas", gen_reportes.crear_ranking_deportistas_medallas, (self.id_evento_activo, self.logo_path, sponsor_logo_paths))
            ]
            for nombre, func, args in reportes_globales:
                if "Clubes" in nombre or "Puntos" in nombre:
                    if not self.sistema_puntuacion_actual: continue
                progress.setLabelText(f"Generando {nombre}..."); progress.setValue(paso_actual)
                doc, _ = func(*args)
                if doc: self._guardar_documento_pdf(doc, os.path.join(directorio, f"{nombre.replace(' ', '_')}.pdf"))
                paso_actual += 1
                
        progress.setValue(num_pasos); progress.close()
        if not progress.wasCanceled(): QMessageBox.information(self, "Generación Completa", f"Todos los reportes han sido generados en:\n{directorio}")

    def generar_sitio_web(self):
        """Genera un sitio web estático completo con todos los resultados."""
        if self.id_evento_activo is None:
            QMessageBox.warning(self, "Sin Evento", "Primero selecciona un evento activo.")
            return
        if not self.sistema_puntuacion_actual:
            QMessageBox.warning(self, "Sin Puntuación", "Calcula la puntuación en la pestaña 'Puntuación' primero. Se usará para los rankings.")
            return
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Guardar el Sitio Web", QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation))
        if not directorio:
            return
        try:
            nombre_evento_limpio = self.nombre_evento_activo.replace(" ", "_").lower()
            ruta_sitio = os.path.join(directorio, f"sitio_web_{nombre_evento_limpio}")
            generador_web.generar_sitio_completo(self.id_evento_activo, self.sistema_puntuacion_actual, ruta_sitio)
            QMessageBox.information(self, "Generación Exitosa", f"El sitio web ha sido generado exitosamente en:\n{ruta_sitio}\n\nAbre el archivo 'index.html' en tu navegador para verlo.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el sitio web: {e}")
            print(f"Error generando sitio web: {e}")