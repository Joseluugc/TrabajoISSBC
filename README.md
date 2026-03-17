# Sistema de Diagnóstico de Traumatismos asistido por LLM

Este proyecto es una aplicación de escritorio desarrollada en Python y PyQt6, diseñada como examen práctico para la asignatura **Ingeniería de Sistemas Basados en Conocimiento (ISSBC)**. Su objetivo es proporcionar una interfaz gráfica bajo una arquitectura estricta **Modelo-Vista-Controlador (MVC)** para un sistema experto de diagnóstico clínico.

---

## 1. Dominio elegido y descripción
El dominio seleccionado para este sistema experto es la **Traumatología**. 
La aplicación asiste en el diagnóstico preliminar de lesiones musculoesqueléticas (esguinces, fracturas, roturas fibrilares, luxaciones, etc.). Para ello, el sistema recopila:
* Síntomas y signos observables (inflamación, dolor, deformidad, etc.).
* Parámetros clínicos categóricos (escala de dolor EVA, zona afectada, mecanismo de lesión y tiempo de evolución).
* Pruebas complementarias (subida de radiografías, ecografías o resonancias).

Se asume que el motor de inferencia subyacente es un **LLM (Large Language Model)**, el cual ha sido simulado (*mockeado*) en el controlador para cumplir con el alcance de evaluación de la interfaz.

---

## 2. Instrucciones de ejecución
Para ejecutar la aplicación correctamente, asegúrese de tener instalado Python (versión 3.10 o superior).

1. Clone o extraiga los archivos del proyecto en un directorio local.
2. Es necesario instalar la librería gráfica `PyQt6`. Puede hacerlo ejecutando el siguiente comando en su terminal:
   ```bash
   pip install PyQt6```
3. Para la ejecucción del programa solo debe ejecutar:
	```python3 main.py```

## 3. Descripción de la arquitectura MVC usada
El proyecto se ha desarrollado respetando rigurosamente el patrón de diseño **Modelo-Vista-Controlador (MVC)**, garantizando una separación total de responsabilidades. La estructura se divide en:

* **Modelo (`model.py`):** Es el cerebro de los datos y gestor del estado. **Es completamente independiente de la interfaz gráfica** (no importa PyQt). Se encarga de:
  * Leer y estructurar el archivo parametrizable `config_sintomas.json`.
  * Almacenar las selecciones del usuario (síntomas, radiografías, modo de consulta).
  * Gestionar en memoria la base de conocimiento local (archivos PDF aportados).
  * Almacenar los resultados finales (hipótesis, diagnósticos, justificaciones y URLs).

* **Vista (`view.py`):** Es una **vista dinámica y parametrizable**. La ventana principal no contiene los componentes estáticos (*hardcodeados*). Se construye iterando sobre la configuración que le proporciona el Modelo proveniente del JSON. Contiene todas las ventanas interactivas (`QMainWindow` y los diferentes `QDialog` para hipótesis, justificaciones, etc.) y solo se encarga de pintar la información.

* **Controlador (`controller.py`):** Ejerce de mediador.
  * Captura las señales emitidas por la Vista (ej. pulsación del botón "Diagnosticar").
  * Extrae los datos actuales de la Vista y actualiza el Modelo.
  * Ejecuta la lógica del negocio (en este caso, la simulación del LLM), calcula las probabilidades de las hipótesis y redacta la justificación, enviando de vuelta los resultados para que la Vista los muestre.

---

## 4. Explicación del modo Local/Web y cómo se refleja en la UI
En la pantalla principal, el usuario dispone de una sección denominada **"Modo de Consulta"** equipada con botones de selección (`QRadioButton`) para definir el contexto que debe utilizar el LLM al inferir:

* **Modo "Solo Local":** Restringe al LLM a utilizar única y exclusivamente la información médica proporcionada por el usuario en el gestor de conocimiento local (las Guías Clínicas o manuales en formato PDF que haya subido).
* **Modo "Web + Local":** Permite al LLM ampliar su contexto buscando información actualizada en bases de datos médicas de internet.

**Cómo se refleja en la Interfaz de Usuario (UI):**
Esta elección impacta directamente en la ventana emergente de **"Fuentes Web"**. 
* Si el diagnóstico se ha ejecutado en modo **"Web + Local"**, al abrir dicha ventana se mostrará un `QListWidget` con una lista trazable de URLs y artículos médicos consultados por el LLM (simulados). 
* Si se ejecutó en modo **"Solo Local"**, la UI reflejará explícitamente un mensaje indicando que no se han consultado fuentes externas para garantizar la privacidad y mantener el enfoque en la base documental estricta del paciente.

