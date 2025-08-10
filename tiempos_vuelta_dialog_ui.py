# tiempos_vuelta_dialog_ui.py
# Diálogo para ingresar los tiempos por vuelta de un competidor.

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
import datetime

class TiemposVueltaDialog(QDialog):
    def __init__(self, numero_vueltas, tiempos_existentes_str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ingresar Tiempos por Vuelta")
        self.setMinimumWidth(350)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.line_edits_vueltas = []

        # Usar un QScrollArea si hay muchas vueltas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container_widget = QWidget()
        container_layout = QFormLayout(container_widget)
        
        tiempos_existentes = []
        if tiempos_existentes_str:
            try:
                import json
                tiempos_existentes = json.loads(tiempos_existentes_str)
            except (json.JSONDecodeError, TypeError):
                tiempos_existentes = []

        for i in range(numero_vueltas):
            tiempo_input = QLineEdit()
            tiempo_input.setPlaceholderText("HH:MM:SS.ms")
            if i < len(tiempos_existentes):
                tiempo_input.setText(tiempos_existentes[i])
            
            container_layout.addRow(f"Tiempo Vuelta {i+1}:", tiempo_input)
            self.line_edits_vueltas.append(tiempo_input)

        scroll_area.setWidget(container_widget)
        self.layout.addWidget(scroll_area)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_tiempos(self):
        """Valida y devuelve los tiempos ingresados y su suma."""
        tiempos_str = []
        suma_tiempos = datetime.timedelta()
        
        for i, line_edit in enumerate(self.line_edits_vueltas):
            tiempo_texto = line_edit.text().strip()
            if not tiempo_texto:
                continue # Ignorar vueltas vacías por ahora

            try:
                # Intentar parsear con milisegundos
                if '.' in tiempo_texto:
                    parte_principal, parte_ms = tiempo_texto.split('.')
                    h, m, s = map(int, parte_principal.split(':'))
                    ms = int(parte_ms.ljust(6, '0')) # Asegurar 6 dígitos para microsegundos
                    td = datetime.timedelta(hours=h, minutes=m, seconds=s, microseconds=ms)
                else: # Parsear sin milisegundos
                    h, m, s = map(int, tiempo_texto.split(':'))
                    td = datetime.timedelta(hours=h, minutes=m, seconds=s)
                
                tiempos_str.append(tiempo_texto)
                suma_tiempos += td
            except ValueError:
                QMessageBox.warning(self, "Formato Inválido", f"El tiempo ingresado para la vuelta {i+1} ('{tiempo_texto}') no es válido.\nUse el formato HH:MM:SS o HH:MM:SS.ms")
                return None, None # Indicar error

        # Formatear el tiempo total
        total_seconds = int(suma_tiempos.total_seconds())
        microseconds = suma_tiempos.microseconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        tiempo_final_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        if microseconds > 0:
            tiempo_final_str += f".{str(microseconds // 1000).zfill(3)}"

        import json
        return json.dumps(tiempos_str), tiempo_final_str
