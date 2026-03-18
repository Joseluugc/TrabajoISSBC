"""
pdf_manager_dialog.py – Diálogo de gestión de PDFs de conocimiento.

Responsabilidad única: interfaz CRUD para la lista de PDFs
de la base de conocimiento local (guías clínicas).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt


class DialogoPDFs(QDialog):
    """Permite añadir, eliminar y listar PDFs de conocimiento local."""

    def __init__(self, pdfs: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Gestión de Conocimiento (PDFs)")
        self.setMinimumSize(660, 420)
        self.pdfs = pdfs
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Base de Conocimiento Local – Guías Clínicas")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        info = QLabel(
            "ℹ️  Los PDFs cargados se usarán como contexto clínico de "
            "referencia al generar diagnósticos."
        )
        info.setStyleSheet("color: #718096; font-size: 11px; padding: 4px 0;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabla de PDFs
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Ruta", "Tamaño"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("alternate-background-color: #F7FAFC;")
        self._refrescar_tabla()
        layout.addWidget(self.tabla)

        # Botones
        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(10)
        self.btn_agregar = QPushButton("➕  Añadir PDF")
        self.btn_agregar.setObjectName("btn_agregar_pdf")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar = QPushButton("🗑️  Eliminar Seleccionado")
        self.btn_eliminar.setObjectName("btn_eliminar_pdf")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        layout_btns.addWidget(self.btn_agregar)
        layout_btns.addWidget(self.btn_eliminar)
        layout_btns.addStretch()
        layout.addLayout(layout_btns)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    def _refrescar_tabla(self):
        """Recarga la tabla con la lista actual de PDFs."""
        self.tabla.setRowCount(len(self.pdfs))
        for fila, pdf in enumerate(self.pdfs):
            self.tabla.setItem(fila, 0, QTableWidgetItem(pdf.get("nombre", "")))
            self.tabla.setItem(fila, 1, QTableWidgetItem(pdf.get("ruta", "")))
            self.tabla.setItem(fila, 2, QTableWidgetItem(pdf.get("tamaño", "")))

    def refrescar(self, pdfs: list[dict]):
        """Actualiza la lista de PDFs y refresca la tabla."""
        self.pdfs = pdfs
        self._refrescar_tabla()

    def obtener_fila_seleccionada(self) -> int:
        """Devuelve el índice de la fila seleccionada o -1."""
        return self.tabla.currentRow()
