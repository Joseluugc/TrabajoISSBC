"""
web_search.py – Módulo de búsqueda web REAL para RAG.

Responsabilidad única (SRP): buscar información médica reciente
usando DuckDuckGo. Realiza consultas reales contra páginas web
para enriquecer el contexto del diagnóstico.
"""

from ddgs import DDGS


def buscar_web(
    sintomas: list[str],
    valores: dict[str, str],
    descripcion_imagen: str = "",
) -> tuple[str, list[str]]:
    """
    Busca información médica reciente en la web usando DuckDuckGo.

    Construye una query enriquecida que incorpora:
    - Zona corporal (de LLaVA o del combobox «Zona afectada»).
    - Signos y síntomas observables (checkboxes marcados).
    - Parámetros clínicos relevantes: mecanismo de lesión, nivel de dolor
      y tiempo de evolución.

    Args:
        sintomas: Lista de síntomas / signos observables del paciente.
        valores: Dict de parámetros clínicos {etiqueta: valor}.
        descripcion_imagen: Descripción de la imagen obtenida por LLaVA
                            (zona corporal + hallazgos). Si está disponible,
                            se prioriza sobre la zona del combobox.

    Returns:
        Tupla (texto_contexto, lista_fuentes):
        - texto_contexto: string con los resultados para inyectar en el prompt.
        - lista_fuentes: lista de URLs/títulos para mostrar al usuario.
    """
    # --- Zona corporal --------------------------------------------------
    # Priorizar la descripción de LLaVA sobre el combobox genérico
    if descripcion_imagen:
        contexto_zona = descripcion_imagen
    else:
        contexto_zona = valores.get("Zona afectada", "extremidad")

    # --- Signos y síntomas observables (todos los marcados) -------------
    signos_str = " ".join(sintomas) if sintomas else ""

    # --- Parámetros clínicos relevantes (todos los seleccionados) -------
    # Valores neutros que no aportan información a la búsqueda
    _NEUTROS = {"ninguno", "desconocido"}

    partes_clinicas: list[str] = []
    for etiqueta, valor in valores.items():
        if etiqueta == "Zona afectada":
            continue  # ya está en contexto_zona
        if valor and valor.lower() not in _NEUTROS:
            if etiqueta == "Nivel de dolor (EVA)":
                partes_clinicas.append(f"dolor EVA {valor}")
            else:
                partes_clinicas.append(valor)

    clinica_str = " ".join(partes_clinicas)

    # --- Query final ----------------------------------------------------
    query_parts = ["traumatología", contexto_zona]
    if signos_str:
        query_parts.append(signos_str)
    if clinica_str:
        query_parts.append(clinica_str)
    query_parts.append("diagnóstico tratamiento")

    query = " ".join(query_parts)

    try:
        return _buscar_duckduckgo(query)
    except Exception as e:
        return "", [f"Error en búsqueda web: {e}"]


def _buscar_duckduckgo(query: str) -> tuple[str, list[str]]:
    """Búsqueda real usando la librería duckduckgo-search."""
    resultados_texto = []
    fuentes = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, region="es-es", max_results=5):
            titulo = r.get("title", "")
            cuerpo = r.get("body", "")
            href = r.get("href", "")
            resultados_texto.append(f"- {titulo}: {cuerpo}")
            if href:
                fuentes.append(f"{titulo} — {href}")

    texto = "\n".join(resultados_texto) if resultados_texto else ""
    return texto, fuentes
