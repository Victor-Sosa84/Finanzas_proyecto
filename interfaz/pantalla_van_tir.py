"""
pantalla_van_tir.py
===================
Pantalla de análisis de VAN y TIR.

Muestra:
  - Formulario: inversión, tasa, flujos por período
  - Métricas: VAN, TIR, Payback, Índice de rentabilidad
  - Tabla de flujos acumulados (payback)
  - Curva VAN vs tasa (gráfico)
  - Gráfico de flujos de caja
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

from logica.van_tir import (
    van, tir, periodo_recupero,
    indice_rentabilidad, van_perfil,
    resumen_proyecto, tir_simple
)
from logica.capital import van_costos, comparar_van_costos
from logica.sensibilidad import variacion_tasa
from graficos.graficos import (
    grafico_van_vs_tasa,
    grafico_flujos
)


class PantallaVanTir(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.fig_canvas_van   = None
        self.fig_canvas_flujos = None

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
            text="VAN y TIR — Evaluación de proyectos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            topbar,
            text="Valor Actual Neto, Tasa Interna de Retorno y período de recupero",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        ctk.CTkButton(
            topbar,
            text="Calcular",
            width=110,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._calcular
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
        self._construir_metricas(scroll)
        self._construir_tabla_payback(scroll)
        self._construir_grafico_van(scroll)
        self._construir_grafico_flujos(scroll)
        self._construir_tir_simple(scroll)
        self._construir_van_costos(scroll)

    # ─────────────────────────────────────
    #  FORMULARIO
    # ─────────────────────────────────────

    def _construir_formulario(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="Datos del proyecto",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 8), sticky="w")

        campos = [
            ("Inversión inicial / CAPEX ($)", "50000",  "entrada_inversion"),
            ("Tasa de descuento (% anual)",   "12",     "entrada_tasa"),
            ("Flujos netos por período (separados por coma)",
             "12000, 15000, 18000, 20000, 22000", "entrada_flujos"),
        ]

        for i, (label, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="gray"
                         ).grid(row=1, column=i, padx=16,
                                pady=(0, 2), sticky="w")
            entrada = ctk.CTkEntry(frame, placeholder_text=f"Ej: {default}")
            entrada.grid(row=2, column=i, padx=16,
                         pady=(0, 14), sticky="ew")
            entrada.insert(0, default)
            setattr(self, attr, entrada)

        # Nota CAPEX/OPEX
        ctk.CTkLabel(
            frame,
            text="Los flujos netos ya deben descontar el OPEX. "
                 "Si no lo has hecho, ve a la pantalla Capital para calcularlo.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=3, column=0, columnspan=3,
               padx=16, pady=(0, 12), sticky="w")

    # ─────────────────────────────────────
    #  MÉTRICAS
    # ─────────────────────────────────────

    def _construir_metricas(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        definiciones = [
            ("VAN ($)",              "van"),
            ("TIR (%)",              "tir"),
            ("Payback (períodos)",   "payback"),
            ("Índice rentabilidad",  "ir"),
        ]
        self.labels_metricas = {}

        for i, (etiqueta, key) in enumerate(definiciones):
            card = ctk.CTkFrame(frame)
            card.grid(row=0, column=i, padx=5, sticky="ew")

            ctk.CTkLabel(
                card, text=etiqueta,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=14, pady=(10, 2))

            lbl_val = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=22, weight="bold")
            )
            lbl_val.pack(anchor="w", padx=14, pady=(0, 4))

            lbl_badge = ctk.CTkLabel(
                card, text="",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            lbl_badge.pack(anchor="w", padx=14, pady=(0, 10))

            self.labels_metricas[key] = (lbl_val, lbl_badge)

    # ─────────────────────────────────────
    #  TABLA PAYBACK
    # ─────────────────────────────────────

    def _construir_tabla_payback(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Flujos acumulados — Período de recupero",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        # Encabezados
        encabezados = ctk.CTkFrame(frame, fg_color=("gray88", "gray22"))
        encabezados.grid(row=1, column=0, padx=16, pady=(0, 2), sticky="ew")
        encabezados.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for i, texto in enumerate(["Período", "Flujo neto ($)",
                                    "Flujo acumulado ($)", "Estado"]):
            ctk.CTkLabel(
                encabezados, text=texto,
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=i, padx=12, pady=6, sticky="w")

        self.frame_payback = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_payback.grid(row=2, column=0, padx=16,
                                 pady=(0, 14), sticky="ew")
        self.frame_payback.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            self.frame_payback,
            text="Los datos aparecerán aquí después de calcular",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, columnspan=4, pady=10)

    # ─────────────────────────────────────
    #  GRÁFICO VAN VS TASA
    # ─────────────────────────────────────

    def _construir_grafico_van(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Curva VAN vs Tasa de descuento",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.frame_graf_van = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_van.grid(row=1, column=0,
                                  padx=16, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            self.frame_graf_van,
            text="El gráfico aparecerá aquí después de calcular",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=40)

    # ─────────────────────────────────────
    #  GRÁFICO FLUJOS
    # ─────────────────────────────────────

    def _construir_grafico_flujos(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=4, column=0, padx=16, pady=(8, 20), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Flujos de caja del proyecto",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.frame_graf_flujos = ctk.CTkFrame(
            frame, fg_color=("gray92", "gray18"))
        self.frame_graf_flujos.grid(row=1, column=0,
                                     padx=16, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            self.frame_graf_flujos,
            text="El gráfico aparecerá aquí después de calcular",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=40)

    # ─────────────────────────────────────
    #  LEER Y VALIDAR DATOS
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
            if inversion <= 0:
                raise ValueError("La inversión debe ser mayor a cero.")
            if tasa <= 0:
                raise ValueError("La tasa debe ser mayor a cero.")
            return inversion, tasa, flujos
        except ValueError as e:
            messagebox.showerror("Error en los datos",
                                  f"Verifica los valores.\n\nDetalle: {e}")
            return None

    # ─────────────────────────────────────
    #  CALCULAR
    # ─────────────────────────────────────

    def _calcular(self):
        datos = self._leer_datos()
        if datos is None:
            return

        inversion, tasa, flujos = datos
        resumen = resumen_proyecto(inversion, flujos, tasa)

        self._actualizar_metricas(resumen, tasa)
        self._actualizar_tabla_payback(flujos, resumen)
        self._actualizar_grafico_van(inversion, flujos, tasa, resumen["tir"])
        self._actualizar_grafico_flujos(inversion, flujos,
                                         resumen["flujos_acum"])

    # ─────────────────────────────────────
    #  ACTUALIZAR MÉTRICAS
    # ─────────────────────────────────────

    def _actualizar_metricas(self, resumen, tasa):
        # VAN
        lbl_v, lbl_b = self.labels_metricas["van"]
        color_van = "#27a060" if resumen["van_viable"] else "#e74c3c"
        lbl_v.configure(text=f"${resumen['van']:,.0f}",
                        text_color=color_van)
        lbl_b.configure(
            text="Viable" if resumen["van_viable"] else "No viable",
            text_color=color_van)

        # TIR
        lbl_v, lbl_b = self.labels_metricas["tir"]
        color_tir = "#27a060" if resumen["tir_supera_tasa"] else "#e74c3c"
        lbl_v.configure(text=f"{resumen['tir']*100:.2f}%",
                        text_color=color_tir)
        lbl_b.configure(
            text=f"{'Supera' if resumen['tir_supera_tasa'] else 'No supera'} "
                 f"tasa {tasa*100:.1f}%",
            text_color=color_tir)

        # Payback
        lbl_v, lbl_b = self.labels_metricas["payback"]
        if resumen["payback_recuperado"]:
            lbl_v.configure(text=str(resumen["payback_periodos"]),
                            text_color=("gray10", "gray90"))
            lbl_b.configure(text="Inversión recuperada",
                            text_color="#27a060")
        else:
            lbl_v.configure(text="No recupera",
                            text_color="#e74c3c")
            lbl_b.configure(text="En los períodos dados",
                            text_color="#e74c3c")

        # Índice rentabilidad
        lbl_v, lbl_b = self.labels_metricas["ir"]
        ir = resumen["indice_rent"]
        color_ir = "#27a060" if ir >= 1 else "#e74c3c"
        lbl_v.configure(text=f"{ir:.4f}", text_color=color_ir)
        lbl_b.configure(
            text="Por cada $1 invertido" if ir >= 1 else "Menor que 1",
            text_color=color_ir)

    # ─────────────────────────────────────
    #  ACTUALIZAR TABLA PAYBACK
    # ─────────────────────────────────────

    def _actualizar_tabla_payback(self, flujos, resumen):
        for widget in self.frame_payback.winfo_children():
            widget.destroy()

        flujos_acum = resumen["flujos_acum"]
        payback_p   = resumen["payback_periodos"]

        # Fila 0 = inversión inicial
        self._fila_payback(0, 0, 0, -resumen["inversion"],
                           flujos_acum[0], es_recupero=False)

        for i, flujo in enumerate(flujos):
            acum       = flujos_acum[i + 1]
            acum_prev  = flujos_acum[i]
            es_recupero = (acum >= 0 and acum_prev < 0)
            self._fila_payback(i + 1, i + 1, flujo,
                               acum, acum, es_recupero)

    def _fila_payback(self, row_idx, periodo, flujo, acum,
                      _acum, es_recupero):
        bg = ("gray93", "gray18") if row_idx % 2 == 0 \
             else ("gray89", "gray21")

        if es_recupero:
            bg = ("#e8f8ef", "#0d3320")

        row = ctk.CTkFrame(self.frame_payback, fg_color=bg)
        row.grid(row=row_idx, column=0, columnspan=4,
                 sticky="ew", pady=1)
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        color_acum = "#27a060" if acum >= 0 else "#e74c3c"
        estado     = "Recuperado" if es_recupero else (
            "Positivo" if acum >= 0 else "Pendiente")

        valores = [
            (str(periodo),             ("gray10", "gray90")),
            (f"${flujo:,.2f}" if periodo > 0 else "Inversion inicial",
             ("gray10", "gray90")),
            (f"${acum:,.2f}",           color_acum),
            (estado,                    "#27a060" if acum >= 0 else "gray"),
        ]

        for j, (texto, color) in enumerate(valores):
            ctk.CTkLabel(
                row, text=texto,
                font=ctk.CTkFont(
                    size=12,
                    weight="bold" if es_recupero else "normal"),
                text_color=color
            ).grid(row=0, column=j, padx=12, pady=5, sticky="w")

    # ─────────────────────────────────────
    #  ACTUALIZAR GRÁFICOS
    # ─────────────────────────────────────

    def _actualizar_grafico_van(self, inversion, flujos, tasa, tir_valor):
        if self.fig_canvas_van is not None:
            self.fig_canvas_van.get_tk_widget().destroy()
            plt.close("all")

        for w in self.frame_graf_van.winfo_children():
            w.destroy()

        vt  = variacion_tasa(inversion, flujos, tasa, rango=0.12, pasos=50)
        fig = grafico_van_vs_tasa(vt, tir_valor, tasa)
        fig.set_size_inches(9, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_van)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_van = canvas

    def _actualizar_grafico_flujos(self, inversion, flujos, flujos_acum):
        if self.fig_canvas_flujos is not None:
            self.fig_canvas_flujos.get_tk_widget().destroy()
            plt.close("all")

        for w in self.frame_graf_flujos.winfo_children():
            w.destroy()

        fig = grafico_flujos(inversion, flujos, flujos_acum)
        fig.set_size_inches(9, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_flujos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_flujos = canvas

    # ─────────────────────────────────────
    #  TIR SIMPLE (sin tasa de descuento)
    # ─────────────────────────────────────

    def _construir_tir_simple(self, parent):
        sep = ctk.CTkFrame(parent, height=1,
                            fg_color=("gray80", "gray30"))
        sep.grid(row=5, column=0, padx=16, pady=(8, 16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=6, column=0, padx=16, pady=(0, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            frame,
            text="TIR independiente",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Calcula la TIR sin necesitar una tasa de descuento. "
                 "Luego tú compares con tu costo de capital.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, columnspan=2,
               padx=16, pady=(0, 10), sticky="w")

        ctk.CTkLabel(frame, text="Inversión inicial ($)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=0, padx=16, pady=(0,2), sticky="w")
        self.entrada_tir_inversion = ctk.CTkEntry(
            frame, placeholder_text="Ej: 50000")
        self.entrada_tir_inversion.grid(row=3, column=0, padx=16,
                                         pady=(0,12), sticky="ew")
        self.entrada_tir_inversion.insert(0, "50000")

        ctk.CTkLabel(frame, text="Flujos de caja (separados por coma)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=1, padx=16, pady=(0,2), sticky="w")
        self.entrada_tir_flujos = ctk.CTkEntry(
            frame, placeholder_text="Ej: 12000, 15000, 18000")
        self.entrada_tir_flujos.grid(row=3, column=1, padx=16,
                                      pady=(0,12), sticky="ew")
        self.entrada_tir_flujos.insert(
            0, "12000, 15000, 18000, 20000, 22000")

        ctk.CTkButton(
            frame, text="Calcular TIR", width=140,
            command=self._calcular_tir_simple
        ).grid(row=4, column=0, padx=16, pady=(0,12), sticky="w")

        self.lbl_tir_simple = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_tir_simple.grid(row=5, column=0, columnspan=2,
                                  padx=16, pady=(0,14), sticky="w")

    def _calcular_tir_simple(self):
        try:
            inversion = float(
                self.entrada_tir_inversion.get().replace(",", ""))
            flujos = [
                float(f.strip())
                for f in self.entrada_tir_flujos.get().split(",")
                if f.strip()
            ]
            res = tir_simple(inversion, flujos)
            color = "#27a060" if res["tir"] > 0 else "#e74c3c"
            self.lbl_tir_simple.configure(
                text=f"TIR = {res['tir_pct']:.4f}%  |  "
                     f"{res['interpretacion']}",
                text_color=color
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  VAN DE COSTOS
    # ─────────────────────────────────────

    def _construir_van_costos(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=7, column=0, padx=16, pady=(0, 20), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="VAN de costos — comparar opciones por eficiencia",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Útil cuando no hay ingresos sino solo gastos. "
                 "La opción con VAN de costos menos negativo es la más eficiente.",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, columnspan=3,
               padx=16, pady=(0, 10), sticky="w")

        # Tasa de descuento
        ctk.CTkLabel(frame, text="Tasa de descuento (% anual)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=0, padx=16, pady=(0,2), sticky="w")
        self.entrada_vc_tasa = ctk.CTkEntry(
            frame, placeholder_text="Ej: 12")
        self.entrada_vc_tasa.grid(row=3, column=0, padx=16,
                                   pady=(0,12), sticky="ew")
        self.entrada_vc_tasa.insert(0, "12")

        # Opción A
        ctk.CTkLabel(frame, text="Opción A — Inversión ($)  |  Costos/período",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=1, padx=16, pady=(0,2), sticky="w")
        self.frame_vc_a = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_vc_a.grid(row=3, column=1, padx=16,
                              pady=(0,12), sticky="ew")
        self.frame_vc_a.grid_columnconfigure((0,1), weight=1)

        self.entrada_vc_a_inv = ctk.CTkEntry(
            self.frame_vc_a, placeholder_text="Inversión")
        self.entrada_vc_a_inv.grid(row=0, column=0, padx=(0,4), sticky="ew")
        self.entrada_vc_a_inv.insert(0, "50000")

        self.entrada_vc_a_costos = ctk.CTkEntry(
            self.frame_vc_a, placeholder_text="Costos por período")
        self.entrada_vc_a_costos.grid(row=0, column=1, padx=(4,0),
                                       sticky="ew")
        self.entrada_vc_a_costos.insert(0, "10000, 10000, 10000, 10000, 10000")

        # Opción B
        ctk.CTkLabel(frame, text="Opción B — Inversión ($)  |  Costos/período",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=2, padx=16, pady=(0,2), sticky="w")
        self.frame_vc_b = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_vc_b.grid(row=3, column=2, padx=16,
                              pady=(0,12), sticky="ew")
        self.frame_vc_b.grid_columnconfigure((0,1), weight=1)

        self.entrada_vc_b_inv = ctk.CTkEntry(
            self.frame_vc_b, placeholder_text="Inversión")
        self.entrada_vc_b_inv.grid(row=0, column=0, padx=(0,4), sticky="ew")
        self.entrada_vc_b_inv.insert(0, "30000")

        self.entrada_vc_b_costos = ctk.CTkEntry(
            self.frame_vc_b, placeholder_text="Costos por período")
        self.entrada_vc_b_costos.grid(row=0, column=1, padx=(4,0),
                                       sticky="ew")
        self.entrada_vc_b_costos.insert(
            0, "15000, 15000, 15000, 15000, 15000")

        ctk.CTkButton(
            frame, text="Comparar opciones", width=180,
            command=self._calcular_van_costos
        ).grid(row=4, column=0, padx=16, pady=(0,12), sticky="w")

        # Resultados
        self.frame_vc_resultados = ctk.CTkFrame(
            frame, fg_color="transparent")
        self.frame_vc_resultados.grid(row=5, column=0, columnspan=3,
                                       padx=16, pady=(0,14), sticky="ew")
        self.frame_vc_resultados.grid_columnconfigure((0,1), weight=1)

    def _calcular_van_costos(self):
        try:
            tasa = float(
                self.entrada_vc_tasa.get().replace("%","")) / 100

            inv_a = float(
                self.entrada_vc_a_inv.get().replace(",",""))
            costos_a = [float(f.strip())
                        for f in self.entrada_vc_a_costos.get().split(",")
                        if f.strip()]

            inv_b = float(
                self.entrada_vc_b_inv.get().replace(",",""))
            costos_b = [float(f.strip())
                        for f in self.entrada_vc_b_costos.get().split(",")
                        if f.strip()]

            opciones = [
                {"nombre": "Opción A", "inversion": inv_a, "costos": costos_a},
                {"nombre": "Opción B", "inversion": inv_b, "costos": costos_b},
            ]
            resultados = comparar_van_costos(opciones, tasa)

            # Limpiar resultados anteriores
            for w in self.frame_vc_resultados.winfo_children():
                w.destroy()

            for i, res in enumerate(resultados):
                color  = "#27a060" if res["es_mejor"] else ("gray10","gray90")
                titulo = " MEJOR OPCIÓN" if res["es_mejor"] else ""
                card   = ctk.CTkFrame(self.frame_vc_resultados)
                card.grid(row=0, column=i, padx=5, sticky="ew")

                ctk.CTkLabel(
                    card,
                    text=f"{res['nombre']}{titulo}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=color
                ).pack(anchor="w", padx=14, pady=(10,4))

                for etiqueta, valor in [
                    ("VAN de costos", f"${res['van_costos']:,.0f}"),
                    ("Costo total",   f"${abs(res['costo_total']):,.0f}"),
                    ("Valor presente costos",
                     f"${abs(res['costo_presente']):,.0f}"),
                ]:
                    ctk.CTkLabel(
                        card,
                        text=f"{etiqueta}: {valor}",
                        font=ctk.CTkFont(size=12)
                    ).pack(anchor="w", padx=14, pady=2)

                ctk.CTkLabel(card, text="").pack(pady=4)

        except ValueError as e:
            messagebox.showerror("Error", str(e))