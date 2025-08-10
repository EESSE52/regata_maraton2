# inscripciones_ui.py
# Versión completa con todas las funcionalidades incluyendo edición de números de competidor

import sys
import sqlite3
import datetime
import csv
import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QGroupBox, QComboBox, QSpinBox, QAbstractItemView,
    QDialog, QFileDialog, QInputDialog, QDialogButtonBox  # Añade QDialogButtonBox aquí
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal, QStandardPaths

import database_maraton as db
from seleccionar_participante_dialog import SeleccionarParticipanteDialog
from importador_csv_ui import ImportadorCsvDialog

class EditarNumeroDialog(QDialog):
    def __init__(self, numero_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Número de Competidor")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        self.spin_numero = QSpinBox()
        self.spin_numero.setRange(1, 9999)
        self.spin_numero.setValue(numero_actual)
        
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(QLabel("Nuevo número:"))
        layout.addWidget(self.spin_numero)
        layout.addWidget(self.button_box)
    
    def get_numero(self):
        return self.spin_numero.value()

class InscripcionesTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.id_categoria_activa = None
        self.id_inscripcion_seleccionada = None
        
        self.participante1_seleccionado = None
        self.participante2_seleccionado = None
        self.participante3_seleccionado = None
        self.participante4_seleccionado = None

        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        panel_seleccion = QGroupBox("Selección de Evento y Categoría")
        layout_seleccion = QHBoxLayout(panel_seleccion)
        
        self.label_evento_activo = QLabel(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        font = self.label_evento_activo.font()
        font.setPointSize(12)
        self.label_evento_activo.setFont(font)
        
        self.combo_categorias = QComboBox()
        self.combo_categorias.setPlaceholderText("Selecciona una categoría...")
        self.combo_categorias.currentIndexChanged.connect(self.cargar_tabla_inscripciones)
        
        self.btn_importar_csv = QPushButton("Importar Inscripciones (CSV)...")
        self.btn_exportar_csv = QPushButton("Exportar Inscripciones (CSV)...")
        
        layout_seleccion.addWidget(self.label_evento_activo, 1)
        layout_seleccion.addWidget(QLabel("<b>Categoría:</b>"), 0)
        layout_seleccion.addWidget(self.combo_categorias, 2)
        layout_seleccion.addWidget(self.btn_importar_csv)
        layout_seleccion.addWidget(self.btn_exportar_csv)
        layout_principal.addWidget(panel_seleccion)

        panel_inscripcion = QGroupBox("Nueva Inscripción")
        layout_inscripcion = QFormLayout(panel_inscripcion)
        
        self.numero_competidor_input = QSpinBox()
        self.numero_competidor_input.setRange(1, 9999)
        
        layout_p1 = QHBoxLayout()
        self.label_p1 = QLabel("<i>(Ninguno seleccionado)</i>")
        self.btn_seleccionar_p1 = QPushButton("Seleccionar...")
        layout_p1.addWidget(self.label_p1, 1)
        layout_p1.addWidget(self.btn_seleccionar_p1)
        
        layout_p2 = QHBoxLayout()
        self.label_p2 = QLabel("<i>(Opcional)</i>")
        self.btn_seleccionar_p2 = QPushButton("Seleccionar...")
        self.btn_limpiar_p2 = QPushButton("Limpiar")
        layout_p2.addWidget(self.label_p2, 1)
        layout_p2.addWidget(self.btn_seleccionar_p2)
        layout_p2.addWidget(self.btn_limpiar_p2)
        
        layout_p3 = QHBoxLayout()
        self.label_p3 = QLabel("<i>(Opcional)</i>")
        self.btn_seleccionar_p3 = QPushButton("Seleccionar...")
        self.btn_limpiar_p3 = QPushButton("Limpiar")
        layout_p3.addWidget(self.label_p3, 1)
        layout_p3.addWidget(self.btn_seleccionar_p3)
        layout_p3.addWidget(self.btn_limpiar_p3)
        
        layout_p4 = QHBoxLayout()
        self.label_p4 = QLabel("<i>(Opcional)</i>")
        self.btn_seleccionar_p4 = QPushButton("Seleccionar...")
        self.btn_limpiar_p4 = QPushButton("Limpiar")
        layout_p4.addWidget(self.label_p4, 1)
        layout_p4.addWidget(self.btn_seleccionar_p4)
        layout_p4.addWidget(self.btn_limpiar_p4)
        
        self.btn_guardar_inscripcion = QPushButton("Guardar Inscripción")
        self.btn_guardar_inscripcion.setEnabled(False)

        layout_inscripcion.addRow("Número Competidor:", self.numero_competidor_input)
        layout_inscripcion.addRow("Participante 1:", layout_p1)
        layout_inscripcion.addRow("Participante 2:", layout_p2)
        layout_inscripcion.addRow("Participante 3:", layout_p3)
        layout_inscripcion.addRow("Participante 4:", layout_p4)
        layout_inscripcion.addRow(self.btn_guardar_inscripcion)
        layout_principal.addWidget(panel_inscripcion)

        panel_tabla = QGroupBox("Inscripciones en la Categoría Seleccionada")
        layout_tabla = QVBoxLayout(panel_tabla)
        
        self.tabla_inscripciones = QTableWidget()
        self.column_headers = ["ID", "Nº", "P1", "Club 1", "P2", "Club 2", "P3", "Club 3", "P4", "Club 4", "Lugar", "Tiempo", "Estado"]
        self.tabla_inscripciones.setColumnCount(len(self.column_headers))
        self.tabla_inscripciones.setHorizontalHeaderLabels(self.column_headers)
        self.tabla_inscripciones.setColumnHidden(0, True)
        self.tabla_inscripciones.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_inscripciones.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_inscripciones.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for i in [2, 4, 6, 8]: 
            self.tabla_inscripciones.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        
        botones_tabla_layout = QHBoxLayout()
        self.btn_eliminar_inscripcion = QPushButton("Eliminar Inscripción")
        self.btn_editar_numero = QPushButton("Editar Número...")
        
        botones_tabla_layout.addStretch()
        botones_tabla_layout.addWidget(self.btn_editar_numero)
        botones_tabla_layout.addWidget(self.btn_eliminar_inscripcion)
        
        layout_tabla.addWidget(self.tabla_inscripciones)
        layout_tabla.addLayout(botones_tabla_layout)
        layout_principal.addWidget(panel_tabla)

        # Conexiones
        self.btn_importar_csv.clicked.connect(self.abrir_dialogo_importacion)
        self.btn_exportar_csv.clicked.connect(self.exportar_inscripciones_csv)
        self.btn_seleccionar_p1.clicked.connect(lambda: self.seleccionar_participante(1))
        self.btn_seleccionar_p2.clicked.connect(lambda: self.seleccionar_participante(2))
        self.btn_limpiar_p2.clicked.connect(lambda: self.seleccionar_participante(2, limpiar=True))
        self.btn_seleccionar_p3.clicked.connect(lambda: self.seleccionar_participante(3))
        self.btn_limpiar_p3.clicked.connect(lambda: self.seleccionar_participante(3, limpiar=True))
        self.btn_seleccionar_p4.clicked.connect(lambda: self.seleccionar_participante(4))
        self.btn_limpiar_p4.clicked.connect(lambda: self.seleccionar_participante(4, limpiar=True))
        self.btn_guardar_inscripcion.clicked.connect(self.guardar_inscripcion)
        self.btn_eliminar_inscripcion.clicked.connect(self.eliminar_inscripcion)
        self.btn_editar_numero.clicked.connect(self.editar_numero_competidor)
        self.tabla_inscripciones.itemClicked.connect(self.seleccionar_inscripcion_tabla)

    def editar_numero_competidor(self):
        if not self.id_inscripcion_seleccionada:
            QMessageBox.warning(self, "Sin Selección", "Selecciona una inscripción de la tabla para editar su número.")
            return
        
        fila = self.tabla_inscripciones.currentRow()
        numero_actual = int(self.tabla_inscripciones.item(fila, 1).text())
        
        dialogo = EditarNumeroDialog(numero_actual, self)
        if dialogo.exec() == QDialog.Accepted:
            nuevo_numero = dialogo.get_numero()
            
            if nuevo_numero == numero_actual:
                return
                
            # Verificar que el nuevo número no esté en uso
            if db.verificar_numero_competidor(self.id_evento_activo, self.id_categoria_activa, nuevo_numero, self.id_inscripcion_seleccionada):
                QMessageBox.warning(self, "Número en Uso", 
                                  f"El número {nuevo_numero} ya está asignado a otra embarcación en esta categoría.")
                return
            
            # Actualizar en la base de datos
            if db.actualizar_numero_competidor(self.id_inscripcion_seleccionada, nuevo_numero):
                QMessageBox.information(self, "Éxito", f"Número de competidor actualizado a {nuevo_numero}.")
                self.cargar_tabla_inscripciones()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el número de competidor.")

    def abrir_dialogo_importacion(self):
        if self.id_evento_activo is None:
            QMessageBox.warning(self, "Evento No Seleccionado", "Por favor, selecciona un evento activo en la pestaña 'Evento' antes de importar inscripciones.")
            return
        dialogo = ImportadorCsvDialog(self.id_evento_activo, self)
        dialogo.exec()
        self.cargar_tabla_inscripciones()

    def exportar_inscripciones_csv(self):
        if self.id_evento_activo is None:
            QMessageBox.warning(self, "Evento No Seleccionado", "Por favor, selecciona un evento activo en la pestaña 'Evento' antes de exportar.")
            return

        nombre_evento_limpio = self.nombre_evento_activo.replace(" ", "_")
        nombre_sugerido = f"Inscripciones_{nombre_evento_limpio}.csv"
        
        directorio = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Exportación CSV", 
            os.path.join(directorio, nombre_sugerido), 
            "Archivos CSV (*.csv)"
        )

        if not ruta_archivo:
            return

        try:
            inscripciones = db.obtener_inscripciones_para_exportar(self.id_evento_activo)
            
            headers = [
                'Codigo Categoria', 'Numero Competidor', 
                'Nombre Completo P1', 'RUT P1', 'Fecha Nacimiento P1', 'Genero P1', 'Club P1',
                'Nombre Completo P2', 'RUT P2', 'Fecha Nacimiento P2', 'Genero P2', 'Club P2',
                'Nombre Completo P3', 'RUT P3', 'Fecha Nacimiento P3', 'Genero P3', 'Club P3',
                'Nombre Completo P4', 'RUT P4', 'Fecha Nacimiento P4', 'Genero P4', 'Club P4'
            ]

            with open(ruta_archivo, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                
                for row_data in inscripciones:
                    fila_completa = list(row_data) + ([None] * (len(headers) - len(row_data)))
                    writer.writerow([str(item) if item is not None else "" for item in fila_completa])

            QMessageBox.information(
                self, "Exportación Exitosa", 
                f"Se han exportado {len(inscripciones)} inscripciones a:\n{ruta_archivo}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo exportar el archivo CSV.\nError: {e}")
            print(f"Error al exportar CSV: {e}")

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        self.label_evento_activo.setText(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        self.cargar_combo_categorias()
    
    def cargar_combo_categorias(self):
        self.combo_categorias.clear()
        self.combo_categorias.addItem("Selecciona una categoría...", None)
        if self.id_evento_activo is not None:
            categorias = db.obtener_categorias()
            for cat_id, nombre, codigo, *_ in categorias:
                self.combo_categorias.addItem(f"{nombre} ({codigo})", cat_id)
    
    def seleccionar_participante(self, numero_participante, limpiar=False):
        if limpiar:
            if numero_participante == 2: 
                self.participante2_seleccionado = None
                self.label_p2.setText("<i>(Opcional)</i>")
            elif numero_participante == 3: 
                self.participante3_seleccionado = None
                self.label_p3.setText("<i>(Opcional)</i>")
            elif numero_participante == 4: 
                self.participante4_seleccionado = None
                self.label_p4.setText("<i>(Opcional)</i>")
            return
        
        dialogo = SeleccionarParticipanteDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            info = dialogo.get_selected_participante_info()
            if info:
                if numero_participante == 1: 
                    self.participante1_seleccionado = info
                    self.label_p1.setText(f"<b>{info['nombre']}</b> (ID: {info['id']})")
                    self.btn_guardar_inscripcion.setEnabled(True)
                elif numero_participante == 2: 
                    self.participante2_seleccionado = info
                    self.label_p2.setText(f"<b>{info['nombre']}</b> (ID: {info['id']})")
                elif numero_participante == 3: 
                    self.participante3_seleccionado = info
                    self.label_p3.setText(f"<b>{info['nombre']}</b> (ID: {info['id']})")
                elif numero_participante == 4: 
                    self.participante4_seleccionado = info
                    self.label_p4.setText(f"<b>{info['nombre']}</b> (ID: {info['id']})")

    def guardar_inscripcion(self):
        if self.id_evento_activo is None: 
            QMessageBox.warning(self, "Error", "Primero selecciona un evento activo.")
            return
        
        self.id_categoria_activa = self.combo_categorias.currentData()
        if self.id_categoria_activa is None: 
            QMessageBox.warning(self, "Error", "Selecciona una categoría.")
            return
        
        if self.participante1_seleccionado is None: 
            QMessageBox.warning(self, "Error", "Debes seleccionar al menos el Participante 1.")
            return
        
        datos = {
            'evento_id': self.id_evento_activo,
            'categoria_id': self.id_categoria_activa,
            'participante1_id': self.participante1_seleccionado['id'],
            'participante2_id': self.participante2_seleccionado['id'] if self.participante2_seleccionado else None,
            'participante3_id': self.participante3_seleccionado['id'] if self.participante3_seleccionado else None,
            'participante4_id': self.participante4_seleccionado['id'] if self.participante4_seleccionado else None,
            'numero_competidor': self.numero_competidor_input.value()
        }
        
        insc_id, mensaje = db.inscribir_embarcacion(datos)
        if insc_id:
            QMessageBox.information(self, "Éxito", mensaje)
            self.cargar_tabla_inscripciones()
            self.limpiar_formulario_inscripcion()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def cargar_tabla_inscripciones(self):
        self.tabla_inscripciones.setRowCount(0)
        self.limpiar_formulario_inscripcion()
        self.id_categoria_activa = self.combo_categorias.currentData()
        
        if self.id_evento_activo is None or self.id_categoria_activa is None: 
            return
        
        evento_info = db.obtener_info_evento(self.id_evento_activo)
        categoria_info = db.obtener_info_categoria(self.id_categoria_activa)
        
        if not evento_info or not categoria_info: 
            return
        
        try: 
            ano_competicion = datetime.datetime.strptime(evento_info[2], "%Y-%m-%d").year
            edad_min_cat = categoria_info[3]
            edad_max_cat = categoria_info[4]
        except (ValueError, TypeError, IndexError) as e: 
            QMessageBox.critical(self, "Error de Datos", f"Datos de evento o categoría inválidos: {e}")
            return
        
        inscripciones = db.obtener_inscripciones_por_categoria(self.id_evento_activo, self.id_categoria_activa)
        
        for row_idx, row_data in enumerate(inscripciones):
            self.tabla_inscripciones.insertRow(row_idx)
            
            # ID
            self.tabla_inscripciones.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            # Número
            self.tabla_inscripciones.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
            # Participante 1
            self.tabla_inscripciones.setItem(row_idx, 2, QTableWidgetItem(row_data[2] or ""))
            # Club 1
            self.tabla_inscripciones.setItem(row_idx, 3, QTableWidgetItem(row_data[3] or ""))
            # Participante 2
            self.tabla_inscripciones.setItem(row_idx, 4, QTableWidgetItem(row_data[5] or ""))
            # Club 2
            self.tabla_inscripciones.setItem(row_idx, 5, QTableWidgetItem(row_data[6] or ""))
            # Participante 3
            self.tabla_inscripciones.setItem(row_idx, 6, QTableWidgetItem(row_data[8] or ""))
            # Club 3
            self.tabla_inscripciones.setItem(row_idx, 7, QTableWidgetItem(row_data[9] or ""))
            # Participante 4
            self.tabla_inscripciones.setItem(row_idx, 8, QTableWidgetItem(row_data[11] or ""))
            # Club 4
            self.tabla_inscripciones.setItem(row_idx, 9, QTableWidgetItem(row_data[12] or ""))
            # Lugar
            self.tabla_inscripciones.setItem(row_idx, 10, QTableWidgetItem(str(row_data[14]) if row_data[14] else ""))
            # Tiempo
            self.tabla_inscripciones.setItem(row_idx, 11, QTableWidgetItem(row_data[15] or ""))
            # Estado
            self.tabla_inscripciones.setItem(row_idx, 12, QTableWidgetItem(row_data[16] or 'Inscrito'))
            
            # Verificar edades de los participantes
            edad_correcta = True
            ids_participantes = list(filter(None, [row_data[4], row_data[7], row_data[10], row_data[13]]))
            
            for p_id in ids_participantes:
                participante_db = db.obtener_info_participante(p_id)
                if not participante_db or not participante_db[4]: 
                    edad_correcta = False
                    break
                
                try:
                    fecha_nac_part = datetime.datetime.strptime(participante_db[4], "%Y-%m-%d").date()
                    edad_calendario = ano_competicion - fecha_nac_part.year
                    
                    if not (edad_min_cat <= edad_calendario <= edad_max_cat): 
                        edad_correcta = False
                        break
                except (ValueError, TypeError): 
                    edad_correcta = False
                    break
            
            if not edad_correcta:
                for col in range(self.tabla_inscripciones.columnCount()):
                    self.tabla_inscripciones.item(row_idx, col).setBackground(QColor(255, 204, 203))
    
    def eliminar_inscripcion(self):
        if self.id_inscripcion_seleccionada is None: 
            QMessageBox.warning(self, "Sin Selección", "Selecciona una inscripción para eliminar.")
            return
        
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación", 
            "¿Seguro que quieres eliminar esta inscripción?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            exito, mensaje = db.eliminar_inscripcion(self.id_inscripcion_seleccionada)
            if exito: 
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_tabla_inscripciones()
            else: 
                QMessageBox.critical(self, "Error", mensaje)
    
    def seleccionar_inscripcion_tabla(self, item):
        fila = self.tabla_inscripciones.row(item)
        self.id_inscripcion_seleccionada = int(self.tabla_inscripciones.item(fila, 0).text())
    
    def limpiar_formulario_inscripcion(self):
        self.id_inscripcion_seleccionada = None
        self.participante1_seleccionado = None
        self.participante2_seleccionado = None
        self.participante3_seleccionado = None
        self.participante4_seleccionado = None
        self.label_p1.setText("<i>(Ninguno seleccionado)</i>")
        self.label_p2.setText("<i>(Opcional)</i>")
        self.label_p3.setText("<i>(Opcional)</i>")
        self.label_p4.setText("<i>(Opcional)</i>")
        self.numero_competidor_input.setValue(1)
        self.tabla_inscripciones.clearSelection()
        self.btn_guardar_inscripcion.setEnabled(False)