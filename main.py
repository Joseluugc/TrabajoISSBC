"""
main.py – Punto de entrada de la aplicación MVC de Diagnóstico de Traumatismos.

Inicializa la aplicación instanciando el Modelo, la Vista y el Controlador,
carga la hoja de estilos QSS y lanza el bucle de eventos de Qt.
"""

import sys
import os

from PyQt6.QtWidgets import QApplication

from model.model import Modelo
from view.view import VentanaPrincipal
from controller.controller import Controlador


def cargar_estilos(app: QApplication) -> None:
    """Carga la hoja de estilos QSS desde view/style.qss."""
    ruta_qss = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "view", "style.qss"
    )
    try:
        with open(ruta_qss, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print(f"[INFO] Hoja de estilos cargada: {ruta_qss}")
    except FileNotFoundError:
        print(f"[AVISO] No se encontró la hoja de estilos: {ruta_qss}")
    except Exception as e:
        print(f"[ERROR] Error al cargar estilos: {e}")


def main():
    """Punto de entrada principal de la aplicación."""
    app = QApplication(sys.argv)

    # Estilo base Fusion (mejora la consistencia cross-platform)
    app.setStyle("Fusion")

    # Cargar hoja de estilos personalizada (QSS)
    cargar_estilos(app)

    # 1. Crear el Modelo (lee config_sintomas.json automáticamente)
    modelo = Modelo()

    # 2. Crear la Vista pasándole el modelo para la construcción dinámica
    vista = VentanaPrincipal(modelo)

    # 3. Crear el Controlador que conecta Vista ↔ Modelo
    controlador = Controlador(modelo, vista)  # noqa: F841

    # 4. Mostrar la ventana principal y ejecutar el bucle de eventos
    vista.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
