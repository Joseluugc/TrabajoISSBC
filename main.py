"""
main.py – Punto de entrada de la aplicación MVC de Diagnóstico de Traumatismos.

Inicializa la aplicación instanciando el Modelo, la Vista y el Controlador,
y lanza el bucle de eventos de Qt.
"""

import sys
from PyQt6.QtWidgets import QApplication

from model import Modelo
from view import VentanaPrincipal
from controller import Controlador


def main():
    """Punto de entrada principal de la aplicación."""
    app = QApplication(sys.argv)

    # Estilo global mínimo para mejorar la apariencia
    app.setStyle("Fusion")

    # 1. Crear el Modelo (lee config_sintomas.json automáticamente)
    modelo = Modelo()

    # 2. Crear la Vista pasándole el modelo para la construcción dinámica
    vista = VentanaPrincipal(modelo)

    # 3. Crear el Controlador que conecta Vista ↔ Modelo
    controlador = Controlador(modelo, vista)  # noqa: F841 – referencia necesaria

    # 4. Mostrar la ventana principal y ejecutar el bucle de eventos
    vista.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
