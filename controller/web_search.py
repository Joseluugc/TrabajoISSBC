"""
web_search.py – Módulo de búsqueda web para RAG.

Responsabilidad única (SRP): buscar información médica reciente
usando DuckDuckGo (con fallback a mock si la librería no está
instalada). Separado del controlador para mantenerlo limpio.
"""


def buscar_web(
    sintomas: list[str],
    valores: dict[str, str],
) -> tuple[str, list[str]]:
    """
    Busca información médica reciente en la web.

    Args:
        sintomas: Lista de síntomas del paciente.
        valores: Dict de parámetros clínicos {etiqueta: valor}.

    Returns:
        Tupla (texto_contexto, lista_fuentes):
        - texto_contexto: string con los resultados para inyectar en el prompt.
        - lista_fuentes: lista de URLs/títulos para mostrar al usuario.
    """
    zona = valores.get("Zona afectada", "extremidad")
    query = (
        f"traumatología {zona} {' '.join(sintomas[:3])} "
        f"diagnóstico tratamiento"
    )

    try:
        return _buscar_duckduckgo(query)
    except ImportError:
        return _mock_busqueda(query, zona, sintomas)
    except Exception as e:
        return "", [f"Error en búsqueda web: {e}"]


def _buscar_duckduckgo(query: str) -> tuple[str, list[str]]:
    """Búsqueda real usando la librería duckduckgo-search."""
    from duckduckgo_search import DDGS

    resultados_texto = []
    fuentes = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            titulo = r.get("title", "")
            cuerpo = r.get("body", "")
            href = r.get("href", "")
            resultados_texto.append(f"- {titulo}: {cuerpo}")
            if href:
                fuentes.append(f"{titulo} — {href}")

    texto = "\n".join(resultados_texto) if resultados_texto else ""
    return texto, fuentes


def _mock_busqueda(
    query: str,
    zona: str,
    sintomas: list[str],
) -> tuple[str, list[str]]:
    """Fallback: mock inteligente de búsqueda web."""
    fuentes = [
        f"https://www.ncbi.nlm.nih.gov/books/ – Búsqueda: {query[:50]}",
        f"https://pubmed.ncbi.nlm.nih.gov/ – Traumatología {zona}",
        "https://www.mayoclinic.org/ – Diagnóstico traumatológico",
        "https://www.cochranelibrary.com/ – Revisiones sistemáticas",
        "https://www.uptodate.com/ – Guías clínicas actualizadas",
    ]
    texto = (
        f"[Simulación] Resultados web para: {query}\n"
        f"- Guías clínicas actualizadas sobre lesiones en {zona}.\n"
        f"- Protocolos de diagnóstico para: {', '.join(sintomas[:3])}.\n"
        "- Evidencia reciente sobre tratamiento conservador vs quirúrgico.\n"
        "(Instale duckduckgo-search para resultados reales: "
        "pip install duckduckgo-search)"
    )
    return texto, fuentes
