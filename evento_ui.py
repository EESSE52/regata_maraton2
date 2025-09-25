# evento_ui.py
# Pestaña para la gestión del Evento principal de la regata.
# CORREGIDO: Conexión a la base de datos actualizada.

import sys
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QListWidget, QListWidgetItem, QGroupBox, QDateEdit,
    QTextEdit, QAbstractItemView, QFileDialog, QInputDialog, QFormLayout
)
from PySide6.QtCore import QDate, Qt, Signal
import database_maraton as db

class EventoTabWidget(QWidget):
    evento_activo_cambiado = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.id_evento_seleccionado = None
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.init_ui()
        self.cargar_lista_eventos()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        
        panel_izquierdo = QWidget()
        layout_izquierdo = QVBoxLayout(panel_izquierdo)
        
        group_form = QGroupBox("Datos del Evento")
        form_layout = QFormLayout(group_form)
        self.nombre_evento_input = QLineEdit()
        self.fecha_evento_edit = QDateEdit(calendarPopup=True)
        self.fecha_evento_edit.setDisplayFormat("yyyy-MM-dd") # Formato estándar para DB
        self.lugar_evento_input = QLineEdit()
        self.notas_evento_input = QTextEdit()
        self.notas_evento_input.setFixedHeight(60)
        form_layout.addRow("Nombre del Evento:", self.nombre_evento_input)
        form_layout.addRow("Fecha:", self.fecha_evento_edit)
        form_layout.addRow("Lugar:", self.lugar_evento_input)
        form_layout.addRow("Notas:", self.notas_evento_input)
        
        botones_layout = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_eliminar = QPushButton("Eliminar")
        botones_layout.addWidget(self.btn_nuevo)
        botones_layout.addWidget(self.btn_guardar)
        botones_layout.addWidget(self.btn_eliminar)
        
        group_lista = QGroupBox("Eventos Guardados")
        layout_lista = QVBoxLayout(group_lista)
        self.lista_eventos_widget = QListWidget()
        self.lista_eventos_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout_lista.addWidget(self.lista_eventos_widget)

        layout_izquierdo.addWidget(group_form)
        layout_izquierdo.addLayout(botones_layout)
        layout_izquierdo.addWidget(group_lista)

        panel_derecho = QWidget()
        layout_derecho = QVBoxLayout(panel_derecho)
        
        group_activo = QGroupBox("Estado del Evento")
        layout_activo = QVBoxLayout(group_activo)
        self.label_evento_activo_titulo = QLabel("EVENTO ACTIVO:")
        font_titulo = self.label_evento_activo_titulo.font(); font_titulo.setPointSize(12)
        self.label_evento_activo_titulo.setFont(font_titulo)
        
        self.label_evento_activo_nombre = QLabel(f"<b>{self.nombre_evento_activo}</b>")
        font_nombre = self.label_evento_activo_nombre.font(); font_nombre.setPointSize(16); font_nombre.setBold(True)
        self.label_evento_activo_nombre.setFont(font_nombre)
        self.label_evento_activo_nombre.setStyleSheet("color: #005A9E;")
        self.label_evento_activo_nombre.setWordWrap(True)
        
        self.btn_seleccionar_activo = QPushButton("Seleccionar como Evento Activo")
        self.btn_seleccionar_activo.setEnabled(False)

        layout_activo.addWidget(self.label_evento_activo_titulo, 0, Qt.AlignCenter)
        layout_activo.addWidget(self.label_evento_activo_nombre, 0, Qt.AlignCenter)
        layout_activo.addStretch()
        layout_activo.addWidget(self.btn_seleccionar_activo)
        
        group_sponsors = QGroupBox("Patrocinadores del Evento Seleccionado")
        layout_sponsors = QVBoxLayout(group_sponsors)
        self.lista_sponsors_widget = QListWidget()
        botones_sponsors_layout = QHBoxLayout()
        self.btn_anadir_sponsor = QPushButton("Añadir Patrocinador...")
        self.btn_quitar_sponsor = QPushButton("Quitar Seleccionado")
        botones_sponsors_layout.addWidget(self.btn_anadir_sponsor)
        botones_sponsors_layout.addWidget(self.btn_quitar_sponsor)
        layout_sponsors.addWidget(self.lista_sponsors_widget)
        layout_sponsors.addLayout(botones_sponsors_layout)

        layout_derecho.addWidget(group_activo)
        layout_derecho.addWidget(group_sponsors)

        layout_principal.addWidget(panel_izquierdo, 1)
        layout_principal.addWidget(panel_derecho, 1)

        self.btn_nuevo.clicked.connect(self.limpiar_formulario)
        self.btn_guardar.clicked.connect(self.guardar_evento)
        self.btn_eliminar.clicked.connect(self.eliminar_evento)
        self.lista_eventos_widget.itemClicked.connect(self.cargar_evento_seleccionado)
        self.btn_seleccionar_activo.clicked.connect(self.seleccionar_evento_activo)
        self.btn_anadir_sponsor.clicked.connect(self.anadir_sponsor)
        self.btn_quitar_sponsor.clicked.connect(self.quitar_sponsor)
        
        self.limpiar_formulario()

    def limpiar_formulario(self):
        self.id_evento_seleccionado = None
        self.nombre_evento_input.clear()
        self.fecha_evento_edit.setDate(QDate.currentDate())
        self.lugar_evento_input.clear()
        self.notas_evento_input.clear()
        self.lista_eventos_widget.clearSelection()
        self.lista_sponsors_widget.clear()
        self.btn_seleccionar_activo.setEnabled(False)

    def cargar_lista_eventos(self):
        self.lista_eventos_widget.clear()
        eventos = db.obtener_eventos()
        for evento_id, nombre, fecha, lugar in eventos:
            item_text = f"{nombre} ({fecha})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, evento_id)
            self.lista_eventos_widget.addItem(item)

    def guardar_evento(self):
        nombre = self.nombre_evento_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del evento es obligatorio.")
            return
        datos = {
            'nombre_evento': nombre,
            'fecha': self.fecha_evento_edit.date().toString("yyyy-MM-dd"),
            'lugar': self.lugar_evento_input.text().strip(),
            'notas': self.notas_evento_input.toPlainText().strip()
        }
        evento_id, mensaje = db.agregar_o_actualizar_evento(datos, self.id_evento_seleccionado)
        if evento_id:
            QMessageBox.information(self, "Éxito", mensaje)
            self.cargar_lista_eventos()
            self.limpiar_formulario()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def eliminar_evento(self):
        if not self.id_evento_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un evento de la lista para eliminar.")
            return
        nombre_macro_seleccionado = self.nombre_evento_input.text()
        confirmacion = QMessageBox.question(self, "Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el evento '{nombre_macro_seleccionado}'?\n¡Esto también eliminará todas sus inscripciones y patrocinadores asociados!\n¡Esta acción no se puede deshacer!", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if confirmacion == QMessageBox.StandardButton.Yes:
            exito, mensaje = db.eliminar_evento(self.id_evento_seleccionado)
            if exito:
                QMessageBox.information(self, "Eliminado", f"Evento '{nombre_macro_seleccionado}' eliminado correctamente.")
                self.cargar_lista_eventos()
                self.limpiar_formulario()
            else:
                QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo eliminar el evento.\nError: {mensaje}")

    def cargar_evento_seleccionado(self, item):
        self.id_evento_seleccionado = item.data(Qt.UserRole)
        try:
            with db.conectar_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre_evento, fecha, lugar, notas FROM eventos WHERE id=?", (self.id_evento_seleccionado,))
                data = cursor.fetchone()
                if data:
                    self.nombre_evento_input.setText(data[0])
                    self.fecha_evento_edit.setDate(QDate.fromString(data[1], "yyyy-MM-dd"))
                    self.lugar_evento_input.setText(data[2])
                    self.notas_evento_input.setPlainText(data[3])
                    self.btn_seleccionar_activo.setEnabled(True)
                    self.cargar_sponsors_del_evento()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el evento: {e}")

    def seleccionar_evento_activo(self):
        if not self.id_evento_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un evento de la lista primero.")
            return
        self.id_evento_activo = self.id_evento_seleccionado
        self.nombre_evento_activo = self.nombre_evento_input.text()
        self.label_evento_activo_nombre.setText(f"<b>{self.nombre_evento_activo}</b>")
        self.evento_activo_cambiado.emit(self.id_evento_activo, self.nombre_evento_activo)
        QMessageBox.information(self, "Evento Activo", f"'{self.nombre_evento_activo}' ha sido seleccionado como el evento activo.")

    def cargar_sponsors_del_evento(self):
        self.lista_sponsors_widget.clear()
        if self.id_evento_seleccionado:
            sponsors = db.obtener_sponsors_por_evento(self.id_evento_seleccionado)
            for sponsor_id, nombre, logo_path in sponsors:
                item = QListWidgetItem(nombre)
                item.setData(Qt.UserRole, sponsor_id)
                self.lista_sponsors_widget.addItem(item)

    def anadir_sponsor(self):
        if not self.id_evento_seleccionado:
            QMessageBox.warning(self, "Sin Evento", "Primero selecciona un evento para añadirle un patrocinador.")
            return
        logo_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Logo del Patrocinador", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not logo_path:
            return
        nombre_sponsor, ok = QInputDialog.getText(self, "Nombre del Patrocinador", "Ingresa el nombre del patrocinador:")
        if ok and nombre_sponsor:
            _, mensaje = db.agregar_sponsor(nombre_sponsor, logo_path, self.id_evento_seleccionado)
            QMessageBox.information(self, "Éxito", mensaje)
            self.cargar_sponsors_del_evento()
        elif ok:
            QMessageBox.warning(self, "Nombre Requerido", "El nombre del patrocinador no puede estar vacío.")

    def quitar_sponsor(self):
        item_seleccionado = self.lista_sponsors_widget.currentItem()
        if not item_seleccionado:
            QMessageBox.warning(self, "Sin Selección", "Selecciona un patrocinador de la lista para quitarlo.")
            return
        sponsor_id = item_seleccionado.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Confirmar", f"¿Seguro que quieres quitar al patrocinador '{item_seleccionado.text()}'?")
        if confirm == QMessageBox.StandardButton.Yes:
            exito, mensaje = db.eliminar_sponsor(sponsor_id)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_sponsors_del_evento()
            else:
                QMessageBox.critical(self, "Error", mensaje)