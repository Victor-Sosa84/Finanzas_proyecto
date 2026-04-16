"""
pantalla_sensibilidad.py
========================
Pantalla de análisis de sensibilidad — la más importante del proyecto.

Muestra:
  - Formulario de datos base (inversión, tasa, flujos)
  - Escenarios optimista / base / pesimista
  - Variación de tasa (curva VAN vs tasa)
  - Variación de flujos (tabla)
  - Heatmap 2D (tasa x flujos)
  - Punto de equilibrio de flujos
  - Tornado chart (variables más críticas)
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

from logica.sensibilidad import (
    escenarios,
    variacion_tasa,
    variacion_flujos,
    tabla_2d,
    punto_equilibrio_flujos,
    tornado_vars,
    resumen_sensibilidad
)
from graficos.graficos import (
    grafico_van_vs_tasa,
    grafico_heatmap,
    grafico_tornado,
    grafico_escenarios
)


class PantallaSensibilidad(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.fig_canvas_van      = None
        self.fig_canvas_heatmap  = None
        self.fig_canvas_tornado  = None
        self.fig_canvas_escen    = None

        self._construir_topbar()
        self._construir_contenido()

    # ─────────────────────────────────────
    #  TOPBAR
    # ─────────────────────────────────────

    def _construir_topbar(self):
        topbar = ctk.CTkFrame(self, corner_radius=0, height=60,
                               fg_color=("gray95", "gray15"))
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topbar,
            text="Análisis de sensibilidad",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            topbar,
            text="Escenarios, variaciones, heatmap y tornado chart",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkButton(
            topbar,
            text="Calcular todo",
            width=130,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._calcular_todo
        ).grid(row=0, column=1, rowspan=2, padx=20, pady=10)

    # ─────────────────────────────────────
    #  CONTENIDO
    # ─────────────────────────────────────

    def _construir_contenido(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self.scroll = scroll

        self._construir_formulario(scroll)
        self._construir_escenarios(scroll)
        self._construir_variacion_tasa(scroll)
        self._construir_variacion_flujos(scroll)
        self._construir_equilibrio(scroll)
        self._construir_heatmap(scroll)
        self._construir_tornado(scroll)

    # ─────────────────────────────────────
    #  FORMULARIO
    # ─────────────────────────────────────

    def _construir_formulario(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="Datos base del proyecto",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 8), sticky="w")

        campos = [
            ("Inversión inicial ($)",
             "50000", "entrada_inversion"),
            ("Tasa de descuento (% anual)",
             "12",    "entrada_tasa"),
            ("Flujos de caja base (separados por coma)",
             "12000, 15000, 18000, 20000, 22000", "entrada_flujos"),
        ]

        for i, (label, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="gray"
                         ).grid(row=1, column=i, padx=16,
                                pady=(0, 2), sticky="w")
            entrada = ctk.CTkEntry(
                frame, placeholder_text=f"Ej: {default}")
            entrada.grid(row=2, column=i, padx=16,
                         pady=(0, 14), sticky="ew")
            entrada.insert(0, default)
            setattr(self, attr, entrada)

    # ─────────────────────────────────────
    #  ESCENARIOS
    # ─────────────────────────────────────

    def _construir_escenarios(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="Escenarios optimista / base / pesimista",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Los flujos varían ±20% respecto al escenario base.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=3,
               padx=16, pady=(0, 10), sticky="w")

        nombres = ["Optimista (+20%)", "Base", "Pesimista (-20%)"]
        colores = ["#27a060",          "#3498db", "#e74c3c"]
        self.cards_escenarios = {}

        for i, (nombre, color) in enumerate(zip(nombres, colores)):
            card = ctk.CTkFrame(frame)
            card.grid(row=2, column=i, padx=10,
                      pady=(0, 14), sticky="ew")

            ctk.CTkLabel(
                card, text=nombre,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color
            ).pack(anchor="w", padx=14, pady=(10, 4))

            lbl_van = ctk.CTkLabel(
                card, text="VAN: —",
                font=ctk.CTkFont(size=13)
            )
            lbl_van.pack(anchor="w", padx=14, pady=2)

            lbl_tir = ctk.CTkLabel(
                card, text="TIR: —",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            lbl_tir.pack(anchor="w", padx=14, pady=(2, 4))

            lbl_estado = ctk.CTkLabel(
                card, text="",
                font=ctk.CTkFont(size=11)
            )
            lbl_estado.pack(anchor="w", padx=14, pady=(0, 10))

            self.cards_escenarios[nombre] = (lbl_van, lbl_tir, lbl_estado)

        # Gráfico escenarios
        self.frame_graf_escen = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_escen.grid(row=3, column=0, columnspan=3,
                                    padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            self.frame_graf_escen,
            text="El gráfico aparecerá aquí después de calcular",
            text_color="gray", font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=30)

    # ─────────────────────────────────────
    #  VARIACIÓN DE TASA
    # ─────────────────────────────────────

    def _construir_variacion_tasa(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Curva VAN vs variacion de tasa",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.frame_graf_van = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_van.grid(row=1, column=0,
                                  padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            self.frame_graf_van,
            text="El gráfico aparecerá aquí después de calcular",
            text_color="gray", font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=30)

    # ─────────────────────────────────────
    #  VARIACIÓN DE FLUJOS
    # ─────────────────────────────────────

    def _construir_variacion_flujos(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Variacion de flujos de caja",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        ctk.CTkLabel(
            frame,
            text="VAN resultante cuando todos los flujos varían en un mismo porcentaje.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        # Encabezados
        enc = ctk.CTkFrame(frame, fg_color=("gray88", "gray22"))
        enc.grid(row=2, column=0, padx=16, pady=(0, 2), sticky="ew")
        enc.grid_columnconfigure((0, 1, 2), weight=1)
        for i, texto in enumerate(["Variacion (%)", "VAN ($)", "Viable"]):
            ctk.CTkLabel(enc, text=texto,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=12, pady=6, sticky="w")

        self.frame_var_flujos = ctk.CTkFrame(
            frame, fg_color="transparent")
        self.frame_var_flujos.grid(row=3, column=0, padx=16,
                                    pady=(0, 14), sticky="ew")
        self.frame_var_flujos.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            self.frame_var_flujos,
            text="Los datos aparecerán aquí después de calcular",
            text_color="gray", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, columnspan=3, pady=10)

    # ─────────────────────────────────────
    #  PUNTO DE EQUILIBRIO
    # ─────────────────────────────────────

    def _construir_equilibrio(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=4, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            frame,
            text="Punto de equilibrio financiero",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Cuanto pueden caer los flujos antes de que VAN = 0.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, columnspan=4,
               padx=16, pady=(0, 10), sticky="w")

        indicadores = [
            ("Factor de equilibrio",   "eq_factor"),
            ("Caida maxima (%)",        "eq_variacion"),
            ("VAN en equilibrio",       "eq_van"),
            ("Estado actual",           "eq_estado"),
        ]
        self.labels_equilibrio = {}

        for i, (etiqueta, key) in enumerate(indicadores):
            card = ctk.CTkFrame(frame)
            card.grid(row=2, column=i, padx=5,
                      pady=(0, 14), sticky="ew")

            ctk.CTkLabel(
                card, text=etiqueta,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=12, pady=(8, 2))

            lbl = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            lbl.pack(anchor="w", padx=12, pady=(0, 8))
            self.labels_equilibrio[key] = lbl

    # ─────────────────────────────────────
    #  HEATMAP
    # ─────────────────────────────────────

    def _construir_heatmap(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=5, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Heatmap de sensibilidad — tasa x flujos",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Verde = VAN positivo  |  Rojo = VAN negativo  "
                 "|  Borde naranja = escenario base",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        self.frame_graf_heatmap = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_heatmap.grid(row=2, column=0,
                                      padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            self.frame_graf_heatmap,
            text="El heatmap aparecerá aquí después de calcular",
            text_color="gray", font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=30)

    # ─────────────────────────────────────
    #  TORNADO CHART
    # ─────────────────────────────────────

    def _construir_tornado(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=6, column=0, padx=16, pady=(8, 20), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Tornado chart — variables mas criticas",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Muestra que variable impacta mas el VAN al variarla "
                 "un 10%. Las barras mas largas son las mas criticas.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        self.frame_graf_tornado = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_tornado.grid(row=2, column=0,
                                      padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            self.frame_graf_tornado,
            text="El tornado chart aparecerá aquí después de calcular",
            text_color="gray", font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=30)

    # ─────────────────────────────────────
    #  LEER DATOS
    # ─────────────────────────────────────

    def _leer_datos(self):
        try:
            inversion = float(
                self.entrada_inversion.get().replace(",", ""))
            tasa = float(
                self.entrada_tasa.get().replace("%", "")) / 100
            flujos = [
                float(f.strip())
                for f in self.entrada_flujos.get().split(",")
                if f.strip()
            ]
            if not flujos:
                raise ValueError("Ingresa al menos un flujo de caja.")
            return inversion, tasa, flujos
        except ValueError as e:
            messagebox.showerror("Error en los datos",
                                  f"Verifica los valores.\n\nDetalle: {e}")
            return None

    # ─────────────────────────────────────
    #  CALCULAR TODO
    # ─────────────────────────────────────

    def _calcular_todo(self):
        datos = self._leer_datos()
        if datos is None:
            return

        inversion, tasa, flujos = datos

        self._actualizar_escenarios(inversion, flujos, tasa)
        self._actualizar_variacion_tasa(inversion, flujos, tasa)
        self._actualizar_variacion_flujos(inversion, flujos, tasa)
        self._actualizar_equilibrio(inversion, flujos, tasa)
        self._actualizar_heatmap(inversion, flujos, tasa)
        self._actualizar_tornado(inversion, flujos, tasa)

    # ─────────────────────────────────────
    #  ACTUALIZAR ESCENARIOS
    # ─────────────────────────────────────

    def _actualizar_escenarios(self, inversion, flujos, tasa):
        esc = escenarios(inversion, flujos, tasa)
        nombres = ["Optimista (+20%)", "Base", "Pesimista (-20%)"]

        for nombre, e in zip(nombres, esc):
            lbl_van, lbl_tir, lbl_estado = self.cards_escenarios[nombre]
            color = "#27a060" if e["van_viable"] else "#e74c3c"
            lbl_van.configure(
                text=f"VAN: ${e['van']:,.0f}",
                text_color=color)
            lbl_tir.configure(
                text=f"TIR: {e['tir']*100:.2f}%")
            lbl_estado.configure(
                text="Viable" if e["van_viable"] else "No viable",
                text_color=color)

        # Gráfico escenarios
        if self.fig_canvas_escen is not None:
            self.fig_canvas_escen.get_tk_widget().destroy()
        for w in self.frame_graf_escen.winfo_children():
            w.destroy()

        fig = grafico_escenarios(esc)
        fig.set_size_inches(9, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_escen)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_escen = canvas

    # ─────────────────────────────────────
    #  ACTUALIZAR CURVA VAN VS TASA
    # ─────────────────────────────────────

    def _actualizar_variacion_tasa(self, inversion, flujos, tasa):
        from logica.van_tir import tir as calcular_tir

        if self.fig_canvas_van is not None:
            self.fig_canvas_van.get_tk_widget().destroy()
        for w in self.frame_graf_van.winfo_children():
            w.destroy()

        vt      = variacion_tasa(inversion, flujos, tasa,
                                  rango=0.12, pasos=50)
        tir_res = calcular_tir(inversion, flujos)
        fig     = grafico_van_vs_tasa(vt, tir_res["tir"], tasa)
        fig.set_size_inches(9, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_van)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_van = canvas

    # ─────────────────────────────────────
    #  ACTUALIZAR VARIACIÓN FLUJOS
    # ─────────────────────────────────────

    def _actualizar_variacion_flujos(self, inversion, flujos, tasa):
        vf = variacion_flujos(inversion, flujos, tasa,
                               variacion_max=0.30, pasos=13)

        for w in self.frame_var_flujos.winfo_children():
            w.destroy()

        for i, fila in enumerate(vf["datos"]):
            bg = ("gray95", "gray17") if i % 2 == 0 \
                 else ("gray90", "gray20")

            # Resaltar fila base (variacion = 0%)
            es_base = abs(fila["variacion_pct"]) < 0.1
            if es_base:
                bg = ("#e6f2fb", "#0a2a42")

            row = ctk.CTkFrame(self.frame_var_flujos, fg_color=bg)
            row.grid(row=i, column=0, columnspan=3,
                     sticky="ew", pady=1)
            row.grid_columnconfigure((0, 1, 2), weight=1)

            color_van = "#27a060" if fila["viable"] else "#e74c3c"
            peso = "bold" if es_base else "normal"

            ctk.CTkLabel(
                row,
                text=f"{fila['variacion_pct']:+.1f}%" +
                     (" (base)" if es_base else ""),
                font=ctk.CTkFont(size=12, weight=peso)
            ).grid(row=0, column=0, padx=12, pady=5, sticky="w")

            ctk.CTkLabel(
                row,
                text=f"${fila['van']:,.0f}",
                font=ctk.CTkFont(size=12, weight=peso),
                text_color=color_van
            ).grid(row=0, column=1, padx=12, pady=5, sticky="w")

            ctk.CTkLabel(
                row,
                text="Si" if fila["viable"] else "No",
                font=ctk.CTkFont(size=12, weight=peso),
                text_color=color_van
            ).grid(row=0, column=2, padx=12, pady=5, sticky="w")

    # ─────────────────────────────────────
    #  ACTUALIZAR PUNTO DE EQUILIBRIO
    # ─────────────────────────────────────

    def _actualizar_equilibrio(self, inversion, flujos, tasa):
        eq = punto_equilibrio_flujos(inversion, flujos, tasa)

        if eq["viable_actualmente"]:
            self.labels_equilibrio["eq_factor"].configure(
                text=str(eq["factor_equilibrio"]),
                text_color=("gray10", "gray90"))
            self.labels_equilibrio["eq_variacion"].configure(
                text=f"{eq['variacion_pct']}%",
                text_color="#e74c3c")
            self.labels_equilibrio["eq_van"].configure(
                text=f"${eq['van_verificacion']:.2f}",
                text_color="gray")
            self.labels_equilibrio["eq_estado"].configure(
                text="Proyecto viable",
                text_color="#27a060")
        else:
            for key in self.labels_equilibrio:
                self.labels_equilibrio[key].configure(
                    text="N/A", text_color="#e74c3c")
            self.labels_equilibrio["eq_estado"].configure(
                text="VAN ya es negativo",
                text_color="#e74c3c")

    # ─────────────────────────────────────
    #  ACTUALIZAR HEATMAP
    # ─────────────────────────────────────

    def _actualizar_heatmap(self, inversion, flujos, tasa):
        if self.fig_canvas_heatmap is not None:
            self.fig_canvas_heatmap.get_tk_widget().destroy()
        for w in self.frame_graf_heatmap.winfo_children():
            w.destroy()

        t2d = tabla_2d(inversion, flujos, tasa)
        fig = grafico_heatmap(t2d)
        fig.set_size_inches(9, 4.2)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_heatmap)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_heatmap = canvas

    # ─────────────────────────────────────
    #  ACTUALIZAR TORNADO
    # ─────────────────────────────────────

    def _actualizar_tornado(self, inversion, flujos, tasa):
        from logica.van_tir import van as calcular_van

        if self.fig_canvas_tornado is not None:
            self.fig_canvas_tornado.get_tk_widget().destroy()
        for w in self.frame_graf_tornado.winfo_children():
            w.destroy()

        tornado  = tornado_vars(inversion, flujos, tasa)
        van_base = calcular_van(inversion, flujos, tasa)

        fig = grafico_tornado(tornado, van_base, top_n=6)
        fig.set_size_inches(9, 4.2)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_tornado)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_tornado = canvas