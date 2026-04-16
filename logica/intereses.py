"""
intereses.py
============
Módulo de cálculo de interés simple, compuesto, capital futuro
y tabla de amortización.

Regla de oro: este archivo no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.
"""


# ─────────────────────────────────────────
#  INTERÉS SIMPLE
# ─────────────────────────────────────────

def interes_simple(capital, tasa, periodos):
    """
    Calcula el interés generado con interés simple.

    El interés siempre se calcula sobre el capital original,
    nunca se acumula.

    Parámetros:
        capital  (float): Capital inicial (ej. 10000)
        tasa     (float): Tasa por período en decimal (ej. 0.05 = 5%)
        periodos (int)  : Número de períodos

    Retorna:
        float: Interés total generado (no incluye el capital)

    Ejemplo:
        >>> interes_simple(10000, 0.05, 3)
        1500.0
    """
    return capital * tasa * periodos


def monto_simple(capital, tasa, periodos):
    """
    Calcula el monto final con interés simple.

    Monto = Capital + Interés simple

    Parámetros:
        capital  (float): Capital inicial
        tasa     (float): Tasa por período en decimal
        periodos (int)  : Número de períodos

    Retorna:
        float: Monto final (capital + intereses)

    Ejemplo:
        >>> monto_simple(10000, 0.05, 3)
        11500.0
    """
    return capital * (1 + tasa * periodos)


# ─────────────────────────────────────────
#  INTERÉS COMPUESTO
# ─────────────────────────────────────────

def interes_compuesto(capital, tasa, periodos):
    """
    Calcula el interés generado con interés compuesto.

    Los intereses se acumulan cada período — cada vez ganan
    intereses sobre los intereses anteriores.

    Parámetros:
        capital  (float): Capital inicial
        tasa     (float): Tasa por período en decimal (ej. 0.05 = 5%)
        periodos (int)  : Número de períodos

    Retorna:
        float: Interés total generado (no incluye el capital)

    Ejemplo:
        >>> interes_compuesto(10000, 0.05, 3)
        1576.25
    """
    monto = capital * (1 + tasa) ** periodos
    return monto - capital


def capital_futuro(capital, tasa, periodos):
    """
    Calcula el monto final con interés compuesto (Capital Futuro).

    Responde: ¿Cuánto valdré en el futuro si invierto hoy?

    Parámetros:
        capital  (float): Capital inicial (valor presente)
        tasa     (float): Tasa por período en decimal
        periodos (int)  : Número de períodos

    Retorna:
        float: Capital futuro (monto final)

    Ejemplo:
        >>> capital_futuro(10000, 0.05, 3)
        11576.25
    """
    return capital * (1 + tasa) ** periodos


def capital_presente(monto_futuro, tasa, periodos):
    """
    Calcula el valor presente dado un monto futuro (descuento).

    Responde: ¿Cuánto vale hoy un dinero que recibiré en el futuro?
    Es la operación inversa de capital_futuro().

    Parámetros:
        monto_futuro (float): Valor que se recibirá en el futuro
        tasa         (float): Tasa por período en decimal
        periodos     (int)  : Número de períodos

    Retorna:
        float: Valor presente

    Ejemplo:
        >>> capital_presente(11576.25, 0.05, 3)
        10000.0
    """
    return monto_futuro / (1 + tasa) ** periodos


# ─────────────────────────────────────────
#  COMPARACIÓN SIMPLE VS COMPUESTO
# ─────────────────────────────────────────

def comparar_simple_vs_compuesto(capital, tasa, periodos):
    """
    Genera una tabla comparativa período a período entre
    interés simple e interés compuesto.

    Útil para visualizar gráficamente la diferencia en el tiempo.

    Parámetros:
        capital  (float): Capital inicial
        tasa     (float): Tasa por período en decimal
        periodos (int)  : Número de períodos

    Retorna:
        list[dict]: Lista con claves:
            - periodo     (int)
            - monto_simple    (float)
            - monto_compuesto (float)
            - diferencia      (float): compuesto - simple

    Ejemplo:
        >>> comparar_simple_vs_compuesto(10000, 0.05, 3)
        [
            {'periodo': 1, 'monto_simple': 10500.0, 'monto_compuesto': 10500.0,   'diferencia': 0.0},
            {'periodo': 2, 'monto_simple': 11000.0, 'monto_compuesto': 11025.0,   'diferencia': 25.0},
            {'periodo': 3, 'monto_simple': 11500.0, 'monto_compuesto': 11576.25,  'diferencia': 76.25},
        ]
    """
    tabla = []
    for i in range(1, periodos + 1):
        ms = monto_simple(capital, tasa, i)
        mc = capital_futuro(capital, tasa, i)
        tabla.append({
            "periodo":          i,
            "monto_simple":     round(ms, 2),
            "monto_compuesto":  round(mc, 2),
            "diferencia":       round(mc - ms, 2)
        })
    return tabla


# ─────────────────────────────────────────
#  TABLA DE AMORTIZACIÓN
# ─────────────────────────────────────────

def tabla_amortizacion(capital, tasa_periodo, n_periodos):
    """
    Genera la tabla de amortización de un préstamo (sistema francés).

    En cada período la cuota es fija, pero la proporción entre
    interés y amortización varía: al inicio se paga más interés,
    al final más capital.

    Parámetros:
        capital       (float): Monto del préstamo
        tasa_periodo  (float): Tasa de interés por período en decimal
                               (si la tasa es anual y los pagos son
                               mensuales, dividir entre 12)
        n_periodos    (int)  : Número total de cuotas

    Retorna:
        dict con:
            - cuota_fija (float): Valor de cada cuota
            - tabla (list[dict]): Una fila por período con:
                - periodo       (int)
                - cuota         (float)
                - interes       (float): Parte de la cuota que es interés
                - amortizacion  (float): Parte que reduce el capital
                - saldo         (float): Capital restante después del pago

    Ejemplo:
        >>> resultado = tabla_amortizacion(10000, 0.01, 12)
        >>> resultado['cuota_fija']
        888.49
    """
    # Fórmula de cuota fija (sistema francés)
    cuota = capital * tasa_periodo / (1 - (1 + tasa_periodo) ** -n_periodos)

    saldo = capital
    filas = []

    for i in range(1, n_periodos + 1):
        interes      = saldo * tasa_periodo
        amortizacion = cuota - interes
        saldo        = saldo - amortizacion

        # Evitar saldo negativo por redondeo en el último período
        if i == n_periodos:
            saldo = 0.0

        filas.append({
            "periodo":      i,
            "cuota":        round(cuota, 2),
            "interes":      round(interes, 2),
            "amortizacion": round(amortizacion, 2),
            "saldo":        round(max(saldo, 0), 2)
        })

    return {
        "cuota_fija": round(cuota, 2),
        "tabla":      filas
    }


# ─────────────────────────────────────────
#  PERÍODOS POR CUOTA
# ─────────────────────────────────────────

import math

def periodos_por_cuota(capital, tasa_periodo, cuota_deseada):
    """
    Calcula cuántos períodos necesitas para pagar un préstamo
    dado que solo puedes pagar una cuota fija determinada.

    Responde: "Solo puedo pagar $X por período,
               ¿en cuántas cuotas termino de pagar?"

    Fórmula de despeje de n:
        n = -ln(1 - (C * i) / M) / ln(1 + i)

    Parámetros:
        capital        (float): Monto del préstamo
        tasa_periodo   (float): Tasa por período en decimal
        cuota_deseada  (float): Cuota máxima que puedes pagar

    Retorna:
        dict con:
            - periodos       (int)  : Períodos necesarios (redondeado arriba)
            - cuota_exacta   (float): Cuota exacta para ese número de períodos
            - total_pagado   (float): Total pagado al final
            - total_intereses(float): Total de intereses pagados
            - viable         (bool) : False si la cuota no cubre
                                      ni los intereses mínimos

    Lanza:
        ValueError: Si la cuota deseada es menor o igual a cero

    Ejemplo:
        >>> periodos_por_cuota(10000, 0.01, 500)
        {
            'periodos':        23,
            'cuota_exacta':    488.49,
            'total_pagado':    11235.27,
            'total_intereses': 1235.27,
            'viable':          True
        }
    """
    if cuota_deseada <= 0:
        raise ValueError("La cuota deseada debe ser mayor a cero.")

    interes_minimo = capital * tasa_periodo

    if cuota_deseada <= interes_minimo:
        return {
            "periodos":        None,
            "cuota_exacta":    None,
            "total_pagado":    None,
            "total_intereses": None,
            "viable":          False,
            "mensaje":         f"La cuota debe ser mayor a ${interes_minimo:,.2f} "
                               f"(interés mínimo del primer período)."
        }

    n = -math.log(1 - (capital * tasa_periodo) / cuota_deseada) \
        / math.log(1 + tasa_periodo)
    n_entero = math.ceil(n)

    # Cuota exacta para ese número exacto de períodos
    cuota_exacta = capital * tasa_periodo / \
                   (1 - (1 + tasa_periodo) ** -n_entero)

    total_pagado    = round(cuota_exacta * n_entero, 2)
    total_intereses = round(total_pagado - capital, 2)

    return {
        "periodos":        n_entero,
        "cuota_exacta":    round(cuota_exacta, 2),
        "total_pagado":    total_pagado,
        "total_intereses": total_intereses,
        "viable":          True,
        "mensaje":         None
    }


# ─────────────────────────────────────────
#  VALOR TERMINAL CON MÚLTIPLO (acceso directo)
# ─────────────────────────────────────────

def valor_terminal(capital, multiple):
    """
    Calcula el valor terminal simple usando un múltiplo de salida.

    Diferencia con capital_futuro():
        capital_futuro() proyecta con tasa de interés compuesto.
        valor_terminal() usa múltiplo de mercado — cómo se valoran
        las startups en la práctica (ej. 6x revenue, 10x EBITDA).

    Para análisis completo con VAN y TIR implícita, usa
    capital_startup.valor_terminal_multiplo().

    Parámetros:
        capital  (float): Inversión o métrica base (revenue, EBITDA, etc.)
        multiple (float): Múltiplo de salida

    Retorna:
        float: Valor terminal

    Ejemplo:
        >>> valor_terminal(500000, 6)
        3000000.0
    """
    return round(capital * multiple, 2)