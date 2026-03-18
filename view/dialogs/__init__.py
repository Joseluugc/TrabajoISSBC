"""Subpaquete view.dialogs – Todos los diálogos secundarios de la aplicación."""
from .hypothesis_dialog import DialogoHipotesis
from .diagnosis_dialog import DialogoDiagnostico
from .justification_dialog import DialogoJustificacion
from .pdf_manager_dialog import DialogoPDFs
from .web_sources_dialog import DialogoFuentesWeb
from .llm_result_dialog import DialogoResultadoLLM

__all__ = [
    "DialogoHipotesis",
    "DialogoDiagnostico",
    "DialogoJustificacion",
    "DialogoPDFs",
    "DialogoFuentesWeb",
    "DialogoResultadoLLM",
]
