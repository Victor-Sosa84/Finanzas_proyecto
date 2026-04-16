"""
graficos.py
===========
Módulo de visualización para el análisis financiero.

Contiene 4 gráficos principales para la defensa:
  1. Curva VAN vs tasa (con TIR marcada)
  2. Flujos de caja y flujo acumulado (barras + línea)
  3. Heatmap de sensibilidad 2D (tasa x flujos)
  4. Tornado chart (impacto de cada variable)

Más gráficos de apoyo:
  5. Comparación interés simple vs compuesto
  6. Tabla de amortización (saldo + composición de cuota)
  7. Escenarios (optimista / base / pesimista)

Regla de oro: este archivo SOLO grafica — no calcula nada.
Recibe los datos ya calculados desde logica/ y los dibuja.

Dependencias: matplotlib, numpy
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap


# ─────────────────────────────────────────
#  CONFIGURACIÓN VISUAL GLOBAL
# ─────────────────────────────────────────

COLOR_POSITIVO  = "#2ecc71"   # verde
COLOR_NEGATIVO  = "#e74c3c"   # rojo
COLOR_BASE      = "#3498db"   # azul
COLOR_ACENTO    = "#f39c12"   # naranja/amarillo
COLOR_NEUTRO    = "#95a5a6"   # gris
COLOR_FONDO     = "#f8f9fa"   # fondo claro
COLOR_TEXTO     = "#2c3e50"   # texto oscuro

FUENTE_TITULO   = {"fontsize": 14, "fontweight": "bold", "color": COLOR_TEXTO}
FUENTE_SUBTITULO = {"fontsize": 11, "color": COLOR_NEUTRO}
FUENTE_EJE      = {"fontsize": 10, "color": COLOR_TEXTO}


def _estilo_base(ax, titulo, subtitulo=""):
    """Aplica estilo consistente a todos los gráficos."""
    ax.set_facecolor(COLOR_FONDO)
    ax.figure.patch.set_facecolor("white")
    ax.set_title(titulo, **FUENTE_TITULO, pad=12)
    if subtitulo:
        ax.set_title(f"{titulo}\n{subtitulo}",
                     **FUENTE_TITULO, pad=12)
    ax.tick_params(colors=COLOR_TEXTO, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dee2e6")
    ax.spines["bottom"].set_color("#dee2e6")
    ax.grid(axis="y", color="#dee2e6", linewidth=0.8, linestyle="--")
    ax.set_axisbelow(True)


# ─────────────────────────────────────────
#  1. CURVA VAN VS TASA
# ─────────────────────────────────────────

def grafico_van_vs_tasa(datos_variacion_tasa, tir_valor, tasa_base):
    """
    Dibuja la curva VAN en función de la tasa de descuento.

    Muestra claramente:
    - Zona verde (VAN > 0): el proyecto es viable
    - Zona roja  (VAN < 0): el proyecto no es viable
    - Punto TIR: donde VAN = 0
    - Línea vertical en la tasa base del proyecto

    Parámetros:
        datos_variacion_tasa (dict): Resultado de sensibilidad.variacion_tasa()
        tir_valor            (float): TIR del proyecto en decimal
        tasa_base            (float): Tasa de descuento base en decimal

    Uso:
        from logica.van_tir      import van, tir
        from logica.sensibilidad import variacion_tasa
        from graficos.graficos   import grafico_van_vs_tasa

        vt  = variacion_tasa(50000, flujos, 0.12)
        tir_res = tir(50000, flujos)
        grafico_van_vs_tasa(vt, tir_res['tir'], 0.12)
        plt.show()
    """
    tasas = [d["tasa"] for d in datos_variacion_tasa["datos"]]
    vanes = [d["van"]  for d in datos_variacion_tasa["datos"]]

    fig, ax = plt.subplots(figsize=(9, 3.8))
    fig.subplots_adjust(top=0.90)
    _estilo_base(ax, f"TIR = {tir_valor*100:.2f}%  |  Tasa base = {tasa_base*100:.1f}%")

    # Línea de VAN = 0
    ax.axhline(0, color=COLOR_TEXTO, linewidth=1, linestyle="-", alpha=0.4)

    # Relleno zonas viable / no viable
    tasas_np = np.array(tasas)
    vanes_np = np.array(vanes)
    ax.fill_between(tasas_np, vanes_np, 0,
                    where=vanes_np >= 0,
                    alpha=0.15, color=COLOR_POSITIVO, label="VAN positivo")
    ax.fill_between(tasas_np, vanes_np, 0,
                    where=vanes_np < 0,
                    alpha=0.15, color=COLOR_NEGATIVO, label="VAN negativo")

    # Curva principal
    ax.plot(tasas_np, vanes_np,
            color=COLOR_BASE, linewidth=2.5, zorder=3)

    # Punto TIR
    ax.scatter([tir_valor], [0],
               color=COLOR_ACENTO, s=100, zorder=5,
               label=f"TIR = {tir_valor*100:.2f}%")
    ax.annotate(f"  TIR\n  {tir_valor*100:.2f}%",
                xy=(tir_valor, 0),
                xytext=(tir_valor + 0.005, max(vanes_np) * 0.15),
                fontsize=9, color=COLOR_ACENTO, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=COLOR_ACENTO,
                                lw=1.2))

    # Línea vertical en tasa base
    van_en_base = datos_variacion_tasa["van_base"]
    ax.axvline(tasa_base, color=COLOR_BASE,
               linewidth=1.5, linestyle="--", alpha=0.7,
               label=f"Tasa base {tasa_base*100:.1f}% → VAN ${van_en_base:,.0f}")
    ax.scatter([tasa_base], [van_en_base],
               color=COLOR_BASE, s=70, zorder=5)

    ax.set_xlabel("Tasa de descuento", **FUENTE_EJE)
    ax.set_ylabel("VAN ($)", **FUENTE_EJE)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=9, framealpha=0.8)

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  2. FLUJOS DE CAJA Y ACUMULADO
# ─────────────────────────────────────────

def grafico_flujos(inversion, flujos, flujos_acumulados):
    """
    Dibuja los flujos de caja por período y el flujo acumulado.

    Barras: flujos netos por período (verdes si positivos, rojos si no)
    Línea:  flujo acumulado — muestra visualmente el período de recupero

    Parámetros:
        inversion         (float)     : Inversión inicial
        flujos            (list[float]): Flujos netos por período
        flujos_acumulados (list[float]): Resultado de periodo_recupero()
                                         ['flujos_acum']

    Uso:
        from logica.van_tir  import periodo_recupero
        from graficos.graficos import grafico_flujos

        payback = periodo_recupero(50000, flujos)
        grafico_flujos(50000, flujos, payback['flujos_acum'])
        plt.show()
    """
    n         = len(flujos)
    periodos  = list(range(1, n + 1))
    colores   = [COLOR_POSITIVO if f >= 0 else COLOR_NEGATIVO
                 for f in flujos]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    _estilo_base(ax1, "Flujos de caja del proyecto",
                 f"Inversión inicial: ${inversion:,.0f}")

    # Barras de flujos
    bars = ax1.bar(periodos, flujos, color=colores,
                   alpha=0.8, width=0.5, zorder=3,
                   label="Flujo neto por período")

    # Etiquetas sobre barras
    for bar, val in zip(bars, flujos):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(flujos) * 0.02,
                 f"${val:,.0f}",
                 ha="center", va="bottom", fontsize=8.5,
                 color=COLOR_TEXTO)

    ax1.set_xlabel("Período", **FUENTE_EJE)
    ax1.set_ylabel("Flujo neto ($)", **FUENTE_EJE)
    ax1.set_xticks(periodos)
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # Eje secundario: flujo acumulado
    ax2 = ax1.twinx()
    periodos_acum = list(range(0, n + 1))
    ax2.plot(periodos_acum, flujos_acumulados,
             color=COLOR_ACENTO, linewidth=2.5,
             marker="o", markersize=6, zorder=4,
             label="Flujo acumulado")
    ax2.axhline(0, color=COLOR_ACENTO,
                linewidth=1, linestyle=":", alpha=0.5)
    ax2.set_ylabel("Flujo acumulado ($)", color=COLOR_ACENTO,
                   fontsize=10)
    ax2.tick_params(axis="y", colors=COLOR_ACENTO)
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.spines["top"].set_visible(False)

    # Leyenda combinada
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=9, framealpha=0.8,
               loc="upper left")

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  3. HEATMAP DE SENSIBILIDAD 2D
# ─────────────────────────────────────────

def grafico_heatmap(datos_tabla_2d):
    """
    Dibuja el heatmap de sensibilidad tasa × flujos.

    Colores:
    - Verde intenso:  VAN muy positivo
    - Blanco/amarillo: VAN cerca de cero
    - Rojo intenso:   VAN muy negativo

    La celda base (tasa y flujos originales) se marca con un borde.

    Parámetros:
        datos_tabla_2d (dict): Resultado de sensibilidad.tabla_2d()

    Uso:
        from logica.sensibilidad import tabla_2d
        from graficos.graficos   import grafico_heatmap

        t2d = tabla_2d(50000, flujos, 0.12)
        grafico_heatmap(t2d)
        plt.show()
    """
    matriz     = np.array(datos_tabla_2d["matriz"])
    tasas      = datos_tabla_2d["tasas"]
    variaciones = datos_tabla_2d["variaciones"]
    tasa_base  = datos_tabla_2d["tasa_base"]

    # Colormap personalizado: rojo → blanco → verde
    cmap = LinearSegmentedColormap.from_list(
        "van_cmap",
        [COLOR_NEGATIVO, "#ffffff", COLOR_POSITIVO]
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_facecolor(COLOR_FONDO)
    fig.patch.set_facecolor("white")

    im = ax.imshow(matriz, cmap=cmap, aspect="auto",
                   vmin=matriz.min(), vmax=matriz.max())

    # Etiquetas en cada celda
    for i in range(len(tasas)):
        for j in range(len(variaciones)):
            val   = matriz[i, j]
            color = "white" if abs(val) > abs(matriz).max() * 0.5 \
                    else COLOR_TEXTO
            ax.text(j, i, f"${val:,.0f}",
                    ha="center", va="center",
                    fontsize=8, color=color, fontweight="bold")

    # Marcar celda base
    tasa_idx = min(range(len(tasas)),
                   key=lambda i: abs(tasas[i] - tasa_base))
    flujo_idx = len(variaciones) // 2
    rect = plt.Rectangle(
        (flujo_idx - 0.5, tasa_idx - 0.5), 1, 1,
        linewidth=2.5, edgecolor=COLOR_ACENTO,
        facecolor="none", zorder=5
    )
    ax.add_patch(rect)

    ax.set_xticks(range(len(variaciones)))
    ax.set_xticklabels([f"{v:+.0f}%" for v in variaciones],
                       fontsize=9)
    ax.set_yticks(range(len(tasas)))
    ax.set_yticklabels([f"{t*100:.1f}%" for t in tasas],
                       fontsize=9)
    ax.set_xlabel("Variación en flujos de caja", **FUENTE_EJE)
    ax.set_ylabel("Tasa de descuento", **FUENTE_EJE)
    ax.set_title("Heatmap de sensibilidad — VAN ($)",
                 **FUENTE_TITULO, pad=12)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("VAN ($)", fontsize=9, color=COLOR_TEXTO)
    cbar.ax.tick_params(labelsize=8)

    leyenda = mpatches.Patch(edgecolor=COLOR_ACENTO,
                              facecolor="none", linewidth=2,
                              label="Escenario base")
    ax.legend(handles=[leyenda], fontsize=9,
              loc="upper right", framealpha=0.8)

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  4. TORNADO CHART
# ─────────────────────────────────────────

def grafico_tornado(datos_tornado, van_base, top_n=6):
    """
    Dibuja el tornado chart de sensibilidad.

    Muestra qué variables impactan más el VAN al variarlas ±10%.
    Las barras más largas = variables más críticas para la decisión.

    Parámetros:
        datos_tornado (list[dict]): Resultado de sensibilidad.tornado_vars()
        van_base      (float)     : VAN del escenario base
        top_n         (int)       : Cuántas variables mostrar (default 6)

    Uso:
        from logica.van_tir      import van
        from logica.sensibilidad import tornado_vars
        from graficos.graficos   import grafico_tornado

        van_b   = van(50000, flujos, 0.12)
        tornado = tornado_vars(50000, flujos, 0.12)
        grafico_tornado(tornado, van_b)
        plt.show()
    """
    datos = datos_tornado[:top_n]
    datos = list(reversed(datos))  # mayor impacto arriba

    variables  = [d["variable"]  for d in datos]
    vanes_bajo = [d["van_bajo"]  for d in datos]
    vanes_alto = [d["van_alto"]  for d in datos]

    fig, ax = plt.subplots(figsize=(9, max(4, len(datos) * 0.9)))
    _estilo_base(ax, "Tornado chart — Sensibilidad del VAN",
                 f"Variación ±10% sobre cada variable  |  VAN base: ${van_base:,.0f}")
    ax.grid(axis="x", color="#dee2e6", linewidth=0.8, linestyle="--")
    ax.grid(axis="y", visible=False)

    y_pos = range(len(datos))

    for i, (vb, va) in enumerate(zip(vanes_bajo, vanes_alto)):
        izq   = min(vb, va)
        der   = max(vb, va)
        ancho = der - izq

        # Barra izquierda (valor bajo)
        ax.barh(i, vb - van_base, left=van_base,
                color=COLOR_NEGATIVO, alpha=0.85, height=0.5)
        # Barra derecha (valor alto)
        ax.barh(i, va - van_base, left=van_base,
                color=COLOR_POSITIVO, alpha=0.85, height=0.5)

        # Etiquetas de valores extremos
        ax.text(min(vb, van_base) - abs(van_base) * 0.02,
                i, f"${vb:,.0f}",
                ha="right", va="center", fontsize=7.5,
                color=COLOR_NEGATIVO)
        ax.text(max(va, van_base) + abs(van_base) * 0.02,
                i, f"${va:,.0f}",
                ha="left", va="center", fontsize=7.5,
                color=COLOR_POSITIVO)

    # Línea vertical en VAN base
    ax.axvline(van_base, color=COLOR_TEXTO,
               linewidth=1.5, linestyle="--", alpha=0.6,
               label=f"VAN base ${van_base:,.0f}")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(variables, fontsize=9)
    ax.set_xlabel("VAN ($)", **FUENTE_EJE)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    parche_bajo = mpatches.Patch(color=COLOR_NEGATIVO,
                                  alpha=0.85, label="Valor bajo (-10%)")
    parche_alto = mpatches.Patch(color=COLOR_POSITIVO,
                                  alpha=0.85, label="Valor alto (+10%)")
    ax.legend(handles=[parche_bajo, parche_alto],
              fontsize=9, framealpha=0.8, loc="lower right")

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  5. SIMPLE VS COMPUESTO
# ─────────────────────────────────────────

def grafico_simple_vs_compuesto(datos_comparacion, capital):
    """
    Compara visualmente el crecimiento del capital con interés
    simple vs interés compuesto a lo largo del tiempo.

    Parámetros:
        datos_comparacion (list[dict]): Resultado de
                           intereses.comparar_simple_vs_compuesto()
        capital           (float)     : Capital inicial

    Uso:
        from logica.intereses  import comparar_simple_vs_compuesto
        from graficos.graficos import grafico_simple_vs_compuesto

        datos = comparar_simple_vs_compuesto(10000, 0.10, 10)
        grafico_simple_vs_compuesto(datos, 10000)
        plt.show()
    """
    periodos   = [0] + [d["periodo"]         for d in datos_comparacion]
    simples    = [capital] + [d["monto_simple"]    for d in datos_comparacion]
    compuestos = [capital] + [d["monto_compuesto"] for d in datos_comparacion]

    fig, ax = plt.subplots(figsize=(9, 3.8))
    fig.subplots_adjust(top=0.90)
    _estilo_base(ax, f"Capital inicial: ${capital:,.0f}  |  Simple vs Compuesto")

    ax.plot(periodos, simples,
            color=COLOR_NEUTRO, linewidth=2.5,
            marker="o", markersize=5,
            label="Interés simple (lineal)")
    ax.plot(periodos, compuestos,
            color=COLOR_BASE, linewidth=2.5,
            marker="o", markersize=5,
            label="Interés compuesto (exponencial)")

    # Relleno de diferencia
    ax.fill_between(periodos, simples, compuestos,
                    alpha=0.12, color=COLOR_BASE,
                    label="Diferencia (efecto del interés sobre interés)")

    # Anotación en el último período
    ultimo = len(periodos) - 1
    dif = compuestos[ultimo] - simples[ultimo]
    ax.annotate(f"Diferencia\n${dif:,.0f}",
                xy=(periodos[ultimo], (simples[ultimo] + compuestos[ultimo]) / 2),
                xytext=(periodos[ultimo] - len(periodos) * 0.25,
                        compuestos[ultimo] * 0.97),
                fontsize=9, color=COLOR_BASE,
                arrowprops=dict(arrowstyle="->", color=COLOR_BASE))

    ax.set_xlabel("Período", **FUENTE_EJE)
    ax.set_ylabel("Monto ($)", **FUENTE_EJE)
    ax.set_xticks(periodos)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=9, framealpha=0.8)

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  6. TABLA DE AMORTIZACIÓN
# ─────────────────────────────────────────

def grafico_amortizacion(datos_amortizacion):
    """
    Visualiza la composición de cada cuota: interés vs amortización,
    y la evolución del saldo a lo largo del tiempo.

    Parámetros:
        datos_amortizacion (dict): Resultado de
                            intereses.tabla_amortizacion()

    Uso:
        from logica.intereses  import tabla_amortizacion
        from graficos.graficos import grafico_amortizacion

        datos = tabla_amortizacion(10000, 0.01, 12)
        grafico_amortizacion(datos)
        plt.show()
    """
    tabla     = datos_amortizacion["tabla"]
    periodos  = [f["periodo"]      for f in tabla]
    intereses = [f["interes"]      for f in tabla]
    amorts    = [f["amortizacion"] for f in tabla]
    saldos    = [f["saldo"]        for f in tabla]
    cuota     = datos_amortizacion["cuota_fija"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8))
    fig.subplots_adjust(top=0.88)

    # Panel izquierdo: composición de cuota (barras apiladas)
    _estilo_base(ax1, f"Composición de la cuota  |  Cuota fija: ${cuota:,.2f}")
    ax1.bar(periodos, intereses,
            color=COLOR_NEGATIVO, alpha=0.85,
            label="Interés", width=0.6)
    ax1.bar(periodos, amorts, bottom=intereses,
            color=COLOR_POSITIVO, alpha=0.85,
            label="Amortización de capital", width=0.6)
    ax1.set_xlabel("Período", **FUENTE_EJE)
    ax1.set_ylabel("Monto ($)", **FUENTE_EJE)
    ax1.set_xticks(periodos)
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax1.legend(fontsize=9, framealpha=0.8)

    # Panel derecho: evolución del saldo
    _estilo_base(ax2, "Evolución del saldo del préstamo")
    ax2.grid(axis="x", color="#dee2e6",
             linewidth=0.8, linestyle="--")
    ax2.plot(periodos, saldos,
             color=COLOR_BASE, linewidth=2.5,
             marker="o", markersize=5, label="Saldo restante")
    ax2.fill_between(periodos, saldos,
                     alpha=0.12, color=COLOR_BASE)
    ax2.set_xlabel("Período", **FUENTE_EJE)
    ax2.set_ylabel("Saldo ($)", **FUENTE_EJE)
    ax2.set_xticks(periodos)
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.legend(fontsize=9, framealpha=0.8)

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  7. ESCENARIOS
# ─────────────────────────────────────────

def grafico_escenarios(datos_escenarios):
    """
    Compara VAN y TIR de los tres escenarios en un gráfico de barras.

    Parámetros:
        datos_escenarios (list[dict]): Resultado de
                          sensibilidad.escenarios()

    Uso:
        from logica.sensibilidad import escenarios
        from graficos.graficos   import grafico_escenarios

        esc = escenarios(50000, flujos, 0.12)
        grafico_escenarios(esc)
        plt.show()
    """
    nombres = [e["escenario"].capitalize() for e in datos_escenarios]
    vanes   = [e["van"] for e in datos_escenarios]
    tires   = [e["tir"] * 100 for e in datos_escenarios]

    colores_barras = [
        COLOR_POSITIVO if v >= 0 else COLOR_NEGATIVO
        for v in vanes
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    # Panel izquierdo: VAN por escenario
    _estilo_base(ax1, "VAN por escenario")
    bars = ax1.bar(nombres, vanes,
                   color=colores_barras, alpha=0.85,
                   width=0.5)
    ax1.axhline(0, color=COLOR_TEXTO,
                linewidth=1, alpha=0.4)

    for bar, val in zip(bars, vanes):
        offset = max(vanes) * 0.03
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 val + (offset if val >= 0 else -offset * 3),
                 f"${val:,.0f}",
                 ha="center", va="bottom",
                 fontsize=9, fontweight="bold",
                 color=COLOR_TEXTO)

    ax1.set_ylabel("VAN ($)", **FUENTE_EJE)
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # Panel derecho: TIR por escenario
    _estilo_base(ax2, "TIR por escenario")
    colores_tir = [
        COLOR_POSITIVO if e["tir_supera"] else COLOR_NEGATIVO
        for e in datos_escenarios
    ]
    bars2 = ax2.bar(nombres, tires,
                    color=colores_tir, alpha=0.85,
                    width=0.5)

    for bar, val in zip(bars2, tires):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 val + max(tires) * 0.02,
                 f"{val:.1f}%",
                 ha="center", va="bottom",
                 fontsize=9, fontweight="bold",
                 color=COLOR_TEXTO)

    ax2.set_ylabel("TIR (%)", **FUENTE_EJE)
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    plt.suptitle("Análisis de escenarios",
                 **FUENTE_TITULO, y=1.01)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
#  MOSTRAR O GUARDAR
# ─────────────────────────────────────────

def mostrar(fig):
    """Muestra el gráfico en pantalla."""
    plt.figure(fig.number)
    plt.show()


def guardar(fig, nombre_archivo, dpi=150):
    """
    Guarda el gráfico como imagen PNG.

    Parámetros:
        fig            : Figura de matplotlib
        nombre_archivo : Ruta de salida (ej. 'reportes/van_tasa.png')
        dpi            : Resolución (default 150)
    """
    fig.savefig(nombre_archivo, dpi=dpi,
                bbox_inches="tight", facecolor="white")
    print(f"  Guardado: {nombre_archivo}")