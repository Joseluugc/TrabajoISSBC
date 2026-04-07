"""
web_search_worker.py – Worker QThread para búsqueda web asíncrona.

Ejecuta la búsqueda web en un hilo secundario para NO bloquear
la GUI mientras se consulta DuckDuckGo. Emite señales al completar.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from controller.web_search import buscar_web


class WebSearchWorker(QThread):
    """
    Hilo de trabajo que ejecuta la búsqueda web en segundo plano.

    Signals:
        resultado_listo (str, list): Emitido con (texto_contexto, lista_fuentes).
        error_ocurrido (str): Emitido si hay un error durante la búsqueda.
    """

    resultado_listo = pyqtSignal(str, list)
    error_ocurrido = pyqtSignal(str)

    def __init__(
        self,
        sintomas: list[str],
        valores: dict[str, str],
        descripcion_imagen: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.sintomas = sintomas
        self.valores = valores
        self.descripcion_imagen = descripcion_imagen

    def run(self):
        """Ejecuta la búsqueda web en el hilo secundario."""
        try:
            texto, fuentes = buscar_web(
                self.sintomas, self.valores, self.descripcion_imagen
            )
            self.resultado_listo.emit(texto, fuentes)
        except Exception as e:
            self.error_ocurrido.emit(f"Error en búsqueda web: {e}")
