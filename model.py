"""
model.py – Modelo de la aplicación MVC de Diagnóstico de Traumatismos.

Responsabilidades:
  - Leer y exponer la configuración de síntomas desde config_sintomas.json.
  - Mantener el estado de la aplicación: síntomas seleccionados, ruta de
    radiografía, PDFs de conocimiento, hipótesis, diagnóstico y fuentes web.
  - No contiene lógica de negocio ni referencias a la interfaz gráfica.
"""

import json
import os


class Modelo:
    """Modelo central de la aplicación. Almacena todo el estado."""

    # Ruta por defecto del archivo de configuración (junto a este módulo)
    _CONFIG_POR_DEFECTO = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config_sintomas.json"
    )

    def __init__(self, ruta_config: str | None = None):
        """
        Inicializa el modelo cargando la configuración de síntomas.

        Args:
            ruta_config: Ruta al JSON de configuración. Si es None se usa
                         la ruta por defecto (config_sintomas.json).
        """
        self._ruta_config = ruta_config or self._CONFIG_POR_DEFECTO

        # --- Datos de configuración (leídos del JSON) ---
        self.config: dict = {}

        # --- Estado de la sesión ---
        self.sintomas_seleccionados: list[str] = []       # checkboxes marcados
        self.valores_combobox: dict[str, str] = {}         # {etiqueta: valor elegido}
        self.ruta_radiografia: str | None = None           # ruta del fichero subido
        self.modo: str = "Solo Local"                      # "Solo Local" o "Web + Local"

        # --- Resultados (rellenados por el controlador) ---
        self.hipotesis: list[dict] = []       # [{"nombre": ..., "probabilidad": ...}, ...]
        self.diagnostico: str = ""
        self.confianza: float = 0.0
        self.recomendaciones: str = ""
        self.justificacion: str = ""

        # --- Gestión de conocimiento ---
        self.pdfs: list[dict] = []            # [{"nombre": ..., "ruta": ..., "tamaño": ...}]
        self.fuentes_web: list[str] = []      # URLs simuladas

        # Cargar configuración al arrancar
        self.cargar_config()

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------
    def cargar_config(self) -> None:
        """Lee el archivo JSON de configuración y lo almacena en self.config."""
        try:
            with open(self._ruta_config, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] No se encontró el archivo de configuración: {self._ruta_config}")
            self.config = {"checkboxes": {"titulo": "Síntomas", "opciones": []}, "comboboxes": []}
        except json.JSONDecodeError as e:
            print(f"[ERROR] El archivo de configuración no tiene un JSON válido: {e}")
            self.config = {"checkboxes": {"titulo": "Síntomas", "opciones": []}, "comboboxes": []}

    def obtener_checkboxes(self) -> dict:
        """Devuelve la sección 'checkboxes' de la configuración."""
        return self.config.get("checkboxes", {"titulo": "Síntomas", "opciones": []})

    def obtener_comboboxes(self) -> list[dict]:
        """Devuelve la lista de definiciones de combobox de la configuración."""
        return self.config.get("comboboxes", [])

    # ------------------------------------------------------------------
    # Radiografía
    # ------------------------------------------------------------------
    def establecer_radiografia(self, ruta: str) -> None:
        """Guarda la ruta de la radiografía o prueba subida."""
        self.ruta_radiografia = ruta

    # ------------------------------------------------------------------
    # PDFs de conocimiento
    # ------------------------------------------------------------------
    def agregar_pdf(self, ruta: str) -> None:
        """Añade un PDF a la base de conocimiento local."""
        nombre = os.path.basename(ruta)
        try:
            tamaño = os.path.getsize(ruta)
        except OSError:
            tamaño = 0
        self.pdfs.append({
            "nombre": nombre,
            "ruta": ruta,
            "tamaño": self._formato_tamaño(tamaño),
        })

    def eliminar_pdf(self, indice: int) -> None:
        """Elimina un PDF de la lista por su índice."""
        if 0 <= indice < len(self.pdfs):
            self.pdfs.pop(indice)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _formato_tamaño(bytes_: int) -> str:
        """Convierte bytes a una cadena legible (KB / MB)."""
        if bytes_ < 1024:
            return f"{bytes_} B"
        elif bytes_ < 1024 * 1024:
            return f"{bytes_ / 1024:.1f} KB"
        else:
            return f"{bytes_ / (1024 * 1024):.2f} MB"

    def limpiar_resultados(self) -> None:
        """Resetea hipótesis, diagnóstico y justificación."""
        self.hipotesis = []
        self.diagnostico = ""
        self.confianza = 0.0
        self.recomendaciones = ""
        self.justificacion = ""

    def hay_sintomas(self) -> bool:
        """Devuelve True si se ha seleccionado al menos un síntoma."""
        return len(self.sintomas_seleccionados) > 0
