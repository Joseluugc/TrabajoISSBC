"""
controller.py – Controlador (Orquestador) de la aplicación MVC.

Responsabilidad única: actuar como "pegamento" entre la Vista y el Modelo.
  - Conecta las señales de la UI con acciones.
  - Recoge datos de la Vista → actualiza el Modelo.
  - Delega la construcción de prompts a prompt_builder.
  - Delega la búsqueda web a web_search.
  - Delega la inferencia asíncrona al LLMWorker (QThread).
  - Abre los diálogos correspondientes con los resultados.

NO contiene lógica de formateo de prompts, búsqueda web ni inferencia.
"""

import os

from PyQt6.QtWidgets import QFileDialog

from model.model import Modelo
from view.main_window import VentanaPrincipal
from view.dialogs import (
    DialogoHipotesis,
    DialogoJustificacion,
    DialogoPDFs,
    DialogoFuentesWeb,
    DialogoResultadoLLM,
)
from controller.llm_worker import LLMWorker
from controller.prompt_builder import construir_prompt
from controller.web_search import buscar_web


class Controlador:
    """Orquestador MVC: conecta Vista ↔ Modelo ↔ LLM."""

    def __init__(self, modelo: Modelo, vista: VentanaPrincipal):
        self.modelo = modelo
        self.vista = vista
        self._worker: LLMWorker | None = None
        self._accion_pendiente: str = ""
        self._conectar_senales()

    # ------------------------------------------------------------------
    # Conexión de señales (botones → slots)
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
    # Recoger datos de la Vista → Modelo
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
    # Slot: Evaluar hipótesis
    # ------------------------------------------------------------------
    def _evaluar_hipotesis(self):
        """Recoge síntomas y lanza QThread para evaluar hipótesis."""
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
    # Slot: Diagnosticar
    # ------------------------------------------------------------------
    def _diagnosticar(self):
        """Recoge síntomas y lanza QThread para diagnóstico completo."""
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
        """Crea y lanza un LLMWorker en un QThread separado."""
        if self._worker and self._worker.isRunning():
            self.vista.mostrar_error(
                "Proceso en curso",
                "Ya hay un análisis en ejecución. Espere a que termine.",
            )
            return

        # Obtener contexto web si corresponde
        contexto_web = ""
        if self.modelo.modo == "Web + Local":
            contexto_web, fuentes = buscar_web(
                self.modelo.sintomas_seleccionados,
                self.modelo.valores_combobox,
            )
            self.modelo.fuentes_web = fuentes
        else:
            self.modelo.fuentes_web = []

        # Construir prompt (delegado a prompt_builder)
        prompt = construir_prompt(
            sintomas=self.modelo.sintomas_seleccionados,
            valores=self.modelo.valores_combobox,
            ruta_radiografia=self.modelo.ruta_radiografia,
            texto_pdfs=self.modelo.extraer_texto_pdfs(),
            contexto_web=contexto_web,
            tipo_analisis=tipo_analisis,
        )

        # Crear y conectar el worker
        imagen_b64 = self.modelo.obtener_imagen_base64()
        self._worker = LLMWorker(prompt=prompt, imagen_base64=imagen_b64)
        self._worker.resultado_listo.connect(self._procesar_resultado)
        self._worker.error_ocurrido.connect(self._procesar_error)
        self._worker.finished.connect(self._inferencia_finalizada)

        # Feedback visual
        self.vista.deshabilitar_botones(True)
        self.vista.mostrar_progreso(
            "🔬 Analizando radiografía y observables clínicos...\n"
            "Por favor espere. Esto puede tardar unos minutos."
        )

        self._worker.start()

    # ------------------------------------------------------------------
    # Callbacks del worker
    # ------------------------------------------------------------------
    def _procesar_resultado(self, resultado: dict):
        """Procesa el resultado del LLM y abre el diálogo correspondiente."""
        self.vista.ocultar_progreso()
        self._guardar_resultado_en_modelo(resultado)

        if self._accion_pendiente == "evaluar" and self.modelo.hipotesis:
            DialogoHipotesis(self.modelo.hipotesis, parent=self.vista).exec()
        else:
            DialogoResultadoLLM(resultado, parent=self.vista).exec()

    def _procesar_error(self, mensaje_error: str):
        """Muestra el error devuelto por el worker."""
        self.vista.ocultar_progreso()
        self.vista.mostrar_error("Error de Inferencia", mensaje_error)

    def _inferencia_finalizada(self):
        """Se ejecuta cuando el QThread termina (éxito o error)."""
        self.vista.deshabilitar_botones(False)
        self._worker = None

    # ------------------------------------------------------------------
    # Actualización del modelo con resultados
    # ------------------------------------------------------------------
    def _guardar_resultado_en_modelo(self, resultado: dict):
        """Parsea el resultado del LLM y actualiza el estado del modelo."""
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

        if self.modelo.hipotesis:
            self.modelo.confianza = max(
                h.get("probabilidad", 0) for h in self.modelo.hipotesis
            )

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
        DialogoJustificacion(self.modelo.justificacion, parent=self.vista).exec()

    # ------------------------------------------------------------------
    # Slot: Gestionar PDFs
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
        DialogoFuentesWeb(self.modelo.fuentes_web, parent=self.vista).exec()
