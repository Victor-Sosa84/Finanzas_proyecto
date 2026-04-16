"""
capital_startup.py
==================
Módulo de métricas financieras para startups.

Cubre:
  - Nota convertible y dilución del fundador (Situación 3)
  - Valor terminal con múltiplo de salida (Situación 6)
  - Línea de crédito revolving (Situación 5)

Regla de oro: no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.
"""


# ─────────────────────────────────────────
#  NOTA CONVERTIBLE Y DILUCIÓN (Situación 3)
# ─────────────────────────────────────────

def nota_convertible(inversion, valoracion_cap, descuento_pct,
                      acciones_fundador, precio_siguiente_ronda=None):
    """
    Calcula la conversión de una nota convertible y el porcentaje
    de dilución del fundador.

    Una nota convertible es deuda que se convierte en equity
    en la siguiente ronda de inversión, con dos beneficios
    para el inversor:
      - Valuation cap: convierte al menor entre cap y valoración real
      - Descuento: convierte a un precio menor al de nuevos inversores

    Parámetros:
        inversion              (float): Monto de la nota (deuda)
        valoracion_cap         (float): Valoración máxima para conversión
        descuento_pct          (float): Descuento sobre precio nueva ronda
                                        en decimal (ej. 0.20 = 20%)
        acciones_fundador      (int)  : Acciones actuales del fundador
        precio_siguiente_ronda (float): Precio por acción en próxima ronda
                                        Si None, se asume valoracion_cap

    Retorna:
        dict con:
            - precio_cap          (float): Precio de conversión por cap
            - precio_descuento    (float): Precio con descuento aplicado
            - precio_conversion   (float): El menor de los dos (más favorable
                                           para el inversor)
            - acciones_inversor   (float): Acciones que recibe el inversor
            - acciones_total      (float): Total acciones post conversión
            - pct_fundador        (float): % del fundador post conversión
            - pct_inversor        (float): % del inversor post conversión
            - dilución_fundador   (float): Puntos porcentuales perdidos

    Ejemplo:
        >>> nota_convertible(200000, 2000000, 0.20, 1000000)
        {
            'precio_conversion': 1.6,
            'acciones_inversor': 125000,
            'pct_fundador':      88.9,
            ...
        }
    """
    if precio_siguiente_ronda is None:
        precio_siguiente_ronda = valoracion_cap / acciones_fundador

    # Precio por cap
    precio_cap = valoracion_cap / acciones_fundador

    # Precio con descuento
    precio_desc = precio_siguiente_ronda * (1 - descuento_pct)

    # El inversor convierte al precio que le es más favorable (menor)
    precio_conv = min(precio_cap, precio_desc)

    # Acciones que recibe el inversor
    acciones_inversor = inversion / precio_conv

    # Total post conversión
    total_acciones = acciones_fundador + acciones_inversor

    pct_fundador  = (acciones_fundador  / total_acciones) * 100
    pct_inversor  = (acciones_inversor  / total_acciones) * 100
    dilucion      = 100 - pct_fundador  # fundador tenía 100% antes

    return {
        "precio_cap":         round(precio_cap, 4),
        "precio_descuento":   round(precio_desc, 4),
        "precio_conversion":  round(precio_conv, 4),
        "acciones_inversor":  round(acciones_inversor, 2),
        "acciones_fundador":  acciones_fundador,
        "acciones_total":     round(total_acciones, 2),
        "pct_fundador":       round(pct_fundador, 2),
        "pct_inversor":       round(pct_inversor, 2),
        "dilucion_fundador":  round(dilucion, 2),
        "mantiene_control":   pct_fundador >= 51
    }


def sensibilidad_nota_convertible(inversion, acciones_fundador,
                                   caps, descuentos,
                                   precio_siguiente_ronda=None):
    """
    Tabla de dilución para distintas combinaciones de cap y descuento.

    Responde: ¿Cuál combinación cap/descuento acepto sin bajar
    del 65% (o cualquier umbral) de propiedad? (Situación 3)

    Parámetros:
        inversion              (float)     : Monto de la nota
        acciones_fundador      (int)       : Acciones del fundador
        caps                   (list[float]): Valoraciones cap a evaluar
        descuentos             (list[float]): Descuentos a evaluar (decimal)
        precio_siguiente_ronda (float)     : Precio referencia

    Retorna:
        list[dict]: Una fila por combinación cap/descuento con
                    resultado de nota_convertible() más etiquetas
    """
    resultados = []
    for cap in caps:
        for desc in descuentos:
            res = nota_convertible(
                inversion, cap, desc,
                acciones_fundador, precio_siguiente_ronda
            )
            res["cap"]           = cap
            res["descuento_pct"] = round(desc * 100, 1)
            res["aceptable_65"]  = res["pct_fundador"] >= 65
            resultados.append(res)

    return resultados


# ─────────────────────────────────────────
#  VALOR TERMINAL CON MÚLTIPLO (Situación 6)
# ─────────────────────────────────────────

def valor_terminal_multiplo(inversion_hoy, multiple_salida,
                              anios, tasa_descuento):
    """
    Calcula el valor terminal de una startup usando múltiplo de salida
    y lo trae a valor presente.

    Responde: ¿Qué múltiplo mínimo justifica mi inversión hoy?

    Diferencia con capital_futuro():
        capital_futuro() usa tasa de crecimiento compuesto.
        Esta función usa múltiplo de mercado (ej. 6x revenue),
        que es como realmente se valoran las startups al salir.

    Parámetros:
        inversion_hoy   (float): Inversión actual
        multiple_salida (float): Múltiplo sobre la inversión al exit
                                  (ej. 6 = valor_exit = 6 * inversion)
        anios           (int)  : Años hasta el exit
        tasa_descuento  (float): Tasa de descuento en decimal

    Retorna:
        dict con:
            - valor_exit      (float): Valor al momento de la salida
            - valor_presente  (float): Valor traído a hoy
            - van_exit        (float): VAN del exit (valor_presente - inversion)
            - roi             (float): Retorno sobre inversión
            - tir_implicita   (float): TIR implícita del múltiplo
            - viable          (bool) : True si VAN > 0

    Ejemplo:
        >>> valor_terminal_multiplo(500000, 6, 5, 0.20)
        {
            'valor_exit':     3000000,
            'valor_presente': 1206290,
            'van_exit':       706290,
            'viable':         True
        }
    """
    valor_exit     = inversion_hoy * multiple_salida
    valor_presente = valor_exit / (1 + tasa_descuento) ** anios
    van_exit       = valor_presente - inversion_hoy
    roi            = (valor_exit - inversion_hoy) / inversion_hoy

    # TIR implícita: tasa que hace VP = inversión
    # valor_exit / (1 + tir)^n = inversion → tir = (valor_exit/inversion)^(1/n) - 1
    tir_implicita  = (multiple_salida ** (1 / anios)) - 1

    return {
        "valor_exit":     round(valor_exit, 2),
        "valor_presente": round(valor_presente, 2),
        "van_exit":       round(van_exit, 2),
        "roi":            round(roi, 4),
        "roi_pct":        round(roi * 100, 2),
        "tir_implicita":  round(tir_implicita, 6),
        "tir_implicita_pct": round(tir_implicita * 100, 2),
        "viable":         van_exit > 0,
        "multiple":       multiple_salida,
        "anios":          anios
    }


def multiplo_minimo_viable(inversion_hoy, anios, tasa_descuento):
    """
    Calcula el múltiplo mínimo de salida para que el VAN sea >= 0.

    Responde: ¿Qué múltiplo mínimo necesito para justificar
    la inversión hoy? (Situación 6)

    Fórmula directa:
        VP = inversion → valor_exit = inversion * (1 + tasa)^n
        multiple_min = (1 + tasa)^n

    Parámetros:
        inversion_hoy  (float): Inversión actual
        anios          (int)  : Años hasta el exit
        tasa_descuento (float): Tasa de descuento

    Retorna:
        dict con:
            - multiple_minimo (float): Múltiplo mínimo para VAN = 0
            - valor_exit_min  (float): Valor de exit mínimo requerido
    """
    multiple_min = (1 + tasa_descuento) ** anios
    valor_min    = inversion_hoy * multiple_min

    return {
        "multiple_minimo": round(multiple_min, 4),
        "valor_exit_min":  round(valor_min, 2)
    }


def sensibilidad_multiplos(inversion_hoy, anios, tasa_descuento,
                            multiples=None):
    """
    Tabla de VAN para distintos múltiplos de salida.

    Parámetros:
        inversion_hoy  (float)     : Inversión actual
        anios          (int)       : Años hasta el exit
        tasa_descuento (float)     : Tasa de descuento
        multiples      (list[float]): Múltiplos a evaluar
                                      (default: 4x, 6x, 8x, 10x)

    Retorna:
        list[dict]: Resultado de valor_terminal_multiplo() por múltiplo,
                    más el múltiplo mínimo viable como referencia
    """
    if multiples is None:
        multiples = [4, 6, 8, 10]

    min_viable = multiplo_minimo_viable(inversion_hoy, anios,
                                        tasa_descuento)
    resultados = []

    for m in multiples:
        res = valor_terminal_multiplo(inversion_hoy, m, anios,
                                      tasa_descuento)
        res["es_minimo_viable"] = abs(m - min_viable["multiple_minimo"]) < 0.5
        resultados.append(res)

    return {
        "tabla":           resultados,
        "multiple_minimo": min_viable["multiple_minimo"],
        "valor_exit_min":  min_viable["valor_exit_min"]
    }


# ─────────────────────────────────────────
#  LÍNEA DE CRÉDITO REVOLVING (Situación 5)
# ─────────────────────────────────────────

def costo_linea_revolving(monto_linea, tasa_anual, ingresos_mensuales,
                           opex_mensual):
    """
    Evalúa si una línea de crédito revolving genera valor neto
    para la empresa.

    Una línea revolving permite usar y repagar el crédito
    repetidamente. El costo es el interés sobre el monto usado.

    Parámetros:
        monto_linea        (float): Monto total de la línea disponible
        tasa_anual         (float): Tasa anual en decimal
        ingresos_mensuales (float): Ingresos operativos mensuales
        opex_mensual       (float): Costos operativos mensuales

    Retorna:
        dict con:
            - tasa_mensual      (float): Tasa mensual equivalente
            - costo_mensual     (float): Interés mensual sobre la línea
            - flujo_neto_ops    (float): Ingresos - OPEX (sin línea)
            - flujo_con_linea   (float): Flujo neto - costo de la línea
            - genera_valor      (bool) : True si flujo_con_linea > 0
            - ingreso_minimo    (float): Ingreso mínimo para que genere valor
            - cobertura_interes (float): Veces que el flujo cubre el interés

    Ejemplo:
        >>> costo_linea_revolving(300000, 0.18, 95000, 70000)
        {'genera_valor': True, 'cobertura_interes': 5.56, ...}
    """
    tasa_mensual    = (1 + tasa_anual) ** (1/12) - 1
    costo_mensual   = monto_linea * tasa_mensual
    flujo_neto_ops  = ingresos_mensuales - opex_mensual
    flujo_con_linea = flujo_neto_ops - costo_mensual

    # Ingreso mínimo para que flujo_con_linea = 0
    ingreso_minimo  = opex_mensual + costo_mensual

    cobertura = (flujo_neto_ops / costo_mensual) if costo_mensual > 0 else 0

    return {
        "tasa_mensual":      round(tasa_mensual, 6),
        "costo_mensual":     round(costo_mensual, 2),
        "flujo_neto_ops":    round(flujo_neto_ops, 2),
        "flujo_con_linea":   round(flujo_con_linea, 2),
        "genera_valor":      flujo_con_linea > 0,
        "ingreso_minimo":    round(ingreso_minimo, 2),
        "cobertura_interes": round(cobertura, 2)
    }


def sensibilidad_linea_revolving(monto_linea, tasa_anual, opex_mensual,
                                  ingresos_escenarios=None):
    """
    Tabla de viabilidad de línea revolving para distintos niveles
    de ingresos mensuales.

    Responde: ¿A qué ingreso mínimo la línea genera valor? (Situación 5)

    Parámetros:
        monto_linea          (float)     : Monto de la línea
        tasa_anual           (float)     : Tasa anual
        opex_mensual         (float)     : Costos operativos fijos
        ingresos_escenarios  (list[float]): Ingresos a evaluar
                                            (default: 80k,95k,110k,125k)

    Retorna:
        list[dict]: Resultado de costo_linea_revolving() por escenario
    """
    if ingresos_escenarios is None:
        ingresos_escenarios = [80000, 95000, 110000, 125000]

    return [
        {**costo_linea_revolving(monto_linea, tasa_anual,
                                  ing, opex_mensual),
         "ingresos": ing}
        for ing in ingresos_escenarios
    ]
