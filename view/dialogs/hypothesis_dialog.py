"""
hypothesis_dialog.py – Diálogo de hipótesis diagnósticas.

Responsabilidad única: mostrar una tabla con las hipótesis
traumatológicas y sus probabilidades.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt


class DialogoHipotesis(QDialog):
    """Muestra las hipótesis traumatológicas con su probabilidad."""

    def __init__(self, hipotesis: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Hipótesis de Diagnóstico")
        self.setMinimumSize(560, 400)
        self._init_ui(hipotesis)

    def _init_ui(self, hipotesis: list[dict]):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Posibles Diagnósticos Traumatológicos")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        tabla = QTableWidget(len(hipotesis), 2)
        tabla.setHorizontalHeaderLabels(["Hipótesis", "Probabilidad (%)"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet("alternate-background-color: #F7FAFC;")

        for fila, h in enumerate(hipotesis):
            tabla.setItem(fila, 0, QTableWidgetItem(h.get("nombre", "")))
            prob = h.get("probabilidad", 0)
            prob_item = QTableWidgetItem(f"{prob:.1f} %")
            prob_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if isinstance(prob, (int, float)) and prob > 50:
                prob_item.setForeground(Qt.GlobalColor.darkGreen)
            tabla.setItem(fila, 1, prob_item)

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)
