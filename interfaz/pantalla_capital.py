"""
pantalla_capital.py
===================
Pantalla de análisis de capital y liquidez empresarial.

Muestra:
  - Capital de Trabajo (activo corriente - pasivo corriente)
  - Capital de Operaciones (NOF)
  - Índices de liquidez corriente y ácida
  - Estructura CAPEX / OPEX con cálculo de flujos netos
"""

import customtkinter as ctk
from tkinter import messagebox

from logica.capital import (
    resumen_capital,
    capital_trabajo_detalle,
    capital_operaciones,
    estructura_capex,
    estructura_opex,
    flujos_netos,
    sensibilidad_runway,
    ciclo_conversion_efectivo,
    sensibilidad_cce
)
from logica.capital_startup import (
    nota_convertible,
    sensibilidad_nota_convertible,
    sensibilidad_multiplos,
    multiplo_minimo_viable,
    costo_linea_revolving,
    sensibilidad_linea_revolving
)


class PantallaCapital(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.items_capex = []
        self.items_opex  = []

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
            text="Capital de trabajo y operaciones",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            topbar,
            text="Liquidez, CAPEX, OPEX y flujos netos del proyecto",
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
        self.scroll = scroll

        self._construir_liquidez(scroll)
        self._construir_capex(scroll)
        self._construir_opex(scroll)
        self._construir_flujos_netos(scroll)
        self._construir_runway(scroll)
        self._construir_ciclo_caja(scroll)
        self._construir_nota_convertible(scroll)
        self._construir_linea_revolving(scroll)
        self._construir_valor_terminal(scroll)

    # ─────────────────────────────────────
    #  SECCIÓN 1: LIQUIDEZ
    # ─────────────────────────────────────

    def _construir_liquidez(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(
            frame,
            text="Capital de trabajo y liquidez",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=5,
               padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Ingresa los componentes del balance corriente.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=5,
               padx=16, pady=(0, 10), sticky="w")

        campos = [
            ("Caja ($)",                  "10000", "liq_caja"),
            ("Cuentas por cobrar ($)",    "30000", "liq_cobrar"),
            ("Inventario ($)",            "40000", "liq_inventario"),
            ("Proveedores ($)",           "20000", "liq_proveedores"),
            ("Préstamos corto plazo ($)", "30000", "liq_prestamos"),
        ]

        for i, (label, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="gray"
                         ).grid(row=2, column=i, padx=10,
                                pady=(0, 2), sticky="w")
            entrada = ctk.CTkEntry(frame, placeholder_text=default)
            entrada.grid(row=3, column=i, padx=10,
                         pady=(0, 12), sticky="ew")
            entrada.insert(0, default)
            setattr(self, attr, entrada)

        ctk.CTkButton(
            frame, text="Calcular liquidez", width=160,
            command=self._calcular_liquidez
        ).grid(row=4, column=0, columnspan=2,
               padx=16, pady=(0, 12), sticky="w")

        # Métricas de liquidez
        frame_metricas = ctk.CTkFrame(frame, fg_color="transparent")
        frame_metricas.grid(row=5, column=0, columnspan=5,
                             padx=10, pady=(0, 14), sticky="ew")
        frame_metricas.grid_columnconfigure((0, 1, 2, 3), weight=1)

        indicadores = [
            ("Capital de trabajo ($)", "liq_ct"),
            ("Capital de operac. ($)", "liq_co"),
            ("Índice liquidez",        "liq_il"),
            ("Liquidez ácida",         "liq_ila"),
        ]
        self.labels_liquidez = {}

        for i, (etiqueta, key) in enumerate(indicadores):
            card = ctk.CTkFrame(frame_metricas)
            card.grid(row=0, column=i, padx=5, sticky="ew")

            ctk.CTkLabel(
                card, text=etiqueta,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=12, pady=(8, 2))

            lbl_val = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            lbl_val.pack(anchor="w", padx=12, pady=(0, 2))

            lbl_badge = ctk.CTkLabel(
                card, text="",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            lbl_badge.pack(anchor="w", padx=12, pady=(0, 8))
            self.labels_liquidez[key] = (lbl_val, lbl_badge)

    def _calcular_liquidez(self):
        try:
            caja       = float(self.liq_caja.get().replace(",", ""))
            cobrar     = float(self.liq_cobrar.get().replace(",", ""))
            inventario = float(self.liq_inventario.get().replace(",", ""))
            proveed    = float(self.liq_proveedores.get().replace(",", ""))
            prestamos  = float(self.liq_prestamos.get().replace(",", ""))

            res = resumen_capital(
                caja + cobrar + inventario,
                proveed + prestamos,
                inventario, cobrar,
                proveed
            )

            # Capital de trabajo
            lv, lb = self.labels_liquidez["liq_ct"]
            color  = "#27a060" if res["capital_trabajo_ok"] else "#e74c3c"
            lv.configure(text=f"${res['capital_trabajo']:,.0f}",
                         text_color=color)
            lb.configure(
                text="Colchon financiero" if res["capital_trabajo_ok"]
                else "Riesgo de insolvencia",
                text_color=color)

            # Capital de operaciones
            lv, lb = self.labels_liquidez["liq_co"]
            lv.configure(
                text=f"${res['capital_operaciones']:,.0f}",
                text_color=("gray10", "gray90"))
            lb.configure(text="Necesario para operar hoy")

            # Índice liquidez
            lv, lb = self.labels_liquidez["liq_il"]
            color  = "#27a060" if res["liquidez_saludable"] else "#e74c3c"
            lv.configure(text=f"{res['indice_liquidez']:.2f}",
                         text_color=color)
            lb.configure(
                text="Saludable (>= 1.5)" if res["liquidez_saludable"]
                else "Bajo (< 1.5)",
                text_color=color)

            # Liquidez ácida
            lv, lb = self.labels_liquidez["liq_ila"]
            color  = "#27a060" if res["liquidez_acida_ok"] else "#e74c3c"
            lv.configure(text=f"{res['indice_liquidez_acida']:.2f}",
                         text_color=color)
            lb.configure(
                text="Cubre deudas sin inventario" if res["liquidez_acida_ok"]
                else "No cubre sin inventario",
                text_color=color)

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  SECCIÓN 2: CAPEX
    # ─────────────────────────────────────

    def _construir_capex(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="CAPEX — Inversión inicial en activos",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Agrega los activos fijos del proyecto "
                 "(maquinaria, equipos, infraestructura, etc.)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Fila de ingreso
        fila = ctk.CTkFrame(frame, fg_color="transparent")
        fila.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        fila.grid_columnconfigure(0, weight=2)
        fila.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fila, text="Nombre del activo",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=0, column=0, pady=(0, 2), sticky="w")
        ctk.CTkLabel(fila, text="Monto ($)",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=0, column=1, padx=(12, 0),
                            pady=(0, 2), sticky="w")

        self.entrada_capex_nombre = ctk.CTkEntry(
            fila, placeholder_text="Ej: Flota de motos")
        self.entrada_capex_nombre.grid(row=1, column=0,
                                        pady=(0, 0), sticky="ew")

        self.entrada_capex_monto = ctk.CTkEntry(
            fila, placeholder_text="Ej: 30000", width=140)
        self.entrada_capex_monto.grid(row=1, column=1,
                                       padx=(12, 0), sticky="ew")

        ctk.CTkButton(
            frame, text="+ Agregar activo", width=160,
            command=self._agregar_capex
        ).grid(row=3, column=0, padx=16, pady=(8, 8), sticky="w")

        # Lista de ítems
        self.frame_lista_capex = ctk.CTkFrame(
            frame, fg_color="transparent")
        self.frame_lista_capex.grid(row=4, column=0, padx=16,
                                     pady=(0, 4), sticky="ew")
        self.frame_lista_capex.grid_columnconfigure(0, weight=1)

        # Total CAPEX
        self.lbl_total_capex = ctk.CTkLabel(
            frame, text="Total CAPEX: $0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db"
        )
        self.lbl_total_capex.grid(row=5, column=0, padx=16,
                                   pady=(4, 14), sticky="w")

    def _agregar_capex(self):
        nombre = self.entrada_capex_nombre.get().strip()
        monto_str = self.entrada_capex_monto.get().strip()

        if not nombre:
            messagebox.showwarning("Datos incompletos",
                                    "Ingresa el nombre del activo.")
            return
        try:
            monto = float(monto_str.replace(",", ""))
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número.")
            return

        self.items_capex.append({"nombre": nombre, "monto": monto})
        self.entrada_capex_nombre.delete(0, "end")
        self.entrada_capex_monto.delete(0, "end")
        self._refrescar_lista_capex()

    def _refrescar_lista_capex(self):
        for w in self.frame_lista_capex.winfo_children():
            w.destroy()

        for i, item in enumerate(self.items_capex):
            bg = ("gray95", "gray17") if i % 2 == 0 \
                 else ("gray90", "gray20")
            fila = ctk.CTkFrame(self.frame_lista_capex, fg_color=bg)
            fila.grid(row=i, column=0, sticky="ew", pady=1)
            fila.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                fila,
                text=f"{item['nombre']}   —   ${item['monto']:,.2f}",
                font=ctk.CTkFont(size=12)
            ).grid(row=0, column=0, padx=12, pady=5, sticky="w")

            idx = i
            ctk.CTkButton(
                fila, text="Quitar", width=70,
                fg_color=("gray80", "gray30"),
                hover_color=("#e74c3c", "#c0392b"),
                font=ctk.CTkFont(size=11),
                command=lambda x=idx: self._quitar_capex(x)
            ).grid(row=0, column=1, padx=8, pady=4)

        res = estructura_capex(self.items_capex) if self.items_capex \
              else {"total_capex": 0}
        self.lbl_total_capex.configure(
            text=f"Total CAPEX: ${res['total_capex']:,.2f}"
                 f"  ({len(self.items_capex)} ítems)")

    def _quitar_capex(self, idx):
        self.items_capex.pop(idx)
        self._refrescar_lista_capex()

    # ─────────────────────────────────────
    #  SECCIÓN 3: OPEX
    # ─────────────────────────────────────

    def _construir_opex(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="OPEX — Costos operativos por período",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Agrega los costos recurrentes del negocio "
                 "(salarios, alquiler, servicios, etc.)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Fila de ingreso
        fila = ctk.CTkFrame(frame, fg_color="transparent")
        fila.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        fila.grid_columnconfigure(0, weight=2)
        fila.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fila, text="Nombre del costo",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=0, column=0, pady=(0, 2), sticky="w")
        ctk.CTkLabel(fila, text="Monto por período ($)",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).grid(row=0, column=1, padx=(12, 0),
                            pady=(0, 2), sticky="w")

        self.entrada_opex_nombre = ctk.CTkEntry(
            fila, placeholder_text="Ej: Salarios")
        self.entrada_opex_nombre.grid(row=1, column=0, sticky="ew")

        self.entrada_opex_monto = ctk.CTkEntry(
            fila, placeholder_text="Ej: 8000", width=140)
        self.entrada_opex_monto.grid(row=1, column=1,
                                      padx=(12, 0), sticky="ew")

        ctk.CTkButton(
            frame, text="+ Agregar costo", width=160,
            command=self._agregar_opex
        ).grid(row=3, column=0, padx=16, pady=(8, 8), sticky="w")

        self.frame_lista_opex = ctk.CTkFrame(
            frame, fg_color="transparent")
        self.frame_lista_opex.grid(row=4, column=0, padx=16,
                                    pady=(0, 4), sticky="ew")
        self.frame_lista_opex.grid_columnconfigure(0, weight=1)

        self.lbl_total_opex = ctk.CTkLabel(
            frame, text="Total OPEX por período: $0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e74c3c"
        )
        self.lbl_total_opex.grid(row=5, column=0, padx=16,
                                  pady=(4, 14), sticky="w")

    def _agregar_opex(self):
        nombre    = self.entrada_opex_nombre.get().strip()
        monto_str = self.entrada_opex_monto.get().strip()

        if not nombre:
            messagebox.showwarning("Datos incompletos",
                                    "Ingresa el nombre del costo.")
            return
        try:
            monto = float(monto_str.replace(",", ""))
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número.")
            return

        self.items_opex.append({"nombre": nombre, "monto": monto})
        self.entrada_opex_nombre.delete(0, "end")
        self.entrada_opex_monto.delete(0, "end")
        self._refrescar_lista_opex()

    def _refrescar_lista_opex(self):
        for w in self.frame_lista_opex.winfo_children():
            w.destroy()

        for i, item in enumerate(self.items_opex):
            bg = ("gray95", "gray17") if i % 2 == 0 \
                 else ("gray90", "gray20")
            fila = ctk.CTkFrame(self.frame_lista_opex, fg_color=bg)
            fila.grid(row=i, column=0, sticky="ew", pady=1)
            fila.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                fila,
                text=f"{item['nombre']}   —   ${item['monto']:,.2f} / período",
                font=ctk.CTkFont(size=12)
            ).grid(row=0, column=0, padx=12, pady=5, sticky="w")

            idx = i
            ctk.CTkButton(
                fila, text="Quitar", width=70,
                fg_color=("gray80", "gray30"),
                hover_color=("#e74c3c", "#c0392b"),
                font=ctk.CTkFont(size=11),
                command=lambda x=idx: self._quitar_opex(x)
            ).grid(row=0, column=1, padx=8, pady=4)

        total = sum(i["monto"] for i in self.items_opex)
        self.lbl_total_opex.configure(
            text=f"Total OPEX por período: ${total:,.2f}"
                 f"  ({len(self.items_opex)} ítems)")

    def _quitar_opex(self, idx):
        self.items_opex.pop(idx)
        self._refrescar_lista_opex()

    # ─────────────────────────────────────
    #  SECCIÓN 4: FLUJOS NETOS
    # ─────────────────────────────────────

    def _construir_flujos_netos(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=3, column=0, padx=16, pady=(8, 20), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Calcular flujos netos (Ingresos - OPEX)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text="Ingresa los ingresos estimados por período. "
                 "El OPEX se resta automáticamente.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        fila = ctk.CTkFrame(frame, fg_color="transparent")
        fila.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        fila.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fila,
                     text="Ingresos por período (separados por coma)",
                     font=ctk.CTkFont(size=12),
                     text_color="gray"
                     ).pack(anchor="w", pady=(0, 2))

        self.entrada_ingresos = ctk.CTkEntry(
            fila,
            placeholder_text="Ej: 20000, 22000, 25000, 28000, 30000")
        self.entrada_ingresos.pack(fill="x")
        self.entrada_ingresos.insert(
            0, "20000, 22000, 25000, 28000, 30000")

        ctk.CTkButton(
            frame, text="Calcular flujos netos", width=200,
            command=self._calcular_flujos_netos
        ).grid(row=3, column=0, padx=16, pady=(8, 8), sticky="w")

        self.lbl_flujos_netos = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_flujos_netos.grid(row=4, column=0, padx=16,
                                    pady=(0, 6), sticky="w")

        self.lbl_flujos_detalle = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_flujos_detalle.grid(row=5, column=0, padx=16,
                                      pady=(0, 14), sticky="w")

    def _calcular_flujos_netos(self):
        try:
            ingresos = [
                float(f.strip())
                for f in self.entrada_ingresos.get().split(",")
                if f.strip()
            ]
            if not ingresos:
                raise ValueError("Ingresa al menos un período de ingresos.")

            if not self.items_opex:
                messagebox.showwarning(
                    "Sin OPEX",
                    "No has agregado ítems de OPEX.\n"
                    "Los flujos netos serán iguales a los ingresos.")

            opex_total = sum(i["monto"] for i in self.items_opex)
            fn = flujos_netos(ingresos, opex_total)

            self.lbl_flujos_netos.configure(
                text=f"OPEX por período: ${opex_total:,.2f}  "
                     f"|  Flujos netos calculados: {len(fn)} períodos",
                text_color="#3498db"
            )
            self.lbl_flujos_detalle.configure(
                text="Flujos netos: " +
                     ", ".join(f"${v:,.0f}" for v in fn) +
                     "\n(Copia estos valores a la pantalla VAN y TIR)"
            )

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  RUNWAY CON INGRESOS VARIABLES
    # ─────────────────────────────────────

    def _construir_runway(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=4, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=5, column=0, padx=16, pady=(0,8), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame, text="Burn Rate y Runway",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="Cuanto tiempo sobrevive la empresa con la caja actual, considerando ingresos variables.",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Caja disponible",       "150000", "rw_caja"),
            ("Burn fijo por periodo", "45000",  "rw_burn"),
            ("Ingresos base periodo", "30000",  "rw_ingresos"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkLabel(frame, text="Factores de ingreso (separados por coma)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=3, padx=10, pady=(0,2), sticky="w")
        self.rw_factores = ctk.CTkEntry(frame, placeholder_text="0.6,0.8,1.0,1.2")
        self.rw_factores.grid(row=3, column=3, padx=10, pady=(0,12), sticky="ew")
        self.rw_factores.insert(0, "0.6, 0.8, 1.0, 1.2")

        ctk.CTkButton(frame, text="Calcular Runway", width=160,
                      command=self._calcular_runway
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=5, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3,4), weight=1)
        for i, t in enumerate(["Factor","Ingresos reales","Burn neto",
                                "Runway (periodos)","Estado"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=10, pady=6, sticky="w")

        self.frame_rw_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_rw_tabla.grid(row=6, column=0, columnspan=4,
                                  padx=16, pady=(0,14), sticky="ew")
        self.frame_rw_tabla.grid_columnconfigure((0,1,2,3,4), weight=1)
        ctk.CTkLabel(self.frame_rw_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=5, pady=10)

    def _calcular_runway(self):
        try:
            caja     = float(self.rw_caja.get().replace(",",""))
            burn     = float(self.rw_burn.get().replace(",",""))
            ingresos = float(self.rw_ingresos.get().replace(",",""))
            factores = [float(f.strip())
                        for f in self.rw_factores.get().split(",") if f.strip()]

            resultados = sensibilidad_runway(caja, burn, ingresos, factores)

            for w in self.frame_rw_tabla.winfo_children():
                w.destroy()

            COLORES_ALERTA = {
                "critico":     "#e74c3c",
                "advertencia": "#f39c12",
                "saludable":   "#27a060",
                "superavit":   "#3498db"
            }

            for i, r in enumerate(resultados):
                bg = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                row = ctk.CTkFrame(self.frame_rw_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=5,
                         sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3,4), weight=1)

                color = COLORES_ALERTA.get(r["alerta"], "gray")
                runway_txt = (f"{r['runway_periodos']}" if r["runway_periodos"]
                              else "Superavit")

                for j, txt in enumerate([
                    f"{r['factor']*100:.0f}%",
                    f"${r['ingresos_reales']:,.0f}",
                    f"${r['burn_neto']:,.0f}",
                    runway_txt,
                    r["alerta"].capitalize()
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12),
                                 text_color=color if j >= 3 else ("gray10","gray90")
                                 ).grid(row=0, column=j, padx=10, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  CICLO DE CONVERSIÓN DE EFECTIVO
    # ─────────────────────────────────────

    def _construir_ciclo_caja(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=6, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=7, column=0, padx=16, pady=(0,8), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame, text="Ciclo de Conversion de Efectivo (CCE)",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="CCE = Dias de cobro + Dias de inventario - Dias de pago. "
                          "Menor CCE = menos capital necesario.",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Ventas mensuales",       "120000", "cce_ventas"),
            ("Dias inventario",        "15",     "cce_inventario"),
            ("Dias pago proveedores",  "30",     "cce_pago"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkLabel(frame, text="Rangos de cobro a evaluar (dias, separados por coma)",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=2, column=3, padx=10, pady=(0,2), sticky="w")
        self.cce_rangos = ctk.CTkEntry(frame, placeholder_text="45, 60, 75, 90")
        self.cce_rangos.grid(row=3, column=3, padx=10, pady=(0,12), sticky="ew")
        self.cce_rangos.insert(0, "45, 60, 75, 90")

        ctk.CTkButton(frame, text="Calcular CCE", width=160,
                      command=self._calcular_cce
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=5, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3), weight=1)
        for i, t in enumerate(["Dias cobro","CCE (dias)",
                                "Capital necesario","Estado"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=10, pady=6, sticky="w")

        self.frame_cce_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_cce_tabla.grid(row=6, column=0, columnspan=4,
                                   padx=16, pady=(0,14), sticky="ew")
        self.frame_cce_tabla.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkLabel(self.frame_cce_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=4, pady=10)

    def _calcular_cce(self):
        try:
            ventas     = float(self.cce_ventas.get().replace(",",""))
            inventario = int(self.cce_inventario.get())
            pago       = int(self.cce_pago.get())
            rangos     = [int(float(r.strip()))
                          for r in self.cce_rangos.get().split(",") if r.strip()]

            resultados = sensibilidad_cce(ventas, inventario, pago, rangos)

            for w in self.frame_cce_tabla.winfo_children():
                w.destroy()

            for i, r in enumerate(resultados):
                bg = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                row = ctk.CTkFrame(self.frame_cce_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=4,
                         sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3), weight=1)

                color = "#27a060" if r["favorable"] else "#e74c3c"
                for j, txt in enumerate([
                    f"{r['dias_cobro']} dias",
                    f"{r['cce']} dias",
                    f"${r['capital_necesario']:,.0f}",
                    "Favorable" if r["favorable"] else "Necesita capital"
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12),
                                 text_color=color if j >= 2 else ("gray10","gray90")
                                 ).grid(row=0, column=j, padx=10, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  NOTA CONVERTIBLE
    # ─────────────────────────────────────

    def _construir_nota_convertible(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=8, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=9, column=0, padx=16, pady=(0,8), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame, text="Nota Convertible — Dilucion del fundador",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="Simula como diferentes combinaciones de cap y descuento afectan tu porcentaje de propiedad.",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Monto de la nota",          "200000",   "nc_inversion"),
            ("Acciones del fundador",     "1000000",  "nc_acciones"),
            ("Caps a evaluar (separados por coma)", "1500000, 2000000, 2500000", "nc_caps"),
            ("Descuentos % (separados por coma)",   "15, 20, 25",               "nc_descuentos"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkButton(frame, text="Calcular dilución", width=180,
                      command=self._calcular_nota_convertible
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=5, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        for i, t in enumerate(["Cap","Descuento","Precio conv.",
                                "% Fundador","% Inversor",">=65%"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=8, pady=6, sticky="w")

        self.frame_nc_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_nc_tabla.grid(row=6, column=0, columnspan=4,
                                  padx=16, pady=(0,14), sticky="ew")
        self.frame_nc_tabla.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        ctk.CTkLabel(self.frame_nc_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=6, pady=10)

    def _calcular_nota_convertible(self):
        try:
            inversion = float(self.nc_inversion.get().replace(",",""))
            acciones  = int(float(self.nc_acciones.get().replace(",","")))
            caps      = [float(c.strip().replace(",",""))
                         for c in self.nc_caps.get().split(",") if c.strip()]
            descuentos = [float(d.strip())/100
                          for d in self.nc_descuentos.get().split(",") if d.strip()]

            resultados = sensibilidad_nota_convertible(
                inversion, acciones, caps, descuentos)

            for w in self.frame_nc_tabla.winfo_children():
                w.destroy()

            for i, r in enumerate(resultados):
                bg = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                color_ok = "#27a060" if r["aceptable_65"] else "#e74c3c"
                row = ctk.CTkFrame(self.frame_nc_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=6,
                         sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3,4,5), weight=1)

                for j, (txt, color) in enumerate([
                    (f"${r['cap']:,.0f}",          ("gray10","gray90")),
                    (f"{r['descuento_pct']:.0f}%", ("gray10","gray90")),
                    (f"{r['precio_conversion']:.4f}", ("gray10","gray90")),
                    (f"{r['pct_fundador']:.2f}%",  color_ok),
                    (f"{r['pct_inversor']:.2f}%",  ("gray10","gray90")),
                    ("Si" if r["aceptable_65"] else "No", color_ok),
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12),
                                 text_color=color
                                 ).grid(row=0, column=j, padx=8, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  LÍNEA REVOLVING
    # ─────────────────────────────────────

    def _construir_linea_revolving(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=10, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=11, column=0, padx=16, pady=(0,8), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame, text="Linea de Credito Revolving",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="Evalua si el costo de la linea de credito es cubierto por el flujo operativo.",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Monto de la linea",       "300000", "rev_monto"),
            ("Tasa anual (%)",          "18",     "rev_tasa"),
            ("OPEX mensual fijo",       "70000",  "rev_opex"),
            ("Escenarios de ingreso (separados por coma)",
             "80000, 95000, 110000, 125000", "rev_ingresos"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkButton(frame, text="Calcular viabilidad", width=180,
                      command=self._calcular_linea_revolving
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=5, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3,4), weight=1)
        for i, t in enumerate(["Ingresos","Costo mensual linea",
                                "Flujo neto ops","Flujo con linea","Genera valor"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=8, pady=6, sticky="w")

        self.frame_rev_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_rev_tabla.grid(row=6, column=0, columnspan=4,
                                   padx=16, pady=(0,14), sticky="ew")
        self.frame_rev_tabla.grid_columnconfigure((0,1,2,3,4), weight=1)
        ctk.CTkLabel(self.frame_rev_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=5, pady=10)

    def _calcular_linea_revolving(self):
        try:
            monto    = float(self.rev_monto.get().replace(",",""))
            tasa     = float(self.rev_tasa.get().replace("%","")) / 100
            opex     = float(self.rev_opex.get().replace(",",""))
            ingresos = [float(v.strip().replace(",",""))
                        for v in self.rev_ingresos.get().split(",") if v.strip()]

            resultados = sensibilidad_linea_revolving(monto, tasa, opex, ingresos)

            for w in self.frame_rev_tabla.winfo_children():
                w.destroy()

            for i, r in enumerate(resultados):
                bg    = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                color = "#27a060" if r["genera_valor"] else "#e74c3c"
                row   = ctk.CTkFrame(self.frame_rev_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=5, sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3,4), weight=1)

                for j, (txt, c) in enumerate([
                    (f"${r['ingresos']:,.0f}",      ("gray10","gray90")),
                    (f"${r['costo_mensual']:,.0f}", ("gray10","gray90")),
                    (f"${r['flujo_neto_ops']:,.0f}",("gray10","gray90")),
                    (f"${r['flujo_con_linea']:,.0f}", color),
                    ("Si" if r["genera_valor"] else "No", color),
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12), text_color=c
                                 ).grid(row=0, column=j, padx=8, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────
    #  VALOR TERMINAL CON MÚLTIPLO
    # ─────────────────────────────────────

    def _construir_valor_terminal(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray80","gray30"))
        sep.grid(row=12, column=0, padx=16, pady=(8,16), sticky="ew")

        frame = ctk.CTkFrame(parent)
        frame.grid(row=13, column=0, padx=16, pady=(0,20), sticky="ew")
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(frame, text="Valor Terminal — Multiplo de salida (Exit)",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=4,
                            padx=16, pady=(12,4), sticky="w")
        ctk.CTkLabel(frame,
                     text="Proyecta el valor de la startup al momento de venta usando multiplos de mercado.",
                     font=ctk.CTkFont(size=12), text_color="gray"
                     ).grid(row=1, column=0, columnspan=4,
                            padx=16, pady=(0,10), sticky="w")

        campos = [
            ("Inversion hoy",             "500000", "vt_inversion"),
            ("Anos hasta el exit",        "5",      "vt_anios"),
            ("Tasa de descuento (%)",     "20",     "vt_tasa"),
            ("Multiplos a evaluar (separados por coma)",
             "4, 6, 8, 10",              "vt_multiplos"),
        ]
        for i, (lbl, default, attr) in enumerate(campos):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(size=12), text_color="gray"
                         ).grid(row=2, column=i, padx=10, pady=(0,2), sticky="w")
            e = ctk.CTkEntry(frame, placeholder_text=default)
            e.grid(row=3, column=i, padx=10, pady=(0,12), sticky="ew")
            e.insert(0, default)
            setattr(self, attr, e)

        ctk.CTkButton(frame, text="Calcular exit", width=160,
                      command=self._calcular_valor_terminal
                      ).grid(row=4, column=0, padx=16, pady=(0,10), sticky="w")

        self.lbl_vt_minimo = ctk.CTkLabel(frame, text="",
                                           font=ctk.CTkFont(size=13),
                                           text_color="#3498db")
        self.lbl_vt_minimo.grid(row=5, column=0, columnspan=4,
                                 padx=16, pady=(0,8), sticky="w")

        enc = ctk.CTkFrame(frame, fg_color=("gray88","gray22"))
        enc.grid(row=6, column=0, columnspan=4, padx=16, pady=(0,2), sticky="ew")
        enc.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        for i, t in enumerate(["Multiplo","Valor exit","Valor presente",
                                "VAN exit","TIR implicita","Viable"]):
            ctk.CTkLabel(enc, text=t,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=i, padx=8, pady=6, sticky="w")

        self.frame_vt_tabla = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_vt_tabla.grid(row=7, column=0, columnspan=4,
                                  padx=16, pady=(0,14), sticky="ew")
        self.frame_vt_tabla.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        ctk.CTkLabel(self.frame_vt_tabla,
                     text="Los datos apareceran aqui despues de calcular",
                     text_color="gray", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, columnspan=6, pady=10)

    def _calcular_valor_terminal(self):
        try:
            inversion = float(self.vt_inversion.get().replace(",",""))
            anios     = int(self.vt_anios.get())
            tasa      = float(self.vt_tasa.get().replace("%","")) / 100
            multiplos = [float(m.strip())
                         for m in self.vt_multiplos.get().split(",") if m.strip()]

            res = sensibilidad_multiplos(inversion, anios, tasa, multiplos)

            self.lbl_vt_minimo.configure(
                text=f"Multiplo minimo viable: {res['multiple_minimo']:.2f}x  "
                     f"|  Valor de exit minimo: ${res['valor_exit_min']:,.0f}"
            )

            for w in self.frame_vt_tabla.winfo_children():
                w.destroy()

            for i, r in enumerate(res["tabla"]):
                bg    = ("gray95","gray17") if i % 2 == 0 else ("gray90","gray20")
                color = "#27a060" if r["viable"] else "#e74c3c"
                row   = ctk.CTkFrame(self.frame_vt_tabla, fg_color=bg)
                row.grid(row=i, column=0, columnspan=6, sticky="ew", pady=1)
                row.grid_columnconfigure((0,1,2,3,4,5), weight=1)

                for j, (txt, c) in enumerate([
                    (f"{r['multiple']:.0f}x",           ("gray10","gray90")),
                    (f"${r['valor_exit']:,.0f}",        ("gray10","gray90")),
                    (f"${r['valor_presente']:,.0f}",    ("gray10","gray90")),
                    (f"${r['van_exit']:,.0f}",          color),
                    (f"{r['tir_implicita_pct']:.2f}%",  color),
                    ("Si" if r["viable"] else "No",      color),
                ]):
                    ctk.CTkLabel(row, text=txt,
                                 font=ctk.CTkFont(size=12), text_color=c
                                 ).grid(row=0, column=j, padx=8, pady=5, sticky="w")

        except ValueError as e:
            messagebox.showerror("Error", str(e))