# ui/participantes_ui.py
# Pestaña para la gestión de Clubes y Participantes

import sys
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QGroupBox, QComboBox, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import QDate, Qt
import database_maraton as db

class ParticipantesTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_club_seleccionado = None
        self.id_participante_seleccionado = None

        # Layout principal de la pestaña (horizontal)
        layout_principal = QHBoxLayout(self)
        layout_principal.setSpacing(15)

        # --- Panel Izquierdo: Gestión de Clubes ---
        panel_clubes = QGroupBox("Gestión de Clubes")
        layout_clubes = QVBoxLayout(panel_clubes)
        
        form_club = QFormLayout()
        self.nombre_club_input = QLineEdit()
        self.abrev_club_input = QLineEdit()
        self.ciudad_club_input = QLineEdit()
        form_club.addRow("Nombre Club:", self.nombre_club_input)
        form_club.addRow("Abreviatura:", self.abrev_club_input)
        form_club.addRow("Ciudad:", self.ciudad_club_input)
        
        botones_club_layout = QHBoxLayout()
        self.btn_club_nuevo = QPushButton("Nuevo")
        self.btn_club_guardar = QPushButton("Guardar")
        self.btn_club_eliminar = QPushButton("Eliminar")
        botones_club_layout.addWidget(self.btn_club_nuevo)
        botones_club_layout.addWidget(self.btn_club_guardar)
        botones_club_layout.addWidget(self.btn_club_eliminar)
        
        self.tabla_clubes = QTableWidget()
        self.tabla_clubes.setColumnCount(4)
        self.tabla_clubes.setHorizontalHeaderLabels(["ID", "Nombre", "Abrev.", "Ciudad"])
        self.tabla_clubes.setColumnHidden(0, True)
        self.tabla_clubes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_clubes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_clubes.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout_clubes.addLayout(form_club)
        layout_clubes.addLayout(botones_club_layout)
        layout_clubes.addWidget(self.tabla_clubes)
        
        # --- Panel Derecho: Gestión de Participantes ---
        panel_participantes = QGroupBox("Gestión de Participantes")
        layout_participantes = QVBoxLayout(panel_participantes)

        form_participante = QFormLayout()
        self.nombre_part_input = QLineEdit()
        self.apellido_part_input = QLineEdit()
        self.rut_part_input = QLineEdit()
        self.fecha_nac_part_edit = QDateEdit(calendarPopup=True)
        self.fecha_nac_part_edit.setDisplayFormat("dd-MM-yyyy")
        self.genero_part_combo = QComboBox()
        self.genero_part_combo.addItems(["Masculino", "Femenino"])
        self.club_part_combo = QComboBox()
        form_participante.addRow("Nombre:", self.nombre_part_input)
        form_participante.addRow("Apellido:", self.apellido_part_input)
        form_participante.addRow("RUT / ID:", self.rut_part_input)
        form_participante.addRow("Fecha Nacimiento:", self.fecha_nac_part_edit)
        form_participante.addRow("Género:", self.genero_part_combo)
        form_participante.addRow("Club:", self.club_part_combo)

        botones_part_layout = QHBoxLayout()
        self.btn_part_nuevo = QPushButton("Nuevo")
        self.btn_part_guardar = QPushButton("Guardar")
        self.btn_part_eliminar = QPushButton("Eliminar")
        botones_part_layout.addWidget(self.btn_part_nuevo)
        botones_part_layout.addWidget(self.btn_part_guardar)
        botones_part_layout.addWidget(self.btn_part_eliminar)

        self.tabla_participantes = QTableWidget()
        self.tabla_participantes.setColumnCount(7)
        self.tabla_participantes.setHorizontalHeaderLabels(["ID", "Nombre", "Apellido", "RUT/ID", "F. Nac.", "Género", "Club"])
        self.tabla_participantes.setColumnHidden(0, True)
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_participantes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_participantes.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout_participantes.addLayout(form_participante)
        layout_participantes.addLayout(botones_part_layout)
        layout_participantes.addWidget(self.tabla_participantes)

        # Añadir paneles al layout principal
        layout_principal.addWidget(panel_clubes, 1)
        layout_principal.addWidget(panel_participantes, 2) # Darle más espacio a los participantes

        # Conexiones
        self.btn_club_nuevo.clicked.connect(self.limpiar_form_club)
        self.btn_club_guardar.clicked.connect(self.guardar_club)
        self.btn_club_eliminar.clicked.connect(self.eliminar_club)
        self.tabla_clubes.itemClicked.connect(self.cargar_club_seleccionado)

        self.btn_part_nuevo.clicked.connect(self.limpiar_form_participante)
        self.btn_part_guardar.clicked.connect(self.guardar_participante)
        self.btn_part_eliminar.clicked.connect(self.eliminar_participante)
        self.tabla_participantes.itemClicked.connect(self.cargar_participante_seleccionado)

        # Carga inicial de datos
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self):
        self.cargar_tabla_clubes()
        self.cargar_tabla_participantes()
        self.cargar_combo_clubes()
        self.limpiar_form_club()
        self.limpiar_form_participante()

    # --- Métodos para Clubes ---
    def cargar_tabla_clubes(self):
        self.tabla_clubes.setRowCount(0)
        clubes = db.obtener_clubes()
        for row_idx, row_data in enumerate(clubes):
            self.tabla_clubes.insertRow(row_idx)
            for col_idx, cell_data in enumerate(row_data):
                self.tabla_clubes.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        self.cargar_combo_clubes() # Actualizar combo de participantes

    def limpiar_form_club(self):
        self.id_club_seleccionado = None
        self.nombre_club_input.clear()
        self.abrev_club_input.clear()
        self.ciudad_club_input.clear()
        self.tabla_clubes.clearSelection()

    def guardar_club(self):
        nombre = self.nombre_club_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del club es obligatorio.")
            return
        
        abrev = self.abrev_club_input.text().strip()
        ciudad = self.ciudad_club_input.text().strip()
        
        _, mensaje = db.agregar_o_actualizar_club(nombre, abrev, ciudad, self.id_club_seleccionado)
        QMessageBox.information(self, "Operación Exitosa", mensaje)
        self.cargar_tabla_clubes()
        self.limpiar_form_club()

    def eliminar_club(self):
        if not self.id_club_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un club de la tabla para eliminar.")
            return
        
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Seguro que quieres eliminar este club?\nLos participantes de este club no serán eliminados, pero quedarán sin club asignado.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            exito, mensaje = db.eliminar_club(self.id_club_seleccionado)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_tabla_clubes()
                self.limpiar_form_club()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def cargar_club_seleccionado(self, item):
        fila = self.tabla_clubes.row(item)
        self.id_club_seleccionado = int(self.tabla_clubes.item(fila, 0).text())
        self.nombre_club_input.setText(self.tabla_clubes.item(fila, 1).text())
        self.abrev_club_input.setText(self.tabla_clubes.item(fila, 2).text())
        self.ciudad_club_input.setText(self.tabla_clubes.item(fila, 3).text())

    # --- Métodos para Participantes ---
    def cargar_combo_clubes(self):
        self.club_part_combo.clear()
        self.club_part_combo.addItem("Sin Club", None) # Opción para participantes sin club
        clubes = db.obtener_clubes()
        for club_id, nombre, _, _ in clubes:
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
        self.nombre_part_input.clear()
        self.apellido_part_input.clear()
        self.rut_part_input.clear()
        self.fecha_nac_part_edit.setDate(QDate(2000, 1, 1))
        self.genero_part_combo.setCurrentIndex(0)
        self.club_part_combo.setCurrentIndex(0)
        self.tabla_participantes.clearSelection()

    def guardar_participante(self):
        datos = {
            'nombre': self.nombre_part_input.text().strip(),
            'apellido': self.apellido_part_input.text().strip(),
            'rut_o_id': self.rut_part_input.text().strip(),
            'fecha_nacimiento': self.fecha_nac_part_edit.date().toString("yyyy-MM-dd"),
            'genero': self.genero_part_combo.currentText(),
            'club_id': self.club_part_combo.currentData()
        }
        if not datos['nombre'] or not datos['apellido']:
            QMessageBox.warning(self, "Campos Requeridos", "Nombre y Apellido son obligatorios.")
            return

        _, mensaje = db.agregar_o_actualizar_participante(datos, self.id_participante_seleccionado)
        QMessageBox.information(self, "Operación Exitosa", mensaje)
        self.cargar_tabla_participantes()
        self.limpiar_form_participante()
    
    def eliminar_participante(self):
        if not self.id_participante_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un participante de la tabla para eliminar.")
            return
        
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Seguro que quieres eliminar a este participante?\nEsto también lo eliminará de cualquier inscripción en la que se encuentre.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            exito, mensaje = db.eliminar_participante(self.id_participante_seleccionado)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_tabla_participantes()
                self.limpiar_form_participante()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def cargar_participante_seleccionado(self, item):
        fila = self.tabla_participantes.row(item)
        self.id_participante_seleccionado = int(self.tabla_participantes.item(fila, 0).text())
        self.nombre_part_input.setText(self.tabla_participantes.item(fila, 1).text())
        self.apellido_part_input.setText(self.tabla_participantes.item(fila, 2).text())
        self.rut_part_input.setText(self.tabla_participantes.item(fila, 3).text())
        self.fecha_nac_part_edit.setDate(QDate.fromString(self.tabla_participantes.item(fila, 4).text(), "yyyy-MM-dd"))
        self.genero_part_combo.setCurrentText(self.tabla_participantes.item(fila, 5).text())
        
        club_nombre = self.tabla_participantes.item(fila, 6).text()
        if club_nombre and club_nombre != "None":
            index = self.club_part_combo.findText(club_nombre)
            if index >= 0:
                self.club_part_combo.setCurrentIndex(index)
        else:
            self.club_part_combo.setCurrentIndex(0) # "Sin Club"