"""
capital.py
==========
Módulo de análisis de capital y liquidez empresarial.

Cubre:
  - Capital de Trabajo (liquidez neta disponible)
  - Capital de Operaciones (dinero necesario para operar hoy)
  - Índice de liquidez
  - CAPEX y OPEX como estructuras de datos para la interfaz

Regla de oro: este archivo no imprime nada, no abre ventanas,
no toca matplotlib. Solo recibe números y devuelve números.
"""


# ─────────────────────────────────────────
#  CAPITAL DE TRABAJO
# ─────────────────────────────────────────

def capital_trabajo(activo_corriente, pasivo_corriente):
    """
    Calcula el Capital de Trabajo (liquidez neta).

    Responde: ¿Cuánto dinero me sobra después de cubrir
    mis deudas a corto plazo?

    Fórmula:
        Capital de Trabajo = Activo Corriente - Pasivo Corriente

    Regla de decisión:
        CT > 0  →  la empresa tiene colchón financiero
        CT = 0  →  la empresa cubre justo sus obligaciones
        CT < 0  →  riesgo de insolvencia a corto plazo

    Parámetros:
        activo_corriente  (float): Dinero y bienes convertibles
                                   en efectivo en menos de 1 año
                                   (caja, cuentas por cobrar,
                                   inventario, inversiones corto plazo)
        pasivo_corriente  (float): Deudas y obligaciones a pagar
                                   en menos de 1 año
                                   (proveedores, préstamos corto plazo,
                                   impuestos por pagar)

    Retorna:
        float: Capital de trabajo (puede ser negativo)

    Ejemplo:
        >>> capital_trabajo(80000, 50000)
        30000.0   # Hay $30,000 de colchón financiero
    """
    return activo_corriente - pasivo_corriente


def capital_trabajo_detalle(caja, cuentas_por_cobrar, inventario,
                             proveedores, prestamos_corto_plazo,
                             otros_pasivos_corrientes=0):
    """
    Calcula el Capital de Trabajo a partir de sus componentes.

    Versión detallada de capital_trabajo() cuando el usuario
    ingresa cada componente por separado en lugar de los totales.

    Parámetros:
        caja                     (float): Efectivo disponible
        cuentas_por_cobrar       (float): Dinero que te deben clientes
        inventario               (float): Valor del stock disponible
        proveedores              (float): Deudas con proveedores
        prestamos_corto_plazo    (float): Préstamos a pagar en < 1 año
        otros_pasivos_corrientes (float): Otros pasivos corrientes

    Retorna:
        dict con:
            - activo_corriente  (float): Suma de activos
            - pasivo_corriente  (float): Suma de pasivos
            - capital_trabajo   (float): Diferencia
            - positivo          (bool) : True si CT > 0

    Ejemplo:
        >>> capital_trabajo_detalle(
        ...     caja=10000, cuentas_por_cobrar=30000, inventario=40000,
        ...     proveedores=20000, prestamos_corto_plazo=30000
        ... )
        {
            'activo_corriente': 80000,
            'pasivo_corriente': 50000,
            'capital_trabajo':  30000,
            'positivo': True
        }
    """
    activo  = caja + cuentas_por_cobrar + inventario
    pasivo  = proveedores + prestamos_corto_plazo + otros_pasivos_corrientes
    ct      = activo - pasivo

    return {
        "activo_corriente": round(activo, 2),
        "pasivo_corriente": round(pasivo, 2),
        "capital_trabajo":  round(ct, 2),
        "positivo":         ct > 0
    }


# ─────────────────────────────────────────
#  CAPITAL DE OPERACIONES (NOF)
# ─────────────────────────────────────────

def capital_operaciones(inventario, cuentas_por_cobrar, cuentas_por_pagar):
    """
    Calcula el Capital de Operaciones (Necesidades Operativas de Fondos).

    Responde: ¿Cuánto dinero necesito tener disponible para que
    el negocio siga operando hoy?

    Fórmula:
        Capital de Operaciones = Inventario + Cuentas por Cobrar
                                 - Cuentas por Pagar

    A diferencia del Capital de Trabajo, este indicador se enfoca
    exclusivamente en el ciclo operativo del negocio — lo que
    entra y sale por las operaciones diarias.

    Parámetros:
        inventario          (float): Valor del stock disponible
        cuentas_por_cobrar  (float): Lo que te deben los clientes
        cuentas_por_pagar   (float): Lo que debes a proveedores

    Retorna:
        float: Capital de operaciones necesario

    Ejemplo:
        >>> capital_operaciones(40000, 30000, 20000)
        50000.0   # Necesitas $50,000 disponibles para operar
    """
    return inventario + cuentas_por_cobrar - cuentas_por_pagar


# ─────────────────────────────────────────
#  ÍNDICES DE LIQUIDEZ
# ─────────────────────────────────────────

def indice_liquidez(activo_corriente, pasivo_corriente):
    """
    Calcula el Índice de Liquidez Corriente (Razón Corriente).

    Responde: ¿Por cada $1 de deuda a corto plazo,
    cuántos pesos tengo disponibles?

    Fórmula:
        IL = Activo Corriente / Pasivo Corriente

    Regla de decisión:
        IL > 1.5  →  liquidez saludable
        IL = 1    →  punto crítico, sin margen de error
        IL < 1    →  riesgo de no cubrir obligaciones

    Parámetros:
        activo_corriente (float): Total de activos corrientes
        pasivo_corriente (float): Total de pasivos corrientes

    Retorna:
        float: Índice de liquidez

    Lanza:
        ValueError: Si pasivo_corriente es cero

    Ejemplo:
        >>> indice_liquidez(80000, 50000)
        1.6   # Por cada $1 de deuda, tienes $1.60 disponibles
    """
    if pasivo_corriente == 0:
        raise ValueError("El pasivo corriente no puede ser cero.")
    return activo_corriente / pasivo_corriente


def indice_liquidez_acida(activo_corriente, inventario, pasivo_corriente):
    """
    Calcula el Índice de Liquidez Ácida (Prueba Ácida).

    Es más conservador que el índice corriente — excluye el
    inventario porque es el activo menos líquido (tarda más
    en convertirse en efectivo).

    Fórmula:
        ILA = (Activo Corriente - Inventario) / Pasivo Corriente

    Parámetros:
        activo_corriente (float): Total de activos corrientes
        inventario       (float): Valor del inventario
        pasivo_corriente (float): Total de pasivos corrientes

    Retorna:
        float: Índice de liquidez ácida

    Ejemplo:
        >>> indice_liquidez_acida(80000, 40000, 50000)
        0.8   # Sin inventario, no cubre las deudas — señal de alerta
    """
    if pasivo_corriente == 0:
        raise ValueError("El pasivo corriente no puede ser cero.")
    return (activo_corriente - inventario) / pasivo_corriente


# ─────────────────────────────────────────
#  CAPEX Y OPEX
# ─────────────────────────────────────────

def estructura_capex(items_capex):
    """
    Procesa una lista de ítems de inversión (CAPEX) y calcula el total.

    CAPEX (Capital Expenditure) = inversiones en activos fijos que
    generan valor a largo plazo: maquinaria, equipos, infraestructura,
    vehículos, software, etc.

    En el VAN, el CAPEX total es la inversión_inicial.

    Parámetros:
        items_capex (list[dict]): Lista de ítems, cada uno con:
            - nombre   (str)  : Descripción del activo
            - monto    (float): Costo del activo
            - vida_util (int) : Años de vida útil (opcional)

    Retorna:
        dict con:
            - items       (list[dict]): Lista original enriquecida
            - total_capex (float)     : Suma total de inversión
            - n_items     (int)       : Cantidad de ítems

    Ejemplo:
        >>> items = [
        ...     {"nombre": "Flota de motos",  "monto": 30000, "vida_util": 5},
        ...     {"nombre": "Software ERP",    "monto": 10000, "vida_util": 3},
        ...     {"nombre": "Adecuación local","monto": 10000, "vida_util": 10},
        ... ]
        >>> estructura_capex(items)
        {'total_capex': 50000, 'n_items': 3, ...}
    """
    total = sum(item["monto"] for item in items_capex)
    return {
        "items":       items_capex,
        "total_capex": round(total, 2),
        "n_items":     len(items_capex)
    }


def estructura_opex(items_opex, periodos):
    """
    Procesa una lista de costos operativos (OPEX) y genera los
    flujos de caja negativos para cada período.

    OPEX (Operational Expenditure) = costos recurrentes para
    mantener el negocio operando: salarios, alquiler, servicios,
    marketing, mantenimiento, etc.

    En el VAN, el OPEX por período se resta a los ingresos
    para obtener el flujo neto de cada período.

    Parámetros:
        items_opex (list[dict]): Lista de costos, cada uno con:
            - nombre  (str)  : Descripción del costo
            - monto   (float): Costo por período
        periodos   (int)     : Número de períodos del proyecto

    Retorna:
        dict con:
            - items        (list[dict]): Lista original
            - opex_periodo (float)     : Total OPEX por período
            - flujos_opex  (list[float]): OPEX como flujos negativos
                                          (uno por período)
            - total_opex   (float)     : OPEX acumulado del proyecto

    Ejemplo:
        >>> items = [
        ...     {"nombre": "Salarios",    "monto": 8000},
        ...     {"nombre": "Alquiler",    "monto": 2000},
        ...     {"nombre": "Servicios",   "monto": 500},
        ... ]
        >>> estructura_opex(items, periodos=5)
        {'opex_periodo': 10500, 'flujos_opex': [-10500, -10500, ...], ...}
    """
    opex_periodo = sum(item["monto"] for item in items_opex)
    flujos_opex  = [-round(opex_periodo, 2)] * periodos

    return {
        "items":        items_opex,
        "opex_periodo": round(opex_periodo, 2),
        "flujos_opex":  flujos_opex,
        "total_opex":   round(opex_periodo * periodos, 2)
    }


def flujos_netos(ingresos_por_periodo, opex_por_periodo):
    """
    Calcula los flujos de caja netos restando el OPEX a los ingresos.

    Los flujos netos son los que se pasan a van() y tir().

    Parámetros:
        ingresos_por_periodo (list[float]): Ingresos estimados por período
        opex_por_periodo     (float)      : OPEX fijo por período

    Retorna:
        list[float]: Flujos netos por período

    Ejemplo:
        >>> flujos_netos([20000, 22000, 25000, 28000, 30000], 10500)
        [9500, 11500, 14500, 17500, 19500]
    """
    return [round(ingreso - opex_por_periodo, 2)
            for ingreso in ingresos_por_periodo]


# ─────────────────────────────────────────
#  RESUMEN DE CAPITAL
# ─────────────────────────────────────────

def resumen_capital(activo_corriente, pasivo_corriente,
                    inventario, cuentas_por_cobrar, cuentas_por_pagar):
    """
    Genera un resumen completo de los indicadores de capital.

    Consolida Capital de Trabajo, Capital de Operaciones e
    Índices de Liquidez en un solo diccionario.
    Es la función que la interfaz llamará para el panel de capital.

    Parámetros:
        activo_corriente    (float): Total activos corrientes
        pasivo_corriente    (float): Total pasivos corrientes
        inventario          (float): Valor del inventario
        cuentas_por_cobrar  (float): Lo que deben los clientes
        cuentas_por_pagar   (float): Lo que se debe a proveedores

    Retorna:
        dict con todos los indicadores calculados y sus
        interpretaciones booleanas para la interfaz.
    """
    ct  = capital_trabajo(activo_corriente, pasivo_corriente)
    co  = capital_operaciones(inventario, cuentas_por_cobrar,
                               cuentas_por_pagar)
    il  = indice_liquidez(activo_corriente, pasivo_corriente)
    ila = indice_liquidez_acida(activo_corriente, inventario,
                                 pasivo_corriente)

    return {
        "capital_trabajo":        round(ct, 2),
        "capital_trabajo_ok":     ct > 0,
        "capital_operaciones":    round(co, 2),
        "indice_liquidez":        round(il, 4),
        "liquidez_saludable":     il >= 1.5,
        "indice_liquidez_acida":  round(ila, 4),
        "liquidez_acida_ok":      ila >= 1.0,
        "activo_corriente":       activo_corriente,
        "pasivo_corriente":       pasivo_corriente,
    }


# ─────────────────────────────────────────
#  BURN RATE Y RUNWAY
# ─────────────────────────────────────────

def burn_rate(gastos_totales, periodos):
    """
    Calcula el Burn Rate — cuánto dinero gasta la empresa por período.

    Responde: ¿Cuánto estoy quemando de capital por mes (o período)?

    Parámetros:
        gastos_totales (float): Total de gastos en el rango analizado
        periodos       (int)  : Número de períodos del rango

    Retorna:
        float: Gasto promedio por período

    Ejemplo:
        >>> burn_rate(90000, 6)
        15000.0   # se gastan $15,000 por período
    """
    if periodos <= 0:
        raise ValueError("Los períodos deben ser mayores a cero.")
    return round(gastos_totales / periodos, 2)


def runway(capital_disponible, burn_rate_periodo):
    """
    Calcula el Runway — cuántos períodos le quedan a la empresa
    antes de quedarse sin dinero.

    Responde: ¿Cuánto tiempo puedo operar con el capital que tengo?

    Parámetros:
        capital_disponible  (float): Dinero disponible en caja
        burn_rate_periodo   (float): Gasto por período (burn rate)

    Retorna:
        dict con:
            - periodos   (float): Períodos de vida restantes
            - viable     (bool) : False si burn_rate <= 0
            - alerta     (str)  : Nivel de alerta según períodos restantes

    Ejemplo:
        >>> runway(90000, 15000)
        {'periodos': 6.0, 'viable': True, 'alerta': 'critico'}
    """
    if burn_rate_periodo <= 0:
        raise ValueError("El burn rate debe ser mayor a cero.")

    periodos = capital_disponible / burn_rate_periodo

    if periodos <= 3:
        alerta = "critico"
    elif periodos <= 6:
        alerta = "advertencia"
    else:
        alerta = "saludable"

    return {
        "periodos": round(periodos, 2),
        "viable":   True,
        "alerta":   alerta
    }


def resumen_runway(capital_disponible, gastos_historicos, periodos_historicos):
    """
    Calcula Burn Rate y Runway en una sola llamada.

    Parámetros:
        capital_disponible    (float): Dinero disponible actualmente
        gastos_historicos     (float): Total gastado en períodos pasados
        periodos_historicos   (int)  : Períodos analizados para el burn rate

    Retorna:
        dict con:
            - burn_rate       (float): Gasto promedio por período
            - runway_periodos (float): Períodos restantes
            - alerta          (str)  : "saludable", "advertencia" o "critico"
            - capital         (float): Capital disponible
    """
    br = burn_rate(gastos_historicos, periodos_historicos)
    rw = runway(capital_disponible, br)

    return {
        "burn_rate":       br,
        "runway_periodos": rw["periodos"],
        "alerta":          rw["alerta"],
        "capital":         capital_disponible
    }


# ─────────────────────────────────────────
#  VAN DE COSTOS
# ─────────────────────────────────────────

def van_costos(inversion_inicial, costos_por_periodo, tasa_descuento):
    """
    Calcula el VAN de Costos para evaluar proyectos donde no hay
    ingresos sino solo gastos.

    Útil para comparar dos opciones de inversión por su costo total:
    la opción con VAN de costos menos negativo es la más eficiente.

    Los costos se ingresan como valores positivos — la función los
    convierte en flujos negativos internamente.

    Parámetros:
        inversion_inicial   (float)     : Inversión inicial (positivo)
        costos_por_periodo  (list[float]): Costos por período (positivos)
        tasa_descuento      (float)     : Tasa de descuento en decimal

    Retorna:
        dict con:
            - van_costos      (float): VAN negativo — menos negativo = mejor
            - costo_total     (float): Suma simple de todos los costos
            - costo_presente  (float): Valor presente de los costos futuros
            - periodos        (int)  : Número de períodos

    Ejemplo:
        >>> van_costos(50000, [10000, 10000, 10000], 0.12)
        {
            'van_costos':     -74018.0,
            'costo_total':    -80000.0,
            'costo_presente': -24018.0,
            'periodos':       3
        }
    """
    costo_presente = 0
    for i, costo in enumerate(costos_por_periodo):
        costo_presente += costo / (1 + tasa_descuento) ** (i + 1)

    van_c = -(inversion_inicial + costo_presente)

    return {
        "van_costos":     round(van_c, 2),
        "costo_total":    round(-(inversion_inicial +
                                  sum(costos_por_periodo)), 2),
        "costo_presente": round(-costo_presente, 2),
        "periodos":       len(costos_por_periodo)
    }


def comparar_van_costos(opciones, tasa_descuento):
    """
    Compara múltiples opciones por su VAN de costos.

    La opción con VAN de costos menos negativo es la más eficiente.

    Parámetros:
        opciones        (list[dict]): Lista de opciones, cada una con:
            - nombre    (str)       : Nombre de la opción
            - inversion (float)     : Inversión inicial
            - costos    (list[float]): Costos por período
        tasa_descuento  (float)     : Tasa de descuento

    Retorna:
        list[dict]: Opciones ordenadas de menor a mayor costo
                    (la primera es la más eficiente), cada una con
                    los resultados de van_costos() más el nombre
                    y un flag 'es_mejor'.
    """
    resultados = []
    for opcion in opciones:
        res = van_costos(
            opcion["inversion"],
            opcion["costos"],
            tasa_descuento
        )
        res["nombre"] = opcion["nombre"]
        resultados.append(res)

    # Ordenar: menos negativo primero = más eficiente
    resultados.sort(key=lambda x: x["van_costos"], reverse=True)

    for i, r in enumerate(resultados):
        r["es_mejor"] = (i == 0)

    return resultados


# ─────────────────────────────────────────
#  BURN RATE NETO (Situación 1)
# ─────────────────────────────────────────

def burn_rate_neto(burn_fijo, ingresos_periodo):
    """
    Burn Rate Neto = gasto fijo - ingresos reales del período.
    Si es negativo, la empresa genera caja (break-even superado).
    """
    burn_neto  = burn_fijo - ingresos_periodo
    break_even = ingresos_periodo >= burn_fijo
    cobertura  = (ingresos_periodo / burn_fijo * 100) if burn_fijo > 0 else 0
    return {
        "burn_bruto":    round(burn_fijo, 2),
        "ingresos":      round(ingresos_periodo, 2),
        "burn_neto":     round(burn_neto, 2),
        "break_even":    break_even,
        "cobertura_pct": round(cobertura, 2)
    }


def runway_con_ingresos(capital_disponible, burn_fijo,
                         ingresos_base, factor_ingresos=1.0):
    """
    Runway real considerando ingresos variables.
    factor_ingresos=0.6 simula caída del 40% en ingresos.
    """
    ingresos_reales = ingresos_base * factor_ingresos
    bn        = burn_rate_neto(burn_fijo, ingresos_reales)
    burn_neto = bn["burn_neto"]

    if burn_neto <= 0:
        return {
            "ingresos_reales":  round(ingresos_reales, 2),
            "burn_neto":        round(burn_neto, 2),
            "runway_periodos":  None,
            "break_even":       True,
            "alerta":           "superavit",
            "factor":           factor_ingresos,
            "cobertura_pct":    bn["cobertura_pct"]
        }

    periodos = capital_disponible / burn_neto
    alerta   = "critico" if periodos <= 3 else (
               "advertencia" if periodos <= 6 else "saludable")

    return {
        "ingresos_reales":  round(ingresos_reales, 2),
        "burn_neto":        round(burn_neto, 2),
        "runway_periodos":  round(periodos, 2),
        "break_even":       False,
        "alerta":           alerta,
        "factor":           factor_ingresos,
        "cobertura_pct":    bn["cobertura_pct"]
    }


def sensibilidad_runway(capital_disponible, burn_fijo,
                         ingresos_base, factores=None):
    """
    Tabla de runway para múltiples escenarios de ingresos.
    Responde: ¿Cuál es el escenario mínimo viable para N períodos?
    """
    if factores is None:
        factores = [0.60, 0.80, 1.00, 1.20]
    return [
        runway_con_ingresos(capital_disponible, burn_fijo,
                             ingresos_base, f)
        for f in factores
    ]


# ─────────────────────────────────────────
#  CICLO DE CONVERSIÓN DE EFECTIVO (Situación 4)
# ─────────────────────────────────────────

def ciclo_conversion_efectivo(dias_cobro, dias_inventario, dias_pago):
    """
    CCE = Días Cobro + Días Inventario - Días Pago.
    CCE positivo = empresa financia a clientes (necesita capital).
    CCE negativo = proveedores financian a la empresa (ideal).
    """
    cce = dias_cobro + dias_inventario - dias_pago

    if cce <= 0:
        interpretacion = (
            f"CCE favorable: los proveedores te financian {abs(cce)} dias. "
            f"No necesitas capital externo para el ciclo operativo."
        )
    else:
        interpretacion = (
            f"Necesitas financiar {cce} dias de operacion propia. "
            f"Reducir dias de cobro o aumentar dias de pago mejora el CCE."
        )

    return {
        "cce":             cce,
        "dias_cobro":      dias_cobro,
        "dias_inventario": dias_inventario,
        "dias_pago":       dias_pago,
        "favorable":       cce <= 0,
        "interpretacion":  interpretacion
    }


def necesidad_capital_cce(ventas_diarias, cce):
    """Capital necesario para financiar el ciclo de efectivo."""
    capital = ventas_diarias * max(cce, 0)
    return {
        "capital_necesario": round(capital, 2),
        "ventas_diarias":    round(ventas_diarias, 2),
        "cce":               cce
    }


def sensibilidad_cce(ventas_mensuales, dias_inventario, dias_pago,
                      rangos_cobro=None):
    """
    Tabla de CCE para distintos plazos de cobro.
    Responde: cuantos dias maximo puedes tolerar sin prestamo externo.
    """
    if rangos_cobro is None:
        rangos_cobro = [45, 60, 75, 90]

    ventas_diarias = ventas_mensuales / 30
    resultados     = []

    for dias_cobro in rangos_cobro:
        cce_res = ciclo_conversion_efectivo(dias_cobro, dias_inventario,
                                             dias_pago)
        cap_res = necesidad_capital_cce(ventas_diarias, cce_res["cce"])
        resultados.append({
            "dias_cobro":        dias_cobro,
            "cce":               cce_res["cce"],
            "favorable":         cce_res["favorable"],
            "capital_necesario": cap_res["capital_necesario"],
            "interpretacion":    cce_res["interpretacion"]
        })

    return resultados