"""
web_sources_dialog.py – Diálogo de fuentes web consultadas.

Responsabilidad única: mostrar la lista de URLs de fuentes
médicas utilizadas durante el diagnóstico web+local.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget,
)
from PyQt6.QtCore import Qt


class DialogoFuentesWeb(QDialog):
    """Muestra las URLs de fuentes web utilizadas."""

    def __init__(self, fuentes: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌐 Fuentes Web Consultadas")
        self.setMinimumSize(560, 380)
        self._init_ui(fuentes)

    def _init_ui(self, fuentes: list[str]):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Fuentes Web Utilizadas en el Diagnóstico")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        lista = QListWidget()
        if fuentes:
            lista.addItems(fuentes)
        else:
            lista.addItem("(No se consultaron fuentes web – Modo solo local)")
        layout.addWidget(lista)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)
