# categorias_ui.py
# Pestaña para la gestión de Categorías de la competición.

import sys
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QAbstractItemView
)
from PySide6.QtCore import Qt
import database_maraton as db

class CategoriasTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id_categoria_seleccionada = None
        self.init_ui()
        self.cargar_tabla_categorias()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setSpacing(15)

        # Panel Izquierdo: Formulario
        panel_formulario = QGroupBox("Detalles de la Categoría")
        form_layout = QFormLayout(panel_formulario)
        
        self.nombre_cat_input = QLineEdit()
        self.codigo_cat_input = QLineEdit()
        self.tipo_emb_input = QLineEdit()
        self.distancia_input = QDoubleSpinBox()
        self.distancia_input.setRange(0, 999.99)
        self.distancia_input.setSuffix(" km")
        self.vueltas_input = QSpinBox()
        self.vueltas_input.setRange(0, 99)
        self.edad_min_input = QSpinBox()
        self.edad_min_input.setRange(0, 99)
        self.edad_max_input = QSpinBox()
        self.edad_max_input.setRange(0, 99)
        self.edad_max_input.setValue(99)
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["Varones", "Damas", "Mixto", "Todo Competidor"])

        form_layout.addRow("Nombre Categoría:", self.nombre_cat_input)
        form_layout.addRow("Código (ej. K1SV):", self.codigo_cat_input)
        form_layout.addRow("Tipo Embarcación (K1, C2...):", self.tipo_emb_input)
        form_layout.addRow("Género:", self.genero_combo)
        form_layout.addRow("Edad Mínima:", self.edad_min_input)
        form_layout.addRow("Edad Máxima:", self.edad_max_input)
        form_layout.addRow("Distancia (km):", self.distancia_input)
        form_layout.addRow("Nº Vueltas:", self.vueltas_input)

        botones_layout = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_eliminar = QPushButton("Eliminar")
        botones_layout.addWidget(self.btn_nuevo)
        botones_layout.addWidget(self.btn_guardar)
        botones_layout.addWidget(self.btn_eliminar)
        form_layout.addRow(botones_layout)

        # Panel Derecho: Tabla
        panel_tabla = QGroupBox("Categorías Definidas")
        layout_tabla = QVBoxLayout(panel_tabla)
        self.tabla_categorias = QTableWidget()
        self.column_headers = ["ID", "Nombre", "Código", "Edades", "Género", "Embarcación", "Dist.", "Vueltas"]
        self.tabla_categorias.setColumnCount(len(self.column_headers))
        self.tabla_categorias.setHorizontalHeaderLabels(self.column_headers)
        self.tabla_categorias.setColumnHidden(0, True)
        self.tabla_categorias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_categorias.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_categorias.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout_tabla.addWidget(self.tabla_categorias)

        layout_principal.addWidget(panel_formulario, 1)
        layout_principal.addWidget(panel_tabla, 2)

        # Conexiones
        self.btn_nuevo.clicked.connect(self.limpiar_formulario)
        self.btn_guardar.clicked.connect(self.guardar_categoria)
        self.btn_eliminar.clicked.connect(self.eliminar_categoria)
        self.tabla_categorias.itemClicked.connect(self.cargar_categoria_seleccionada)
        
        self.limpiar_formulario()
        print("[INFO] Pestaña Categorías inicializada.")

    def cargar_tabla_categorias(self):
        self.tabla_categorias.setRowCount(0)
        categorias = db.obtener_categorias()
        for row_idx, row_data in enumerate(categorias):
            self.tabla_categorias.insertRow(row_idx)
            # id, nombre, codigo, edad_min, edad_max, genero, tipo_emb, dist, vueltas
            self.tabla_categorias.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0]))) # ID
            self.tabla_categorias.setItem(row_idx, 1, QTableWidgetItem(row_data[1])) # Nombre
            self.tabla_categorias.setItem(row_idx, 2, QTableWidgetItem(row_data[2])) # Código
            self.tabla_categorias.setItem(row_idx, 3, QTableWidgetItem(f"{row_data[3]}-{row_data[4]}")) # Edades
            self.tabla_categorias.setItem(row_idx, 4, QTableWidgetItem(row_data[5])) # Género
            self.tabla_categorias.setItem(row_idx, 5, QTableWidgetItem(row_data[6])) # Embarcación
            self.tabla_categorias.setItem(row_idx, 6, QTableWidgetItem(str(row_data[7]))) # Distancia
            self.tabla_categorias.setItem(row_idx, 7, QTableWidgetItem(str(row_data[8]))) # Vueltas

    def limpiar_formulario(self):
        self.id_categoria_seleccionada = None
        self.nombre_cat_input.clear()
        self.codigo_cat_input.clear()
        self.tipo_emb_input.clear()
        self.distancia_input.setValue(0)
        self.vueltas_input.setValue(0)
        self.edad_min_input.setValue(0)
        self.edad_max_input.setValue(99)
        self.genero_combo.setCurrentIndex(0)
        self.tabla_categorias.clearSelection()

    def guardar_categoria(self):
        datos = {
            'nombre_categoria': self.nombre_cat_input.text().strip(),
            'codigo_categoria': self.codigo_cat_input.text().strip().upper(),
            'tipo_embarcacion': self.tipo_emb_input.text().strip().upper(),
            'genero': self.genero_combo.currentText(),
            'edad_min': self.edad_min_input.value(),
            'edad_max': self.edad_max_input.value(),
            'distancia_km': self.distancia_input.value(),
            'numero_vueltas': self.vueltas_input.value()
        }
        if not datos['nombre_categoria'] or not datos['codigo_categoria']:
            QMessageBox.warning(self, "Campos Requeridos", "Nombre y Código de la categoría son obligatorios.")
            return
        
        _, mensaje = db.agregar_o_actualizar_categoria(datos, self.id_categoria_seleccionada)
        QMessageBox.information(self, "Operación Exitosa", mensaje)
        self.cargar_tabla_categorias()
        self.limpiar_formulario()

    def eliminar_categoria(self):
        if not self.id_categoria_seleccionada:
            QMessageBox.warning(self, "Sin Selección", "Selecciona una categoría de la tabla para eliminar.")
            return
        
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Seguro que quieres eliminar esta categoría?\nEsto la eliminará de cualquier inscripción existente.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            exito, mensaje = db.eliminar_categoria(self.id_categoria_seleccionada)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_tabla_categorias()
                self.limpiar_formulario()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def cargar_categoria_seleccionada(self, item):
        fila = self.tabla_categorias.row(item)
        self.id_categoria_seleccionada = int(self.tabla_categorias.item(fila, 0).text())
        
        # Cargar datos desde la DB para mayor precisión
        conn = db.conectar_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categorias WHERE id=?", (self.id_categoria_seleccionada,))
            data = cursor.fetchone()
            if data:
                self.nombre_cat_input.setText(data[1])
                self.codigo_cat_input.setText(data[2])
                self.edad_min_input.setValue(data[3])
                self.edad_max_input.setValue(data[4])
                self.genero_combo.setCurrentText(data[5])
                self.tipo_emb_input.setText(data[6])
                self.distancia_input.setValue(data[7])
                self.vueltas_input.setValue(data[8])
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la categoría: {e}")
        finally:
            conn.close()