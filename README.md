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
   pip install PyQt6
