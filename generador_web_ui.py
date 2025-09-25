# generador_web_ui.py
# Diálogo para la generación del sitio web de la regata.

import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QProgressBar, QFormLayout, QGroupBox,
    QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread
import database_maraton as db
import generador_web as gw
from utils_maraton import resource_path

class GeneracionWebThread(QThread):
    progreso_actualizado = Signal(int)
    finalizado = Signal(bool, str)

    def __init__(self, evento_id, ruta_destino, generar_todo):
        super().__init__()
        self.evento_id = evento_id
        self.ruta_destino = ruta_destino
        self.generar_todo = generar_todo

    def run(self):
        try:
            total_pasos = 4
            self.progreso_actualizado.emit(0)

            # Paso 1: Generar página de inicio
            self.progreso_actualizado.emit(10)
            gw.generar_estilos_css(self.ruta_destino)
            self.progreso_actualizado.emit(25)

            # Paso 2: Generar resultados (puntuación general, medallero, etc.)
            gw.generar_todos_los_reportes(self.evento_id, self.ruta_destino, self.generar_todo)
            self.progreso_actualizado.emit(50)
            
            # Paso 3: Generar página principal
            gw.generar_pagina_inicio_evento(self.evento_id, self.ruta_destino)
            self.progreso_actualizado.emit(75)

            # Paso 4: Copiar logos y otros archivos necesarios
            gw.copiar_archivos_necesarios(self.evento_id, self.ruta_destino)
            self.progreso_actualizado.emit(100)

            self.finalizado.emit(True, f"Sitio web generado correctamente en:\n{self.ruta_destino}")
        except Exception as e:
            self.finalizado.emit(False, f"Error al generar el sitio web: {e}")

class GeneradorWebDialog(QDialog):
    def __init__(self, evento_id, parent=None):
        super().__init__(parent)
        self.evento_id = evento_id
        if not self.evento_id:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar un evento activo para generar el sitio web.")
            self.reject()
            return
            
        self.setWindowTitle("Generar Sitio Web de la Regata")
        self.setFixedSize(500, 300)

        self.worker = None
        self.thread = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_evento_box = QGroupBox("Evento Seleccionado")
        info_layout = QFormLayout(info_evento_box)
        evento_info = db.obtener_info_evento(self.evento_id)
        if evento_info:
            info_layout.addRow("Nombre:", QLabel(evento_info[1]))
            info_layout.addRow("Fecha:", QLabel(evento_info[2]))
        layout.addWidget(info_evento_box)

        # Opciones
        opciones_box = QGroupBox("Opciones de Generación")
        opciones_layout = QVBoxLayout(opciones_box)
        self.chk_generar_todo = QCheckBox("Generar todos los resultados (incluye los no finalizados)")
        opciones_layout.addWidget(self.chk_generar_todo)
        layout.addWidget(opciones_box)
        
        # Ruta de destino
        ruta_layout = QHBoxLayout()
        self.label_ruta = QLabel("<i>Carpeta de destino no seleccionada.</i>")
        self.btn_seleccionar_carpeta = QPushButton("Seleccionar Carpeta de Destino...")
        ruta_layout.addWidget(QLabel("Carpeta:"))
        ruta_layout.addWidget(self.label_ruta, 1)
        ruta_layout.addWidget(self.btn_seleccionar_carpeta)
        layout.addLayout(ruta_layout)

        # Barra de progreso y botones
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.btn_generar = QPushButton("Generar")
        self.btn_cancelar = QPushButton("Cancelar")
        btn_layout.addWidget(self.btn_generar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        # Conexiones
        self.btn_seleccionar_carpeta.clicked.connect(self.seleccionar_carpeta)
        self.btn_generar.clicked.connect(self.iniciar_generacion)
        self.btn_cancelar.clicked.connect(self.cancelar_generacion)

        self.btn_generar.setEnabled(False)

    def seleccionar_carpeta(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec() == QDialog.Accepted:
            self.ruta_destino = dialog.selectedFiles()[0]
            self.label_ruta.setText(os.path.basename(self.ruta_destino))
            self.btn_generar.setEnabled(True)

    def iniciar_generacion(self):
        if not self.ruta_destino:
            QMessageBox.warning(self, "Error", "Debes seleccionar una carpeta de destino.")
            return

        self.btn_generar.setEnabled(False)
        self.progress_bar.setValue(0)
        self.thread = GeneracionWebThread(self.evento_id, self.ruta_destino, self.chk_generar_todo.isChecked())
        self.thread.progreso_actualizado.connect(self.progress_bar.setValue)
        self.thread.finalizado.connect(self.generacion_finalizada)
        self.thread.start()

    def cancelar_generacion(self):
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            QMessageBox.information(self, "Cancelado", "La generación del sitio web ha sido cancelada.")
            self.progress_bar.setValue(0)
            self.btn_generar.setEnabled(True)
    
    def generacion_finalizada(self, exito, mensaje):
        if exito:
            QMessageBox.information(self, "Generación Exitosa", mensaje)
        else:
            QMessageBox.critical(self, "Error", mensaje)
        self.progress_bar.setValue(100)
        self.btn_generar.setEnabled(True)