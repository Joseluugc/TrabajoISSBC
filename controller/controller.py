"""
controller.py – Controlador de la aplicación MVC de Diagnóstico de Traumatismos.

Responsabilidades:
  - Conectar las señales de la Vista con los métodos del Controlador.
  - Recoger datos de la Vista, actualizar el Modelo.
  - Construir prompts dinámicos para LLaVa (ingeniería del prompt).
  - Gestionar la ejecución asíncrona (QThread) para no bloquear la GUI.
  - Implementar los modos Local (RAG con PDFs) y Web + Local (búsqueda web).
"""

import os
import json

from PyQt6.QtWidgets import QFileDialog

from model.model import Modelo
from view.view import (
    VentanaPrincipal, DialogoHipotesis, DialogoDiagnostico,
    DialogoJustificacion, DialogoPDFs, DialogoFuentesWeb,
    DialogoResultadoLLM,
)
from controller.llm_worker import LLMWorker


class Controlador:
    """Controlador que conecta la Vista y el Modelo, gestiona LLM."""

    def __init__(self, modelo: Modelo, vista: VentanaPrincipal):
        self.modelo = modelo
        self.vista = vista
        self._worker: LLMWorker | None = None
        self._accion_pendiente: str = ""  # "evaluar" o "diagnosticar"
        self._conectar_senales()

    # ------------------------------------------------------------------
    # Conexión de señales (botones → métodos)
    # ------------------------------------------------------------------
    def _conectar_senales(self):
        """Conecta cada botón de la vista con su slot correspondiente."""
        self.vista.btn_subir_radiografia.clicked.connect(self._subir_radiografia)
        self.vista.btn_evaluar.clicked.connect(self._evaluar_hipotesis)
        self.vista.btn_diagnosticar.clicked.connect(self._diagnosticar)
        self.vista.btn_justificacion.clicked.connect(self._ver_justificacion)
        self.vista.btn_pdfs.clicked.connect(self._gestionar_pdfs)
        self.vista.btn_fuentes.clicked.connect(self._ver_fuentes_web)

    # ------------------------------------------------------------------
    # Recoger síntomas de la vista → modelo
    # ------------------------------------------------------------------
    def _recoger_datos_vista(self):
        """Lee los valores actuales de la vista y los almacena en el modelo."""
        self.modelo.sintomas_seleccionados = self.vista.obtener_sintomas_marcados()
        self.modelo.valores_combobox = self.vista.obtener_valores_combobox()
        self.modelo.modo = self.vista.obtener_modo()

    # ------------------------------------------------------------------
    # Slot: Subir radiografía
    # ------------------------------------------------------------------
    def _subir_radiografia(self):
        """Abre un diálogo para seleccionar una imagen de radiografía."""
        ruta, _ = QFileDialog.getOpenFileName(
            self.vista,
            "Seleccionar Radiografía o Prueba",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp);;Todos (*)",
        )
        if ruta:
            self.modelo.establecer_radiografia(ruta)
            self.vista.mostrar_ruta_radiografia(os.path.basename(ruta))
            self.vista.mostrar_preview_imagen(ruta)

    # ------------------------------------------------------------------
    # Ingeniería del Prompt
    # ------------------------------------------------------------------
    def _construir_prompt(self, tipo_analisis: str = "completo") -> str:
        """
        Construye un prompt dinámico para LLaVa basado en los datos
        del paciente, síntomas, y contexto clínico.

        Args:
            tipo_analisis: "evaluar" para solo hipótesis, "completo" para todo.
        """
        sintomas = self.modelo.sintomas_seleccionados
        valores = self.modelo.valores_combobox
        modo = self.modelo.modo

        # --- System prompt ---
        prompt = (
            "Eres un traumatólogo experto con 20 años de experiencia clínica. "
            "Analiza la información clínica proporcionada"
        )

        if self.modelo.ruta_radiografia:
            prompt += " y la imagen de radiografía adjunta"

        prompt += (
            ". Tu análisis debe ser detallado, profesional y basado en "
            "evidencia médica. "
        )

        # --- Datos del paciente ---
        prompt += "\n\n--- DATOS CLÍNICOS DEL PACIENTE ---\n"
        prompt += f"Síntomas reportados: {', '.join(sintomas)}\n"

        for etiqueta, valor in valores.items():
            prompt += f"{etiqueta}: {valor}\n"

        if self.modelo.ruta_radiografia:
            prompt += (
                f"\nSe adjunta imagen de radiografía: "
                f"{os.path.basename(self.modelo.ruta_radiografia)}\n"
                "Analiza la imagen para detectar hallazgos radiológicos relevantes "
                "(fracturas, luxaciones, edemas óseos, etc.).\n"
            )

        # --- Contexto de PDFs (RAG Local) ---
        texto_pdfs = self.modelo.extraer_texto_pdfs()
        if texto_pdfs:
            prompt += (
                "\n--- CONTEXTO CLÍNICO DE REFERENCIA (Base de Conocimiento Local) ---\n"
                f"{texto_pdfs[:3000]}\n"  # Limitar a 3000 chars para no saturar
                "Usa este contexto como referencia clínica para tu análisis.\n"
            )

        # --- Contexto web (si modo Web + Local) ---
        if modo == "Web + Local":
            resultados_web = self._buscar_web(sintomas, valores)
            if resultados_web:
                prompt += (
                    "\n--- INFORMACIÓN WEB RECIENTE ---\n"
                    f"{resultados_web}\n"
                    "Incorpora esta información reciente en tu análisis.\n"
                )

        # --- Formato de respuesta esperado ---
        if tipo_analisis == "evaluar":
            prompt += (
                "\n--- INSTRUCCIONES DE RESPUESTA ---\n"
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
            prompt += (
                "\n--- INSTRUCCIONES DE RESPUESTA ---\n"
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

        return prompt

    # ------------------------------------------------------------------
    # Búsqueda Web (DuckDuckGo o mock)
    # ------------------------------------------------------------------
    def _buscar_web(self, sintomas: list[str], valores: dict) -> str:
        """
        Busca información médica reciente en la web usando duckduckgo-search.
        Si la librería no está instalada, usa un mock inteligente.
        """
        zona = valores.get("Zona afectada", "extremidad")
        query = f"traumatología {zona} {' '.join(sintomas[:3])} diagnóstico tratamiento"

        try:
            from duckduckgo_search import DDGS

            resultados = []
            self.modelo.fuentes_web = []

            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    titulo = r.get("title", "")
                    cuerpo = r.get("body", "")
                    href = r.get("href", "")
                    resultados.append(f"- {titulo}: {cuerpo}")
                    if href:
                        self.modelo.fuentes_web.append(f"{titulo} — {href}")

            return "\n".join(resultados) if resultados else ""

        except ImportError:
            # Fallback: mock inteligente basado en los síntomas
            self.modelo.fuentes_web = [
                f"https://www.ncbi.nlm.nih.gov/books/ – Búsqueda: {query[:50]}",
                f"https://pubmed.ncbi.nlm.nih.gov/ – Traumatología {zona}",
                "https://www.mayoclinic.org/ – Diagnóstico traumatológico",
                "https://www.cochranelibrary.com/ – Revisiones sistemáticas",
                "https://www.uptodate.com/ – Guías clínicas actualizadas",
            ]
            return (
                f"[Simulación] Resultados web para: {query}\n"
                f"- Guías clínicas actualizadas sobre lesiones en {zona}.\n"
                f"- Protocolos de diagnóstico para: {', '.join(sintomas[:3])}.\n"
                "- Evidencia reciente sobre tratamiento conservador vs quirúrgico.\n"
                "(Instale duckduckgo-search para resultados reales: "
                "pip install duckduckgo-search)"
            )
        except Exception as e:
            self.modelo.fuentes_web = [f"Error en búsqueda web: {e}"]
            return ""

    # ------------------------------------------------------------------
    # Slot: Evaluar hipótesis (LLM real vía QThread)
    # ------------------------------------------------------------------
    def _evaluar_hipotesis(self):
        """Recoge síntomas y lanza QThread para evaluar hipótesis con LLaVa."""
        self._recoger_datos_vista()

        if not self.modelo.hay_sintomas():
            self.vista.mostrar_error(
                "Sin síntomas",
                "Debe seleccionar al menos un síntoma antes de evaluar hipótesis.",
            )
            return

        self._accion_pendiente = "evaluar"
        self._lanzar_worker("evaluar")

    # ------------------------------------------------------------------
    # Slot: Diagnosticar (LLM real vía QThread)
    # ------------------------------------------------------------------
    def _diagnosticar(self):
        """Recoge síntomas y lanza QThread para diagnóstico completo con LLaVa."""
        self._recoger_datos_vista()

        if not self.modelo.hay_sintomas():
            self.vista.mostrar_error(
                "Sin síntomas",
                "Debe seleccionar al menos un síntoma antes de diagnosticar.",
            )
            return

        self._accion_pendiente = "diagnosticar"
        self._lanzar_worker("completo")

    # ------------------------------------------------------------------
    # Lanzar el worker de inferencia
    # ------------------------------------------------------------------
    def _lanzar_worker(self, tipo_analisis: str):
        """
        Crea y lanza un LLMWorker en un QThread separado.
        Muestra progreso y deshabilita botones para evitar doble ejecución.
        """
        # Evitar lanzar múltiples workers simultáneamente
        if self._worker and self._worker.isRunning():
            self.vista.mostrar_error(
                "Proceso en curso",
                "Ya hay un análisis en ejecución. Espere a que termine.",
            )
            return

        # Construir el prompt
        prompt = self._construir_prompt(tipo_analisis)

        # Obtener imagen en base64 si existe
        imagen_b64 = self.modelo.obtener_imagen_base64()

        # Crear el worker QThread
        self._worker = LLMWorker(
            prompt=prompt,
            imagen_base64=imagen_b64,
            parent=None,
        )

        # Conectar señales del worker
        self._worker.resultado_listo.connect(self._procesar_resultado)
        self._worker.error_ocurrido.connect(self._procesar_error)
        self._worker.finished.connect(self._inferencia_finalizada)

        # Mostrar progreso y deshabilitar botones
        self.vista.deshabilitar_botones(True)
        self.vista.mostrar_progreso(
            "🔬 Analizando radiografía y observables clínicos...\n"
            "Por favor espere. Esto puede tardar unos minutos."
        )

        # ¡Iniciar el hilo! (no bloquea la GUI)
        self._worker.start()

    # ------------------------------------------------------------------
    # Callbacks del worker
    # ------------------------------------------------------------------
    def _procesar_resultado(self, resultado: dict):
        """Procesa el resultado devuelto por el LLM."""
        self.vista.ocultar_progreso()

        # Guardar resultados en el modelo
        hipotesis_raw = resultado.get("hipotesis", [])
        if isinstance(hipotesis_raw, list):
            self.modelo.hipotesis = []
            for h in hipotesis_raw:
                if isinstance(h, dict):
                    self.modelo.hipotesis.append({
                        "nombre": h.get("nombre", h.get("hipotesis", str(h))),
                        "probabilidad": float(h.get("probabilidad", h.get("porcentaje", 0))),
                    })
                elif isinstance(h, str):
                    self.modelo.hipotesis.append({"nombre": h, "probabilidad": 0})

        self.modelo.diagnostico = str(resultado.get("diagnostico", ""))
        self.modelo.justificacion = str(
            resultado.get("justificacion", resultado.get("justificación", ""))
        )
        self.modelo.recomendaciones = str(resultado.get("recomendaciones", ""))

        # Calcular confianza
        if self.modelo.hipotesis:
            self.modelo.confianza = max(
                h.get("probabilidad", 0) for h in self.modelo.hipotesis
            )

        # Mostrar diálogo según la acción
        if self._accion_pendiente == "evaluar" and self.modelo.hipotesis:
            dialogo = DialogoHipotesis(self.modelo.hipotesis, parent=self.vista)
            dialogo.exec()
        else:
            # Mostrar resultado completo
            dialogo = DialogoResultadoLLM(resultado, parent=self.vista)
            dialogo.exec()

    def _procesar_error(self, mensaje_error: str):
        """Muestra el error devuelto por el worker."""
        self.vista.ocultar_progreso()
        self.vista.mostrar_error("Error de Inferencia", mensaje_error)

    def _inferencia_finalizada(self):
        """Se ejecuta cuando el QThread termina (éxito o error)."""
        self.vista.deshabilitar_botones(False)
        self._worker = None

    # ------------------------------------------------------------------
    # Slot: Ver justificación
    # ------------------------------------------------------------------
    def _ver_justificacion(self):
        """Muestra la justificación del último diagnóstico."""
        if not self.modelo.justificacion:
            self.vista.mostrar_error(
                "Sin justificación",
                "Primero debe realizar un diagnóstico para ver la justificación.",
            )
            return

        dialogo = DialogoJustificacion(self.modelo.justificacion, parent=self.vista)
        dialogo.exec()

    # ------------------------------------------------------------------
    # Slot: Gestionar PDFs de conocimiento
    # ------------------------------------------------------------------
    def _gestionar_pdfs(self):
        """Abre el diálogo de gestión de PDFs."""
        dialogo = DialogoPDFs(self.modelo.pdfs, parent=self.vista)

        dialogo.btn_agregar.clicked.connect(lambda: self._agregar_pdf(dialogo))
        dialogo.btn_eliminar.clicked.connect(lambda: self._eliminar_pdf(dialogo))

        dialogo.exec()

    def _agregar_pdf(self, dialogo: DialogoPDFs):
        """Añade un PDF a la base de conocimiento."""
        ruta, _ = QFileDialog.getOpenFileName(
            dialogo, "Seleccionar PDF", "", "Archivos PDF (*.pdf);;Todos (*)"
        )
        if ruta:
            self.modelo.agregar_pdf(ruta)
            dialogo.refrescar(self.modelo.pdfs)

    def _eliminar_pdf(self, dialogo: DialogoPDFs):
        """Elimina el PDF seleccionado de la base de conocimiento."""
        fila = dialogo.obtener_fila_seleccionada()
        if fila < 0:
            self.vista.mostrar_error(
                "Sin selección",
                "Seleccione un PDF de la tabla para eliminarlo.",
            )
            return
        self.modelo.eliminar_pdf(fila)
        dialogo.refrescar(self.modelo.pdfs)

    # ------------------------------------------------------------------
    # Slot: Ver fuentes web
    # ------------------------------------------------------------------
    def _ver_fuentes_web(self):
        """Muestra el diálogo de fuentes web consultadas."""
        dialogo = DialogoFuentesWeb(self.modelo.fuentes_web, parent=self.vista)
        dialogo.exec()
