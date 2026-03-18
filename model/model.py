"""
model.py – Modelo de la aplicación MVC de Diagnóstico de Traumatismos.

Responsabilidades:
  - Leer y exponer la configuración de síntomas desde config_sintomas.json.
  - Mantener el estado de la aplicación: síntomas seleccionados, ruta de
    radiografía, PDFs de conocimiento, hipótesis, diagnóstico y fuentes web.
  - Extraer texto de los PDFs cargados (para RAG con LLaVa).
  - No contiene lógica de negocio ni referencias a la interfaz gráfica.
"""

import json
import os
import base64


class Modelo:
    """Modelo central de la aplicación. Almacena todo el estado."""

    # Ruta por defecto del archivo de configuración (en la raíz del proyecto)
    _CONFIG_POR_DEFECTO = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config_sintomas.json",
    )

    def __init__(self, ruta_config: str | None = None):
        """
        Inicializa el modelo cargando la configuración de síntomas.

        Args:
            ruta_config: Ruta al JSON de configuración. Si es None se usa
                         la ruta por defecto (config_sintomas.json en raíz).
        """
        self._ruta_config = ruta_config or self._CONFIG_POR_DEFECTO

        # --- Datos de configuración (leídos del JSON) ---
        self.config: dict = {}

        # --- Estado de la sesión ---
        self.sintomas_seleccionados: list[str] = []
        self.valores_combobox: dict[str, str] = {}
        self.ruta_radiografia: str | None = None
        self.modo: str = "Solo Local"

        # --- Resultados (rellenados por el controlador) ---
        self.hipotesis: list[dict] = []
        self.diagnostico: str = ""
        self.confianza: float = 0.0
        self.recomendaciones: str = ""
        self.justificacion: str = ""

        # --- Gestión de conocimiento ---
        self.pdfs: list[dict] = []
        self.fuentes_web: list[str] = []

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

    def obtener_imagen_base64(self) -> str | None:
        """
        Lee la imagen de radiografía y la devuelve codificada en base64.
        Necesario para enviar al modelo multimodal LLaVa.
        Retorna None si no hay imagen o si no se puede leer.
        """
        if not self.ruta_radiografia or not os.path.isfile(self.ruta_radiografia):
            return None
        try:
            with open(self.ruta_radiografia, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except (IOError, OSError) as e:
            print(f"[ERROR] No se pudo leer la imagen: {e}")
            return None

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

    def extraer_texto_pdfs(self) -> str:
        """
        Extrae y concatena el texto de todos los PDFs cargados.
        Utiliza PyPDF2 para la extracción. Si no está instalado,
        devuelve un aviso. Esto se usa para inyectar contexto
        clínico de referencia en el prompt del LLM (RAG local).
        """
        if not self.pdfs:
            return ""

        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return (
                "[AVISO] PyPDF2 no está instalado. "
                "Instálelo con: pip install PyPDF2 para habilitar "
                "la extracción de texto de PDFs."
            )

        textos = []
        for pdf_info in self.pdfs:
            ruta = pdf_info.get("ruta", "")
            if not os.path.isfile(ruta):
                textos.append(f"[No se encontró el archivo: {ruta}]")
                continue
            try:
                reader = PdfReader(ruta)
                contenido = []
                for pagina in reader.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        contenido.append(texto_pagina)
                if contenido:
                    textos.append(
                        f"--- Documento: {pdf_info.get('nombre', 'Desconocido')} ---\n"
                        + "\n".join(contenido)
                    )
            except Exception as e:
                textos.append(f"[Error leyendo {pdf_info.get('nombre', '')}: {e}]")

        return "\n\n".join(textos)

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
