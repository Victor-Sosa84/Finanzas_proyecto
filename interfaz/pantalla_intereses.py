"""
pantalla_intereses.py
=====================
Pantalla de análisis de interés simple y compuesto.

Muestra:
  - Formulario: capital, tasa, períodos
  - Comparación simple vs compuesto (tabla + métricas)
  - Gráfico de crecimiento simple vs compuesto
  - Tabla de amortización con gráfico de composición de cuota
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

from logica.intereses import (
    interes_simple, monto_simple,
    interes_compuesto, capital_futuro,
    comparar_simple_vs_compuesto,
    tabla_amortizacion,
    periodos_por_cuota,
    valor_terminal
)
from logica.capital_startup import (
    valor_terminal_multiplo,
    sensibilidad_multiplos,
    multiplo_minimo_viable
)
from graficos.graficos import (
    grafico_simple_vs_compuesto,
    grafico_amortizacion
)


class PantallaIntereses(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.fig_canvas_comparacion  = None
        self.fig_canvas_amortizacion = None

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
            text="Interés simple y compuesto",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            topbar,
            text="Compara el crecimiento del capital en ambos esquemas",
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
        self._construir_tabla_comparacion(scroll)
        self._construir_grafico_comparacion(scroll)
        self._construir_seccion_amortizacion(scroll)
        self._construir_valor_terminal(scroll)

    # ─────────────────────────────────────
    #  FORMULARIO
    # ─────────────────────────────────────

    def _construir_formulario(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="Datos de entrada",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 8), sticky="w")

        campos = [
            ("Capital inicial ($)",       "10000",  "entrada_capital"),
            ("Tasa por período (%)",       "10",     "entrada_tasa"),
            ("Número de períodos",         "5",      "entrada_periodos"),
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

    # ─────────────────────────────────────
    #  MÉTRICAS
    # ─────────────────────────────────────

    def _construir_metricas(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        etiquetas = [
            "Interés simple ($)",
            "Monto simple ($)",
            "Interés compuesto ($)",
            "Capital futuro ($)",
        ]
        self.labels_metricas = {}

        for i, etiqueta in enumerate(etiquetas):
            card = ctk.CTkFrame(frame)
            card.grid(row=0, column=i, padx=5, sticky="ew")

            ctk.CTkLabel(
                card, text=etiqueta,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=14, pady=(10, 2))

            lbl = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            lbl.pack(anchor="w", padx=14, pady=(0, 10))
            self.labels_metricas[etiqueta] = lbl

    # ─────────────────────────────────────
    #  TABLA COMPARACIÓN
    # ─────────────────────────────────────

    def _construir_tabla_comparacion(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Comparación período a período",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        # Encabezados
        encabezados = ctk.CTkFrame(frame, fg_color=("gray88", "gray22"))
        encabezados.grid(row=1, column=0, padx=16, pady=(0, 2), sticky="ew")
        encabezados.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for i, texto in enumerate(["Período", "Simple ($)",
                                    "Compuesto ($)", "Diferencia ($)"]):
            ctk.CTkLabel(
                encabezados, text=texto,
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=i, padx=12, pady=6, sticky="w")

        # Contenedor de filas (se rellena al calcular)
        self.frame_filas = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_filas.grid(row=2, column=0, padx=16,
                               pady=(0, 14), sticky="ew")
        self.frame_filas.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            self.frame_filas,
            text="Los datos aparecerán aquí después de calcular",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, columnspan=4, pady=10)

    # ─────────────────────────────────────
    #  GRÁFICO COMPARACIÓN
    # ─────────────────────────────────────

    def _construir_grafico_comparacion(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Crecimiento del capital",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.frame_graf_comp = ctk.CTkFrame(
            frame, height=260,
            fg_color=("gray92", "gray18")
        )
        self.frame_graf_comp.grid(row=1, column=0,
                                   padx=16, pady=(0, 16), sticky="ew")
        self.frame_graf_comp.grid_propagate(False)

        ctk.CTkLabel(
            self.frame_graf_comp,
            text="El gráfico aparecerá aquí después de calcular",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ─────────────────────────────────────
    #  SECCIÓN AMORTIZACIÓN
    # ─────────────────────────────────────

    def _construir_seccion_amortizacion(self, parent):
        sep = ctk.CTkFrame(parent, height=1,
                            fg_color=("gray80", "gray30"))
        sep.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=5, column=0, padx=16, pady=(0, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            frame,
            text="Tabla de amortización de préstamo",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="¿Sabes cuántas cuotas vas a pagar, "
                 "o cuánto puedes pagar por período?",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=3,
               padx=16, pady=(0, 10), sticky="w")

        # Selector de modo
        self.modo_amort = ctk.StringVar(value="cuotas")
        frame_modo = ctk.CTkFrame(frame, fg_color="transparent")
        frame_modo.grid(row=2, column=0, columnspan=3,
                        padx=16, pady=(0, 10), sticky="w")

        ctk.CTkRadioButton(
            frame_modo,
            text="Conozco el número de cuotas",
            variable=self.modo_amort,
            value="cuotas",
            command=self._toggle_modo_amort
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            frame_modo,
            text="Conozco la cuota máxima que puedo pagar",
            variable=self.modo_amort,
            value="cuota_max",
            command=self._toggle_modo_amort
        ).pack(side="left")

        # Campos comunes
        ctk.CTkLabel(frame, text="Monto del préstamo ($)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=3, column=0, padx=16,
                            pady=(0, 2), sticky="w")
        self.entrada_amort_capital = ctk.CTkEntry(
            frame, placeholder_text="Ej: 10000")
        self.entrada_amort_capital.grid(row=4, column=0, padx=16,
                                         pady=(0, 12), sticky="ew")
        self.entrada_amort_capital.insert(0, "10000")

        ctk.CTkLabel(frame, text="Tasa por período (%)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=3, column=1, padx=16,
                            pady=(0, 2), sticky="w")
        self.entrada_amort_tasa = ctk.CTkEntry(
            frame, placeholder_text="Ej: 1")
        self.entrada_amort_tasa.grid(row=4, column=1, padx=16,
                                      pady=(0, 12), sticky="ew")
        self.entrada_amort_tasa.insert(0, "1")

        # Campo dinámico
        self.lbl_campo_dinamico = ctk.CTkLabel(
            frame, text="Número de cuotas",
            font=ctk.CTkFont(size=12), text_color="gray")
        self.lbl_campo_dinamico.grid(row=3, column=2, padx=16,
                                      pady=(0, 2), sticky="w")

        self.entrada_amort_dinamica = ctk.CTkEntry(
            frame, placeholder_text="Ej: 12")
        self.entrada_amort_dinamica.grid(row=4, column=2, padx=16,
                                          pady=(0, 12), sticky="ew")
        self.entrada_amort_dinamica.insert(0, "12")

        ctk.CTkButton(
            frame,
            text="Calcular amortización",
            width=200,
            command=self._calcular_amortizacion
        ).grid(row=5, column=0, columnspan=3,
               padx=16, pady=(0, 14), sticky="w")

        self.lbl_cuota_fija = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.lbl_cuota_fija.grid(row=6, column=0, columnspan=3,
                                  padx=16, pady=(0, 8), sticky="w")

        # Gráfico amortización
        self.frame_graf_amort = ctk.CTkFrame(
            parent, fg_color=("gray92", "gray18"))
        self.frame_graf_amort.grid(row=6, column=0, padx=16,
                                    pady=(0, 20), sticky="ew")

        ctk.CTkLabel(
            self.frame_graf_amort,
            text="El gráfico de amortización aparecerá aquí",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(padx=20, pady=40)

    def _toggle_modo_amort(self):
        if self.modo_amort.get() == "cuotas":
            self.lbl_campo_dinamico.configure(text="Número de cuotas")
            self.entrada_amort_dinamica.delete(0, "end")
            self.entrada_amort_dinamica.insert(0, "12")
        else:
            self.lbl_campo_dinamico.configure(
                text="Cuota máxima que puedes pagar ($)")
            self.entrada_amort_dinamica.delete(0, "end")
            self.entrada_amort_dinamica.insert(0, "1000")

    # ─────────────────────────────────────
    #  CÁLCULO INTERESES
    # ─────────────────────────────────────

    def _leer_datos_intereses(self):
        try:
            capital  = float(self.entrada_capital.get().replace(",", ""))
            tasa     = float(self.entrada_tasa.get().replace("%", "")) / 100
            periodos = int(self.entrada_periodos.get())
            if periodos <= 0:
                raise ValueError("Los períodos deben ser mayores a 0.")
            return capital, tasa, periodos
        except ValueError as e:
            messagebox.showerror("Error en los datos",
                                  f"Verifica los valores.\n\nDetalle: {e}")
            return None

    def _calcular(self):
        datos = self._leer_datos_intereses()
        if datos is None:
            return

        capital, tasa, periodos = datos

        # Métricas
        self.labels_metricas["Interés simple ($)"].configure(
            text=f"${interes_simple(capital, tasa, periodos):,.2f}")
        self.labels_metricas["Monto simple ($)"].configure(
            text=f"${monto_simple(capital, tasa, periodos):,.2f}")
        self.labels_metricas["Interés compuesto ($)"].configure(
            text=f"${interes_compuesto(capital, tasa, periodos):,.2f}")
        self.labels_metricas["Capital futuro ($)"].configure(
            text=f"${capital_futuro(capital, tasa, periodos):,.2f}")

        # Tabla comparación
        datos_comp = comparar_simple_vs_compuesto(capital, tasa, periodos)
        self._actualizar_tabla(datos_comp)

        # Gráfico
        self._actualizar_grafico_comparacion(datos_comp, capital)

    def _actualizar_tabla(self, datos_comp):
        for widget in self.frame_filas.winfo_children():
            widget.destroy()

        for i, fila in enumerate(datos_comp):
            bg = ("gray95", "gray17") if i % 2 == 0 else ("gray90", "gray20")
            row_frame = ctk.CTkFrame(self.frame_filas, fg_color=bg)
            row_frame.grid(row=i, column=0, columnspan=4,
                           sticky="ew", pady=1)
            row_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            color_dif = "#27a060" if fila["diferencia"] >= 0 else "#e74c3c"

            valores = [
                (str(fila["periodo"]),              "gray10", "gray90"),
                (f"${fila['monto_simple']:,.2f}",   "gray10", "gray90"),
                (f"${fila['monto_compuesto']:,.2f}", "gray10", "gray90"),
                (f"${fila['diferencia']:,.2f}",      color_dif, color_dif),
            ]

            for j, (texto, color_l, color_d) in enumerate(valores):
                ctk.CTkLabel(
                    row_frame, text=texto,
                    font=ctk.CTkFont(size=12),
                    text_color=(color_l, color_d)
                ).grid(row=0, column=j, padx=12, pady=5, sticky="w")

    def _actualizar_grafico_comparacion(self, datos_comp, capital):
        if self.fig_canvas_comparacion is not None:
            self.fig_canvas_comparacion.get_tk_widget().destroy()
            plt.close("all")

        for widget in self.frame_graf_comp.winfo_children():
            widget.destroy()

        fig = grafico_simple_vs_compuesto(datos_comp, capital)
        fig.set_size_inches(8, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_comp)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_comparacion = canvas

    # ─────────────────────────────────────
    #  CÁLCULO AMORTIZACIÓN
    # ─────────────────────────────────────

    def _leer_datos_amortizacion(self):
        try:
            capital = float(
                self.entrada_amort_capital.get().replace(",", ""))
            tasa    = float(
                self.entrada_amort_tasa.get().replace("%", "")) / 100
            valor   = float(
                self.entrada_amort_dinamica.get().replace(",", ""))
            if capital <= 0 or tasa <= 0 or valor <= 0:
                raise ValueError("Todos los valores deben ser mayores a 0.")
            return capital, tasa, valor
        except ValueError as e:
            messagebox.showerror("Error en los datos",
                                  f"Verifica los valores.\n\nDetalle: {e}")
            return None

    def _calcular_amortizacion(self):
        datos = self._leer_datos_amortizacion()
        if datos is None:
            return

        capital, tasa, valor = datos
        modo = self.modo_amort.get()

        if modo == "cuota_max":
            # Modo: cuota conocida → calcular períodos
            res_periodos = periodos_por_cuota(capital, tasa, valor)

            if not res_periodos["viable"]:
                messagebox.showwarning(
                    "Cuota insuficiente",
                    res_periodos["mensaje"])
                return

            n = res_periodos["periodos"]
            self.lbl_cuota_fija.configure(
                text=f"Con cuota de ${valor:,.2f}/período necesitas "
                     f"{n} períodos  "
                     f"|  Cuota exacta: ${res_periodos['cuota_exacta']:,.2f}  "
                     f"|  Total pagado: ${res_periodos['total_pagado']:,.2f}  "
                     f"|  Total intereses: ${res_periodos['total_intereses']:,.2f}",
                text_color="#3498db"
            )
            resultado = tabla_amortizacion(capital, tasa, n)

        else:
            # Modo: períodos conocidos → calcular cuota
            n = int(valor)
            resultado = tabla_amortizacion(capital, tasa, n)
            self.lbl_cuota_fija.configure(
                text=f"Cuota fija: ${resultado['cuota_fija']:,.2f}  "
                     f"|  Total pagado: "
                     f"${resultado['cuota_fija'] * n:,.2f}  "
                     f"|  Total intereses: "
                     f"${resultado['cuota_fija'] * n - capital:,.2f}",
                text_color="gray"
            )

        # Gráfico
        if self.fig_canvas_amortizacion is not None:
            self.fig_canvas_amortizacion.get_tk_widget().destroy()
            plt.close("all")

        for widget in self.frame_graf_amort.winfo_children():
            widget.destroy()

        fig = grafico_amortizacion(resultado)
        fig.set_size_inches(9, 3.8)
        fig.patch.set_alpha(0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf_amort)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True,
                                     padx=8, pady=8)
        self.fig_canvas_amortizacion = canvas

    # ─────────────────────────────────────
    #  VALOR TERMINAL CON MÚLTIPLO
    # ─────────────────────────────────────

    def _construir_valor_terminal(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=7, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=8, column=0, padx=16, pady=(0,20), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame,
                     text="Capital Futuro con Multiplo de salida",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="A diferencia del interes compuesto, el multiplo refleja "
                          "como se valoran startups al momento de venta (exit).",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Inversion hoy",           "500000", "vt_inv"),
            ("Anos hasta el exit",      "5",      "vt_anios"),
            ("Tasa de descuento (%)",   "20",     "vt_tasa"),
            ("Multiplos (separados por coma)", "4,6,8,10", "vt_mult"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkButton(frame, text="Calcular", width=140,
                      command=self._calcular_valor_terminal
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        self.lbl_vt_min = ctk.CTkLabel(frame, text="",
                                        font=ctk.CTkFont(size=13),
                                        text_color="#3498db")
        self.lbl_vt_min.grid(row=5, column=0, columnspan=4,
                              padx=16, pady=(0,8), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=6, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3,4), weight=1)
        for i, t in enumerate(["Multiplo","Valor exit","Valor presente",
                                "VAN exit","TIR implicita"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=8, pady=6, sticky="w")

        self.frame_vt_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_vt_tabla.grid(row=7, column=0, columnspan=4,
                                  padx=16, pady=(0,14), sticky="ew")
        self.frame_vt_tabla.grid_columnconfigure((0,1,2,3,4), weight=1)
        ctk.CTkLabel(self.frame_vt_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=5, pady=10)

    def _calcular_valor_terminal(self):
        try:
            inversion = float(self.vt_inv.get().replace(",",""))
            anios     = int(self.vt_anios.get())
            tasa      = float(self.vt_tasa.get().replace("%","")) / 100
            multiplos = [float(m.strip())
                         for m in self.vt_mult.get().split(",") if m.strip()]

            res = sensibilidad_multiplos(inversion, anios, tasa, multiplos)

            self.lbl_vt_min.configure(
                text=f"Multiplo minimo viable: {res['multiple_minimo']:.2f}x  "
                     f"|  Exit minimo: ${res['valor_exit_min']:,.0f}"
            )

            for w in self.frame_vt_tabla.winfo_children():
                w.destroy()

            for i, r in enumerate(res["tabla"]):
                bg    = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                color = "#27a060" if r["viable"] else "#e74c3c"
                row   = ctk.CTkFrame(self.frame_vt_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=5, sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3,4), weight=1)

                for j, (txt, c) in enumerate([
                    (f"{r['multiple']:.0f}x",          ("gray10","gray90")),
                    (f"${r['valor_exit']:,.0f}",       ("gray10","gray90")),
                    (f"${r['valor_presente']:,.0f}",   ("gray10","gray90")),
                    (f"${r['van_exit']:,.0f}",         color),
                    (f"{r['tir_implicita_pct']:.2f}%", color),
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12), text_color=c
                                 ).grid(row=0, column=j, padx=8, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))