"""
llm_worker.py – Worker QThread para la inferencia asíncrona con Ollama.

Aísla la llamada al LLM (modelo LLaVa) en un hilo secundario para
NO bloquear el hilo principal de la GUI (requisito crítico de examen).

Emite señales pyqtSignal al completar o al detectar un error.
"""

import json
import requests

from PyQt6.QtCore import QThread, pyqtSignal


class LLMWorker(QThread):
    """
    Hilo de trabajo que ejecuta la inferencia contra Ollama (LLaVa).

    Signals:
        resultado_listo (dict): Emitido con el resultado parseado del LLM.
        error_ocurrido (str):   Emitido si hay un error de conexión o parseo.
    """

    resultado_listo = pyqtSignal(dict)
    error_ocurrido = pyqtSignal(str)

    # URL base de la API de Ollama
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODELO = "llava"

    def __init__(
        self,
        prompt: str,
        imagen_base64: str | None = None,
        parent=None,
    ):
        """
        Args:
            prompt: Prompt completo (system + user) para enviar a LLaVa.
            imagen_base64: Imagen codificada en base64 (para modelo multimodal).
            parent: Parent QObject.
        """
        super().__init__(parent)
        self.prompt = prompt
        self.imagen_base64 = imagen_base64

    def run(self):
        """
        Método ejecutado en el hilo secundario.
        Llama a la API de Ollama y emite el resultado o error.
        """
        try:
            # Construir el payload para Ollama
            payload = {
                "model": self.MODELO,
                "prompt": self.prompt,
                "stream": False,
                "format": "json",
            }

            # Si hay imagen, incluirla (LLaVa es multimodal)
            if self.imagen_base64:
                payload["images"] = [self.imagen_base64]

            # Realizar la petición HTTP a Ollama
            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=300,  # 5 minutos máximo de espera
            )
            response.raise_for_status()

            # Parsear la respuesta de Ollama
            data = response.json()
            texto_respuesta = data.get("response", "")

            # Intentar parsear como JSON estructurado
            try:
                resultado = json.loads(texto_respuesta)
            except json.JSONDecodeError:
                # Si LLaVa no devolvió JSON válido, envolver en dict
                resultado = {
                    "hipotesis": [],
                    "diagnostico": texto_respuesta,
                    "justificacion": "El modelo no devolvió un formato JSON estructurado.",
                    "recomendaciones": "Consulte con un especialista para confirmar.",
                    "respuesta_cruda": texto_respuesta,
                }

            self.resultado_listo.emit(resultado)

        except requests.exceptions.ConnectionError:
            self.error_ocurrido.emit(
                "No se pudo conectar con Ollama.\n\n"
                "Asegúrese de que Ollama está ejecutándose:\n"
                "  → Inicie con: ollama serve\n"
                "  → Descargue el modelo: ollama pull llava\n\n"
                "URL esperada: http://localhost:11434"
            )
        except requests.exceptions.Timeout:
            self.error_ocurrido.emit(
                "La petición a Ollama ha excedido el tiempo de espera (5 min).\n"
                "El modelo puede estar sobrecargado. Inténtelo de nuevo."
            )
        except requests.exceptions.HTTPError as e:
            self.error_ocurrido.emit(
                f"Error HTTP de Ollama: {e}\n\n"
                "Verifique que el modelo 'llava' está descargado:\n"
                "  → ollama pull llava"
            )
        except Exception as e:
            self.error_ocurrido.emit(
                f"Error inesperado durante la inferencia:\n{type(e).__name__}: {e}"
            )
