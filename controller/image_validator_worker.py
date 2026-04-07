"""
image_validator_worker.py – Worker QThread para validar imágenes con LLaVA.

Envía la imagen al modelo LLaVA para:
1. Verificar si corresponde al dominio de traumatología.
2. Identificar la zona corporal y posible lesión visible.

Emite señales con el resultado de la validación y la descripción.
"""

import json
import requests

from PyQt6.QtCore import QThread, pyqtSignal


class ImageValidatorWorker(QThread):
    """
    Hilo de trabajo que valida si una imagen es médica/traumatológica
    y extrae la zona corporal y hallazgos visibles.

    Signals:
        validacion_lista (bool, str, str): (es_medica, razon, descripcion_clinica).
        error_ocurrido (str): Emitido si hay error de conexión.
    """

    validacion_lista = pyqtSignal(bool, str, str)
    error_ocurrido = pyqtSignal(str)

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODELO = "llava"

    PROMPT_VALIDACION = (
        "Analiza esta imagen y determina:\n"
        "1. Si es una imagen médica relacionada con traumatología "
        "(radiografía, TAC, resonancia magnética, ecografía "
        "musculoesquelética, fotografía clínica de lesión, etc.).\n"
        "2. Qué zona corporal muestra (ej: rodilla, tobillo, muñeca, "
        "hombro, columna, cadera, codo, mano, pie, cráneo, nariz, etc.).\n"
        "3. Qué hallazgos o lesiones son visibles.\n\n"
        "Responde EXCLUSIVAMENTE con JSON:\n"
        "{\n"
        '  "es_medica": true o false,\n'
        '  "razon": "Breve justificación",\n'
        '  "zona_corporal": "nombre de la zona corporal",\n'
        '  "hallazgos": "descripción breve de hallazgos visibles"\n'
        "}"
    )

    def __init__(self, imagen_base64: str, parent=None):
        super().__init__(parent)
        self.imagen_base64 = imagen_base64

    def run(self):
        """Ejecuta la validación de imagen en el hilo secundario."""
        try:
            payload = {
                "model": self.MODELO,
                "prompt": self.PROMPT_VALIDACION,
                "stream": False,
                "format": "json",
                "images": [self.imagen_base64],
            }

            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            texto = data.get("response", "")

            try:
                resultado = json.loads(texto)
                es_medica = bool(resultado.get("es_medica", True))
                razon = str(resultado.get("razon", "Sin detalle"))
                # Construir descripción clínica para la búsqueda web
                zona = resultado.get("zona_corporal", "")
                hallazgos = resultado.get("hallazgos", "")
                descripcion = ""
                if zona:
                    descripcion = zona
                if hallazgos:
                    descripcion += f" {hallazgos}" if descripcion else hallazgos
                self.validacion_lista.emit(es_medica, razon, descripcion.strip())
            except json.JSONDecodeError:
                self.validacion_lista.emit(True, "No se pudo verificar el formato", "")

        except requests.exceptions.ConnectionError:
            self.error_ocurrido.emit(
                "No se pudo conectar con Ollama para validar la imagen.\n"
                "Asegúrese de que Ollama está ejecutándose."
            )
        except Exception as e:
            self.error_ocurrido.emit(f"Error validando imagen: {e}")
