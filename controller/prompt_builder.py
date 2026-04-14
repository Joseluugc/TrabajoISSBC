"""
prompt_builder.py – Constructor de prompts para LLaVa.

Responsabilidad única (SRP): ensamblar el prompt dinámico a partir
de los datos clínicos del paciente, el contexto de PDFs (RAG) y
el contexto web. Separado del controlador para mantenerlo como
orquestador puro.
"""

import os


def construir_prompt(
    sintomas: list[str],
    valores: dict[str, str],
    ruta_radiografia: str | None,
    texto_pdfs: str,
    contexto_web: str,
    tipo_analisis: str = "completo",
    descripcion_imagen: str = "",
) -> str:
    """
    Construye un prompt estructurado para LLaVa.

    Args:
        sintomas: Lista de síntomas marcados por el usuario.
        valores: Dict de {etiqueta: valor} de los comboboxes clínicos.
        ruta_radiografia: Ruta al archivo de radiografía (o None).
        texto_pdfs: Texto extraído de los PDFs de conocimiento (RAG local).
        contexto_web: Texto de resultados web (RAG web) o cadena vacía.
        tipo_analisis: "evaluar" (solo hipótesis) o "completo" (todo).

    Returns:
        Prompt completo listo para enviar a la API de Ollama.
    """
    secciones = []

    # --- 1. System prompt ---
    secciones.append(_seccion_system(ruta_radiografia))

    # --- 2. Datos clínicos del paciente ---
    secciones.append(_seccion_datos_paciente(sintomas, valores, ruta_radiografia, descripcion_imagen))

    # --- 3. Contexto RAG local (PDFs) ---
    if texto_pdfs:
        secciones.append(
            "--- CONTEXTO CLÍNICO DE REFERENCIA (Base de Conocimiento Local) ---\n"
            f"{texto_pdfs[:3000]}\n"
            "Usa este contexto como referencia clínica para tu análisis."
        )

    # --- 4. Contexto web ---
    if contexto_web:
        secciones.append(
            "--- INFORMACIÓN WEB RECIENTE ---\n"
            f"{contexto_web}\n"
            "Incorpora esta información reciente en tu análisis."
        )

    # --- 5. Instrucciones de formato JSON ---
    secciones.append(_seccion_instrucciones(tipo_analisis))

    return "\n\n".join(secciones)


# ------------------------------------------------------------------
# Secciones internas del prompt
# ------------------------------------------------------------------
def _seccion_system(ruta_radiografia: str | None) -> str:
    """Genera el system prompt del traumatólogo experto."""
    prompt = (
        "Eres un traumatólogo experto con 20 años de experiencia clínica. "
        "Analiza la información clínica proporcionada"
    )
    if ruta_radiografia:
        prompt += " y la imagen de radiografía adjunta"
    prompt += (
        ". Tu análisis debe ser detallado, profesional y basado en "
        "evidencia médica."
    )
    return prompt


def _seccion_datos_paciente(
    sintomas: list[str],
    valores: dict[str, str],
    ruta_radiografia: str | None,
    descripcion_imagen: str = "",
) -> str:
    """Genera la sección con los datos clínicos del paciente."""
    lineas = ["--- DATOS CLÍNICOS DEL PACIENTE ---"]
    lineas.append(f"Síntomas reportados: {', '.join(sintomas)}")

    for etiqueta, valor in valores.items():
        lineas.append(f"{etiqueta}: {valor}")

    if ruta_radiografia:
        lineas.append(
            f"\nSe adjunta imagen de radiografía: "
            f"{os.path.basename(ruta_radiografia)}"
        )
        if descripcion_imagen:
            lineas.append(
                f"**Informe radiológico preliminar (generado por IA):** {descripcion_imagen}\n"
                "Utiliza esta descripción como referencia fiable de la zona anatómica y hallazgos visibles. "
                "No la contradigas a menos que tengas evidencia muy clara en la imagen."
            )
        lineas.append(
            "Analiza la imagen para detectar hallazgos radiológicos relevantes "
            "(fracturas, luxaciones, edemas óseos, etc.)."
        )

    return "\n".join(lineas)


def _seccion_instrucciones(tipo_analisis: str) -> str:
    """Genera las instrucciones de formato de respuesta JSON."""
    if tipo_analisis == "evaluar":
        return (
            "--- INSTRUCCIONES DE RESPUESTA ---\n"
            "Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON con la "
            "siguiente estructura:\n"
            "{\n"
            '  "hipotesis": [\n'
            '    {"nombre": "Nombre del diagnóstico", "probabilidad": 85.0},\n'
            '    {"nombre": "Otro diagnóstico", "probabilidad": 10.0}\n'
            "  ]\n"
            "}\n"
            "Incluye entre 3 y 5 hipótesis ordenadas de mayor a menor probabilidad. "
            "Las probabilidades deben sumar aproximadamente 100%."
        )
    else:
        return (
            "--- INSTRUCCIONES DE RESPUESTA ---\n"
            "Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON con la "
            "siguiente estructura:\n"
            "{\n"
            '  "hipotesis": [\n'
            '    {"nombre": "Nombre del diagnóstico", "probabilidad": 85.0},\n'
            '    {"nombre": "Otro diagnóstico", "probabilidad": 10.0}\n'
            "  ],\n"
            '  "diagnostico": "Diagnóstico principal más probable",\n'
            '  "justificacion": "Justificación clínica detallada...",\n'
            '  "recomendaciones": "Recomendaciones de tratamiento..."\n'
            "}\n"
            "Incluye entre 3 y 5 hipótesis. Proporciona una justificación "
            "clínica detallada y recomendaciones de tratamiento específicas."
        )
