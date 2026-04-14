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
        "Eres un radiólogo especializado en traumatología. Analiza la imagen proporcionada.\n\n"
        "1. Determina si la imagen corresponde al dominio médico-traumatológico "
        "(radiografía, TAC, RM, ecografía musculoesquelética o fotografía clínica de lesión).\n"
        "2. Identifica la zona anatómica exacta entre las siguientes opciones:\n"
        "   - Cráneo / Cara\n"
        "   - Columna cervical\n"
        "   - Columna dorsolumbar\n"
        "   - Hombro (incluyendo clavícula y escápula)\n"
        "   - Brazo / Húmero\n"
        "   - Codo\n"
        "   - Antebrazo (cúbito/radio)\n"
        "   - Muñeca / Carpo\n"
        "   - Mano / Dedos (metacarpianos, falanges)\n"
        "   - Cadera / Pelvis\n"
        "   - Muslo / Fémur\n"
        "   - Rodilla\n"
        "   - Pierna (tibia/peroné)\n"
        "   - Tobillo\n"
        "   - Pie / Dedos del pie\n"
        "   - Otro (especificar)\n\n"
        "3. Describe brevemente los hallazgos radiológicos visibles (fracturas, luxaciones, "
        "edema de partes blandas, etc.).\n\n"
        "INSTRUCCIONES IMPORTANTES:\n"
        "- Si la imagen es una radiografía, fíjate en la forma y número de huesos largos, "
        "presencia de articulaciones características (ej. codo: olécranon, cabeza radial; "
        "mano: múltiples huesos pequeños, falanges).\n"
        "- Si ves múltiples huesos cortos alineados en filas, es muy probable que sea una mano o un pie.\n"
        "- No asumas la zona por el contexto; analiza exclusivamente la imagen.\n\n"
        "Responde EXCLUSIVAMENTE con un objeto JSON válido:\n"
        "{\n"
        '  "es_medica": true/false,\n'
        '  "razon": "Breve justificación de por qué es o no médica",\n'
        '  "zona_corporal": "Una de las opciones de la lista anterior",\n'
        '  "hallazgos": "Descripción concisa de los hallazgos radiológicos observados"\n'
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
