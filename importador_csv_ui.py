# importador_csv_ui.py
# Diálogo y lógica para importar inscripciones masivas desde un archivo CSV.
# VERSIÓN COMPLETA Y ACTUALIZADA

import sys
import csv
import os
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QTextEdit, QProgressBar, QApplication
)
from PySide6.QtCore import Qt
import database_maraton as db

class ImportadorCsvDialog(QDialog):
    def __init__(self, evento_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importador de Inscripciones desde CSV")
        self.setMinimumSize(600, 400)

        if not evento_id:
            raise ValueError("Se requiere un ID de evento para la importación.")
        
        self.evento_id = evento_id
        self.ruta_archivo_csv = None

        # Layout
        layout = QVBoxLayout(self)

        # Selección de archivo
        layout_archivo = QHBoxLayout()
        self.label_archivo = QLabel("<i>Ningún archivo seleccionado.</i>")
        self.btn_seleccionar_archivo = QPushButton("Seleccionar Archivo CSV...")
        layout_archivo.addWidget(QLabel("Archivo:"))
        layout_archivo.addWidget(self.label_archivo, 1)
        layout_archivo.addWidget(self.btn_seleccionar_archivo)
        layout.addLayout(layout_archivo)

        # Log de importación
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setPlaceholderText("El progreso y los resultados de la importación se mostrarán aquí...")
        layout.addWidget(QLabel("Registro de Importación:"))
        layout.addWidget(self.log_text_edit)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Botones de acción
        layout_botones = QHBoxLayout()
        self.btn_iniciar_importacion = QPushButton("Iniciar Importación")
        self.btn_iniciar_importacion.setEnabled(False)
        self.btn_cerrar = QPushButton("Cerrar")
        layout_botones.addStretch()
        layout_botones.addWidget(self.btn_iniciar_importacion)
        layout_botones.addWidget(self.btn_cerrar)
        layout.addLayout(layout_botones)

        # Conexiones
        self.btn_seleccionar_archivo.clicked.connect(self.seleccionar_archivo)
        self.btn_iniciar_importacion.clicked.connect(self.iniciar_importacion)
        self.btn_cerrar.clicked.connect(self.accept)

    def seleccionar_archivo(self):
        """Abre un diálogo para que el usuario seleccione un archivo .csv."""
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo CSV", "", "Archivos CSV (*.csv)")
        if ruta:
            self.ruta_archivo_csv = ruta
            self.label_archivo.setText(f"<b>{os.path.basename(ruta)}</b>")
            self.btn_iniciar_importacion.setEnabled(True)
            self.log_text_edit.clear()

    def log(self, mensaje):
        """Añade un mensaje al cuadro de registro."""
        self.log_text_edit.append(mensaje)
        QApplication.processEvents() # Forzar actualización de la UI

    def iniciar_importacion(self):
        if not self.ruta_archivo_csv:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un archivo CSV primero.")
            return

        self.btn_iniciar_importacion.setEnabled(False)
        self.log("--- Iniciando proceso de importación ---")

        try:
            with open(self.ruta_archivo_csv, mode='r', encoding='utf-8-sig') as csvfile:
                try:
                    sample = csvfile.read(2048)
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                    csvfile.seek(0)
                    self.log(f"Dialecto CSV detectado: Delimitador='{dialect.delimiter}'")
                except csv.Error:
                    self.log("ADVERTENCIA: No se pudo detectar el dialecto del CSV. Se intentará con delimitador punto y coma (;).")
                    dialect = csv.excel 
                    dialect.delimiter = ';'
                    csvfile.seek(0)

                lector_csv = list(csv.DictReader(csvfile, dialect=dialect))
                
                if not lector_csv:
                    raise ValueError("El archivo CSV está vacío o no tiene un formato de tabla válido.")

                headers = [h.strip() for h in lector_csv[0].keys()]
                required_headers = ['Codigo Categoria', 'Nombre Completo P1', 'RUT P1']
                missing_headers = [h for h in required_headers if h not in headers]
                if missing_headers:
                    raise ValueError(f"Faltan las siguientes columnas obligatorias en el archivo CSV: {', '.join(missing_headers)}")
                
                total_filas = len(lector_csv)
                self.progress_bar.setMaximum(total_filas)
                
                exitos = 0
                fallos = 0
                
                for i, fila in enumerate(lector_csv):
                    fila_limpia = {k.strip(): v.strip() for k, v in fila.items()}
                    self.progress_bar.setValue(i + 1)
                    try:
                        self.procesar_fila(fila_limpia)
                        exitos += 1
                    except Exception as e:
                        fallos += 1
                        self.log(f"<b><font color='red'>ERROR en fila {i+2}:</font></b> {e}")
                
                self.log("\n--- Proceso de importación finalizado ---")
                resumen = (f"Resumen:\n"
                           f" - Filas procesadas: {total_filas}\n"
                           f" - Inscripciones exitosas: {exitos}\n"
                           f" - Filas con errores: {fallos}")
                self.log(resumen)
                QMessageBox.information(self, "Importación Completa", resumen)

        except Exception as e:
            error_msg = f"No se pudo leer o procesar el archivo CSV.\nError: {e}"
            self.log(f"<b><font color='red'>ERROR FATAL:</font></b> {error_msg}")
            QMessageBox.critical(self, "Error de Archivo", error_msg)
        
        self.btn_iniciar_importacion.setEnabled(True)

    def procesar_fila(self, fila):
        """Procesa una única fila del archivo CSV."""
        codigo_categoria = fila.get('Codigo Categoria')
        if not codigo_categoria:
            raise ValueError("La columna 'Codigo Categoria' es obligatoria y no puede estar vacía.")

        categoria_id = db.obtener_categoria_por_codigo(codigo_categoria)
        if not categoria_id:
            raise ValueError(f"La categoría con código '{codigo_categoria}' no fue encontrada en la base de datos. Por favor, créala primero.")

        participantes_ids = []
        for i in range(1, 5):
            nombre_completo = fila.get(f'Nombre Completo P{i}')
            rut = fila.get(f'RUT P{i}')
            
            if nombre_completo and rut:
                datos_p = {
                    'nombre_completo': nombre_completo,
                    'rut_o_id': rut,
                    'fecha_nacimiento': fila.get(f'Fecha Nacimiento P{i}'),
                    'genero': fila.get(f'Genero P{i}'),
                    'club': fila.get(f'Club P{i}')
                }
                participante_id = db.buscar_o_crear_participante(datos_p)
                if participante_id:
                    participantes_ids.append(participante_id)
                else:
                    raise ValueError(f"No se pudo buscar o crear al participante {i} ({nombre_completo}).")
        
        if not participantes_ids:
            raise ValueError("La inscripción no contiene ningún participante válido.")

        numero_competidor_str = fila.get('Numero Competidor')
        if numero_competidor_str:
            try:
                numero_competidor = int(numero_competidor_str)
            except ValueError:
                raise ValueError(f"El 'Numero Competidor' ('{numero_competidor_str}') no es un número válido.")
        else:
            self.log(f"INFO Fila {self.progress_bar.value()}: 'Numero Competidor' no encontrado. Asignando el siguiente número disponible...")
            numero_competidor = db.obtener_siguiente_numero_competidor(self.evento_id, categoria_id)

        datos_inscripcion = {
            'evento_id': self.evento_id,
            'categoria_id': categoria_id,
            'numero_competidor': numero_competidor,
            'participante1_id': participantes_ids[0] if len(participantes_ids) > 0 else None,
            'participante2_id': participantes_ids[1] if len(participantes_ids) > 1 else None,
            'participante3_id': participantes_ids[2] if len(participantes_ids) > 2 else None,
            'participante4_id': participantes_ids[3] if len(participantes_ids) > 3 else None,
        }

        insc_id, mensaje = db.inscribir_embarcacion(datos_inscripcion)
        if "Error" in mensaje:
            raise Exception(mensaje)
        
        self.log(f"ÉXITO Fila {self.progress_bar.value()}: Inscripción para Nº{numero_competidor} en categoría '{codigo_categoria}' guardada.")
