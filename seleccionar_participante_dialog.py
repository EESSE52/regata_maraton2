# seleccionar_participante_dialog.py
# Diálogo para buscar y seleccionar un participante.

import sys
import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QDialogButtonBox, QMessageBox, QPushButton
)
from PySide6.QtCore import Qt
import database_maraton as db

class SeleccionarParticipanteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Participante")
        self.setMinimumSize(700, 500)
        self.selected_participante_info = None

        layout = QVBoxLayout(self)

        # Filtro
        filter_layout = QHBoxLayout()
        self.filtro_input = QLineEdit()
        self.filtro_input.setPlaceholderText("Buscar por nombre, apellido, RUT o club...")
        self.filtro_input.textChanged.connect(self.filtrar_tabla)
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.filtro_input)
        layout.addLayout(filter_layout)

        # Tabla
        self.tabla_participantes = QTableWidget()
        self.column_headers = ["ID", "Nombre", "Apellido", "RUT/ID", "Club"] 
        self.tabla_participantes.setColumnCount(len(self.column_headers))
        self.tabla_participantes.setHorizontalHeaderLabels(self.column_headers)
        self.tabla_participantes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_participantes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_participantes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_participantes.setColumnHidden(0, True) # Ocultar ID
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_participantes.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        self.tabla_participantes.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.tabla_participantes)

        # Botones
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.cargar_tabla_participantes()

    def cargar_tabla_participantes(self, filtro=None):
        self.tabla_participantes.setRowCount(0)
        participantes = db.obtener_participantes_con_club()
        
        for row_idx, row_data in enumerate(participantes):
            # p.id, p.nombre, p.apellido, p.rut_o_id, ..., c.nombre_club
            id_part, nombre, apellido, rut, _, _, club = row_data
            
            if filtro:
                filtro_lower = filtro.lower()
                if not (filtro_lower in nombre.lower() or 
                        filtro_lower in apellido.lower() or 
                        (rut and filtro_lower in rut.lower()) or 
                        (club and filtro_lower in club.lower())):
                    continue

            self.tabla_participantes.insertRow(self.tabla_participantes.rowCount())
            current_row = self.tabla_participantes.rowCount() - 1
            
            self.tabla_participantes.setItem(current_row, 0, QTableWidgetItem(str(id_part)))
            self.tabla_participantes.setItem(current_row, 1, QTableWidgetItem(nombre))
            self.tabla_participantes.setItem(current_row, 2, QTableWidgetItem(apellido))
            self.tabla_participantes.setItem(current_row, 3, QTableWidgetItem(rut or ""))
            self.tabla_participantes.setItem(current_row, 4, QTableWidgetItem(club or "Sin Club"))

    def filtrar_tabla(self):
        self.cargar_tabla_participantes(self.filtro_input.text())

    def accept(self):
        selected_items = self.tabla_participantes.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona un participante de la tabla.")
            return
        
        selected_row = selected_items[0].row()
        part_id = int(self.tabla_participantes.item(selected_row, 0).text())
        nombre_completo = f"{self.tabla_participantes.item(selected_row, 1).text()} {self.tabla_participantes.item(selected_row, 2).text()}"
        
        self.selected_participante_info = {"id": part_id, "nombre": nombre_completo}
        super().accept()

    def get_selected_participante_info(self):
        return self.selected_participante_info