"""Paquete Model – Capa de datos y estado de la aplicación."""
from .model import Modelo
from .config_loader import ConfigLoader
from .pdf_manager import PDFManager

__all__ = ["Modelo", "ConfigLoader", "PDFManager"]
