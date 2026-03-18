"""
main_window.py – Ventana principal de la aplicación.

Responsabilidad única: construir y gestionar la interfaz gráfica
principal (checkboxes dinámicos, comboboxes, radiografía, botones).
No contiene lógica de negocio ni diálogos secundarios.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QFrame,
    QCheckBox, QComboBox, QLabel, QPushButton, QRadioButton,
    QButtonGroup, QMessageBox, QSizePolicy,
    QScrollArea, QProgressDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap


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
        self._crear_header(layout_principal)

        # --- Separador visual ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        layout_principal.addWidget(sep)

        # --- Secciones dinámicas ---
        self._crear_seccion_checkboxes(layout_principal)
        self._crear_seccion_comboboxes(layout_principal)
        self._crear_seccion_radiografia(layout_principal)
        self._crear_seccion_modo(layout_principal)
        self._crear_seccion_acciones(layout_principal)

        layout_principal.addStretch()
        scroll.setWidget(contenedor)
        self.setCentralWidget(scroll)

    # ------------------------------------------------------------------
    # Secciones de la UI (cada una en su propio método)
    # ------------------------------------------------------------------
    def _crear_header(self, layout):
        """Crea el header con título y subtítulo."""
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

        layout.addWidget(header)

    def _crear_seccion_checkboxes(self, layout):
        """Crea la sección de checkboxes dinámica desde la configuración."""
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
        layout.addWidget(grupo_cb)

    def _crear_seccion_comboboxes(self, layout):
        """Crea la sección de comboboxes dinámica desde la configuración."""
        datos_cmb = self.modelo.obtener_comboboxes()
        if not datos_cmb:
            return
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
        layout.addWidget(grupo_cmb)

    def _crear_seccion_radiografia(self, layout):
        """Crea la sección de carga de radiografía con preview."""
        grupo_radio = QGroupBox("🩻  Radiografía / Prueba Complementaria")
        layout_radio = QVBoxLayout()
        layout_radio.setSpacing(10)

        fila_radio = QHBoxLayout()
        self.btn_subir_radiografia = QPushButton("📂  Subir Radiografía / Prueba")
        self.btn_subir_radiografia.setObjectName("btn_subir")
        self.btn_subir_radiografia.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_radiografia = QLabel("Ningún archivo seleccionado")
        self.lbl_radiografia.setObjectName("lbl_ruta_radiografia")
        fila_radio.addWidget(self.btn_subir_radiografia)
        fila_radio.addWidget(self.lbl_radiografia, 1)
        layout_radio.addLayout(fila_radio)

        self.lbl_preview = QLabel("Sin imagen")
        self.lbl_preview.setObjectName("lbl_preview")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setFixedHeight(160)
        self.lbl_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout_radio.addWidget(self.lbl_preview)

        grupo_radio.setLayout(layout_radio)
        layout.addWidget(grupo_radio)

    def _crear_seccion_modo(self, layout):
        """Crea la sección de selección del modo de consulta."""
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
        layout.addWidget(grupo_modo)

    def _crear_seccion_acciones(self, layout):
        """Crea la sección de botones de acción."""
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
        layout.addWidget(grupo_acciones)

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
