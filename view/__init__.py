"""
Paquete View – Capa de presentación (ventanas y diálogos).

Re-exporta todas las clases de la UI para imports limpios:
    from view import VentanaPrincipal, DialogoHipotesis, ...
"""
from .main_window import VentanaPrincipal
from .dialogs import (
    DialogoHipotesis,
    DialogoDiagnostico,
    DialogoJustificacion,
    DialogoPDFs,
    DialogoFuentesWeb,
    DialogoResultadoLLM,
)

__all__ = [
    "VentanaPrincipal",
    "DialogoHipotesis",
    "DialogoDiagnostico",
    "DialogoJustificacion",
    "DialogoPDFs",
    "DialogoFuentesWeb",
    "DialogoResultadoLLM",
]
