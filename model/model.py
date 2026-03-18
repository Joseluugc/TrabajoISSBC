"""
model.py – Modelo de la aplicación MVC de Diagnóstico de Traumatismos.

Responsabilidad: contenedor de estado puro de la sesión clínica.
Compone internamente ConfigLoader (lectura JSON) y PDFManager (PDFs/imágenes),
delegando las operaciones especializadas a cada uno.

No contiene lógica de negocio ni referencias a la interfaz gráfica.
"""

from model.config_loader import ConfigLoader
from model.pdf_manager import PDFManager


class Modelo:
    """Modelo central de la aplicación. Fachada sobre ConfigLoader + PDFManager."""

    def __init__(self, ruta_config: str | None = None):
        # --- Componentes especializados ---
        self._config = ConfigLoader(ruta_config)
        self._pdf_manager = PDFManager()

        # --- Estado de la sesión ---
        self.sintomas_seleccionados: list[str] = []
        self.valores_combobox: dict[str, str] = {}
        self.modo: str = "Solo Local"

        # --- Resultados (rellenados por el controlador) ---
        self.hipotesis: list[dict] = []
        self.diagnostico: str = ""
        self.confianza: float = 0.0
        self.recomendaciones: str = ""
        self.justificacion: str = ""

        # --- Fuentes web ---
        self.fuentes_web: list[str] = []

    # ------------------------------------------------------------------
    # Delegación → ConfigLoader
    # ------------------------------------------------------------------
    def obtener_checkboxes(self) -> dict:
        """Devuelve la sección 'checkboxes' de la configuración."""
        return self._config.obtener_checkboxes()

    def obtener_comboboxes(self) -> list[dict]:
        """Devuelve la lista de definiciones de combobox."""
        return self._config.obtener_comboboxes()

    # ------------------------------------------------------------------
    # Delegación → PDFManager (radiografía)
    # ------------------------------------------------------------------
    @property
    def ruta_radiografia(self) -> str | None:
        return self._pdf_manager.ruta_radiografia

    def establecer_radiografia(self, ruta: str) -> None:
        self._pdf_manager.establecer_radiografia(ruta)

    def obtener_imagen_base64(self) -> str | None:
        return self._pdf_manager.obtener_imagen_base64()

    # ------------------------------------------------------------------
    # Delegación → PDFManager (PDFs de conocimiento)
    # ------------------------------------------------------------------
    @property
    def pdfs(self) -> list[dict]:
        return self._pdf_manager.pdfs

    def agregar_pdf(self, ruta: str) -> None:
        self._pdf_manager.agregar_pdf(ruta)

    def eliminar_pdf(self, indice: int) -> None:
        self._pdf_manager.eliminar_pdf(indice)

    def extraer_texto_pdfs(self) -> str:
        return self._pdf_manager.extraer_texto_pdfs()

    # ------------------------------------------------------------------
    # Estado de la sesión
    # ------------------------------------------------------------------
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
