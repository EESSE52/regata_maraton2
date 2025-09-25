# programa_ui.py
# CORREGIDO: Se añaden los widgets de hora y minutos al layout para que sean visibles.

import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
    QTimeEdit, QSpinBox
)
from PySide6.QtCore import Qt, QTime
import database_maraton as db

class ProgramaTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"

        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        
        # --- Panel Izquierdo: Categorías Disponibles ---
        panel_izquierdo = QGroupBox("Categorías Disponibles")
        layout_izquierdo = QVBoxLayout(panel_izquierdo)
        self.lista_categorias_disponibles = QListWidget()
        self.btn_anadir_categoria = QPushButton("Añadir al Programa →")
        layout_izquierdo.addWidget(self.lista_categorias_disponibles)
        layout_izquierdo.addWidget(self.btn_anadir_categoria)

        # --- Panel Central: Programa de Pruebas ---
        panel_central = QGroupBox("Programa del Evento")
        layout_central = QVBoxLayout(panel_central)
        self.lista_programa = QListWidget()
        self.lista_programa.setDragDropMode(QListWidget.InternalMove) # Permite reordenar
        layout_central.addWidget(self.lista_programa)

        # --- Panel Derecho: Controles y Acciones ---
        panel_derecho = QGroupBox("Configuración y Acciones")
        layout_derecho = QVBoxLayout(panel_derecho)
        
        layout_controles = QVBoxLayout()
        layout_controles.addWidget(QLabel("Hora de Inicio (1ª Prueba):"))
        self.time_edit_inicio = QTimeEdit()
        self.time_edit_inicio.setDisplayFormat("HH:mm")
        self.time_edit_inicio.setTime(QTime(9, 0))
        layout_controles.addWidget(self.time_edit_inicio) # <-- LÍNEA AÑADIDA
        
        layout_controles.addWidget(QLabel("Minutos entre Pruebas:"))
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 120)
        self.spin_intervalo.setValue(15)
        layout_controles.addWidget(self.spin_intervalo) # <-- LÍNEA AÑADIDA
        
        self.btn_calcular_horarios = QPushButton("Calcular Horarios")
        self.btn_quitar_categoria = QPushButton("← Quitar del Programa")
        self.btn_guardar_programa = QPushButton("Guardar Programa")
        
        layout_derecho.addLayout(layout_controles)
        layout_derecho.addWidget(self.btn_calcular_horarios)
        layout_derecho.addStretch()
        layout_derecho.addWidget(self.btn_quitar_categoria)
        layout_derecho.addWidget(self.btn_guardar_programa)

        layout_principal.addWidget(panel_izquierdo, 1)
        layout_principal.addWidget(panel_central, 2)
        layout_principal.addWidget(panel_derecho, 1)

        # Conexiones
        self.btn_anadir_categoria.clicked.connect(self.anadir_categoria_al_programa)
        self.btn_quitar_categoria.clicked.connect(self.quitar_categoria_del_programa)
        self.btn_calcular_horarios.clicked.connect(self.calcular_horarios)
        self.btn_guardar_programa.clicked.connect(self.guardar_programa)

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        self.cargar_listas()

    def cargar_listas(self):
        self.lista_categorias_disponibles.clear()
        self.lista_programa.clear()

        if not self.id_evento_activo:
            return

        categorias_en_programa_ids = {item[0] for item in db.obtener_programa_pruebas(self.id_evento_activo)}
        
        # Cargar programa existente
        programa_guardado = db.obtener_programa_pruebas(self.id_evento_activo)
        for cat_id, nombre, codigo, hora in programa_guardado:
            item_text = f"{hora or 'HH:MM'} - {nombre} ({codigo})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, cat_id)
            self.lista_programa.addItem(item)
            
        # Cargar categorías que no están en el programa
        todas_las_categorias = db.obtener_categorias()
        for cat_id, nombre, codigo, *_ in todas_las_categorias:
            if cat_id not in categorias_en_programa_ids:
                item_text = f"{nombre} ({codigo})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, cat_id)
                self.lista_categorias_disponibles.addItem(item)

    def anadir_categoria_al_programa(self):
        item_seleccionado = self.lista_categorias_disponibles.currentItem()
        if not item_seleccionado:
            return
            
        # Lo quitamos de la lista de disponibles y lo añadimos al programa
        item = self.lista_categorias_disponibles.takeItem(self.lista_categorias_disponibles.row(item_seleccionado))
        item.setText(f"HH:MM - {item.text()}") # Añadimos placeholder de hora
        self.lista_programa.addItem(item)
    
    def quitar_categoria_del_programa(self):
        item_seleccionado = self.lista_programa.currentItem()
        if not item_seleccionado:
            return
            
        item = self.lista_programa.takeItem(self.lista_programa.row(item_seleccionado))
        # Le quitamos el formato de hora antes de devolverlo
        texto_original = item.text().split(' - ', 1)[1]
        item.setText(texto_original)
        self.lista_categorias_disponibles.addItem(item)

    def calcular_horarios(self):
        hora_actual = self.time_edit_inicio.time().toPython()
        intervalo = timedelta(minutes=self.spin_intervalo.value())
        
        for i in range(self.lista_programa.count()):
            item = self.lista_programa.item(i)
            texto_original = item.text().split(' - ', 1)[1]
            item.setText(f"{hora_actual.strftime('%H:%M')} - {texto_original}")
            
            # Sumamos el intervalo para la siguiente prueba
            dt_hora_actual = datetime.combine(datetime.today(), hora_actual)
            hora_actual = (dt_hora_actual + intervalo).time()
            
    def guardar_programa(self):
        if not self.id_evento_activo:
            QMessageBox.warning(self, "Sin Evento", "No hay un evento activo seleccionado.")
            return

        programa_para_db = []
        for i in range(self.lista_programa.count()):
            item = self.lista_programa.item(i)
            cat_id = item.data(Qt.UserRole)
            hora = item.text().split(' - ', 1)[0]
            if hora == "HH:MM": # Si no se calcularon los horarios, no guardar hora
                hora = None
                
            # Formato: (evento_id, categoria_id, orden, hora_inicio)
            programa_para_db.append((self.id_evento_activo, cat_id, i + 1, hora))

        exito, mensaje = db.guardar_programa_pruebas(self.id_evento_activo, programa_para_db)
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el programa: {mensaje}")