"""
pantalla_tasas.py
=================
Pantalla de conversión y análisis de tasas de interés.

Muestra:
  - Conversión TN ↔ TEA
  - Conversión entre períodos (cualquier período a cualquier otro)
  - Tasa real ajustada por inflación
  - Tabla de equivalencias completa para una TEA dada
"""

import customtkinter as ctk
from tkinter import messagebox

from logica.tasas import (
    tn_a_tea, tea_a_tn,
    convertir_tasa, tasa_real,
    spread, tabla_equivalencias,
    PERIODOS_POR_ANIO
)

PERIODOS = list(PERIODOS_POR_ANIO.keys())


class PantallaTasas(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

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
            text="Conversión de tasas de interés",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            topbar,
            text="TN, TEA, tasas por período y tasa real",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

    # ─────────────────────────────────────
    #  CONTENIDO
    # ─────────────────────────────────────

    def _construir_contenido(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._construir_tn_tea(scroll)
        self._construir_convertir_periodos(scroll)
        self._construir_tasa_real(scroll)
        self._construir_equivalencias(scroll)

    # ─────────────────────────────────────
    #  SECCIÓN 1: TN ↔ TEA
    # ─────────────────────────────────────

    def _construir_tn_tea(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            frame,
            text="Conversión TN  ↔  TEA",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="La TN es la tasa anunciada. La TEA es lo que realmente pagas o ganas.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=4,
               padx=16, pady=(0, 10), sticky="w")

        # Campos
        campos = [
            ("Tasa Nominal anual (%)", "12",    "entrada_tn"),
            ("Capitalizaciones por año", "12",  "entrada_m"),
        ]
        for i, (label, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="gray"
                         ).grid(row=2, column=i, padx=16,
                                pady=(0, 2), sticky="w")
            entrada = ctk.CTkEntry(frame, placeholder_text=default)
            entrada.grid(row=3, column=i, padx=16,
                         pady=(0, 12), sticky="ew")
            entrada.insert(0, default)
            setattr(self, attr, entrada)

        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.grid(row=3, column=2, columnspan=2,
                           padx=16, pady=(0, 12), sticky="w")

        ctk.CTkButton(
            frame_botones, text="TN -> TEA", width=130,
            command=self._calcular_tn_a_tea
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            frame_botones, text="TEA -> TN", width=130,
            fg_color=("gray75", "gray35"),
            hover_color=("gray65", "gray45"),
            command=self._calcular_tea_a_tn
        ).pack(side="left")

        # Resultado
        self.lbl_tn_tea = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_tn_tea.grid(row=4, column=0, columnspan=4,
                              padx=16, pady=(0, 14), sticky="w")

    def _calcular_tn_a_tea(self):
        try:
            tn = float(self.entrada_tn.get().replace("%", "")) / 100
            m  = int(self.entrada_m.get())
            resultado = tn_a_tea(tn, m)
            self.lbl_tn_tea.configure(
                text=f"TN {tn*100:.4f}% capitalizable {m} veces/año  "
                     f"→  TEA = {resultado*100:.4f}%",
                text_color="#27a060"
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _calcular_tea_a_tn(self):
        try:
            tea = float(self.entrada_tn.get().replace("%", "")) / 100
            m   = int(self.entrada_m.get())
            resultado = tea_a_tn(tea, m)
            self.lbl_tn_tea.configure(
                text=f"TEA {tea*100:.4f}%  →  "
                     f"TN = {resultado*100:.4f}% capitalizable {m} veces/año",
                text_color="#3498db"
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  SECCIÓN 2: CONVERTIR ENTRE PERÍODOS
    # ─────────────────────────────────────

    def _construir_convertir_periodos(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            frame,
            text="Convertir tasa entre períodos",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Convierte una tasa de cualquier período a cualquier otro.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=4,
               padx=16, pady=(0, 10), sticky="w")

        # Tasa origen
        ctk.CTkLabel(frame, text="Tasa (%)",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=2, column=0, padx=16,
                            pady=(0, 2), sticky="w")
        self.entrada_tasa_conv = ctk.CTkEntry(
            frame, placeholder_text="Ej: 12")
        self.entrada_tasa_conv.grid(row=3, column=0, padx=16,
                                     pady=(0, 12), sticky="ew")
        self.entrada_tasa_conv.insert(0, "12")

        # Período origen
        ctk.CTkLabel(frame, text="Período origen",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=2, column=1, padx=16,
                            pady=(0, 2), sticky="w")
        self.combo_origen = ctk.CTkComboBox(
            frame, values=PERIODOS, state="readonly")
        self.combo_origen.grid(row=3, column=1, padx=16,
                                pady=(0, 12), sticky="ew")
        self.combo_origen.set("anual")

        # Período destino
        ctk.CTkLabel(frame, text="Período destino",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=2, column=2, padx=16,
                            pady=(0, 2), sticky="w")
        self.combo_destino = ctk.CTkComboBox(
            frame, values=PERIODOS, state="readonly")
        self.combo_destino.grid(row=3, column=2, padx=16,
                                 pady=(0, 12), sticky="ew")
        self.combo_destino.set("mensual")

        ctk.CTkButton(
            frame, text="Convertir", width=120,
            command=self._calcular_conversion
        ).grid(row=3, column=3, padx=16,
               pady=(0, 12), sticky="w")

        self.lbl_conversion = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_conversion.grid(row=4, column=0, columnspan=4,
                                  padx=16, pady=(0, 14), sticky="w")

    def _calcular_conversion(self):
        try:
            tasa    = float(self.entrada_tasa_conv.get()
                            .replace("%", "")) / 100
            origen  = self.combo_origen.get()
            destino = self.combo_destino.get()
            resultado = convertir_tasa(tasa, origen, destino)
            self.lbl_conversion.configure(
                text=f"{tasa*100:.4f}% {origen}  "
                     f"→  {resultado*100:.6f}% {destino}",
                text_color="#27a060"
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  SECCIÓN 3: TASA REAL + SPREAD
    # ─────────────────────────────────────

    def _construir_tasa_real(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            frame,
            text="Tasa real e inflación",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Fórmula de Fisher: tasa real = (1 + nominal) / (1 + inflación) - 1",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=4,
               padx=16, pady=(0, 10), sticky="w")

        campos = [
            ("Tasa nominal anual (%)",  "12", "entrada_nominal"),
            ("Inflación anual (%)",     "8",  "entrada_inflacion"),
            ("Tasa activa (%)",         "15", "entrada_activa"),
            ("Tasa pasiva (%)",         "4",  "entrada_pasiva"),
        ]
        for i, (label, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="gray"
                         ).grid(row=2, column=i, padx=16,
                                pady=(0, 2), sticky="w")
            entrada = ctk.CTkEntry(frame, placeholder_text=default)
            entrada.grid(row=3, column=i, padx=16,
                         pady=(0, 12), sticky="ew")
            entrada.insert(0, default)
            setattr(self, attr, entrada)

        ctk.CTkButton(
            frame, text="Calcular", width=120,
            command=self._calcular_tasa_real
        ).grid(row=4, column=0, padx=16, pady=(0, 12), sticky="w")

        self.lbl_tasa_real = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_tasa_real.grid(row=5, column=0, columnspan=4,
                                 padx=16, pady=(0, 14), sticky="w")

    def _calcular_tasa_real(self):
        try:
            nominal   = float(self.entrada_nominal.get()
                              .replace("%", "")) / 100
            inflacion = float(self.entrada_inflacion.get()
                              .replace("%", "")) / 100
            activa    = float(self.entrada_activa.get()
                              .replace("%", "")) / 100
            pasiva    = float(self.entrada_pasiva.get()
                              .replace("%", "")) / 100

            real   = tasa_real(nominal, inflacion)
            spread_val = spread(activa, pasiva)
            color  = "#27a060" if real > 0 else "#e74c3c"

            self.lbl_tasa_real.configure(
                text=f"Tasa real: {real*100:.4f}%  "
                     f"({'el dinero gana poder adquisitivo' if real > 0 else 'el dinero pierde valor real'})  "
                     f"|  Spread bancario: {spread_val*100:.2f}%",
                text_color=color
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  SECCIÓN 4: TABLA DE EQUIVALENCIAS
    # ─────────────────────────────────────

    def _construir_equivalencias(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=3, column=0, padx=16, pady=(8, 20), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Tabla de equivalencias de tasas",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Muestra cómo se expresa una TEA en todos los períodos estándar.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Entrada + botón
        fila_entrada = ctk.CTkFrame(frame, fg_color="transparent")
        fila_entrada.grid(row=2, column=0, padx=16,
                          pady=(0, 12), sticky="w")

        ctk.CTkLabel(fila_entrada, text="TEA (Tasa Efectiva Anual) %",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).pack(side="left", padx=(0, 8))

        self.entrada_tea_equiv = ctk.CTkEntry(
            fila_entrada, width=120,
            placeholder_text="Ej: 12")
        self.entrada_tea_equiv.pack(side="left", padx=(0, 12))
        self.entrada_tea_equiv.insert(0, "12")

        ctk.CTkButton(
            fila_entrada, text="Generar tabla",
            width=140,
            command=self._calcular_equivalencias
        ).pack(side="left")

        # Encabezados tabla
        encabezados = ctk.CTkFrame(frame, fg_color=("gray88", "gray22"))
        encabezados.grid(row=3, column=0, padx=16,
                         pady=(0, 2), sticky="ew")
        encabezados.grid_columnconfigure((0, 1, 2), weight=1)

        for i, texto in enumerate(["Período", "Tasa (%)", "Tasa (decimal)"]):
            ctk.CTkLabel(
                encabezados, text=texto,
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=i, padx=16, pady=6, sticky="w")

        # Contenedor filas
        self.frame_equiv = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_equiv.grid(row=4, column=0, padx=16,
                               pady=(0, 16), sticky="ew")
        self.frame_equiv.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            self.frame_equiv,
            text="Ingresa una TEA y presiona Generar tabla",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, columnspan=3, pady=10)

    def _calcular_equivalencias(self):
        try:
            tea = float(self.entrada_tea_equiv.get()
                        .replace("%", "")) / 100
            equiv = tabla_equivalencias(tea)

            # Limpiar filas anteriores
            for widget in self.frame_equiv.winfo_children():
                widget.destroy()

            for i, fila in enumerate(equiv):
                bg = ("gray95", "gray17") if i % 2 == 0 \
                     else ("gray90", "gray20")
                row_frame = ctk.CTkFrame(
                    self.frame_equiv, fg_color=bg)
                row_frame.grid(row=i, column=0, columnspan=3,
                               sticky="ew", pady=1)
                row_frame.grid_columnconfigure((0, 1, 2), weight=1)

                # Resaltar fila anual
                es_anual = fila["periodo"] == "anual"
                peso = "bold" if es_anual else "normal"

                ctk.CTkLabel(
                    row_frame,
                    text=fila["periodo"].capitalize(),
                    font=ctk.CTkFont(size=12, weight=peso)
                ).grid(row=0, column=0, padx=16, pady=5, sticky="w")

                ctk.CTkLabel(
                    row_frame,
                    text=f"{fila['tasa_pct']:.4f}%",
                    font=ctk.CTkFont(size=12, weight=peso),
                    text_color="#3498db" if es_anual else ("gray10", "gray90")
                ).grid(row=0, column=1, padx=16, pady=5, sticky="w")

                ctk.CTkLabel(
                    row_frame,
                    text=f"{fila['tasa']:.6f}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                ).grid(row=0, column=2, padx=16, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))