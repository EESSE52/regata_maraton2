# pdf_preview_dialog_ui.py
# Diálogo para previsualizar el contenido de un reporte antes de guardarlo como PDF.

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox, QPushButton
)
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import Qt

class PdfPreviewDialog(QDialog):
    def __init__(self, documento_a_previsualizar: QTextDocument, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Previsualización de Reporte")
        self.setMinimumSize(800, 600) 

        self.documento = documento_a_previsualizar

        layout = QVBoxLayout(self)

        self.text_browser = QTextBrowser()
        # Usar clone() es más seguro para no modificar el documento original
        doc_clone = self.documento.clone()
        self.text_browser.setDocument(doc_clone) 
        self.text_browser.setReadOnly(True)
        
        layout.addWidget(self.text_browser)

        self.button_box = QDialogButtonBox()
        self.btn_guardar = self.button_box.addButton("Guardar como PDF...", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Cancelar", QDialogButtonBox.RejectRole)
        
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.setLayout(layout)