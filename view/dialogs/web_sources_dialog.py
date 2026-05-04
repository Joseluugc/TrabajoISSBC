"""
web_sources_dialog.py – Diálogo de fuentes web consultadas.

Responsabilidad única: mostrar la lista de URLs de fuentes
médicas utilizadas durante el diagnóstico web+local.
"""

import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser,
)
from PyQt6.QtCore import Qt


class DialogoFuentesWeb(QDialog):
    """Muestra las URLs de fuentes web utilizadas como enlaces clicables."""

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

        # Usar QTextBrowser con HTML para que los enlaces sean clicables
        texto = QTextBrowser()
        texto.setOpenExternalLinks(True)
        texto.setHtml(self._generar_html(fuentes))
        layout.addWidget(texto)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    @staticmethod
    def _generar_html(fuentes: list[str]) -> str:
        """Genera HTML con las fuentes como enlaces clicables."""
        if not fuentes:
            return (
                '<p style="color: #718096; font-style: italic;">'
                "(No se consultaron fuentes web – Modo solo local)</p>"
            )

        # Patrón para detectar URLs en el texto
        patron_url = re.compile(r'(https?://[^\s<>"\']+)')

        items_html = []
        for fuente in fuentes:
            # Intentar convertir URLs encontradas en enlaces clicables
            fuente_html = patron_url.sub(
                r'<a href="\1" style="color: #2B6CB0; '
                r'text-decoration: underline;">\1</a>',
                fuente,
            )
            items_html.append(
                f'<li style="margin-bottom: 8px; padding: 6px 0; '
                f'border-bottom: 1px solid #EDF2F7;">{fuente_html}</li>'
            )

        return (
            '<ul style="list-style-type: none; padding-left: 0; margin: 0;">'
            + "".join(items_html)
            + "</ul>"
        )
