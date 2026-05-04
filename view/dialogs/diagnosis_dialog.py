"""
diagnosis_dialog.py – Diálogo de diagnóstico final.

Responsabilidad única: mostrar el diagnóstico definitivo,
nivel de confianza y recomendaciones de tratamiento.
"""

import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextBrowser,
)
from PyQt6.QtCore import Qt


class DialogoDiagnostico(QDialog):
    """Muestra el diagnóstico definitivo, confianza y recomendaciones."""

    def __init__(self, diagnostico: str, confianza: float,
                 recomendaciones: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✅ Diagnóstico Final")
        self.setMinimumSize(560, 420)
        self._init_ui(diagnostico, confianza, recomendaciones)

    def _init_ui(self, diagnostico: str, confianza: float, recomendaciones: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Diagnóstico Definitivo")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Diagnóstico
        grupo_diag = QGroupBox("Diagnóstico")
        l_diag = QVBoxLayout()
        lbl_diag = QLabel(diagnostico)
        lbl_diag.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2D3748; padding: 8px;"
        )
        lbl_diag.setWordWrap(True)
        l_diag.addWidget(lbl_diag)
        grupo_diag.setLayout(l_diag)
        layout.addWidget(grupo_diag)

        # Confianza
        grupo_conf = QGroupBox("Nivel de Confianza")
        l_conf = QVBoxLayout()
        lbl_conf = QLabel(f"{confianza:.1f} %")
        color = "#38A169" if confianza >= 70 else "#DD6B20" if confianza >= 40 else "#E53E3E"
        lbl_conf.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {color}; padding: 8px;"
        )
        lbl_conf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_conf.addWidget(lbl_conf)
        grupo_conf.setLayout(l_conf)
        layout.addWidget(grupo_conf)

        # Recomendaciones
        grupo_rec = QGroupBox("Recomendaciones")
        l_rec = QVBoxLayout()
        txt_rec = QTextBrowser()
        txt_rec.setOpenExternalLinks(True)
        patron_url = re.compile(r'(https?://[^\s<>"\')]+)')
        recom_html = patron_url.sub(
            r'<a href="\1" style="color: #2B6CB0; '
            r'text-decoration: underline;">\1</a>',
            recomendaciones,
        )
        txt_rec.setHtml(f'<p>{recom_html}</p>')
        l_rec.addWidget(txt_rec)
        grupo_rec.setLayout(l_rec)
        layout.addWidget(grupo_rec)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)
