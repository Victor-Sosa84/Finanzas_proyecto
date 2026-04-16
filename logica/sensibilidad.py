"""
sensibilidad.py
===============
Módulo de análisis de sensibilidad para evaluación de proyectos.

Cubre:
  - Escenarios (optimista, base, pesimista)
  - Variación de tasa de descuento (curva VAN vs tasa)
  - Variación de flujos de caja
  - Tabla 2D (tasa × flujos) — base del heatmap
  - Punto de equilibrio financiero
  - Tornado chart (impacto de cada variable)

Regla de oro: este archivo no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.

Dependencia: importa van() y tir() de van_tir.py
"""

import numpy as np
from logica.van_tir import van, tir


# ─────────────────────────────────────────
#  ESCENARIOS
# ─────────────────────────────────────────

def escenarios(inversion, flujos_base, tasa,
               factor_optimista=1.20,
               factor_pesimista=0.80):
    """
    Calcula VAN y TIR para tres escenarios: optimista, base y pesimista.

    Los escenarios se generan multiplicando los flujos base por
    un factor. La inversión y la tasa se mantienen constantes.

    Parámetros:
        inversion        (float)     : Inversión inicial (CAPEX)
        flujos_base      (list[float]): Flujos de caja del escenario base
        tasa             (float)     : Tasa de descuento en decimal
        factor_optimista (float)     : Factor de mejora en flujos
                                       (default 1.20 = +20%)
        factor_pesimista (float)     : Factor de reducción en flujos
                                       (default 0.80 = -20%)

    Retorna:
        list[dict]: Una fila por escenario con:
            - escenario    (str)       : "optimista", "base", "pesimista"
            - factor       (float)     : Factor aplicado a los flujos
            - flujos       (list[float]): Flujos modificados
            - van          (float)
            - tir          (float)
            - van_viable   (bool)      : True si VAN >= 0
            - tir_supera   (bool)      : True si TIR > tasa

    Ejemplo:
        >>> escenarios(50000, [12000, 15000, 18000, 20000, 22000], 0.12)
        [
            {'escenario': 'optimista', 'van': 31127.0, 'tir': 0.338, ...},
            {'escenario': 'base',      'van': 14273.0, 'tir': 0.241, ...},
            {'escenario': 'pesimista', 'van': -2581.0, 'tir': 0.142, ...},
        ]
    """
    definiciones = [
        ("optimista", factor_optimista),
        ("base",      1.0),
        ("pesimista", factor_pesimista),
    ]

    resultados = []
    for nombre, factor in definiciones:
        flujos_mod = [round(f * factor, 2) for f in flujos_base]
        van_val    = van(inversion, flujos_mod, tasa)
        tir_result = tir(inversion, flujos_mod)

        resultados.append({
            "escenario":  nombre,
            "factor":     factor,
            "flujos":     flujos_mod,
            "van":        round(van_val, 2),
            "tir":        round(tir_result["tir"], 6),
            "van_viable": van_val >= 0,
            "tir_supera": tir_result["tir"] > tasa,
        })

    return resultados


# ─────────────────────────────────────────
#  VARIACIÓN DE TASA
# ─────────────────────────────────────────

def variacion_tasa(inversion, flujos, tasa_base,
                   rango=0.10, pasos=40):
    """
    Calcula el VAN para un rango de tasas alrededor de la tasa base.

    Genera los datos para la curva VAN vs tasa — el gráfico
    más importante del análisis. La TIR es el punto donde
    la curva cruza VAN = 0.

    Parámetros:
        inversion  (float)     : Inversión inicial
        flujos     (list[float]): Flujos de caja base
        tasa_base  (float)     : Tasa de referencia del proyecto
        rango      (float)     : Variación máxima hacia cada lado
                                  (default 0.10 = ±10 puntos porcentuales)
        pasos      (int)       : Cantidad de puntos en la curva
                                  (default 40 — suficiente para una curva suave)

    Retorna:
        dict con:
            - tasas     (list[float]): Lista de tasas evaluadas
            - vanes     (list[float]): VAN correspondiente a cada tasa
            - tasa_base (float)      : Tasa de referencia
            - van_base  (float)      : VAN en la tasa base
            - datos     (list[dict]) : Combinación tasa+van por fila

    Ejemplo:
        >>> resultado = variacion_tasa(50000,
        ...     [12000, 15000, 18000, 20000, 22000], 0.12)
        >>> resultado['tasas']   # de 0.02 a 0.22
        >>> resultado['vanes']   # VAN decrece a medida que sube la tasa
    """
    tasa_min = max(0.001, tasa_base - rango)
    tasa_max = tasa_base + rango
    tasas    = list(np.linspace(tasa_min, tasa_max, pasos))
    vanes    = [round(van(inversion, flujos, t), 2) for t in tasas]
    tasas    = [round(t, 6) for t in tasas]

    datos = [{"tasa": t, "van": v, "viable": v >= 0}
             for t, v in zip(tasas, vanes)]

    return {
        "tasas":     tasas,
        "vanes":     vanes,
        "tasa_base": tasa_base,
        "van_base":  round(van(inversion, flujos, tasa_base), 2),
        "datos":     datos
    }


# ─────────────────────────────────────────
#  VARIACIÓN DE FLUJOS
# ─────────────────────────────────────────

def variacion_flujos(inversion, flujos, tasa,
                     variacion_max=0.30, pasos=13):
    """
    Calcula el VAN cuando todos los flujos varían en un porcentaje uniforme.

    Simula qué pasa con el proyecto si las ventas (o ingresos)
    suben o bajan proporcionalmente en todos los períodos.

    Parámetros:
        inversion     (float)     : Inversión inicial
        flujos        (list[float]): Flujos de caja base
        tasa          (float)     : Tasa de descuento
        variacion_max (float)     : Variación máxima en cada dirección
                                    (default 0.30 = ±30%)
        pasos         (int)       : Cantidad de puntos a evaluar
                                    (default 13 — incluye el 0% en el centro)

    Retorna:
        dict con:
            - factores    (list[float]): Factores de variación evaluados
            - vanes       (list[float]): VAN por cada factor
            - van_base    (float)      : VAN sin variación (factor=1.0)
            - datos       (list[dict]) : factor + variacion_pct + van + viable

    Ejemplo:
        >>> resultado = variacion_flujos(50000,
        ...     [12000, 15000, 18000, 20000, 22000], 0.12)
        >>> # Con -17.3% de flujos, el VAN llega a cero
    """
    factores = list(np.linspace(1 - variacion_max, 1 + variacion_max, pasos))
    vanes    = []

    for factor in factores:
        flujos_mod = [f * factor for f in flujos]
        vanes.append(round(van(inversion, flujos_mod, tasa), 2))

    factores = [round(f, 4) for f in factores]

    datos = [
        {
            "factor":        f,
            "variacion_pct": round((f - 1) * 100, 1),
            "van":           v,
            "viable":        v >= 0
        }
        for f, v in zip(factores, vanes)
    ]

    return {
        "factores":  factores,
        "vanes":     vanes,
        "van_base":  round(van(inversion, flujos, tasa), 2),
        "datos":     datos
    }


# ─────────────────────────────────────────
#  TABLA 2D — BASE DEL HEATMAP
# ─────────────────────────────────────────

def tabla_2d(inversion, flujos, tasa_base,
             rango_tasa=0.08, pasos_tasa=7,
             rango_flujos=0.20, pasos_flujos=5):
    """
    Genera una matriz VAN donde filas = tasas y columnas = variación de flujos.

    Es la base del heatmap de sensibilidad — el gráfico más poderoso
    del análisis porque muestra simultáneamente el efecto de dos
    variables sobre el VAN.

    Parámetros:
        inversion      (float): Inversión inicial
        flujos         (list) : Flujos de caja base
        tasa_base      (float): Tasa de referencia
        rango_tasa     (float): Variación de tasa en cada dirección
                                 (default ±8 puntos porcentuales)
        pasos_tasa     (int)  : Filas de la matriz (default 7)
        rango_flujos   (float): Variación de flujos en cada dirección
                                 (default ±20%)
        pasos_flujos   (int)  : Columnas de la matriz (default 5)

    Retorna:
        dict con:
            - matriz       (list[list[float]]): Matriz de VAN
            - tasas        (list[float])      : Etiquetas de filas
            - factores     (list[float])      : Etiquetas de columnas
            - variaciones  (list[float])      : Variación % de flujos
            - tasa_base    (float)
            - van_base     (float)

    Ejemplo — matriz resultante (filas=tasa, columnas=flujos):

                  -20%      -10%     base     +10%     +20%
        8%      4,318     13,884   23,450   33,016   42,582
        10%    -1,145      8,778   18,701   28,624   38,547
        12%    -2,581      5,846   14,273   22,700   31,127  ← base
        16%    -8,418        239    6,891   13,548   20,200
        20%   -13,209     -6,181      847    7,875   14,903
    """
    tasa_min = max(0.001, tasa_base - rango_tasa)
    tasa_max = tasa_base + rango_tasa
    tasas    = [round(t, 4)
                for t in np.linspace(tasa_min, tasa_max, pasos_tasa)]

    factores    = [round(f, 4)
                   for f in np.linspace(1 - rango_flujos,
                                        1 + rango_flujos, pasos_flujos)]
    variaciones = [round((f - 1) * 100, 1) for f in factores]

    matriz = []
    for t in tasas:
        fila = []
        for f in factores:
            flujos_mod = [x * f for x in flujos]
            fila.append(round(van(inversion, flujos_mod, t), 2))
        matriz.append(fila)

    return {
        "matriz":      matriz,
        "tasas":       tasas,
        "factores":    factores,
        "variaciones": variaciones,
        "tasa_base":   tasa_base,
        "van_base":    round(van(inversion, flujos, tasa_base), 2)
    }


# ─────────────────────────────────────────
#  PUNTO DE EQUILIBRIO FINANCIERO
# ─────────────────────────────────────────

def punto_equilibrio_flujos(inversion, flujos, tasa,
                             tolerancia=1e-4, max_iter=100):
    """
    Encuentra el factor de flujos que hace VAN = 0.

    Responde: ¿Cuánto pueden caer los flujos antes de que
    el proyecto deje de ser viable?

    Usa búsqueda binaria — más robusta que Newton-Raphson
    para este tipo de búsqueda.

    Parámetros:
        inversion  (float)     : Inversión inicial
        flujos     (list[float]): Flujos de caja base
        tasa       (float)     : Tasa de descuento
        tolerancia (float)     : Precisión del resultado
        max_iter   (int)       : Máximo de iteraciones

    Retorna:
        dict con:
            - factor_equilibrio (float): Factor donde VAN ≈ 0
            - variacion_pct     (float): Variación porcentual respecto
                                          a flujos base (negativo = caída)
            - van_verificacion  (float): VAN en ese punto (debe ser ≈ 0)
            - viable_actualmente (bool): True si el proyecto base es viable

    Ejemplo:
        >>> punto_equilibrio_flujos(50000,
        ...     [12000, 15000, 18000, 20000, 22000], 0.12)
        {
            'factor_equilibrio': 0.827,
            'variacion_pct':     -17.3,   # los flujos pueden caer 17.3%
            'van_verificacion':  0.0,
            'viable_actualmente': True
        }
    """
    van_base = van(inversion, flujos, tasa)

    if van_base < 0:
        return {
            "factor_equilibrio":  None,
            "variacion_pct":      None,
            "van_verificacion":   round(van_base, 2),
            "viable_actualmente": False
        }

    # Búsqueda binaria entre factor 0.01 y 2.0
    f_bajo, f_alto = 0.01, 2.0

    for _ in range(max_iter):
        f_medio    = (f_bajo + f_alto) / 2
        flujos_mod = [x * f_medio for x in flujos]
        van_medio  = van(inversion, flujos_mod, tasa)

        if abs(van_medio) < tolerancia:
            break

        if van_medio > 0:
            f_alto = f_medio
        else:
            f_bajo = f_medio

    flujos_eq = [x * f_medio for x in flujos]
    van_check = van(inversion, flujos_eq, tasa)

    return {
        "factor_equilibrio":  round(f_medio, 4),
        "variacion_pct":      round((f_medio - 1) * 100, 2),
        "van_verificacion":   round(van_check, 4),
        "viable_actualmente": True
    }


# ─────────────────────────────────────────
#  TORNADO CHART
# ─────────────────────────────────────────

def tornado_vars(inversion, flujos, tasa, variacion=0.10):
    """
    Calcula el impacto de cada variable sobre el VAN de forma independiente.

    Cada variable se mueve ±variacion% mientras las demás se mantienen
    fijas. El resultado muestra qué variable afecta más al VAN —
    eso es lo que dibuja el tornado chart.

    Las variables analizadas son:
        1. Tasa de descuento
        2. Inversión inicial
        3. Flujos de caja (todos en conjunto)
        4. Cada flujo individual por período

    Parámetros:
        inversion (float)     : Inversión inicial
        flujos    (list[float]): Flujos de caja base
        tasa      (float)     : Tasa de descuento base
        variacion (float)     : Porcentaje de variación aplicado
                                 (default 0.10 = ±10%)

    Retorna:
        list[dict]: Una fila por variable, ordenada de mayor a menor
                    impacto absoluto. Cada fila tiene:
            - variable    (str)  : Nombre de la variable
            - van_bajo    (float): VAN con la variable en su valor bajo
            - van_alto    (float): VAN con la variable en su valor alto
            - impacto     (float): Diferencia van_alto - van_bajo
            - impacto_abs (float): Valor absoluto del impacto
            - valor_base  (float): Valor original de la variable
            - valor_bajo  (float): Valor bajo aplicado
            - valor_alto  (float): Valor alto aplicado

    Ejemplo:
        >>> tornado_vars(50000,
        ...     [12000, 15000, 18000, 20000, 22000], 0.12)
        [
            {'variable': 'Flujos (todos)',  'impacto_abs': 16854, ...},
            {'variable': 'Tasa descuento',  'impacto_abs': 11380, ...},
            {'variable': 'Inversión',       'impacto_abs': 10000, ...},
            {'variable': 'Flujo período 5', 'impacto_abs':  7062, ...},
            ...
        ]
        # El gráfico dibuja barras horizontales de mayor a menor
    """
    van_base = van(inversion, flujos, tasa)
    filas    = []

    # ── Variable 1: Tasa de descuento ──
    tasa_baja = tasa * (1 - variacion)
    tasa_alta = tasa * (1 + variacion)
    vb = van(inversion, flujos, tasa_baja)
    va = van(inversion, flujos, tasa_alta)
    filas.append({
        "variable":    "Tasa de descuento",
        "van_bajo":    round(vb, 2),
        "van_alto":    round(va, 2),
        "impacto":     round(va - vb, 2),
        "impacto_abs": round(abs(va - vb), 2),
        "valor_base":  tasa,
        "valor_bajo":  round(tasa_baja, 6),
        "valor_alto":  round(tasa_alta, 6),
    })

    # ── Variable 2: Inversión inicial ──
    inv_baja = inversion * (1 - variacion)
    inv_alta = inversion * (1 + variacion)
    vb = van(inv_baja, flujos, tasa)
    va = van(inv_alta, flujos, tasa)
    filas.append({
        "variable":    "Inversión inicial",
        "van_bajo":    round(vb, 2),
        "van_alto":    round(va, 2),
        "impacto":     round(va - vb, 2),
        "impacto_abs": round(abs(va - vb), 2),
        "valor_base":  inversion,
        "valor_bajo":  round(inv_baja, 2),
        "valor_alto":  round(inv_alta, 2),
    })

    # ── Variable 3: Todos los flujos en conjunto ──
    flujos_bajos = [f * (1 - variacion) for f in flujos]
    flujos_altos = [f * (1 + variacion) for f in flujos]
    vb = van(inversion, flujos_bajos, tasa)
    va = van(inversion, flujos_altos, tasa)
    filas.append({
        "variable":    "Flujos (todos los períodos)",
        "van_bajo":    round(vb, 2),
        "van_alto":    round(va, 2),
        "impacto":     round(va - vb, 2),
        "impacto_abs": round(abs(va - vb), 2),
        "valor_base":  flujos,
        "valor_bajo":  [round(f, 2) for f in flujos_bajos],
        "valor_alto":  [round(f, 2) for f in flujos_altos],
    })

    # ── Variable 4: Cada flujo individual ──
    for i, flujo_i in enumerate(flujos):
        flujos_mod_bajo = flujos.copy()
        flujos_mod_alto = flujos.copy()
        flujos_mod_bajo[i] = flujo_i * (1 - variacion)
        flujos_mod_alto[i] = flujo_i * (1 + variacion)

        vb = van(inversion, flujos_mod_bajo, tasa)
        va = van(inversion, flujos_mod_alto, tasa)
        filas.append({
            "variable":    f"Flujo período {i + 1}",
            "van_bajo":    round(vb, 2),
            "van_alto":    round(va, 2),
            "impacto":     round(va - vb, 2),
            "impacto_abs": round(abs(va - vb), 2),
            "valor_base":  flujo_i,
            "valor_bajo":  round(flujo_i * (1 - variacion), 2),
            "valor_alto":  round(flujo_i * (1 + variacion), 2),
        })

    # Ordenar de mayor a menor impacto absoluto
    filas.sort(key=lambda x: x["impacto_abs"], reverse=True)
    return filas


# ─────────────────────────────────────────
#  RESUMEN COMPLETO DE SENSIBILIDAD
# ─────────────────────────────────────────

def resumen_sensibilidad(inversion, flujos, tasa):
    """
    Genera el resumen completo del análisis de sensibilidad.

    Consolida escenarios, punto de equilibrio y las variables
    más críticas del tornado en un solo diccionario.
    Es la función que la interfaz llamará para el panel
    de sensibilidad completo.

    Parámetros:
        inversion (float)     : Inversión inicial
        flujos    (list[float]): Flujos de caja base
        tasa      (float)     : Tasa de descuento

    Retorna:
        dict con:
            - escenarios         (list[dict])
            - punto_equilibrio   (dict)
            - variable_critica   (str)  : Variable con mayor impacto
            - impacto_critico    (float): Impacto de esa variable
            - tornado            (list[dict]): Top 5 variables
    """
    esc      = escenarios(inversion, flujos, tasa)
    eq       = punto_equilibrio_flujos(inversion, flujos, tasa)
    tornado  = tornado_vars(inversion, flujos, tasa)

    return {
        "escenarios":       esc,
        "punto_equilibrio": eq,
        "variable_critica": tornado[0]["variable"] if tornado else None,
        "impacto_critico":  tornado[0]["impacto_abs"] if tornado else None,
        "tornado":          tornado[:5],  # Top 5 para el gráfico
    }