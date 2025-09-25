# resultados_ui.py
# CORREGIDO: Ajustados los índices de las columnas para leer correctamente
# los datos de la base de datos (lugar, tiempo, estado, etc.).

import sys
import sqlite3
import datetime
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QComboBox, QAbstractItemView, QDialog,
    QInputDialog, QCheckBox
)
from PySide6.QtCore import Qt
import database_maraton as db
from tiempos_vuelta_dialog_ui import TiemposVueltaDialog

class ResultadosTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_evento_activo = None
        self.nombre_evento_activo = "Ninguno"
        self.id_categoria_activa = None
        self.categorias_info = {} 

        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        panel_seleccion = QGroupBox("Selección de Evento y Categoría")
        layout_seleccion = QHBoxLayout(panel_seleccion)
        
        self.label_evento_activo = QLabel(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        font = self.label_evento_activo.font(); font.setPointSize(12); self.label_evento_activo.setFont(font)
        
        self.combo_categorias = QComboBox()
        self.combo_categorias.setPlaceholderText("Selecciona una categoría para ver/editar resultados...")
        
        self.check_categoria_valida = QCheckBox("Prueba Válida para Puntuación")
        self.check_categoria_valida.setChecked(True); self.check_categoria_valida.setVisible(False)

        layout_seleccion.addWidget(self.label_evento_activo, 1)
        layout_seleccion.addWidget(QLabel("<b>Categoría:</b>"), 0)
        layout_seleccion.addWidget(self.combo_categorias, 2)
        layout_seleccion.addWidget(self.check_categoria_valida, 1)
        layout_seleccion.addStretch()
        layout_principal.addWidget(panel_seleccion)
        
        panel_tabla = QGroupBox("Resultados de la Categoría")
        layout_tabla = QVBoxLayout(panel_tabla)
        self.tabla_resultados = QTableWidget()
        self.column_headers = ["ID", "Nº", "Participantes", "Club(es)", "Lugar", "Tiempo Final", "Estado"]
        self.tabla_resultados.setColumnCount(len(self.column_headers))
        self.tabla_resultados.setHorizontalHeaderLabels(self.column_headers)
        self.tabla_resultados.setColumnHidden(0, True)
        self.tabla_resultados.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_resultados.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_resultados.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_resultados.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for i in [2, 3]: self.tabla_resultados.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        layout_tabla.addWidget(self.tabla_resultados)
        
        botones_layout = QHBoxLayout()
        self.btn_gestionar_tiempos = QPushButton("Ingresar/Editar Tiempos...")
        self.btn_gestionar_tiempos.setEnabled(False)
        self.btn_cambiar_estado = QPushButton("Cambiar Estado (DNF, DSQ, etc.)...")
        self.btn_cambiar_estado.setEnabled(False)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_gestionar_tiempos)
        botones_layout.addWidget(self.btn_cambiar_estado)
        layout_tabla.addLayout(botones_layout)
        
        layout_principal.addWidget(panel_tabla)

        # Conexiones
        self.combo_categorias.currentIndexChanged.connect(self.cargar_tabla_resultados)
        self.tabla_resultados.itemSelectionChanged.connect(self.actualizar_estado_botones)
        self.btn_gestionar_tiempos.clicked.connect(self.abrir_dialogo_tiempos)
        self.btn_cambiar_estado.clicked.connect(self.cambiar_estado_inscripcion)
        self.check_categoria_valida.stateChanged.connect(self.actualizar_estado_validez_categoria)
        
        print("[INFO] Pestaña Resultados inicializada.")

    def actualizar_estado_botones(self):
        is_selected = len(self.tabla_resultados.selectedItems()) > 0
        self.btn_gestionar_tiempos.setEnabled(is_selected)
        self.btn_cambiar_estado.setEnabled(is_selected)

    def actualizar_evento_activo(self, evento_id, nombre_evento):
        self.id_evento_activo = evento_id
        self.nombre_evento_activo = nombre_evento
        self.label_evento_activo.setText(f"<b>Evento Activo:</b> {self.nombre_evento_activo}")
        self.cargar_combo_categorias()

    def cargar_combo_categorias(self):
        self.combo_categorias.clear()
        self.categorias_info.clear()
        self.combo_categorias.addItem("Selecciona una categoría...", None)
        if self.id_evento_activo is not None:
            categorias = db.obtener_categorias()
            for cat_id, nombre, codigo, _, _, _, _, _, num_vueltas in categorias:
                self.combo_categorias.addItem(f"{nombre} ({codigo})", cat_id)
                self.categorias_info[cat_id] = {"numero_vueltas": num_vueltas}

    def cargar_tabla_resultados(self):
        self.tabla_resultados.blockSignals(True)
        self.tabla_resultados.setRowCount(0)
        self.actualizar_estado_botones()
        
        self.id_categoria_activa = self.combo_categorias.currentData()
        
        if self.id_evento_activo is None or self.id_categoria_activa is None:
            self.check_categoria_valida.setVisible(False)
            self.tabla_resultados.blockSignals(False)
            return
        
        self.check_categoria_valida.setVisible(True)
        es_valida_int = db.obtener_estado_categoria(self.id_evento_activo, self.id_categoria_activa)
        self.check_categoria_valida.blockSignals(True)
        self.check_categoria_valida.setChecked(bool(es_valida_int))
        self.check_categoria_valida.blockSignals(False)

        inscripciones = db.obtener_inscripciones_por_categoria(self.id_evento_activo, self.id_categoria_activa)
        for row_idx, row_data in enumerate(inscripciones):
            self.tabla_resultados.insertRow(row_idx)
            
            # --- ÍNDICES CORREGIDOS PARA LEER LOS DATOS CORRECTAMENTE ---
            nombres_list = [row_data[2], row_data[6], row_data[10], row_data[14]]
            clubes_list = [row_data[4], row_data[8], row_data[12], row_data[16]]
            
            lugar = row_data[18]
            tiempo_final = row_data[19]
            estado = row_data[20]
            # -------------------------------------------------------------

            nombres = " / ".join(filter(None, nombres_list))
            clubes = " / ".join(filter(None, clubes_list))

            self.tabla_resultados.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0]))) # ID
            self.tabla_resultados.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1]))) # Número
            self.tabla_resultados.setItem(row_idx, 2, QTableWidgetItem(nombres))
            self.tabla_resultados.setItem(row_idx, 3, QTableWidgetItem(clubes))
            self.tabla_resultados.setItem(row_idx, 4, QTableWidgetItem(str(lugar) if lugar else ""))
            self.tabla_resultados.setItem(row_idx, 5, QTableWidgetItem(tiempo_final or ""))
            self.tabla_resultados.setItem(row_idx, 6, QTableWidgetItem(estado or 'Inscrito'))

        self.tabla_resultados.blockSignals(False)

    def actualizar_estado_validez_categoria(self):
        if self.id_evento_activo is None or self.id_categoria_activa is None: return
        es_valida = self.check_categoria_valida.isChecked()
        db.actualizar_estado_categoria(self.id_evento_activo, self.id_categoria_activa, es_valida)
        
    def abrir_dialogo_tiempos(self):
        selected_items = self.tabla_resultados.selectedItems()
        if not selected_items: return

        fila_seleccionada = selected_items[0].row()
        inscripcion_id = int(self.tabla_resultados.item(fila_seleccionada, 0).text())
        numero_competidor = self.tabla_resultados.item(fila_seleccionada, 1).text()
        
        categoria_info = self.categorias_info.get(self.id_categoria_activa)
        
        if not categoria_info or categoria_info.get("numero_vueltas", 0) < 1:
            tiempo_actual = self.tabla_resultados.item(fila_seleccionada, 5).text()
            tiempo, ok = QInputDialog.getText(self, f"Tiempo Final para Nº {numero_competidor}", "Ingresa el tiempo final (HH:MM:SS.ms):", text=tiempo_actual)
            if ok and tiempo:
                db.actualizar_resultado_inscripcion(inscripcion_id, tiempo.strip(), "Finalizado")
                db.recalcular_posiciones_categoria(self.id_evento_activo, self.id_categoria_activa)
                self.cargar_tabla_resultados()
            return

        numero_vueltas = categoria_info["numero_vueltas"]
        
        inscripciones_actuales = db.obtener_inscripciones_por_categoria(self.id_evento_activo, self.id_categoria_activa)
        tiempos_vueltas_json = None
        for insc in inscripciones_actuales:
            if insc[0] == inscripcion_id:
                tiempos_vueltas_json = insc[21] # <-- ÍNDICE CORREGIDO
                break
        
        dialogo = TiemposVueltaDialog(numero_vueltas, tiempos_vueltas_json, self)
        if dialogo.exec() == QDialog.Accepted:
            tiempos_vueltas_json, tiempo_final_calculado = dialogo.get_tiempos()
            if tiempos_vueltas_json is not None:
                db.actualizar_resultado_inscripcion(inscripcion_id, tiempo_final_calculado, "Finalizado", tiempos_vueltas_json)
                db.recalcular_posiciones_categoria(self.id_evento_activo, self.id_categoria_activa)
                self.cargar_tabla_resultados()

    def cambiar_estado_inscripcion(self):
        selected_items = self.tabla_resultados.selectedItems()
        if not selected_items: return

        fila_seleccionada = selected_items[0].row()
        inscripcion_id = int(self.tabla_resultados.item(fila_seleccionada, 0).text())
        estado_actual = self.tabla_resultados.item(fila_seleccionada, 6).text()

        estados = ['Inscrito', 'Finalizado', 'DNS', 'DNF', 'DSQ']
        try: current_index = estados.index(estado_actual)
        except ValueError: current_index = 0

        estado, ok = QInputDialog.getItem(self, "Cambiar Estado", "Selecciona el nuevo estado:", estados, current_index, False)

        if ok and estado != estado_actual:
            tiempo_final = self.tabla_resultados.item(fila_seleccionada, 5).text() if estado == 'Finalizado' else None
            
            inscripciones_actuales = db.obtener_inscripciones_por_categoria(self.id_evento_activo, self.id_categoria_activa)
            tiempos_vueltas_json = None
            for insc in inscripciones_actuales:
                if insc[0] == inscripcion_id:
                    tiempos_vueltas_json = insc[21] # <-- ÍNDICE CORREGIDO
                    break
            
            exito, mensaje = db.actualizar_resultado_inscripcion(inscripcion_id, tiempo_final, estado, tiempos_vueltas_json)
            
            if exito:
                db.recalcular_posiciones_categoria(self.id_evento_activo, self.id_categoria_activa)
                self.cargar_tabla_resultados()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el estado: {mensaje}")