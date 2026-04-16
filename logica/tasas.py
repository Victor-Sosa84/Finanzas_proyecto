"""
tasas.py
========
Módulo de conversión y análisis de tasas de interés.

Cubre:
  - Conversión entre Tasa Nominal (TN) y Tasa Efectiva Anual (TEA)
  - Conversión entre períodos (anual, mensual, diario, etc.)
  - Tasa referencial y tasa real (ajustada por inflación)

Regla de oro: este archivo no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.
"""


# ─────────────────────────────────────────
#  CONVERSIÓN TN ↔ TEA
# ─────────────────────────────────────────

def tn_a_tea(tasa_nominal, capitalizaciones_por_anio):
    """
    Convierte una Tasa Nominal (TN) a Tasa Efectiva Anual (TEA).

    La TN es la tasa "anunciada" por los bancos. La TEA es la tasa
    real que terminas pagando o ganando, considerando la frecuencia
    de capitalización.

    Parámetros:
        tasa_nominal             (float): Tasa nominal anual en decimal
                                          (ej. 0.12 = 12% anual)
        capitalizaciones_por_anio (int) : Cuántas veces se capitaliza
                                          por año (ej. 12 = mensual,
                                          4 = trimestral, 365 = diario)

    Retorna:
        float: TEA en decimal

    Ejemplo:
        >>> tn_a_tea(0.12, 12)   # 12% nominal capitalizable mensualmente
        0.12682503...            # ≈ 12.68% efectivo anual
    """
    m = capitalizaciones_por_anio
    return (1 + tasa_nominal / m) ** m - 1


def tea_a_tn(tasa_efectiva_anual, capitalizaciones_por_anio):
    """
    Convierte una Tasa Efectiva Anual (TEA) a Tasa Nominal (TN).

    Operación inversa de tn_a_tea(). Útil cuando conoces la TEA
    y necesitas expresarla como tasa nominal para un período dado.

    Parámetros:
        tasa_efectiva_anual      (float): TEA en decimal
        capitalizaciones_por_anio (int) : Frecuencia de capitalización

    Retorna:
        float: Tasa nominal anual en decimal

    Ejemplo:
        >>> tea_a_tn(0.1268, 12)
        0.11999...   # ≈ 12% nominal
    """
    m = capitalizaciones_por_anio
    return m * ((1 + tasa_efectiva_anual) ** (1 / m) - 1)


# ─────────────────────────────────────────
#  CONVERSIÓN ENTRE PERÍODOS
# ─────────────────────────────────────────

# Factores estándar de períodos por año
PERIODOS_POR_ANIO = {
    "diario":      365,
    "semanal":     52,
    "quincenal":   24,
    "mensual":     12,
    "bimestral":   6,
    "trimestral":  4,
    "semestral":   2,
    "anual":       1,
}


def tea_a_tasa_periodo(tea, periodo):
    """
    Convierte una TEA a la tasa equivalente para un período específico.

    Útil cuando los flujos de caja son mensuales pero la tasa de
    descuento está expresada en términos anuales.

    Parámetros:
        tea    (float): Tasa Efectiva Anual en decimal
        periodo (str) : Nombre del período destino. Opciones:
                        "diario", "semanal", "quincenal", "mensual",
                        "bimestral", "trimestral", "semestral", "anual"

    Retorna:
        float: Tasa efectiva para el período solicitado

    Lanza:
        ValueError: Si el período no está en la lista de opciones

    Ejemplo:
        >>> tea_a_tasa_periodo(0.12, "mensual")
        0.00948879...   # ≈ 0.95% mensual
    """
    if periodo not in PERIODOS_POR_ANIO:
        opciones = list(PERIODOS_POR_ANIO.keys())
        raise ValueError(f"Período '{periodo}' no reconocido. Opciones: {opciones}")

    m = PERIODOS_POR_ANIO[periodo]
    return (1 + tea) ** (1 / m) - 1


def tasa_periodo_a_tea(tasa_periodo, periodo):
    """
    Convierte la tasa de un período específico a TEA.

    Operación inversa de tea_a_tasa_periodo().

    Parámetros:
        tasa_periodo (float): Tasa efectiva del período en decimal
        periodo       (str) : Nombre del período origen

    Retorna:
        float: TEA equivalente en decimal

    Ejemplo:
        >>> tasa_periodo_a_tea(0.0095, "mensual")
        0.11966...   # ≈ 11.97% anual
    """
    if periodo not in PERIODOS_POR_ANIO:
        opciones = list(PERIODOS_POR_ANIO.keys())
        raise ValueError(f"Período '{periodo}' no reconocido. Opciones: {opciones}")

    m = PERIODOS_POR_ANIO[periodo]
    return (1 + tasa_periodo) ** m - 1


def convertir_tasa(tasa, periodo_origen, periodo_destino):
    """
    Convierte una tasa de cualquier período a cualquier otro período.

    Hace la conversión en dos pasos internamente:
    período origen → TEA → período destino.

    Parámetros:
        tasa           (float): Tasa en decimal del período origen
        periodo_origen  (str) : Período de la tasa original
        periodo_destino (str) : Período al que se quiere convertir

    Retorna:
        float: Tasa equivalente en el período destino

    Ejemplo:
        >>> convertir_tasa(0.01, "mensual", "anual")
        0.12682...   # ≈ 12.68% anual

        >>> convertir_tasa(0.12, "anual", "mensual")
        0.00948...   # ≈ 0.95% mensual
    """
    tea = tasa_periodo_a_tea(tasa, periodo_origen)
    return tea_a_tasa_periodo(tea, periodo_destino)


# ─────────────────────────────────────────
#  TASA REFERENCIAL
# ─────────────────────────────────────────

def tasa_real(tasa_nominal_anual, inflacion_anual):
    """
    Calcula la tasa de interés real ajustada por inflación.

    Usa la fórmula de Fisher:
        tasa_real = (1 + tasa_nominal) / (1 + inflacion) - 1

    Una tasa real positiva significa que el dinero gana poder
    adquisitivo. Una tasa real negativa significa que la inflación
    supera el rendimiento — el dinero pierde valor real.

    Parámetros:
        tasa_nominal_anual (float): Tasa nominal anual en decimal
        inflacion_anual    (float): Inflación anual en decimal
                                    (ej. 0.08 = 8%)

    Retorna:
        float: Tasa real anual en decimal

    Ejemplo:
        >>> tasa_real(0.12, 0.08)
        0.03703...   # ≈ 3.7% real — el dinero sí crece en términos reales
    """
    return (1 + tasa_nominal_anual) / (1 + inflacion_anual) - 1


def spread(tasa_activa, tasa_pasiva):
    """
    Calcula el spread bancario (diferencial de tasas).

    El spread es la diferencia entre la tasa que cobra el banco
    por préstamos (activa) y la que paga por depósitos (pasiva).
    Representa el margen de ganancia del banco.

    Parámetros:
        tasa_activa (float): Tasa que cobra el banco (préstamos)
        tasa_pasiva (float): Tasa que paga el banco (depósitos/ahorros)

    Retorna:
        float: Spread en decimal

    Ejemplo:
        >>> spread(0.15, 0.04)
        0.11   # 11% de margen bancario
    """
    return tasa_activa - tasa_pasiva


def tabla_equivalencias(tea, periodos=None):
    """
    Genera una tabla con las tasas equivalentes para todos los períodos.

    Útil para mostrar en la interfaz cómo una TEA se expresa
    en diferentes frecuencias de tiempo.

    Parámetros:
        tea     (float)     : Tasa Efectiva Anual en decimal
        periodos (list[str]): Lista de períodos a incluir.
                              Si es None, incluye todos los disponibles.

    Retorna:
        list[dict]: Una fila por período con:
            - periodo (str)
            - tasa    (float): Tasa equivalente en decimal
            - tasa_pct (float): Tasa equivalente en porcentaje

    Ejemplo:
        >>> tabla_equivalencias(0.12)
        [
            {'periodo': 'diario',     'tasa': 0.000310, 'tasa_pct': 0.031},
            {'periodo': 'mensual',    'tasa': 0.009489, 'tasa_pct': 0.949},
            {'periodo': 'trimestral', 'tasa': 0.028737, 'tasa_pct': 2.874},
            ...
            {'periodo': 'anual',      'tasa': 0.120000, 'tasa_pct': 12.0},
        ]
    """
    if periodos is None:
        periodos = list(PERIODOS_POR_ANIO.keys())

    tabla = []
    for p in periodos:
        t = tea_a_tasa_periodo(tea, p)
        tabla.append({
            "periodo":   p,
            "tasa":      round(t, 6),
            "tasa_pct":  round(t * 100, 4)
        })
    return tabla