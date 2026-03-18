# Sistema de Diagnóstico de Traumatismos asistido por IA (LLaVA)

Este proyecto es una aplicación de escritorio desarrollada en Python y PyQt6, diseñada como examen práctico para la asignatura Ingeniería de Sistemas Basados en Conocimiento (ISSBC).

Su objetivo es proporcionar una interfaz gráfica bajo una arquitectura estricta Modelo-Vista-Controlador (MVC) para un sistema experto de diagnóstico clínico.

---

## 1. Dominio elegido y descripción

El dominio seleccionado para este sistema experto es la Traumatología.

La aplicación asiste en el diagnóstico preliminar de lesiones musculoesqueléticas, tales como:

* Esguinces
* Fracturas
* Roturas fibrilares
* Luxaciones

Para ello, el sistema recopila:

* Síntomas y signos observables: inflamación, dolor, deformidad, etc.
* Parámetros clínicos categóricos: escala de dolor (EVA), zona afectada, mecanismo de lesión y tiempo de evolución
* Pruebas complementarias: radiografías, ecografías o resonancias

### Motor de Inferencia

El sistema realiza una integración real con el modelo multimodal LLaVA (ejecutado localmente mediante Ollama).

Gracias a sus capacidades de visión-lenguaje, el modelo puede:

* Analizar imágenes médicas (como radiografías)
* Interpretar síntomas textuales
* Generar un diagnóstico fundamentado combinando ambas fuentes

---

## 2. Instrucciones de ejecución

### Requisitos previos

* Python 3.10 o superior
* Ollama instalado

### Instalación

1. Descargar el modelo multimodal:

```bash
ollama pull llava
```

2. Clonar o descargar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

3. Instalar dependencias:

```bash
pip install PyQt6 requests duckduckgo-search
```

4. Asegurarse de que Ollama está en ejecución y lanzar la aplicación:

```bash
python main.py
```

---

## 3. Arquitectura MVC

El proyecto sigue una arquitectura Modelo-Vista-Controlador (MVC) estricta, aplicando principios SOLID y separación de responsabilidades.

### Modelo (`/model/`)

Gestiona el estado y la lógica de datos. No depende de la interfaz gráfica.

* `model.py` → Estado central del sistema
* `config_loader.py` → Carga y estructura de `config_sintomas.json`
* `pdf_manager.py` → Gestión de documentos PDF locales

---

### Vista (`/view/`)

Encargada de la interfaz gráfica. Totalmente desacoplada de la lógica.

* `main_window.py` → Construcción dinámica basada en JSON
* `/dialogs/` → Ventanas secundarias modulares:

  * `diagnosis_dialog.py`
  * `hypothesis_dialog.py`
  * `web_sources_dialog.py`
* `style.qss` → Estilo visual clínico moderno

---

### Controlador (`/controller/`)

Actúa como intermediario entre la Vista y el Modelo.

* `controller.py` → Orquestador principal
* `llm_worker.py` → Ejecución asíncrona del LLM con QThread (evita bloqueos en la UI)
* `prompt_builder.py` → Generación de prompts estructurados
* `web_search.py` → Integración con búsqueda web (DuckDuckGo)

---

## 4. Modo Local vs Web

El sistema permite seleccionar el contexto de inferencia mediante la sección "Modo de Consulta" en la interfaz.

### Modo "Solo Local"

* Usa exclusivamente documentos cargados por el usuario
* No realiza consultas externas
* Garantiza privacidad total

En la interfaz:
"No se consultaron fuentes web – Modo solo local"

---

### Modo "Web + Local"

* Combina conocimiento local con información de internet
* Realiza búsquedas en tiempo real mediante DuckDuckGo
* Mejora la calidad y actualidad del diagnóstico

En la interfaz:

* Se muestra una lista de fuentes reales consultadas
* URLs accesibles desde la ventana "Fuentes Web"

---

## Características destacadas

* Integración real con IA multimodal (LLaVA)
* Arquitectura profesional MVC
* Interfaz dinámica basada en JSON
* Ejecución asíncrona (UI siempre fluida)
* Soporte para imágenes médicas
* Modo offline (privado) y online (enriquecido)

---

## Licencia

Este proyecto ha sido desarrollado con fines académicos.
