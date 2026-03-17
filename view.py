"""
view.py – Vistas de la aplicación MVC de Diagnóstico de Traumatismos.

Contiene todas las ventanas gráficas (QMainWindow y QDialogs).
Los componentes de la ventana principal se construyen dinámicamente
leyendo la configuración expuesta por el Modelo.

No contiene lógica de negocio.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QCheckBox, QComboBox, QLabel, QPushButton, QRadioButton,
    QButtonGroup, QTableWidget, QTableWidgetItem, QListWidget,
    QTextEdit, QFileDialog, QMessageBox, QHeaderView, QSizePolicy,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon


# ======================================================================
# 1. VENTANA PRINCIPAL – Entrada de síntomas y observables
# ======================================================================
class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación.
    Construye dinámicamente los checkboxes y comboboxes a partir de los
    datos que expone el Modelo (leídos de config_sintomas.json).
    """

    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.checkboxes: list[QCheckBox] = []
        self.comboboxes: dict[str, QComboBox] = {}   # {etiqueta: widget}
        self._init_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _init_ui(self):
        self.setWindowTitle("🩺 Diagnóstico de Traumatismos – Asistido por LLM")
        self.setMinimumSize(780, 620)

        # Widget central con scroll por si la configuración es larga
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenedor = QWidget()
        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setSpacing(12)

        # --- Título ---
        titulo = QLabel("Sistema de Diagnóstico Traumatológico")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # --- Sección de checkboxes (dinámica) ---
        datos_cb = self.modelo.obtener_checkboxes()
        grupo_cb = QGroupBox(datos_cb.get("titulo", "Síntomas"))
        grid_cb = QGridLayout()
        opciones = datos_cb.get("opciones", [])
        columnas = 2  # 2 columnas de checkboxes
        for i, texto in enumerate(opciones):
            cb = QCheckBox(texto)
            cb.setFont(QFont("Segoe UI", 10))
            self.checkboxes.append(cb)
            grid_cb.addWidget(cb, i // columnas, i % columnas)
        grupo_cb.setLayout(grid_cb)
        layout_principal.addWidget(grupo_cb)

        # --- Sección de comboboxes (dinámica) ---
        datos_cmb = self.modelo.obtener_comboboxes()
        if datos_cmb:
            grupo_cmb = QGroupBox("Parámetros Clínicos")
            layout_cmb = QGridLayout()
            for idx, combo_def in enumerate(datos_cmb):
                etiqueta = combo_def.get("etiqueta", f"Parámetro {idx + 1}")
                lbl = QLabel(f"{etiqueta}:")
                lbl.setFont(QFont("Segoe UI", 10))
                cmb = QComboBox()
                cmb.addItems(combo_def.get("opciones", []))
                cmb.setFont(QFont("Segoe UI", 10))
                self.comboboxes[etiqueta] = cmb
                layout_cmb.addWidget(lbl, idx, 0)
                layout_cmb.addWidget(cmb, idx, 1)
            grupo_cmb.setLayout(layout_cmb)
            layout_principal.addWidget(grupo_cmb)

        # --- Radiografía ---
        grupo_radio = QGroupBox("Radiografía / Prueba Complementaria")
        layout_radio = QHBoxLayout()
        self.lbl_radiografia = QLabel("Ningún archivo seleccionado")
        self.lbl_radiografia.setFont(QFont("Segoe UI", 9))
        self.btn_subir_radiografia = QPushButton("📂 Subir Radiografía / Prueba")
        self.btn_subir_radiografia.setFont(QFont("Segoe UI", 10))
        layout_radio.addWidget(self.lbl_radiografia)
        layout_radio.addWidget(self.btn_subir_radiografia)
        grupo_radio.setLayout(layout_radio)
        layout_principal.addWidget(grupo_radio)

        # --- Modo de ejecución (RadioButtons) ---
        grupo_modo = QGroupBox("Modo de Consulta")
        layout_modo = QHBoxLayout()
        self.rb_local = QRadioButton("Solo Local")
        self.rb_web = QRadioButton("Web + Local")
        self.rb_local.setChecked(True)
        self.rb_local.setFont(QFont("Segoe UI", 10))
        self.rb_web.setFont(QFont("Segoe UI", 10))
        self.grupo_modo = QButtonGroup()
        self.grupo_modo.addButton(self.rb_local)
        self.grupo_modo.addButton(self.rb_web)
        layout_modo.addWidget(self.rb_local)
        layout_modo.addWidget(self.rb_web)
        grupo_modo.setLayout(layout_modo)
        layout_principal.addWidget(grupo_modo)

        # --- Botones de acción ---
        grupo_acciones = QGroupBox("Acciones")
        layout_acciones = QGridLayout()

        self.btn_evaluar = QPushButton("🔍 Evaluar Hipótesis")
        self.btn_diagnosticar = QPushButton("🩻 Diagnosticar")
        self.btn_justificacion = QPushButton("📝 Ver Justificación")
        self.btn_pdfs = QPushButton("📚 Gestión Conocimiento (PDFs)")
        self.btn_fuentes = QPushButton("🌐 Fuentes Web")

        botones = [
            self.btn_evaluar, self.btn_diagnosticar,
            self.btn_justificacion, self.btn_pdfs, self.btn_fuentes,
        ]
        for btn in botones:
            btn.setFont(QFont("Segoe UI", 10))
            btn.setMinimumHeight(36)

        layout_acciones.addWidget(self.btn_evaluar, 0, 0)
        layout_acciones.addWidget(self.btn_diagnosticar, 0, 1)
        layout_acciones.addWidget(self.btn_justificacion, 1, 0)
        layout_acciones.addWidget(self.btn_pdfs, 1, 1)
        layout_acciones.addWidget(self.btn_fuentes, 2, 0, 1, 2)
        grupo_acciones.setLayout(layout_acciones)
        layout_principal.addWidget(grupo_acciones)

        # Añadir al scroll y establecer como widget central
        scroll.setWidget(contenedor)
        self.setCentralWidget(scroll)

    # ------------------------------------------------------------------
    # Métodos auxiliares para el controlador
    # ------------------------------------------------------------------
    def obtener_sintomas_marcados(self) -> list[str]:
        """Devuelve los textos de los checkboxes marcados."""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]

    def obtener_valores_combobox(self) -> dict[str, str]:
        """Devuelve un dict {etiqueta: valor seleccionado}."""
        return {etiqueta: cmb.currentText() for etiqueta, cmb in self.comboboxes.items()}

    def obtener_modo(self) -> str:
        """Devuelve el modo seleccionado ("Solo Local" o "Web + Local")."""
        return "Solo Local" if self.rb_local.isChecked() else "Web + Local"

    def mostrar_ruta_radiografia(self, ruta: str):
        """Actualiza la etiqueta con la ruta de la radiografía subida."""
        self.lbl_radiografia.setText(ruta if ruta else "Ningún archivo seleccionado")

    def mostrar_error(self, titulo: str, mensaje: str):
        """Muestra un cuadro de diálogo de error."""
        QMessageBox.warning(self, titulo, mensaje)

    def mostrar_info(self, titulo: str, mensaje: str):
        """Muestra un cuadro de diálogo informativo."""
        QMessageBox.information(self, titulo, mensaje)


# ======================================================================
# 2. VENTANA DE HIPÓTESIS
# ======================================================================
class DialogoHipotesis(QDialog):
    """Muestra las hipótesis traumatológicas con su probabilidad."""

    def __init__(self, hipotesis: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Hipótesis de Diagnóstico")
        self.setMinimumSize(520, 350)
        self._init_ui(hipotesis)

    def _init_ui(self, hipotesis: list[dict]):
        layout = QVBoxLayout(self)

        titulo = QLabel("Posibles Diagnósticos Traumatológicos")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Tabla de hipótesis
        tabla = QTableWidget(len(hipotesis), 2)
        tabla.setHorizontalHeaderLabels(["Hipótesis", "Probabilidad (%)"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setFont(QFont("Segoe UI", 10))

        for fila, h in enumerate(hipotesis):
            tabla.setItem(fila, 0, QTableWidgetItem(h.get("nombre", "")))
            prob_item = QTableWidgetItem(f"{h.get('probabilidad', 0):.1f} %")
            prob_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla.setItem(fila, 1, prob_item)

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)


# ======================================================================
# 3. VENTANA DE DIAGNÓSTICO FINAL
# ======================================================================
class DialogoDiagnostico(QDialog):
    """Muestra el diagnóstico definitivo, confianza y recomendaciones."""

    def __init__(self, diagnostico: str, confianza: float,
                 recomendaciones: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✅ Diagnóstico Final")
        self.setMinimumSize(500, 360)
        self._init_ui(diagnostico, confianza, recomendaciones)

    def _init_ui(self, diagnostico: str, confianza: float, recomendaciones: str):
        layout = QVBoxLayout(self)

        titulo = QLabel("Diagnóstico Definitivo")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Diagnóstico
        grupo_diag = QGroupBox("Diagnóstico")
        l_diag = QVBoxLayout()
        lbl_diag = QLabel(diagnostico)
        lbl_diag.setFont(QFont("Segoe UI", 12))
        lbl_diag.setWordWrap(True)
        l_diag.addWidget(lbl_diag)
        grupo_diag.setLayout(l_diag)
        layout.addWidget(grupo_diag)

        # Confianza
        grupo_conf = QGroupBox("Nivel de Confianza")
        l_conf = QVBoxLayout()
        lbl_conf = QLabel(f"{confianza:.1f} %")
        lbl_conf.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl_conf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_conf.addWidget(lbl_conf)
        grupo_conf.setLayout(l_conf)
        layout.addWidget(grupo_conf)

        # Recomendaciones
        grupo_rec = QGroupBox("Recomendaciones")
        l_rec = QVBoxLayout()
        txt_rec = QTextEdit()
        txt_rec.setReadOnly(True)
        txt_rec.setPlainText(recomendaciones)
        txt_rec.setFont(QFont("Segoe UI", 10))
        l_rec.addWidget(txt_rec)
        grupo_rec.setLayout(l_rec)
        layout.addWidget(grupo_rec)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)


# ======================================================================
# 4. VENTANA DE JUSTIFICACIÓN
# ======================================================================
class DialogoJustificacion(QDialog):
    """Muestra la justificación detallada del diagnóstico."""

    def __init__(self, justificacion: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Justificación del Diagnóstico")
        self.setMinimumSize(540, 400)
        self._init_ui(justificacion)

    def _init_ui(self, justificacion: str):
        layout = QVBoxLayout(self)

        titulo = QLabel("Justificación Clínica")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        texto = QTextEdit()
        texto.setReadOnly(True)
        texto.setPlainText(justificacion)
        texto.setFont(QFont("Segoe UI", 10))
        layout.addWidget(texto)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)


# ======================================================================
# 5. VENTANA DE GESTIÓN DE PDFs (Conocimiento Local)
# ======================================================================
class DialogoPDFs(QDialog):
    """Permite añadir, eliminar y listar PDFs de conocimiento local."""

    def __init__(self, pdfs: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Gestión de Conocimiento (PDFs)")
        self.setMinimumSize(620, 380)
        self.pdfs = pdfs
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        titulo = QLabel("Base de Conocimiento Local – Guías Clínicas")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Tabla de PDFs
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Ruta", "Tamaño"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setFont(QFont("Segoe UI", 10))
        self._refrescar_tabla()
        layout.addWidget(self.tabla)

        # Botones
        layout_btns = QHBoxLayout()
        self.btn_agregar = QPushButton("➕ Añadir PDF")
        self.btn_eliminar = QPushButton("🗑️ Eliminar Seleccionado")
        self.btn_agregar.setFont(QFont("Segoe UI", 10))
        self.btn_eliminar.setFont(QFont("Segoe UI", 10))
        layout_btns.addWidget(self.btn_agregar)
        layout_btns.addWidget(self.btn_eliminar)
        layout.addLayout(layout_btns)

        btn_cerrar = QPushButton("Cerrar")
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
        seleccion = self.tabla.currentRow()
        return seleccion


# ======================================================================
# 6. VENTANA DE FUENTES WEB (simulada)
# ======================================================================
class DialogoFuentesWeb(QDialog):
    """Muestra las URLs de fuentes web utilizadas (simuladas)."""

    def __init__(self, fuentes: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌐 Fuentes Web Consultadas")
        self.setMinimumSize(500, 320)
        self._init_ui(fuentes)

    def _init_ui(self, fuentes: list[str]):
        layout = QVBoxLayout(self)

        titulo = QLabel("Fuentes Web Utilizadas en el Diagnóstico")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        lista = QListWidget()
        lista.setFont(QFont("Segoe UI", 10))
        if fuentes:
            lista.addItems(fuentes)
        else:
            lista.addItem("(No se consultaron fuentes web – Modo solo local)")
        layout.addWidget(lista)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)
