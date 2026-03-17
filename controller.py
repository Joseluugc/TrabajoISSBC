"""
controller.py – Controlador de la aplicación MVC de Diagnóstico de Traumatismos.

Responsabilidades:
  - Conectar las señales de la Vista con los métodos del Controlador.
  - Recoger datos de la Vista, actualizar el Modelo.
  - Simular (mockear) las llamadas al LLM para generar hipótesis,
    diagnósticos, justificaciones y fuentes web.
"""

import random
import os

from PyQt6.QtWidgets import QFileDialog

from model import Modelo
from view import (
    VentanaPrincipal, DialogoHipotesis, DialogoDiagnostico,
    DialogoJustificacion, DialogoPDFs, DialogoFuentesWeb,
)


class Controlador:
    """Controlador que conecta la Vista y el Modelo."""

    def __init__(self, modelo: Modelo, vista: VentanaPrincipal):
        self.modelo = modelo
        self.vista = vista
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
        """Abre un diálogo para seleccionar una imagen/PDF de radiografía."""
        ruta, _ = QFileDialog.getOpenFileName(
            self.vista,
            "Seleccionar Radiografía o Prueba",
            "",
            "Imágenes y PDFs (*.png *.jpg *.jpeg *.bmp *.dcm *.pdf);;Todos (*)",
        )
        if ruta:
            self.modelo.establecer_radiografia(ruta)
            self.vista.mostrar_ruta_radiografia(os.path.basename(ruta))

    # ------------------------------------------------------------------
    # Slot: Evaluar hipótesis (mock LLM)
    # ------------------------------------------------------------------
    def _evaluar_hipotesis(self):
        """Recoge síntomas, simula el LLM y muestra hipótesis."""
        self._recoger_datos_vista()

        if not self.modelo.hay_sintomas():
            self.vista.mostrar_error(
                "Sin síntomas",
                "Debe seleccionar al menos un síntoma antes de evaluar hipótesis.",
            )
            return

        # --- Mock LLM: generar hipótesis simuladas ---
        self.modelo.hipotesis = self._mock_generar_hipotesis()

        # Mostrar diálogo de hipótesis
        dialogo = DialogoHipotesis(self.modelo.hipotesis, parent=self.vista)
        dialogo.exec()

    # ------------------------------------------------------------------
    # Slot: Diagnosticar (mock LLM)
    # ------------------------------------------------------------------
    def _diagnosticar(self):
        """Recoge síntomas, simula el LLM y muestra el diagnóstico final."""
        self._recoger_datos_vista()

        if not self.modelo.hay_sintomas():
            self.vista.mostrar_error(
                "Sin síntomas",
                "Debe seleccionar al menos un síntoma antes de diagnosticar.",
            )
            return

        # Si no hay hipótesis previas, generarlas primero
        if not self.modelo.hipotesis:
            self.modelo.hipotesis = self._mock_generar_hipotesis()

        # --- Mock LLM: diagnóstico final ---
        mejor = max(self.modelo.hipotesis, key=lambda h: h["probabilidad"])
        self.modelo.diagnostico = mejor["nombre"]
        self.modelo.confianza = mejor["probabilidad"]
        self.modelo.recomendaciones = self._mock_recomendaciones(mejor["nombre"])
        self.modelo.justificacion = self._mock_justificacion()

        # Generar fuentes web si el modo es Web + Local
        if self.modelo.modo == "Web + Local":
            self.modelo.fuentes_web = self._mock_fuentes_web()
        else:
            self.modelo.fuentes_web = []

        dialogo = DialogoDiagnostico(
            self.modelo.diagnostico,
            self.modelo.confianza,
            self.modelo.recomendaciones,
            parent=self.vista,
        )
        dialogo.exec()

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

        # Conectar botones del diálogo
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

    # ==================================================================
    # MOCK LLM – Simulación de inferencia
    # ==================================================================
    def _mock_generar_hipotesis(self) -> list[dict]:
        """
        Simula la respuesta de un LLM generando hipótesis
        traumatológicas con probabilidades aleatorias basadas en los
        síntomas seleccionados.
        """
        # Catálogo de posibles diagnósticos traumatológicos
        catalogo = [
            "Esguince de tobillo grado I",
            "Esguince de tobillo grado II",
            "Esguince de tobillo grado III",
            "Fractura de estrés",
            "Fractura diafisaria",
            "Luxación articular",
            "Rotura fibrilar parcial",
            "Rotura fibrilar completa",
            "Contusión ósea",
            "Tendinopatía aguda",
            "Bursitis traumática",
            "Meniscopatía",
            "Rotura de ligamento cruzado anterior",
            "Hernia discal traumática",
            "Fisura costal",
        ]

        num_sintomas = len(self.modelo.sintomas_seleccionados)

        # Seleccionar entre 3 y 5 hipótesis al azar
        n = min(random.randint(3, 5), len(catalogo))
        seleccion = random.sample(catalogo, n)

        # Generar probabilidades proporcionales a la cantidad de síntomas
        probabilidades_brutas = [
            random.uniform(10, 30) + num_sintomas * random.uniform(2, 8)
            for _ in seleccion
        ]
        # Normalizar para que no superen 100 %
        total = sum(probabilidades_brutas)
        factor = min(95.0 / total, 1.0) if total > 0 else 1.0

        hipotesis = []
        for nombre, prob in zip(seleccion, probabilidades_brutas):
            hipotesis.append({
                "nombre": nombre,
                "probabilidad": round(prob * factor, 1),
            })

        # Ordenar de mayor a menor probabilidad
        hipotesis.sort(key=lambda h: h["probabilidad"], reverse=True)
        return hipotesis

    def _mock_recomendaciones(self, diagnostico: str) -> str:
        """Devuelve recomendaciones simuladas según el diagnóstico."""
        recomendaciones = {
            "Esguince": (
                "• Reposo relativo con descarga parcial.\n"
                "• Aplicar hielo 15-20 min cada 2-3 horas las primeras 48 h.\n"
                "• Compresión con vendaje elástico.\n"
                "• Elevación del miembro afectado.\n"
                "• Control de seguimiento en 7 días."
            ),
            "Fractura": (
                "• Inmovilización del segmento afectado.\n"
                "• Derivación urgente a Traumatología.\n"
                "• Valorar necesidad de reducción quirúrgica.\n"
                "• Analgesia pautada (paracetamol / AINEs).\n"
                "• Radiografía de control en 10-14 días."
            ),
            "Rotura": (
                "• Reposo deportivo absoluto mínimo 3 semanas.\n"
                "• Ecografía de partes blandas de control.\n"
                "• Fisioterapia progresiva a partir de la 2.ª semana.\n"
                "• Evitar estiramientos forzados.\n"
                "• Valorar PRP en roturas de grado alto."
            ),
            "Luxación": (
                "• Reducción cerrada bajo sedación.\n"
                "• Inmovilización 2-3 semanas.\n"
                "• Radiografía post-reducción.\n"
                "• Rehabilitación propioceptiva precoz.\n"
                "• Vigilar signos neurovasculares distales."
            ),
        }
        # Buscar por prefijo
        for clave, texto in recomendaciones.items():
            if clave.lower() in diagnostico.lower():
                return texto

        # Recomendación genérica
        return (
            "• Reposo y evitar esfuerzos sobre la zona afectada.\n"
            "• Analgesia según necesidad.\n"
            "• Seguimiento clínico en consulta de Traumatología.\n"
            "• Pruebas complementarias si no mejora en 7-10 días.\n"
            "• Acudir a urgencias si aparecen signos de alarma."
        )

    def _mock_justificacion(self) -> str:
        """Genera un texto de justificación basándose en los síntomas marcados."""
        sintomas = self.modelo.sintomas_seleccionados
        valores = self.modelo.valores_combobox
        radiografia = self.modelo.ruta_radiografia
        modo = self.modelo.modo
        diagnostico = self.modelo.diagnostico
        confianza = self.modelo.confianza

        lineas = [
            f"JUSTIFICACIÓN DEL DIAGNÓSTICO: {diagnostico}",
            f"Nivel de confianza: {confianza:.1f} %",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "SÍNTOMAS SELECCIONADOS:",
        ]
        for s in sintomas:
            lineas.append(f"  ✓ {s}")

        lineas.append("")
        lineas.append("PARÁMETROS CLÍNICOS:")
        for etiqueta, valor in valores.items():
            lineas.append(f"  • {etiqueta}: {valor}")

        lineas.append("")
        if radiografia:
            lineas.append(f"PRUEBA COMPLEMENTARIA ADJUNTA: {os.path.basename(radiografia)}")
        else:
            lineas.append("PRUEBA COMPLEMENTARIA: No se adjuntó radiografía.")

        lineas.append(f"MODO DE CONSULTA: {modo}")
        lineas.append("")
        lineas.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lineas.append("")
        lineas.append("RAZONAMIENTO (simulado por mock-LLM):")
        lineas.append(
            f"Basándose en la presencia de {len(sintomas)} síntoma(s) — "
            f"entre ellos {', '.join(sintomas[:3])}{'…' if len(sintomas) > 3 else ''} — "
            f"y considerando la zona afectada "
            f"({valores.get('Zona afectada', 'no especificada')}), "
            f"el mecanismo de lesión "
            f"({valores.get('Mecanismo de lesión', 'no especificado')}), "
            f"así como el nivel de dolor EVA "
            f"({valores.get('Nivel de dolor (EVA)', 'N/D')}), "
            f"el sistema ha determinado que la hipótesis más probable es "
            f"«{diagnostico}» con un {confianza:.1f} % de confianza."
        )
        if radiografia:
            lineas.append(
                f"\nLa radiografía adjunta ({os.path.basename(radiografia)}) ha sido "
                "considerada en el análisis como prueba complementaria de soporte."
            )

        return "\n".join(lineas)

    def _mock_fuentes_web(self) -> list[str]:
        """Devuelve una lista de URLs simuladas de fuentes médicas."""
        return [
            "https://www.ncbi.nlm.nih.gov/books/NBK559213/ – Ankle Sprains (StatPearls)",
            "https://www.mayoclinic.org/diseases-conditions/fractures/symptoms-causes/syc-20356658",
            "https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD012774.pub2/full",
            "https://pubmed.ncbi.nlm.nih.gov/31246847/ – Muscle Injuries in Sports",
            "https://www.uptodate.com/contents/overview-of-musculoskeletal-injuries",
            "https://www.who.int/news-room/fact-sheets/detail/musculoskeletal-conditions",
        ]
