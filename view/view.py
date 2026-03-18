"""
view.py – Vistas de la aplicación MVC de Diagnóstico de Traumatismos.

Contiene todas las ventanas gráficas (QMainWindow y QDialogs) con un
diseño moderno, limpio y profesional orientado al sector clínico/médico.

Los componentes de la ventana principal se construyen dinámicamente
leyendo la configuración expuesta por el Modelo.

No contiene lógica de negocio.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QFrame,
    QCheckBox, QComboBox, QLabel, QPushButton, QRadioButton,
    QButtonGroup, QTableWidget, QTableWidgetItem, QListWidget,
    QTextEdit, QFileDialog, QMessageBox, QHeaderView, QSizePolicy,
    QScrollArea, QProgressDialog, QSplitter,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap


# ======================================================================
# 1. VENTANA PRINCIPAL – Entrada de síntomas y observables
# ======================================================================
class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación con diseño clínico moderno.
    Construye dinámicamente los checkboxes y comboboxes a partir de los
    datos que expone el Modelo (leídos de config_sintomas.json).
    """

    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.checkboxes: list[QCheckBox] = []
        self.comboboxes: dict[str, QComboBox] = {}
        self._progress_dialog = None
        self._init_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _init_ui(self):
        self.setWindowTitle("🩺 Diagnóstico de Traumatismos – Asistido por IA")
        self.setMinimumSize(900, 720)
        self.resize(960, 780)

        # Widget central con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        contenedor = QWidget()
        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setSpacing(8)
        layout_principal.setContentsMargins(24, 12, 24, 24)

        # --- Header ---
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        titulo = QLabel("🩺  Sistema de Diagnóstico Traumatológico")
        titulo.setObjectName("titulo_app")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(titulo)

        subtitulo = QLabel("Análisis asistido por IA multimodal (LLaVa / Ollama)")
        subtitulo.setObjectName("subtitulo_app")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitulo)

        layout_principal.addWidget(header)

        # --- Separador visual ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        layout_principal.addWidget(sep)

        # --- Sección de checkboxes (dinámica) ---
        datos_cb = self.modelo.obtener_checkboxes()
        grupo_cb = QGroupBox(f"🔍  {datos_cb.get('titulo', 'Síntomas')}")
        grid_cb = QGridLayout()
        grid_cb.setSpacing(6)
        opciones = datos_cb.get("opciones", [])
        columnas = 2
        for i, texto in enumerate(opciones):
            cb = QCheckBox(texto)
            self.checkboxes.append(cb)
            grid_cb.addWidget(cb, i // columnas, i % columnas)
        grupo_cb.setLayout(grid_cb)
        layout_principal.addWidget(grupo_cb)

        # --- Sección de comboboxes (dinámica) ---
        datos_cmb = self.modelo.obtener_comboboxes()
        if datos_cmb:
            grupo_cmb = QGroupBox("📋  Parámetros Clínicos")
            layout_cmb = QGridLayout()
            layout_cmb.setSpacing(10)
            layout_cmb.setColumnStretch(1, 1)
            for idx, combo_def in enumerate(datos_cmb):
                etiqueta = combo_def.get("etiqueta", f"Parámetro {idx + 1}")
                lbl = QLabel(f"{etiqueta}:")
                lbl.setStyleSheet("font-weight: bold; color: #2D3748;")
                cmb = QComboBox()
                cmb.addItems(combo_def.get("opciones", []))
                self.comboboxes[etiqueta] = cmb
                layout_cmb.addWidget(lbl, idx, 0)
                layout_cmb.addWidget(cmb, idx, 1)
            grupo_cmb.setLayout(layout_cmb)
            layout_principal.addWidget(grupo_cmb)

        # --- Radiografía con preview ---
        grupo_radio = QGroupBox("🩻  Radiografía / Prueba Complementaria")
        layout_radio = QVBoxLayout()
        layout_radio.setSpacing(10)

        # Fila superior: botón + ruta
        fila_radio = QHBoxLayout()
        self.btn_subir_radiografia = QPushButton("📂  Subir Radiografía / Prueba")
        self.btn_subir_radiografia.setObjectName("btn_subir")
        self.btn_subir_radiografia.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_radiografia = QLabel("Ningún archivo seleccionado")
        self.lbl_radiografia.setObjectName("lbl_ruta_radiografia")
        fila_radio.addWidget(self.btn_subir_radiografia)
        fila_radio.addWidget(self.lbl_radiografia, 1)
        layout_radio.addLayout(fila_radio)

        # Preview de imagen
        self.lbl_preview = QLabel("Sin imagen")
        self.lbl_preview.setObjectName("lbl_preview")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setFixedHeight(160)
        self.lbl_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout_radio.addWidget(self.lbl_preview)

        grupo_radio.setLayout(layout_radio)
        layout_principal.addWidget(grupo_radio)

        # --- Modo de ejecución (RadioButtons) ---
        grupo_modo = QGroupBox("⚙️  Modo de Consulta")
        layout_modo = QHBoxLayout()
        layout_modo.setSpacing(24)
        self.rb_local = QRadioButton("🖥️  Solo Local (PDFs)")
        self.rb_web = QRadioButton("🌐  Web + Local (RAG)")
        self.rb_local.setChecked(True)
        self.grupo_modo = QButtonGroup()
        self.grupo_modo.addButton(self.rb_local)
        self.grupo_modo.addButton(self.rb_web)
        layout_modo.addWidget(self.rb_local)
        layout_modo.addWidget(self.rb_web)
        layout_modo.addStretch()
        grupo_modo.setLayout(layout_modo)
        layout_principal.addWidget(grupo_modo)

        # --- Botones de acción ---
        grupo_acciones = QGroupBox("🚀  Acciones")
        layout_acciones = QGridLayout()
        layout_acciones.setSpacing(10)

        self.btn_evaluar = QPushButton("🔍  Evaluar Hipótesis")
        self.btn_evaluar.setObjectName("btn_evaluar")
        self.btn_evaluar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_evaluar.setToolTip("Generar hipótesis diagnósticas con IA")

        self.btn_diagnosticar = QPushButton("🩻  Diagnosticar")
        self.btn_diagnosticar.setObjectName("btn_diagnosticar")
        self.btn_diagnosticar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_diagnosticar.setToolTip("Obtener diagnóstico completo con IA")

        self.btn_justificacion = QPushButton("📝  Ver Justificación")
        self.btn_justificacion.setObjectName("btn_justificacion")
        self.btn_justificacion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_justificacion.setToolTip("Ver la justificación del último diagnóstico")

        self.btn_pdfs = QPushButton("📚  Gestión Conocimiento (PDFs)")
        self.btn_pdfs.setObjectName("btn_pdfs")
        self.btn_pdfs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pdfs.setToolTip("Gestionar base de conocimiento local")

        self.btn_fuentes = QPushButton("🌐  Fuentes Web")
        self.btn_fuentes.setObjectName("btn_fuentes")
        self.btn_fuentes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fuentes.setToolTip("Ver fuentes web consultadas")

        layout_acciones.addWidget(self.btn_evaluar, 0, 0)
        layout_acciones.addWidget(self.btn_diagnosticar, 0, 1)
        layout_acciones.addWidget(self.btn_justificacion, 1, 0)
        layout_acciones.addWidget(self.btn_pdfs, 1, 1)
        layout_acciones.addWidget(self.btn_fuentes, 2, 0, 1, 2)
        grupo_acciones.setLayout(layout_acciones)
        layout_principal.addWidget(grupo_acciones)

        # Espaciador final
        layout_principal.addStretch()

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
        """Devuelve el modo seleccionado."""
        return "Solo Local" if self.rb_local.isChecked() else "Web + Local"

    def mostrar_ruta_radiografia(self, ruta: str):
        """Actualiza la etiqueta con la ruta de la radiografía subida."""
        self.lbl_radiografia.setText(ruta if ruta else "Ningún archivo seleccionado")

    def mostrar_preview_imagen(self, ruta_completa: str):
        """Muestra un thumbnail de la imagen de radiografía."""
        pixmap = QPixmap(ruta_completa)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(400, 150),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_preview.setPixmap(scaled)
        else:
            self.lbl_preview.setText("📄 Archivo seleccionado (sin preview)")

    def mostrar_error(self, titulo: str, mensaje: str):
        """Muestra un cuadro de diálogo de error."""
        QMessageBox.warning(self, titulo, mensaje)

    def mostrar_info(self, titulo: str, mensaje: str):
        """Muestra un cuadro de diálogo informativo."""
        QMessageBox.information(self, titulo, mensaje)

    # ------------------------------------------------------------------
    # Progreso (spinner mientras el LLM trabaja)
    # ------------------------------------------------------------------
    def mostrar_progreso(self, mensaje: str = "Analizando..."):
        """
        Muestra un QProgressDialog indeterminado mientras el QThread trabaja.
        NO bloquea el hilo principal de la GUI.
        """
        self._progress_dialog = QProgressDialog(mensaje, None, 0, 0, self)
        self._progress_dialog.setWindowTitle("⏳ Procesando")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setMinimumWidth(420)
        self._progress_dialog.show()

    def ocultar_progreso(self):
        """Cierra el QProgressDialog."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

    def deshabilitar_botones(self, deshabilitar: bool = True):
        """Deshabilita/habilita los botones de acción durante inferencia."""
        for btn in [
            self.btn_evaluar, self.btn_diagnosticar,
            self.btn_justificacion, self.btn_pdfs, self.btn_fuentes,
        ]:
            btn.setDisabled(deshabilitar)


# ======================================================================
# 2. VENTANA DE HIPÓTESIS
# ======================================================================
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

        # Tabla de hipótesis
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
            # Colorear según probabilidad
            if isinstance(prob, (int, float)) and prob > 50:
                prob_item.setForeground(Qt.GlobalColor.darkGreen)
            tabla.setItem(fila, 1, prob_item)

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
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
        lbl_diag.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D3748; padding: 8px;")
        lbl_diag.setWordWrap(True)
        l_diag.addWidget(lbl_diag)
        grupo_diag.setLayout(l_diag)
        layout.addWidget(grupo_diag)

        # Confianza
        grupo_conf = QGroupBox("Nivel de Confianza")
        l_conf = QVBoxLayout()
        lbl_conf = QLabel(f"{confianza:.1f} %")
        color_conf = "#38A169" if confianza >= 70 else "#DD6B20" if confianza >= 40 else "#E53E3E"
        lbl_conf.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {color_conf}; padding: 8px;"
        )
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
        l_rec.addWidget(txt_rec)
        grupo_rec.setLayout(l_rec)
        layout.addWidget(grupo_rec)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
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


# ======================================================================
# 5. VENTANA DE GESTIÓN DE PDFs (Conocimiento Local)
# ======================================================================
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


# ======================================================================
# 6. VENTANA DE FUENTES WEB
# ======================================================================
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


# ======================================================================
# 7. VENTANA DE RESULTADO COMPLETO del LLM
# ======================================================================
class DialogoResultadoLLM(QDialog):
    """
    Muestra el resultado completo devuelto por el LLM estructurado
    en secciones: hipótesis, diagnóstico, justificación, recomendaciones.
    """

    def __init__(self, resultado: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🤖 Resultado del Análisis IA")
        self.setMinimumSize(680, 560)
        self._init_ui(resultado)

    def _init_ui(self, resultado: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Resultado del Análisis con IA (LLaVa)")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1A365D; padding: 8px 0;"
        )
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Área de texto con el resultado completo formateado
        texto = QTextEdit()
        texto.setReadOnly(True)

        contenido = self._formatear_resultado(resultado)
        texto.setPlainText(contenido)
        layout.addWidget(texto)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    @staticmethod
    def _formatear_resultado(resultado: dict) -> str:
        """Formatea el dict de resultado en texto legible."""
        lineas = []

        # Diagnóstico
        diag = resultado.get("diagnostico", "")
        if diag:
            lineas.append("═══ DIAGNÓSTICO ═══")
            lineas.append(str(diag))
            lineas.append("")

        # Hipótesis
        hipotesis = resultado.get("hipotesis", [])
        if hipotesis:
            lineas.append("═══ HIPÓTESIS ═══")
            if isinstance(hipotesis, list):
                for i, h in enumerate(hipotesis, 1):
                    if isinstance(h, dict):
                        nombre = h.get("nombre", h.get("hipotesis", str(h)))
                        prob = h.get("probabilidad", h.get("porcentaje", "N/D"))
                        lineas.append(f"  {i}. {nombre} — {prob}%")
                    else:
                        lineas.append(f"  {i}. {h}")
            else:
                lineas.append(f"  {hipotesis}")
            lineas.append("")

        # Justificación
        justif = resultado.get("justificacion", resultado.get("justificación", ""))
        if justif:
            lineas.append("═══ JUSTIFICACIÓN CLÍNICA ═══")
            lineas.append(str(justif))
            lineas.append("")

        # Recomendaciones
        recom = resultado.get("recomendaciones", "")
        if recom:
            lineas.append("═══ RECOMENDACIONES ═══")
            lineas.append(str(recom))
            lineas.append("")

        # Respuesta cruda (si no se parseó bien)
        cruda = resultado.get("respuesta_cruda", "")
        if cruda:
            lineas.append("═══ RESPUESTA CRUDA DEL MODELO ═══")
            lineas.append(str(cruda))

        return "\n".join(lineas) if lineas else "Sin resultados disponibles."
