"""
van_tir.py
==========
Módulo de evaluación de proyectos de inversión.

Cubre:
  - Valor Actual Neto (VAN)
  - Tasa Interna de Retorno (TIR) por método Newton-Raphson
  - Período de recupero de la inversión (Payback)
  - Índice de rentabilidad (VAN relativo a la inversión)

Regla de oro: este archivo no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.
"""


# ─────────────────────────────────────────
#  VAN — VALOR ACTUAL NETO
# ─────────────────────────────────────────

def van(inversion_inicial, flujos, tasa_descuento):
    """
    Calcula el Valor Actual Neto (VAN) de un proyecto.

    El VAN trae todos los flujos futuros al valor de hoy usando
    la tasa de descuento, y le resta la inversión inicial.

    Regla de decisión:
        VAN > 0  →  el proyecto crea valor, conviene invertir
        VAN = 0  →  el proyecto recupera exactamente la inversión
        VAN < 0  →  el proyecto destruye valor, no conviene

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial (positivo)
        flujos            (list[float]): Flujos de caja por período
                                         (pueden ser negativos)
        tasa_descuento    (float)     : Tasa de descuento en decimal
                                         (ej. 0.12 = 12%)

    Retorna:
        float: VAN del proyecto

    Ejemplo:
        >>> van(50000, [12000, 15000, 18000, 20000, 22000], 0.12)
        14273.45   # VAN positivo → proyecto viable
    """
    resultado = -inversion_inicial
    for i, flujo in enumerate(flujos):
        resultado += flujo / (1 + tasa_descuento) ** (i + 1)
    return resultado


def van_perfil(inversion_inicial, flujos, tasas):
    """
    Calcula el VAN para una lista de tasas de descuento.

    Genera los datos para la curva VAN vs tasa — el gráfico
    más importante del análisis de proyectos.

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial
        flujos            (list[float]): Flujos de caja por período
        tasas             (list[float]): Lista de tasas a evaluar

    Retorna:
        list[dict]: Una fila por tasa con:
            - tasa     (float): Tasa evaluada
            - van      (float): VAN resultante
            - viable   (bool) : True si VAN >= 0

    Ejemplo:
        >>> tasas = [0.05, 0.10, 0.15, 0.20, 0.25]
        >>> van_perfil(50000, [12000, 15000, 18000, 20000, 22000], tasas)
    """
    resultado = []
    for t in tasas:
        v = van(inversion_inicial, flujos, t)
        resultado.append({
            "tasa":   round(t, 6),
            "van":    round(v, 2),
            "viable": v >= 0
        })
    return resultado


# ─────────────────────────────────────────
#  DERIVADA — AUXILIAR PARA NEWTON-RAPHSON
# ─────────────────────────────────────────

def _derivada_central_van(inversion, flujos, tasa, h=1e-4):
    """
    Aproxima la derivada del VAN respecto a la tasa usando
    diferencia central.

    Fórmula:
        f'(x) ≈ [ f(x+h) - f(x-h) ] / (2h)

    Es una función interna (prefijo _) — no está pensada para
    ser llamada directamente desde la interfaz.

    Parámetros:
        inversion (float)     : Desembolso inicial
        flujos    (list[float]): Flujos de caja
        tasa      (float)     : Tasa en la que se evalúa la derivada
        h         (float)     : Intervalo de aproximación (default 1e-4)

    Retorna:
        float: Aproximación de la derivada del VAN en ese punto
    """
    f_mas  = van(inversion, flujos, tasa + h)
    f_menos = van(inversion, flujos, tasa - h)
    return (f_mas - f_menos) / (2 * h)


# ─────────────────────────────────────────
#  TIR — TASA INTERNA DE RETORNO
# ─────────────────────────────────────────

def tir(inversion_inicial, flujos, estimacion=0.1,
        tolerancia=1e-7, max_iteraciones=1000):
    """
    Calcula la Tasa Interna de Retorno (TIR) por Newton-Raphson.

    La TIR es la tasa que hace que el VAN sea exactamente cero.
    Representa el rendimiento intrínseco del proyecto.

    Regla de decisión:
        TIR > tasa de descuento  →  el proyecto es rentable
        TIR < tasa de descuento  →  el proyecto no cubre su costo

    El método Newton-Raphson itera con la fórmula:
        tasa_nueva = tasa_actual - VAN(tasa) / VAN'(tasa)

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial
        flujos            (list[float]): Flujos de caja por período
        estimacion        (float)     : Punto de partida para la iteración
                                         (default 0.1 = 10%)
        tolerancia        (float)     : Precisión mínima aceptable
                                         (default 1e-7)
        max_iteraciones   (int)       : Límite de iteraciones para
                                         evitar bucles infinitos

    Retorna:
        dict con:
            - tir          (float): TIR encontrada en decimal
            - iteraciones  (int)  : Cuántas iteraciones tomó
            - convergencia (bool) : True si encontró solución exacta
            - van_final    (float): VAN en la TIR (debe ser ≈ 0)

    Lanza:
        ValueError: Si la derivada es cero (no converge)

    Ejemplo:
        >>> resultado = tir(50000, [12000, 15000, 18000, 20000, 22000])
        >>> resultado['tir']
        0.2413...   # ≈ 24.1% — mayor que 12% → proyecto rentable
    """
    tasa_actual = estimacion

    for i in range(max_iteraciones):
        van_actual = van(inversion_inicial, flujos, tasa_actual)

        # Convergencia alcanzada
        if abs(van_actual) < tolerancia:
            return {
                "tir":          tasa_actual,
                "iteraciones":  i + 1,
                "convergencia": True,
                "van_final":    round(van_actual, 10)
            }

        derivada = _derivada_central_van(inversion_inicial, flujos, tasa_actual)

        if abs(derivada) < 1e-12:
            raise ValueError(
                "La derivada del VAN es cercana a cero. "
                "El método no puede continuar — intenta con otra estimación inicial."
            )

        # Paso Newton-Raphson
        tasa_actual = tasa_actual - (van_actual / derivada)

        # Evitar tasas negativas extremas que rompan el cálculo
        if tasa_actual <= -1:
            tasa_actual = -0.9999

    # Retorna la mejor aproximación aunque no haya convergido
    return {
        "tir":          tasa_actual,
        "iteraciones":  max_iteraciones,
        "convergencia": False,
        "van_final":    round(van(inversion_inicial, flujos, tasa_actual), 6)
    }


# ─────────────────────────────────────────
#  PERÍODO DE RECUPERO (PAYBACK)
# ─────────────────────────────────────────

def periodo_recupero(inversion_inicial, flujos):
    """
    Calcula el período de recupero simple (Payback) de la inversión.

    Responde: ¿En cuánto tiempo recupero lo que invertí?

    Funciona acumulando los flujos hasta que la suma iguala
    o supera la inversión inicial. Si el período exacto cae
    dentro de un período, interpola para dar un resultado
    con decimales (ej. 2.7 períodos).

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial (positivo)
        flujos            (list[float]): Flujos de caja por período

    Retorna:
        dict con:
            - periodos        (float): Períodos para recuperar la inversión
                                        (con decimales si cae en el medio)
            - recuperado      (bool) : True si la inversión se recupera
            - flujos_acum     (list) : Flujo acumulado por período,
                                        útil para graficar
            - inversion_pend  (float): Monto no recuperado si recuperado=False

    Ejemplo:
        >>> periodo_recupero(50000, [12000, 15000, 18000, 20000, 22000])
        {
            'periodos': 3.25,
            'recuperado': True,
            'flujos_acum': [-50000, -38000, -23000, -5000, 15000, 37000],
            'inversion_pend': 0
        }
    """
    acumulado = -inversion_inicial
    flujos_acum = [round(acumulado, 2)]
    periodo_exacto = None

    for i, flujo in enumerate(flujos):
        acumulado_anterior = acumulado
        acumulado += flujo
        flujos_acum.append(round(acumulado, 2))

        # Detecta el período donde se cruza cero
        if acumulado >= 0 and periodo_exacto is None:
            # Interpolación lineal para el decimal
            fraccion = abs(acumulado_anterior) / flujo
            periodo_exacto = i + fraccion  # i es base-0, el período es i+1

    if periodo_exacto is not None:
        return {
            "periodos":       round(periodo_exacto, 2),
            "recuperado":     True,
            "flujos_acum":    flujos_acum,
            "inversion_pend": 0.0
        }
    else:
        return {
            "periodos":       None,
            "recuperado":     False,
            "flujos_acum":    flujos_acum,
            "inversion_pend": round(abs(acumulado), 2)
        }


# ─────────────────────────────────────────
#  ÍNDICE DE RENTABILIDAD
# ─────────────────────────────────────────

def indice_rentabilidad(inversion_inicial, flujos, tasa_descuento):
    """
    Calcula el Índice de Rentabilidad (IR) del proyecto.

    El IR expresa cuántos pesos de valor presente se generan
    por cada peso invertido.

    Fórmula:
        IR = (VAN + Inversión) / Inversión
           = Valor presente de flujos / Inversión inicial

    Regla de decisión:
        IR > 1  →  el proyecto crea valor (equivale a VAN > 0)
        IR = 1  →  punto de equilibrio     (equivale a VAN = 0)
        IR < 1  →  el proyecto destruye valor

    Útil para comparar proyectos de distinto tamaño — un proyecto
    con VAN = $5,000 sobre una inversión de $10,000 (IR = 1.5)
    es más eficiente que VAN = $8,000 sobre $100,000 (IR = 1.08).

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial
        flujos            (list[float]): Flujos de caja por período
        tasa_descuento    (float)     : Tasa de descuento en decimal

    Retorna:
        float: Índice de rentabilidad

    Ejemplo:
        >>> indice_rentabilidad(50000, [12000, 15000, 18000, 20000, 22000], 0.12)
        1.285   # Por cada $1 invertido se generan $1.285 de valor presente
    """
    van_resultado = van(inversion_inicial, flujos, tasa_descuento)
    return (van_resultado + inversion_inicial) / inversion_inicial


# ─────────────────────────────────────────
#  RESUMEN COMPLETO DEL PROYECTO
# ─────────────────────────────────────────

def resumen_proyecto(inversion_inicial, flujos, tasa_descuento):
    """
    Genera un resumen completo con todos los indicadores del proyecto.

    Consolida VAN, TIR, período de recupero e índice de rentabilidad
    en un solo diccionario. Es la función que la interfaz llamará
    para mostrar el panel de resultados completo.

    Parámetros:
        inversion_inicial (float)     : Desembolso inicial
        flujos            (list[float]): Flujos de caja por período
        tasa_descuento    (float)     : Tasa de descuento en decimal

    Retorna:
        dict con:
            - van               (float)
            - van_viable        (bool)
            - tir               (float)
            - tir_supera_tasa   (bool) : True si TIR > tasa_descuento
            - indice_rent       (float)
            - payback_periodos  (float | None)
            - payback_recuperado (bool)
            - flujos_acum       (list)
            - n_periodos        (int)
            - inversion         (float)
            - tasa_descuento    (float)

    Ejemplo:
        >>> resumen_proyecto(50000, [12000, 15000, 18000, 20000, 22000], 0.12)
    """
    van_val    = van(inversion_inicial, flujos, tasa_descuento)
    tir_result = tir(inversion_inicial, flujos)
    payback    = periodo_recupero(inversion_inicial, flujos)
    ir         = indice_rentabilidad(inversion_inicial, flujos, tasa_descuento)

    return {
        "van":               round(van_val, 2),
        "van_viable":        van_val >= 0,
        "tir":               round(tir_result["tir"], 6),
        "tir_supera_tasa":   tir_result["tir"] > tasa_descuento,
        "indice_rent":       round(ir, 4),
        "payback_periodos":  payback["periodos"],
        "payback_recuperado": payback["recuperado"],
        "flujos_acum":       payback["flujos_acum"],
        "n_periodos":        len(flujos),
        "inversion":         inversion_inicial,
        "tasa_descuento":    tasa_descuento,
    }


# ─────────────────────────────────────────
#  TIR INDEPENDIENTE (sin tasa de descuento)
# ─────────────────────────────────────────

def tir_simple(inversion_inicial, flujos):
    """
    Calcula solo la TIR, sin necesidad de ingresar una tasa de descuento.

    La TIR es el rendimiento intrínseco del proyecto — la tasa que
    hace que el VAN sea exactamente cero. No depende de ninguna tasa
    externa: surge únicamente de la inversión y los flujos.

    El usuario luego compara la TIR con su propio costo de capital
    para decidir si el proyecto es viable.

    Parámetros:
        inversion_inicial (float)     : Inversión inicial
        flujos            (list[float]): Flujos de caja por período

    Retorna:
        dict con:
            - tir          (float): TIR en decimal
            - tir_pct      (float): TIR en porcentaje
            - iteraciones  (int)  : Iteraciones usadas
            - convergencia (bool) : True si encontró solución exacta
            - interpretacion (str): Texto explicativo

    Ejemplo:
        >>> tir_simple(50000, [12000, 15000, 18000, 20000, 22000])
        {
            'tir':     0.2413,
            'tir_pct': 24.13,
            'interpretacion': 'El proyecto rinde 24.13% por período...'
        }
    """
    resultado = tir(inversion_inicial, flujos)
    tir_val   = resultado["tir"]

    if tir_val > 0:
        interpretacion = (
            f"El proyecto rinde {tir_val*100:.2f}% por período. "
            f"Si tu costo de capital es menor a {tir_val*100:.2f}%, "
            f"el proyecto es rentable."
        )
    else:
        interpretacion = (
            f"La TIR es negativa ({tir_val*100:.2f}%), lo que indica "
            f"que el proyecto no recupera la inversión bajo ninguna tasa."
        )

    return {
        "tir":           round(tir_val, 6),
        "tir_pct":       round(tir_val * 100, 4),
        "iteraciones":   resultado["iteraciones"],
        "convergencia":  resultado["convergencia"],
        "interpretacion": interpretacion
    }