# gestion_deportista_ui.py
# Nueva pestaña para buscar un deportista y gestionar sus inscripciones.

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QAbstractItemView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
import database_maraton as db

class GestionDeportistaTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.deportista_seleccionado_id = None

        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # --- Panel Izquierdo: Búsqueda y Selección ---
        panel_izquierdo = QGroupBox("Buscar Deportista")
        layout_izquierdo = QVBoxLayout(panel_izquierdo)

        self.buscador_input = QLineEdit()
        self.buscador_input.setPlaceholderText("Escribe un nombre o apellido para buscar...")
        
        self.lista_resultados_busqueda = QListWidget()

        layout_izquierdo.addWidget(self.buscador_input)
        layout_izquierdo.addWidget(self.lista_resultados_busqueda)

        # --- Panel Derecho: Inscripciones del Deportista ---
        panel_derecho = QGroupBox("Inscripciones en el Evento Activo")
        layout_derecho = QVBoxLayout(panel_derecho)

        self.label_deportista_seleccionado = QLabel("<i>Ningún deportista seleccionado.</i>")
        font = self.label_deportista_seleccionado.font()
        font.setPointSize(12)
        self.label_deportista_seleccionado.setFont(font)
        self.label_deportista_seleccionado.setAlignment(Qt.AlignCenter)

        self.tabla_inscripciones_deportista = QTableWidget()
        self.tabla_inscripciones_deportista.setColumnCount(4)
        self.tabla_inscripciones_deportista.setHorizontalHeaderLabels(["ID Inscripción", "Categoría", "Nº Bote", "Compañeros de Bote"])
        self.tabla_inscripciones_deportista.setColumnHidden(0, True)
        self.tabla_inscripciones_deportista.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_inscripciones_deportista.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla_inscripciones_deportista.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_inscripciones_deportista.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.btn_eliminar_inscripcion = QPushButton("Eliminar Inscripción Seleccionada")
        self.btn_eliminar_inscripcion.setEnabled(False)

        layout_derecho.addWidget(self.label_deportista_seleccionado)
        layout_derecho.addWidget(self.tabla_inscripciones_deportista)
        layout_derecho.addWidget(self.btn_eliminar_inscripcion, 0, Qt.AlignRight)
        
        layout_principal.addWidget(panel_izquierdo, 1)
        layout_principal.addWidget(panel_derecho, 2)

        # Conexiones
        self.buscador_input.textChanged.connect(self._buscar_deportistas)
        self.lista_resultados_busqueda.itemClicked.connect(self._seleccionar_deportista)
        self.tabla_inscripciones_deportista.itemSelectionChanged.connect(lambda: self.btn_eliminar_inscripcion.setEnabled(True))
        self.btn_eliminar_inscripcion.clicked.connect(self.eliminar_inscripcion_seleccionada)

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        """Se activa cuando cambia el evento activo en la pestaña principal."""
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        # Si ya había un deportista seleccionado, recargamos sus inscripciones para el nuevo evento
        if self.deportista_seleccionado_id:
            self._cargar_inscripciones_deportista()

    def _buscar_deportistas(self):
        """Busca en la BD y actualiza la lista de resultados."""
        texto = self.buscador_input.text()
        self.lista_resultados_busqueda.clear()
        if len(texto) < 3: # No buscar hasta que haya al menos 3 caracteres
            return
        
        resultados = db.buscar_deportistas_por_nombre(texto)
        for deportista_id, nombre, club in resultados:
            item = QListWidgetItem(f"{nombre} ({club or 'Sin Club'})")
            item.setData(Qt.UserRole, deportista_id)
            self.lista_resultados_busqueda.addItem(item)

    def _seleccionar_deportista(self, item):
        """Al hacer clic en un deportista, carga sus datos."""
        self.deportista_seleccionado_id = item.data(Qt.UserRole)
        nombre_completo = item.text()
        self.label_deportista_seleccionado.setText(f"Mostrando inscripciones para: <b>{nombre_completo}</b>")
        self._cargar_inscripciones_deportista()

    def _cargar_inscripciones_deportista(self):
        """Rellena la tabla con las inscripciones del deportista seleccionado."""
        self.tabla_inscripciones_deportista.setRowCount(0)
        self.btn_eliminar_inscripcion.setEnabled(False)

        if not self.deportista_seleccionado_id or not self.id_evento_activo:
            return
            
        inscripciones = db.obtener_inscripciones_de_deportista(self.id_evento_activo, self.deportista_seleccionado_id)
        
        for row, data in enumerate(inscripciones):
            self.tabla_inscripciones_deportista.insertRow(row)
            self.tabla_inscripciones_deportista.setItem(row, 0, QTableWidgetItem(str(data['inscripcion_id'])))
            self.tabla_inscripciones_deportista.setItem(row, 1, QTableWidgetItem(data['categoria']))
            self.tabla_inscripciones_deportista.setItem(row, 2, QTableWidgetItem(str(data['numero_bote'])))
            self.tabla_inscripciones_deportista.setItem(row, 3, QTableWidgetItem(data['companeros']))

    def eliminar_inscripcion_seleccionada(self):
        """Elimina la inscripción que está seleccionada en la tabla."""
        selected_items = self.tabla_inscripciones_deportista.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Sin selección", "Por favor, selecciona una inscripción de la tabla para eliminarla.")
            return

        fila = selected_items[0].row()
        inscripcion_id = int(self.tabla_inscripciones_deportista.item(fila, 0).text())
        
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Estás seguro de que quieres eliminar esta inscripción?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            exito, mensaje = db.eliminar_inscripcion(inscripcion_id)
            if exito:
                QMessageBox.information(self, "Éxito", "Inscripción eliminada correctamente.")
                # Recargamos la lista para que desaparezca la inscripción eliminada
                self._cargar_inscripciones_deportista()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la inscripción: {mensaje}")