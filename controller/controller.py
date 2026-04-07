"""
controller.py – Controlador (Orquestador) de la aplicación MVC.

Responsabilidad única: actuar como "pegamento" entre la Vista y el Modelo.
  - Conecta las señales de la UI con acciones.
  - Recoge datos de la Vista → actualiza el Modelo.
  - Delega la construcción de prompts a prompt_builder.
  - Delega la búsqueda web a web_search (vía WebSearchWorker).
  - Delega la inferencia asíncrona al LLMWorker (QThread).
  - Valida la imagen subida con ImageValidatorWorker (LLaVA).
  - Abre los diálogos correspondientes con los resultados.

NO contiene lógica de formateo de prompts, búsqueda web ni inferencia.
"""

import os

from PyQt6.QtWidgets import QFileDialog, QMessageBox

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
from controller.web_search_worker import WebSearchWorker
from controller.image_validator_worker import ImageValidatorWorker
from controller.prompt_builder import construir_prompt


class Controlador:
    """Orquestador MVC: conecta Vista ↔ Modelo ↔ LLM."""

    def __init__(self, modelo: Modelo, vista: VentanaPrincipal):
        self.modelo = modelo
        self.vista = vista
        self._worker: LLMWorker | None = None
        self._web_worker: WebSearchWorker | None = None
        self._img_validator: ImageValidatorWorker | None = None
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
        nuevos_sintomas = self.vista.obtener_sintomas_marcados()
        nuevos_valores = self.vista.obtener_valores_combobox()
        nuevo_modo = self.vista.obtener_modo()

        # Invalidar caché web si cambiaron los datos de entrada
        if (nuevos_sintomas != self.modelo.sintomas_seleccionados
                or nuevos_valores != self.modelo.valores_combobox
                or nuevo_modo != self.modelo.modo):
            self.modelo.contexto_web = ""
            self.modelo.fuentes_web = []

        self.modelo.sintomas_seleccionados = nuevos_sintomas
        self.modelo.valores_combobox = nuevos_valores
        self.modelo.modo = nuevo_modo

    # ------------------------------------------------------------------
    # Validación de PDFs según modo
    # ------------------------------------------------------------------
    def _validar_pdfs_modo(self) -> bool:
        """
        Valida que haya PDFs según el modo seleccionado.

        Returns:
            True si se puede continuar, False si se debe abortar.
        """
        tiene_pdfs = len(self.modelo.pdfs) > 0

        if self.modelo.modo == "Solo Local" and not tiene_pdfs:
            self.vista.mostrar_error(
                "Sin base de conocimiento",
                "En modo 'Solo Local' es necesario tener al menos un PDF "
                "en la base de conocimiento.\n\n"
                "Use el botón '📚 Gestión Conocimiento (PDFs)' para añadir "
                "documentos clínicos de referencia.",
            )
            return False

        if self.modelo.modo == "Web + Local" and not tiene_pdfs:
            QMessageBox.warning(
                self.vista,
                "Sin PDFs locales",
                "No hay PDFs en la base de conocimiento local.\n\n"
                "El análisis se realizará únicamente con información "
                "de búsqueda web, sin contexto clínico local.\n\n"
                "Puede añadir PDFs desde '📚 Gestión Conocimiento (PDFs)' "
                "para mejorar la calidad del diagnóstico.",
            )
            # No bloquea: permite continuar solo con web

        return True

    # ------------------------------------------------------------------
    # Slot: Subir radiografía (con validación LLaVA)
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
            # Invalidar caché web (nueva imagen = nuevo contexto)
            self.modelo.contexto_web = ""
            self.modelo.fuentes_web = []
            self.modelo.descripcion_imagen = ""
            self.vista.mostrar_ruta_radiografia(os.path.basename(ruta))
            self.vista.mostrar_preview_imagen(ruta)
            # Lanzar validación de dominio con LLaVA
            self._validar_imagen_dominio()

    def _validar_imagen_dominio(self):
        """Lanza un worker para validar si la imagen es de traumatología."""
        imagen_b64 = self.modelo.obtener_imagen_base64()
        if not imagen_b64:
            return

        # Si ya hay un validador en ejecución, no lanzar otro
        if self._img_validator and self._img_validator.isRunning():
            return

        self._img_validator = ImageValidatorWorker(imagen_b64)
        self._img_validator.validacion_lista.connect(self._procesar_validacion_imagen)
        self._img_validator.error_ocurrido.connect(self._error_validacion_imagen)
        self._img_validator.finished.connect(self._validacion_imagen_finalizada)

        self.vista.mostrar_progreso(
            "🔍 Verificando que la imagen sea de dominio traumatológico...\n"
            "Esto puede tardar unos segundos."
        )
        self._img_validator.start()

    def _procesar_validacion_imagen(self, es_medica: bool, razon: str, descripcion: str):
        """Procesa el resultado de la validación de imagen."""
        self.vista.ocultar_progreso()
        # Guardar la descripción de la imagen para búsquedas web
        self.modelo.descripcion_imagen = descripcion
        if not es_medica:
            QMessageBox.warning(
                self.vista,
                "⚠️ Imagen no relacionada con traumatología",
                f"La imagen subida no parece ser una imagen médica "
                f"de traumatología.\n\n"
                f"Motivo: {razon}\n\n"
                f"El sistema está diseñado para analizar radiografías, "
                f"TACs, resonancias y otras pruebas traumatológicas.\n\n"
                f"Puede continuar, pero los resultados podrían no ser "
                f"fiables.",
            )

    def _error_validacion_imagen(self, mensaje: str):
        """Maneja errores en la validación de imagen."""
        self.vista.ocultar_progreso()
        # No bloquear: si falla la validación, el usuario puede continuar
        print(f"[WARN] Validación de imagen: {mensaje}")

    def _validacion_imagen_finalizada(self):
        """Limpia la referencia al worker de validación."""
        self._img_validator = None

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
        if not self._validar_pdfs_modo():
            return
        self._accion_pendiente = "evaluar"
        self._iniciar_analisis("evaluar")

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
        if not self._validar_pdfs_modo():
            return
        self._accion_pendiente = "diagnosticar"
        self._iniciar_analisis("completo")

    # ------------------------------------------------------------------
    # Flujo de análisis: web search → LLM
    # ------------------------------------------------------------------
    def _iniciar_analisis(self, tipo_analisis: str):
        """Inicia el flujo de análisis: búsqueda web (si aplica) → LLM."""
        if self._worker and self._worker.isRunning():
            self.vista.mostrar_error(
                "Proceso en curso",
                "Ya hay un análisis en ejecución. Espere a que termine.",
            )
            return

        self._tipo_analisis_pendiente = tipo_analisis

        if self.modelo.modo == "Web + Local":
            # Reutilizar caché si ya hay resultados web previos
            if self.modelo.contexto_web and self.modelo.fuentes_web:
                self._lanzar_worker_llm(contexto_web=self.modelo.contexto_web)
            else:
                # Paso 1: búsqueda web asíncrona con barra de progreso
                self._lanzar_busqueda_web()
        else:
            # Sin búsqueda web: ir directo al LLM
            self.modelo.fuentes_web = []
            self.modelo.contexto_web = ""
            self._lanzar_worker_llm(contexto_web="")

    def _lanzar_busqueda_web(self):
        """Lanza el WebSearchWorker con barra de progreso."""
        if self._web_worker and self._web_worker.isRunning():
            return

        self._web_worker = WebSearchWorker(
            sintomas=self.modelo.sintomas_seleccionados,
            valores=self.modelo.valores_combobox,
            descripcion_imagen=self.modelo.descripcion_imagen,
        )
        self._web_worker.resultado_listo.connect(self._busqueda_web_completada)
        self._web_worker.error_ocurrido.connect(self._error_busqueda_web)
        self._web_worker.finished.connect(self._busqueda_web_finalizada)

        self.vista.deshabilitar_botones(True)
        self.vista.mostrar_progreso(
            "🌐 Buscando información médica en la web...\n"
            "Consultando fuentes clínicas actualizadas."
        )
        self._web_worker.start()

    def _busqueda_web_completada(self, contexto_web: str, fuentes: list):
        """Callback cuando la búsqueda web termina con éxito."""
        self.vista.ocultar_progreso()
        # Cachear resultados para reutilizarlos en análisis sucesivos
        self.modelo.fuentes_web = fuentes
        self.modelo.contexto_web = contexto_web
        # Paso 2: lanzar el LLM con el contexto web obtenido
        self._lanzar_worker_llm(contexto_web=contexto_web)

    def _error_busqueda_web(self, mensaje: str):
        """Callback si la búsqueda web falla."""
        self.vista.ocultar_progreso()
        self.modelo.fuentes_web = [mensaje]
        # Continuar sin contexto web
        self._lanzar_worker_llm(contexto_web="")

    def _busqueda_web_finalizada(self):
        """Limpia la referencia al worker de búsqueda web."""
        self._web_worker = None

    # ------------------------------------------------------------------
    # Lanzar el worker de inferencia LLM
    # ------------------------------------------------------------------
    def _lanzar_worker_llm(self, contexto_web: str):
        """Crea y lanza un LLMWorker en un QThread separado."""
        # Construir prompt (delegado a prompt_builder)
        prompt = construir_prompt(
            sintomas=self.modelo.sintomas_seleccionados,
            valores=self.modelo.valores_combobox,
            ruta_radiografia=self.modelo.ruta_radiografia,
            texto_pdfs=self.modelo.extraer_texto_pdfs(),
            contexto_web=contexto_web,
            tipo_analisis=self._tipo_analisis_pendiente,
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
    # Callbacks del worker LLM
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
