"""
app.py
======
Ventana principal de la aplicación.

Responsabilidades:
  - Crear la ventana CustomTkinter
  - Renderizar el menú lateral
  - Toggle de tema claro/oscuro
  - Cargar cada pantalla según la sección activa

Patrón MVC:
  - Este archivo es el Controller principal
  - Las pantallas son las Views
  - logica/ es el Model
"""

import customtkinter as ctk
from interfaz.pantalla_intereses     import PantallaIntereses
from interfaz.pantalla_tasas         import PantallaTasas
from interfaz.pantalla_van_tir       import PantallaVanTir
from interfaz.pantalla_capital       import PantallaCapital
from interfaz.pantalla_sensibilidad  import PantallaSensibilidad


# ─────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────

TEMA_INICIAL   = "light"      # "dark" o "light"
COLOR_ACENTO   = "#3498db"    # azul — color principal de la app
ANCHO_SIDEBAR  = 200
ANCHO_VENTANA  = 1100
ALTO_VENTANA   = 660

SECCIONES = [
    ("Intereses",     PantallaIntereses),
    ("Tasas",         PantallaTasas),
    ("VAN y TIR",     PantallaVanTir),
    ("Capital",       PantallaCapital),
    ("Sensibilidad",  PantallaSensibilidad),
]


# ─────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración inicial de tema
        ctk.set_appearance_mode(TEMA_INICIAL)
        ctk.set_default_color_theme("blue")

        self.title("FinanzasPro — Análisis de Inversión")
        self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.minsize(900, 580)
        self.after(0, lambda: self.state("zoomed"))

        self.seccion_activa = SECCIONES[0][0]
        self.botones_nav    = {}
        self.pantalla_actual = None

        self._construir_layout()
        self._cargar_pantalla(SECCIONES[0][0], SECCIONES[0][1])

    # ─────────────────────────────────────
    #  LAYOUT PRINCIPAL
    # ─────────────────────────────────────

    def _construir_layout(self):
        """Crea sidebar + área de contenido."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=ANCHO_SIDEBAR,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)  # empuja el toggle al fondo

        # Área de contenido (donde se cargan las pantallas)
        self.area_contenido = ctk.CTkFrame(
            self, corner_radius=0,
            fg_color="transparent"
        )
        self.area_contenido.grid(row=0, column=1, sticky="nsew")
        self.area_contenido.grid_columnconfigure(0, weight=1)
        self.area_contenido.grid_rowconfigure(0, weight=1)

        self._construir_sidebar()

    def _construir_sidebar(self):
        """Rellena el sidebar con logo, navegación y toggle de tema."""

        # Logo / título
        frame_logo = ctk.CTkFrame(
            self.sidebar, fg_color="transparent"
        )
        frame_logo.grid(row=0, column=0, padx=16, pady=(20, 12), sticky="ew")

        ctk.CTkLabel(
            frame_logo,
            text="FinanzasPro",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame_logo,
            text="Análisis de inversión",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")

        # Separador
        ctk.CTkFrame(
            self.sidebar, height=1,
            fg_color=("gray80", "gray30")
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        # Botones de navegación
        for idx, (nombre, _clase) in enumerate(SECCIONES):
            btn = ctk.CTkButton(
                self.sidebar,
                text=nombre,
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                hover_color=("gray90", "gray25"),
                corner_radius=6,
                height=36,
                command=lambda n=nombre, c=_clase: self._cargar_pantalla(n, c)
            )
            btn.grid(row=idx + 2, column=0,
                     padx=10, pady=2, sticky="ew")
            self.botones_nav[nombre] = btn

        # Separador inferior
        ctk.CTkFrame(
            self.sidebar, height=1,
            fg_color=("gray80", "gray30")
        ).grid(row=9, column=0, sticky="ew", padx=12, pady=(0, 8))

        # Toggle de tema
        frame_toggle = ctk.CTkFrame(
            self.sidebar, fg_color="transparent"
        )
        frame_toggle.grid(row=10, column=0,
                          padx=16, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            frame_toggle,
            text="Tema oscuro",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="left")

        self.switch_tema = ctk.CTkSwitch(
            frame_toggle,
            text="",
            width=40,
            command=self._toggle_tema,
            onvalue="dark",
            offvalue="light"
        )
        self.switch_tema.pack(side="right")

        # Inicializar switch según tema inicial
        if TEMA_INICIAL == "dark":
            self.switch_tema.select()
        else:
            self.switch_tema.deselect()

    # ─────────────────────────────────────
    #  NAVEGACIÓN
    # ─────────────────────────────────────

    def _cargar_pantalla(self, nombre, clase_pantalla):
        """
        Destruye la pantalla actual y carga la nueva.
        Actualiza el estado visual del botón activo.
        """
        # Limpiar pantalla anterior
        if self.pantalla_actual is not None:
            self.pantalla_actual.destroy()

        # Resetear estilos de todos los botones
        for n, btn in self.botones_nav.items():
            btn.configure(
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                font=ctk.CTkFont(size=13, weight="normal")
            )

        # Marcar botón activo
        self.botones_nav[nombre].configure(
            fg_color=("gray85", "gray25"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_ACENTO
        )

        self.seccion_activa = nombre

        # Instanciar y mostrar la nueva pantalla
        self.pantalla_actual = clase_pantalla(self.area_contenido)
        self.pantalla_actual.grid(row=0, column=0, sticky="nsew")

    # ─────────────────────────────────────
    #  TOGGLE DE TEMA
    # ─────────────────────────────────────

    def _toggle_tema(self):
        """Cambia entre tema claro y oscuro."""
        tema = self.switch_tema.get()
        ctk.set_appearance_mode(tema)


# ─────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────

def iniciar():
    app = App()
    app.mainloop()