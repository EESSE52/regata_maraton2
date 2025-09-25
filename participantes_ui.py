# participantes_ui.py
# CORREGIDO: Añadida la funcionalidad para seleccionar y previsualizar el logo de un club.

import sys
import sqlite3
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QGroupBox, QComboBox, QDateEdit, QAbstractItemView,
    QFileDialog
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QDate, Qt, QStandardPaths

import database_maraton as db

class ParticipantesTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_club_seleccionado = None
        self.logo_club_path = None
        self.id_participante_seleccionado = None
        self.init_ui()
        self.cargar_datos_iniciales()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setSpacing(15)

        # --- Panel de Clubes ---
        panel_clubes = QGroupBox("Gestión de Clubes")
        layout_clubes = QVBoxLayout(panel_clubes)
        form_club = QFormLayout()
        
        self.nombre_club_input = QLineEdit()
        self.abrev_club_input = QLineEdit()
        self.ciudad_club_input = QLineEdit()
        
        # Nuevos widgets para el logo
        layout_logo = QHBoxLayout()
        self.preview_logo_label = QLabel("Sin logo")
        self.preview_logo_label.setFixedSize(100, 100)
        self.preview_logo_label.setAlignment(Qt.AlignCenter)
        self.preview_logo_label.setStyleSheet("border: 1px solid #9cc0d6; border-radius: 4px; background-color: white;")
        
        layout_botones_logo = QVBoxLayout()
        self.btn_seleccionar_logo = QPushButton("Seleccionar Logo...")
        self.btn_quitar_logo = QPushButton("Quitar Logo")
        layout_botones_logo.addWidget(self.btn_seleccionar_logo)
        layout_botones_logo.addWidget(self.btn_quitar_logo)
        
        layout_logo.addWidget(self.preview_logo_label)
        layout_logo.addLayout(layout_botones_logo)
        
        form_club.addRow("Nombre Club:", self.nombre_club_input)
        form_club.addRow("Abreviatura:", self.abrev_club_input)
        form_club.addRow("Ciudad:", self.ciudad_club_input)
        form_club.addRow("Logo:", layout_logo)

        botones_club_layout = QHBoxLayout()
        self.btn_club_nuevo = QPushButton("Nuevo")
        self.btn_club_guardar = QPushButton("Guardar")
        self.btn_club_eliminar = QPushButton("Eliminar")
        botones_club_layout.addWidget(self.btn_club_nuevo); botones_club_layout.addWidget(self.btn_club_guardar); botones_club_layout.addWidget(self.btn_club_eliminar)
        
        self.tabla_clubes = QTableWidget()
        self.tabla_clubes.setColumnCount(5) # Aumentado para el path del logo
        self.tabla_clubes.setHorizontalHeaderLabels(["ID", "Nombre", "Abrev.", "Ciudad", "Ruta Logo"])
        self.tabla_clubes.setColumnHidden(0, True); self.tabla_clubes.setColumnHidden(4, True) # Ocultar ID y Ruta
        self.tabla_clubes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_clubes.setSelectionBehavior(QAbstractItemView.SelectRows); self.tabla_clubes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout_clubes.addLayout(form_club); layout_clubes.addLayout(botones_club_layout); layout_clubes.addWidget(self.tabla_clubes)
        
        # --- Panel de Participantes ---
        panel_participantes = QGroupBox("Gestión de Participantes")
        layout_participantes = QVBoxLayout(panel_participantes)
        form_participante = QFormLayout()
        self.nombre_part_input = QLineEdit()
        self.apellido_part_input = QLineEdit()
        self.rut_part_input = QLineEdit()
        self.fecha_nac_part_edit = QDateEdit(calendarPopup=True); self.fecha_nac_part_edit.setDisplayFormat("yyyy-MM-dd")
        self.genero_part_combo = QComboBox(); self.genero_part_combo.addItems(["Masculino", "Femenino"])
        self.club_part_combo = QComboBox()
        form_participante.addRow("Nombre:", self.nombre_part_input); form_participante.addRow("Apellido:", self.apellido_part_input)
        form_participante.addRow("RUT / ID:", self.rut_part_input); form_participante.addRow("Fecha Nacimiento:", self.fecha_nac_part_edit)
        form_participante.addRow("Género:", self.genero_part_combo); form_participante.addRow("Club:", self.club_part_combo)
        botones_part_layout = QHBoxLayout()
        self.btn_part_nuevo = QPushButton("Nuevo"); self.btn_part_guardar = QPushButton("Guardar"); self.btn_part_eliminar = QPushButton("Eliminar")
        botones_part_layout.addWidget(self.btn_part_nuevo); botones_part_layout.addWidget(self.btn_part_guardar); botones_part_layout.addWidget(self.btn_part_eliminar)
        self.tabla_participantes = QTableWidget()
        self.tabla_participantes.setColumnCount(7); self.tabla_participantes.setHorizontalHeaderLabels(["ID", "Nombre", "Apellido", "RUT/ID", "F. Nac.", "Género", "Club"])
        self.tabla_participantes.setColumnHidden(0, True); self.tabla_participantes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_participantes.setSelectionBehavior(QAbstractItemView.SelectRows); self.tabla_participantes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout_participantes.addLayout(form_participante); layout_participantes.addLayout(botones_part_layout); layout_participantes.addWidget(self.tabla_participantes)

        layout_principal.addWidget(panel_clubes, 1); layout_principal.addWidget(panel_participantes, 2)
        
        # Conexiones
        self.btn_club_nuevo.clicked.connect(self.limpiar_form_club)
        self.btn_club_guardar.clicked.connect(self.guardar_club)
        self.btn_club_eliminar.clicked.connect(self.eliminar_club)
        self.tabla_clubes.itemClicked.connect(self.cargar_club_seleccionado)
        self.btn_seleccionar_logo.clicked.connect(self.seleccionar_logo)
        self.btn_quitar_logo.clicked.connect(self.quitar_logo)
        self.btn_part_nuevo.clicked.connect(self.limpiar_form_participante)
        self.btn_part_guardar.clicked.connect(self.guardar_participante)
        self.btn_part_eliminar.clicked.connect(self.eliminar_participante)
        self.tabla_participantes.itemClicked.connect(self.cargar_participante_seleccionado)

    def cargar_datos_iniciales(self):
        self.cargar_tabla_clubes()
        self.cargar_tabla_participantes()
        self.limpiar_form_club()
        self.limpiar_form_participante()

    def cargar_tabla_clubes(self):
        self.tabla_clubes.setRowCount(0)
        clubes = db.obtener_clubes()
        for row_idx, row_data in enumerate(clubes):
            self.tabla_clubes.insertRow(row_idx)
            for col_idx, cell_data in enumerate(row_data):
                self.tabla_clubes.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data) if cell_data is not None else ""))
        self.cargar_combo_clubes()

    def limpiar_form_club(self):
        self.id_club_seleccionado = None
        self.logo_club_path = None
        self.nombre_club_input.clear(); self.abrev_club_input.clear(); self.ciudad_club_input.clear()
        self.preview_logo_label.clear()
        self.preview_logo_label.setText("Sin logo")
        self.tabla_clubes.clearSelection()

    def guardar_club(self):
        nombre = self.nombre_club_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del club es obligatorio."); return
        
        exito, mensaje = db.agregar_o_actualizar_club(
            nombre, 
            self.abrev_club_input.text().strip(), 
            self.ciudad_club_input.text().strip(),
            self.logo_club_path,
            self.id_club_seleccionado
        )

        if exito:
            QMessageBox.information(self, "Operación Exitosa", mensaje)
            self.cargar_tabla_clubes(); self.limpiar_form_club()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def eliminar_club(self):
        if not self.id_club_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un club de la tabla para eliminar."); return
        confirm = QMessageBox.question(self, "Confirmar Eliminación", "¿Seguro que quieres eliminar este club?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            exito, mensaje = db.eliminar_club(self.id_club_seleccionado)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje); self.cargar_tabla_clubes(); self.limpiar_form_club()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def cargar_club_seleccionado(self, item):
        fila = self.tabla_clubes.row(item)
        self.id_club_seleccionado = int(self.tabla_clubes.item(fila, 0).text())
        self.nombre_club_input.setText(self.tabla_clubes.item(fila, 1).text())
        self.abrev_club_input.setText(self.tabla_clubes.item(fila, 2).text())
        self.ciudad_club_input.setText(self.tabla_clubes.item(fila, 3).text())
        
        self.logo_club_path = self.tabla_clubes.item(fila, 4).text()
        if self.logo_club_path and os.path.exists(self.logo_club_path):
            pixmap = QPixmap(self.logo_club_path)
            self.preview_logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.preview_logo_label.clear()
            self.preview_logo_label.setText("Sin logo")

    def seleccionar_logo(self):
        directorio = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Logo", directorio, "Imágenes (*.png *.jpg *.jpeg)"
        )
        if ruta_archivo:
            self.logo_club_path = ruta_archivo
            pixmap = QPixmap(self.logo_club_path)
            self.preview_logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def quitar_logo(self):
        self.logo_club_path = None
        self.preview_logo_label.clear()
        self.preview_logo_label.setText("Sin logo")

    def cargar_combo_clubes(self):
        self.club_part_combo.clear(); self.club_part_combo.addItem("Sin Club", None)
        clubes = db.obtener_clubes()
        for club_id, nombre, _, _, _ in clubes:
            self.club_part_combo.addItem(nombre, club_id)

    def cargar_tabla_participantes(self):
        self.tabla_participantes.setRowCount(0)
        participantes = db.obtener_participantes_con_club()
        for row_idx, row_data in enumerate(participantes):
            self.tabla_participantes.insertRow(row_idx)
            for col_idx, cell_data in enumerate(row_data):
                self.tabla_participantes.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data) if cell_data is not None else ""))

    def limpiar_form_participante(self):
        self.id_participante_seleccionado = None
        self.nombre_part_input.clear(); self.apellido_part_input.clear(); self.rut_part_input.clear()
        self.fecha_nac_part_edit.setDate(QDate(2000, 1, 1))
        self.genero_part_combo.setCurrentIndex(0); self.club_part_combo.setCurrentIndex(0)
        self.tabla_participantes.clearSelection()

    def guardar_participante(self):
        datos = {
            'nombre': self.nombre_part_input.text().strip(), 'apellido': self.apellido_part_input.text().strip(),
            'rut_o_id': self.rut_part_input.text().strip(), 'fecha_nacimiento': self.fecha_nac_part_edit.date().toString("yyyy-MM-dd"),
            'genero': self.genero_part_combo.currentText(), 'club_id': self.club_part_combo.currentData()
        }
        if not datos['nombre'] or not datos['apellido']:
            QMessageBox.warning(self, "Campos Requeridos", "Nombre y Apellido son obligatorios."); return
        exito, mensaje = db.agregar_o_actualizar_participante(datos, self.id_participante_seleccionado)
        if exito:
            QMessageBox.information(self, "Operación Exitosa", mensaje)
            self.cargar_tabla_participantes(); self.limpiar_form_participante()
        else:
            QMessageBox.critical(self, "Error", mensaje)
    
    def eliminar_participante(self):
        if not self.id_participante_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un participante de la tabla para eliminar."); return
        confirm = QMessageBox.question(self, "Confirmar Eliminación", "¿Seguro que quieres eliminar a este participante?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            exito, mensaje = db.eliminar_participante(self.id_participante_seleccionado)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje); self.cargar_tabla_participantes(); self.limpiar_form_participante()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def cargar_participante_seleccionado(self, item):
        fila = self.tabla_participantes.row(item)
        self.id_participante_seleccionado = int(self.tabla_participantes.item(fila, 0).text())
        try:
            with db.conectar_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, apellido, rut_o_id, fecha_nacimiento, genero, club_id FROM participantes WHERE id=?", (self.id_participante_seleccionado,))
                data = cursor.fetchone()
                if data:
                    self.nombre_part_input.setText(data[0])
                    self.apellido_part_input.setText(data[1])
                    self.rut_part_input.setText(data[2])
                    self.fecha_nac_part_edit.setDate(QDate.fromString(data[3], "yyyy-MM-dd"))
                    self.genero_part_combo.setCurrentText(data[4])
                    club_id = data[5]
                    index = self.club_part_combo.findData(club_id) if club_id else 0
                    self.club_part_combo.setCurrentIndex(index)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo cargar al participante: {e}")