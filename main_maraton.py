# main_maraton.py
# Versión con generación de reportes PNG para TV

import sys
import os 
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import database_maraton as db

# --- IMPORTACIONES DE PESTAÑAS ---
from evento_ui import EventoTabWidget
from participantes_ui import ParticipantesTabWidget 
from categorias_ui import CategoriasTabWidget
from inscripciones_ui import InscripcionesTabWidget
from resultados_ui import ResultadosTabWidget
from puntuacion_ui import PuntuacionTabWidget
from reportes_ui import ReportesTabWidget

class VentanaPrincipalMaraton(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Regatas de Maratón")
        self.resize(1200, 800)
        
        # Aplicar estilo global
        self.aplicar_estilo_profesional()
        
        self.pestanas = QTabWidget()
        self.setCentralWidget(self.pestanas)

        # Crear e instanciar cada pestaña
        self.tab_evento = EventoTabWidget()
        self.pestanas.addTab(self.tab_evento, "Evento")

        self.tab_participantes = ParticipantesTabWidget()
        self.pestanas.addTab(self.tab_participantes, "Participantes y Clubes")
        
        self.tab_categorias = CategoriasTabWidget()
        self.pestanas.addTab(self.tab_categorias, "Categorías")
        
        self.tab_inscripciones = InscripcionesTabWidget()
        self.pestanas.addTab(self.tab_inscripciones, "Inscripciones")
        
        self.tab_resultados = ResultadosTabWidget()
        self.pestanas.addTab(self.tab_resultados, "Resultados")
        
        self.tab_puntuacion = PuntuacionTabWidget()
        self.pestanas.addTab(self.tab_puntuacion, "Puntuación por Clubes")
        
        self.tab_reportes = ReportesTabWidget()
        self.pestanas.addTab(self.tab_reportes, "Reportes")

        self.crear_menu()
        self.conectar_senales()
        
        print("[INFO] Ventana principal del Gestor de Regatas de Maratón inicializada.")

    def aplicar_estilo_profesional(self):
        """Aplica un estilo profesional con degradados celestes"""
        estilo = """
        /* Estilo general de la aplicación */
        QMainWindow {
            background-color: #f0f9ff;
        }
        
        /* Estilo de las pestañas */
        QTabWidget::pane {
            border: 1px solid #c4d8e2;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #e6f3fa, stop:1 #c4e0f0);
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #d4ebf7, stop:1 #a8d4f0);
            border: 1px solid #9cc0d6;
            border-bottom-color: #c4d8e2;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 12px;
            margin-right: 2px;
            color: #2a5c7a;
        }
        
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #b8e2f8, stop:1 #7ac1ea);
            border-bottom-color: #e6f3fa;
            font-weight: bold;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #c8e9f8, stop:1 #98d4f2);
        }
        
        /* Estilo de los grupos */
        QGroupBox {
            border: 1px solid #9cc0d6;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #e6f3fa, stop:1 #d4ebf7);
            color: #2a5c7a;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        
        /* Estilo de los botones */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #d4ebf7, stop:1 #a8d4f0);
            border: 1px solid #9cc0d6;
            border-radius: 4px;
            padding: 5px 10px;
            min-width: 80px;
            color: #2a5c7a;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #b8e2f8, stop:1 #7ac1ea);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #7ac1ea, stop:1 #b8e2f8);
        }
        
        /* Estilo de las tablas */
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f0f9ff;
            gridline-color: #c4d8e2;
            border: 1px solid #9cc0d6;
        }
        
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #d4ebf7, stop:1 #a8d4f0);
            padding: 5px;
            border: 1px solid #9cc0d6;
            color: #2a5c7a;
        }
        
        /* Estilo de combos y spinboxes */
        QComboBox, QSpinBox {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f8fcff, stop:1 #e6f3fa);
            border: 1px solid #9cc0d6;
            border-radius: 3px;
            padding: 2px 5px;
            min-height: 24px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        /* Estilo de las etiquetas */
        QLabel {
            color: #2a5c7a;
        }
        """
        self.setStyleSheet(estilo)

    def crear_menu(self):
        menu_bar = self.menuBar()
        menu_archivo = menu_bar.addMenu("&Archivo")
        accion_salir = QAction("&Salir", self)
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

    def conectar_senales(self):
        """Conecta las señales entre las diferentes pestañas."""
        self.tab_evento.evento_activo_cambiado.connect(self.tab_inscripciones.actualizar_evento_activo)
        self.tab_evento.evento_activo_cambiado.connect(self.tab_resultados.actualizar_evento_activo)
        self.tab_evento.evento_activo_cambiado.connect(self.tab_puntuacion.actualizar_evento_activo)
        self.tab_evento.evento_activo_cambiado.connect(self.tab_reportes.actualizar_evento_activo)
        
        # Conectar la señal del cálculo de puntuación a la pestaña de reportes
        self.tab_puntuacion.btn_calcular.clicked.connect(
            lambda: self.tab_reportes.actualizar_sistema_puntuacion(
                {lugar: spinner.value() for lugar, spinner in self.tab_puntuacion.spinboxes_puntuacion.items()}
            )
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    try:
        db.inicializar_db()
    except Exception as e:
        QMessageBox.critical(None, "Error Crítico de Base de Datos", 
                             f"No se pudo inicializar la base de datos de regatas.\nError: {e}\nLa aplicación se cerrará.")
        sys.exit(1)

    ventana = VentanaPrincipalMaraton()
    ventana.show()
    
    sys.exit(app.exec())