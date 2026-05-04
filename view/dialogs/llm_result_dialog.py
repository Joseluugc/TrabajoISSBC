"""
llm_result_dialog.py – Diálogo de resultado completo del LLM.

Responsabilidad única: mostrar el resultado estructurado devuelto
por LLaVa (hipótesis, diagnóstico, justificación, recomendaciones).
"""

import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser,
)
from PyQt6.QtCore import Qt


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

        texto = QTextBrowser()
        texto.setOpenExternalLinks(True)
        texto.setHtml(self._formatear_resultado(resultado))
        layout.addWidget(texto)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    _PATRON_URL = re.compile(r'(https?://[^\s<>"\')]+)')

    @classmethod
    def _enlazar_urls(cls, texto: str) -> str:
        """Convierte URLs en texto plano a enlaces HTML clicables."""
        return cls._PATRON_URL.sub(
            r'<a href="\1" style="color: #2B6CB0; text-decoration: underline;">\1</a>',
            texto,
        )

    @classmethod
    def _formatear_resultado(cls, resultado: dict) -> str:
        """Formatea el dict de resultado en HTML legible con enlaces clicables."""
        secciones = []
        estilo_titulo = (
            'style="color: #1A365D; font-weight: bold; '
            'font-size: 14px; margin-top: 12px;"'
        )

        diag = resultado.get("diagnostico", "")
        if diag:
            secciones.append(f'<p {estilo_titulo}>═══ DIAGNÓSTICO ═══</p>')
            secciones.append(f'<p>{cls._enlazar_urls(str(diag))}</p>')

        hipotesis = resultado.get("hipotesis", [])
        if hipotesis:
            secciones.append(f'<p {estilo_titulo}>═══ HIPÓTESIS ═══</p>')
            if isinstance(hipotesis, list):
                items = []
                for i, h in enumerate(hipotesis, 1):
                    if isinstance(h, dict):
                        nombre = h.get("nombre", h.get("hipotesis", str(h)))
                        prob = h.get("probabilidad", h.get("porcentaje", "N/D"))
                        items.append(f'<li>{nombre} — {prob}%</li>')
                    else:
                        items.append(f'<li>{h}</li>')
                secciones.append('<ol>' + ''.join(items) + '</ol>')
            else:
                secciones.append(f'<p>{cls._enlazar_urls(str(hipotesis))}</p>')

        justif = resultado.get("justificacion", resultado.get("justificación", ""))
        if justif:
            secciones.append(f'<p {estilo_titulo}>═══ JUSTIFICACIÓN CLÍNICA ═══</p>')
            secciones.append(f'<p>{cls._enlazar_urls(str(justif))}</p>')

        recom = resultado.get("recomendaciones", "")
        if recom:
            secciones.append(f'<p {estilo_titulo}>═══ RECOMENDACIONES ═══</p>')
            secciones.append(f'<p>{cls._enlazar_urls(str(recom))}</p>')

        cruda = resultado.get("respuesta_cruda", "")
        if cruda:
            secciones.append(f'<p {estilo_titulo}>═══ RESPUESTA CRUDA DEL MODELO ═══</p>')
            secciones.append(f'<p>{cls._enlazar_urls(str(cruda))}</p>')

        return ''.join(secciones) if secciones else '<p>Sin resultados disponibles.</p>'
