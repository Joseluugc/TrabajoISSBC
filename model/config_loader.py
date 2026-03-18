"""
config_loader.py – Cargador de configuración de síntomas.

Responsabilidad única (SRP): leer, parsear y validar el archivo
config_sintomas.json que define los checkboxes y comboboxes de la UI.
"""

import json
import os


class ConfigLoader:
    """Lee y expone la configuración de síntomas desde un archivo JSON."""

    _CONFIG_POR_DEFECTO = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config_sintomas.json",
    )

    _CONFIG_VACIA = {
        "checkboxes": {"titulo": "Síntomas", "opciones": []},
        "comboboxes": [],
    }

    def __init__(self, ruta_config: str | None = None):
        self._ruta = ruta_config or self._CONFIG_POR_DEFECTO
        self._config: dict = {}
        self.cargar()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def cargar(self) -> None:
        """Lee el archivo JSON y almacena la configuración."""
        try:
            with open(self._ruta, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] No se encontró la configuración: {self._ruta}")
            self._config = dict(self._CONFIG_VACIA)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON inválido en la configuración: {e}")
            self._config = dict(self._CONFIG_VACIA)

    # ------------------------------------------------------------------
    # Accesores
    # ------------------------------------------------------------------
    def obtener_checkboxes(self) -> dict:
        """Devuelve la sección 'checkboxes' de la configuración."""
        return self._config.get(
            "checkboxes", self._CONFIG_VACIA["checkboxes"]
        )

    def obtener_comboboxes(self) -> list[dict]:
        """Devuelve la lista de definiciones de combobox."""
        return self._config.get("comboboxes", [])

    @property
    def config_completa(self) -> dict:
        """Acceso de solo lectura a la configuración completa."""
        return self._config
