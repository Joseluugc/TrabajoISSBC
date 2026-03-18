"""
llm_result_dialog.py – Diálogo de resultado completo del LLM.

Responsabilidad única: mostrar el resultado estructurado devuelto
por LLaVa (hipótesis, diagnóstico, justificación, recomendaciones).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit,
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

        texto = QTextEdit()
        texto.setReadOnly(True)
        texto.setPlainText(self._formatear_resultado(resultado))
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

        diag = resultado.get("diagnostico", "")
        if diag:
            lineas.append("═══ DIAGNÓSTICO ═══")
            lineas.append(str(diag))
            lineas.append("")

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

        justif = resultado.get("justificacion", resultado.get("justificación", ""))
        if justif:
            lineas.append("═══ JUSTIFICACIÓN CLÍNICA ═══")
            lineas.append(str(justif))
            lineas.append("")

        recom = resultado.get("recomendaciones", "")
        if recom:
            lineas.append("═══ RECOMENDACIONES ═══")
            lineas.append(str(recom))
            lineas.append("")

        cruda = resultado.get("respuesta_cruda", "")
        if cruda:
            lineas.append("═══ RESPUESTA CRUDA DEL MODELO ═══")
            lineas.append(str(cruda))

        return "\n".join(lineas) if lineas else "Sin resultados disponibles."
