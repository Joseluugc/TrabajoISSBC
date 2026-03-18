"""
justification_dialog.py – Diálogo de justificación clínica.

Responsabilidad única: mostrar la justificación detallada
del diagnóstico emitido por el LLM.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit,
)
from PyQt6.QtCore import Qt


class DialogoJustificacion(QDialog):
    """Muestra la justificación detallada del diagnóstico."""

    def __init__(self, justificacion: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Justificación del Diagnóstico")
        self.setMinimumSize(600, 460)
        self._init_ui(justificacion)

    def _init_ui(self, justificacion: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Justificación Clínica")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        texto = QTextEdit()
        texto.setReadOnly(True)
        texto.setPlainText(justificacion)
        layout.addWidget(texto)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)
