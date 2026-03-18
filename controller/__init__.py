"""Paquete Controller – Lógica de negocio y coordinación MVC."""
from .controller import Controlador
from .llm_worker import LLMWorker
from .prompt_builder import construir_prompt
from .web_search import buscar_web

__all__ = ["Controlador", "LLMWorker", "construir_prompt", "buscar_web"]
