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

El modelo es capaz de:

* Analizar imágenes médicas (como radiografías)
* Interpretar síntomas textuales
* Generar un diagnóstico fundamentado combinando ambas fuentes

---

## 2. Ejecución rápida

Siga estos pasos exactamente para ejecutar el proyecto sin errores:

```bash
git clone https://github.com/Joseluugc/TrabajoISSBC.git
cd TrabajoISSBC
pip install -r requirements.txt
ollama pull llava
python main.py
```

---

## 3. Requisitos

* Python 3.10 o superior
* Ollama instalado

### Probado con

* Python 3.10
* Python 3.11

---

## 4. Dependencias

El proyecto incluye un archivo `requirements.txt` con todas las dependencias necesarias:

```txt
PyQt6
requests
duckduckgo-search
```

Instalación:

```bash
pip install -r requirements.txt
```

---

## 5. Configuración de Ollama (IMPORTANTE)

Este proyecto depende de Ollama para ejecutar el modelo LLaVA.

Asegúrese de:

1. Tener Ollama instalado
2. Tener el modelo descargado:

```bash
ollama pull llava
```

3. Tener Ollama ejecutándose en segundo plano:

```bash
ollama serve
```

Si Ollama no está activo, el sistema de diagnóstico no funcionará.

---

## 6. Arquitectura MVC

El proyecto sigue una arquitectura Modelo-Vista-Controlador (MVC) estricta, aplicando principios SOLID y separación de responsabilidades.

### Modelo (`/model/`)

Gestiona el estado y la lógica de datos.

* `model.py` → Estado central del sistema
* `config_loader.py` → Carga de configuración JSON
* `pdf_manager.py` → Gestión de documentos PDF

---

### Vista (`/view/`)

Encargada de la interfaz gráfica.

* `main_window.py` → Construcción dinámica basada en JSON
* `/dialogs/` → Ventanas secundarias
* `style.qss` → Estilos visuales

---

### Controlador (`/controller/`)

Coordina la lógica entre modelo y vista.

* `controller.py` → Orquestador principal
* `llm_worker.py` → Ejecución asíncrona del modelo
* `prompt_builder.py` → Construcción de prompts
* `web_search.py` → Búsqueda web con DuckDuckGo

---

## 7. Estructura del proyecto

```bash
TrabajoISSBC/
│
├── main.py
├── requirements.txt
├── config_sintomas.json
│
├── model/
├── view/
├── controller/
```

---

## 8. Modo de funcionamiento

### Modo "Solo Local"

* Usa únicamente documentos cargados por el usuario
* No realiza consultas externas
* Garantiza privacidad

La interfaz muestra:
"No se consultaron fuentes web – Modo solo local"

---

### Modo "Web + Local"

* Combina conocimiento local con información de internet
* Realiza búsquedas en tiempo real
* Mejora la calidad del diagnóstico

La interfaz muestra:

* Lista de fuentes web consultadas
* URLs accesibles desde la ventana correspondiente

---

## 9. Problemas comunes

**Error: no responde el modelo**

* Ejecutar: `ollama pull llava`

**Error de conexión con Ollama**

* Asegurarse de que está ejecutándose: `ollama serve`

**Error de módulos faltantes**

* Ejecutar: `pip install -r requirements.txt`

---

## 10. Notas

* La aplicación está diseñada con fines académicos
* El diagnóstico generado es orientativo y no sustituye a un profesional médico

---

## 11. Participantes

* José Luis García Corbacho
* Javier Jesus Costa Ruiz-Canela
* Marcos Hidalgo Moreno

---

## 12. Licencia

Proyecto desarrollado con fines educativos.
