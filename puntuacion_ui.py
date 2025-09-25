# puntuacion_ui.py
# CORREGIDO: Actualizados los bucles para manejar la nueva estructura de datos con logo_path.

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSpinBox, QFormLayout, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import database_maraton as db

class PuntuacionTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.spinboxes_puntuacion = {}

        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(15)

        panel_control = QGroupBox("Control del Evento y Puntuación")
        panel_control.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2a5c7a;
            }
        """)
        layout_control = QHBoxLayout(panel_control)
        
        self.label_evento_activo = QLabel(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_evento_activo.setFont(font)
        self.label_evento_activo.setStyleSheet("color: #2a5c7a;")
        
        self.btn_calcular = QPushButton("Calcular Puntuaciones y Medallero")
        self.btn_calcular.setStyleSheet("""
            QPushButton {
                font-weight: bold; 
                padding: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4ca1d9, stop:1 #2a7bb9);
                color: white;
                border: 1px solid #1a6da9;
                border-radius: 5px;
                min-width: 250px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5cb1e9, stop:1 #3a8bc9);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2a7bb9, stop:1 #4ca1d9);
            }
        """)

        layout_control.addWidget(self.label_evento_activo, 1)
        layout_control.addWidget(self.btn_calcular)
        
        layout_principal.addWidget(panel_control)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #c4d8e2, stop:1 #a8d4f0);
                width: 5px;
            }
        """)

        panel_izquierdo = QWidget()
        layout_izquierdo = QVBoxLayout(panel_izquierdo)
        layout_izquierdo.setContentsMargins(5, 5, 5, 5)
        layout_izquierdo.setSpacing(10)

        group_config = QGroupBox("Sistema de Puntuación")
        group_config.setStyleSheet("QGroupBox { font-weight: bold; color: #2a5c7a; }")
        form_puntuacion = QFormLayout(group_config)
        form_puntuacion.setVerticalSpacing(8); form_puntuacion.setHorizontalSpacing(15)
        
        for i in range(1, 11):
            spinner = QSpinBox()
            spinner.setRange(0, 100)
            puntajes_defecto = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
            spinner.setValue(puntajes_defecto.get(i, 0))
            spinner.setStyleSheet("QSpinBox { min-width: 60px; max-width: 80px; }")
            self.spinboxes_puntuacion[i] = spinner
            form_puntuacion.addRow(f"{i}º Lugar:", spinner)

        group_tabla_puntos = QGroupBox("Ranking por Puntos")
        group_tabla_puntos.setStyleSheet("QGroupBox { font-weight: bold; color: #2a5c7a; }")
        layout_tabla_puntos = QVBoxLayout(group_tabla_puntos)
        self.tabla_puntuacion = QTableWidget()
        self.tabla_puntuacion.setColumnCount(3)
        self.tabla_puntuacion.setHorizontalHeaderLabels(["Lugar", "Club", "Puntuación Total"])
        self.tabla_puntuacion.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_puntuacion.setEditTriggers(QTableWidget.NoEditTriggers)
        layout_tabla_puntos.addWidget(self.tabla_puntuacion)

        layout_izquierdo.addWidget(group_config)
        layout_izquierdo.addWidget(group_tabla_puntos)
        
        panel_derecho = QWidget()
        layout_derecho = QVBoxLayout(panel_derecho)
        layout_derecho.setContentsMargins(5, 5, 5, 5)
        layout_derecho.setSpacing(10)
        
        group_tabla_medallas = QGroupBox("Ranking por Medallas (Medallero)")
        group_tabla_medallas.setStyleSheet("QGroupBox { font-weight: bold; color: #2a5c7a; }")
        layout_tabla_medallas = QVBoxLayout(group_tabla_medallas)
        self.tabla_medallas = QTableWidget()
        self.tabla_medallas.setColumnCount(5)
        self.tabla_medallas.setHorizontalHeaderLabels(["Lugar", "Club", "🥇 Oro", "🥈 Plata", "🥉 Bronce"])
        self.tabla_medallas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_medallas.setEditTriggers(QTableWidget.NoEditTriggers)
        layout_tabla_medallas.addWidget(self.tabla_medallas)
        
        layout_derecho.addWidget(group_tabla_medallas)

        splitter.addWidget(panel_izquierdo)
        splitter.addWidget(panel_derecho)
        splitter.setSizes([350, 650])

        layout_principal.addWidget(splitter)

        self.btn_calcular.clicked.connect(self.calcular_y_mostrar_todo)

        print("[INFO] Pestaña Puntuación inicializada.")

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        """Slot para recibir la señal del evento activo."""
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        self.label_evento_activo.setText(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        self.tabla_puntuacion.setRowCount(0)
        self.tabla_medallas.setRowCount(0)

    def calcular_y_mostrar_todo(self):
        if self.id_evento_activo is None:
            QMessageBox.warning(self, "Sin Evento", "Primero selecciona un evento activo en la pestaña 'Evento'.")
            return
        
        self.calcular_puntuacion()
        self.calcular_medallero()

        QMessageBox.information(self, "Cálculo Completo", "Se ha actualizado el ranking por puntos y el medallero.")

    def calcular_puntuacion(self):
        sistema_puntuacion = {lugar: spinner.value() for lugar, spinner in self.spinboxes_puntuacion.items() if spinner.value() > 0}
        if not sistema_puntuacion:
            QMessageBox.warning(self, "Sin Puntuación", "Define al menos un puntaje para poder calcular el ranking por puntos.")
            return

        resultados_clubes = db.calcular_puntuacion_clubes(self.id_evento_activo, sistema_puntuacion)
        
        self.tabla_puntuacion.setRowCount(0)
        # --- CORRECCIÓN AQUÍ ---
        # Ahora desempaquetamos 3 valores: nombre, logo y puntuación.
        for row_idx, (nombre_club, logo_path, puntuacion) in enumerate(resultados_clubes):
            self.tabla_puntuacion.insertRow(row_idx)
            self.tabla_puntuacion.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            self.tabla_puntuacion.setItem(row_idx, 1, QTableWidgetItem(nombre_club))
            self.tabla_puntuacion.setItem(row_idx, 2, QTableWidgetItem(str(puntuacion)))

    def calcular_medallero(self):
        medallero = db.calcular_ranking_medallas(self.id_evento_activo)
        
        self.tabla_medallas.setRowCount(0)
        # --- CORRECCIÓN AQUÍ ---
        # Ahora desempaquetamos 5 valores: nombre, logo, oro, plata y bronce.
        for row_idx, (nombre_club, logo_path, oro, plata, bronce) in enumerate(medallero):
            self.tabla_medallas.insertRow(row_idx)
            self.tabla_medallas.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            self.tabla_medallas.setItem(row_idx, 1, QTableWidgetItem(nombre_club))
            self.tabla_medallas.setItem(row_idx, 2, QTableWidgetItem(str(oro)))
            self.tabla_medallas.setItem(row_idx, 3, QTableWidgetItem(str(plata)))
            self.tabla_medallas.setItem(row_idx, 4, QTableWidgetItem(str(bronce)))