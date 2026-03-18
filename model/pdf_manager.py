"""
pdf_manager.py – Gestor de documentos PDF y radiografías.

Responsabilidad única (SRP): gestionar la lista de PDFs de conocimiento,
extraer texto (PyPDF2), y codificar imágenes de radiografía a base64.
"""

import os
import base64


class PDFManager:
    """Gestiona la base de conocimiento local (PDFs) y las radiografías."""

    def __init__(self):
        self.pdfs: list[dict] = []
        self.ruta_radiografia: str | None = None

    # ------------------------------------------------------------------
    # Radiografía
    # ------------------------------------------------------------------
    def establecer_radiografia(self, ruta: str) -> None:
        """Guarda la ruta de la radiografía o prueba subida."""
        self.ruta_radiografia = ruta

    def obtener_imagen_base64(self) -> str | None:
        """
        Lee la imagen de radiografía y la devuelve codificada en base64.
        Necesario para el modelo multimodal LLaVa.
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
        Utiliza PyPDF2. Si no está instalado, devuelve un aviso.
        Se usa para inyectar contexto clínico en el prompt (RAG local).
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
