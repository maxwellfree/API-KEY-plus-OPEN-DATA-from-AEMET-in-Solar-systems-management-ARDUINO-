#!/usr/bin/env python3
"""
dispatch.py

Despacho horario sostenible-predictivo.

================================================================
OBJETIVO
================================================================

Este módulo genera el plan operativo horario del sistema:

    - autoconsumo FV;
    - compra de red;
    - venta de excedentes;
    - carga de batería;
    - descarga de batería;
    - evolución del SOC.

La filosofía principal es preservar la vida útil de la batería.

La batería NO se utiliza simplemente porque:

    - exista déficit;
    - el precio sea alto;
    - exista excedente FV.

Antes de utilizarla se evalúa:

    1. necesidad energética futura;
    2. valor económico futuro;
    3. SOC disponible;
    4. profundidad de ciclo;
    5. coste equivalente de degradación;
    6. reserva deseada para el final del día.

================================================================
JERARQUÍA SOSTENIBLE
================================================================

1. AUTOCONSUMO DIRECTO

2. DESPLAZAMIENTO DE CARGAS
   Se gestiona principalmente desde optimizer.py.

3. RED
   Se utiliza si el coste de ciclar batería no está justificado.

4. CARGA DE BATERÍA
   Solo hasta alcanzar la reserva futura necesaria.

5. DESCARGA DE BATERÍA
   Solo cuando el valor de evitar una compra compensa el coste
   de degradación y existe SOC por encima de la reserva.

6. VENTA DE EXCEDENTES
   Cuando no existe necesidad razonable de almacenar energía.

================================================================
MODELO PREDICTIVO
================================================================

El algoritmo mira el horizonte restante:

    E_deficit_futuro =
        suma de déficits horarios posteriores

pero no todos los déficits se consideran igualmente interesantes.

Cada déficit futuro se pondera según:

    - precio de compra;
    - coste de degradación;
    - eficiencia de ciclo.

Se calcula una energía objetivo de batería suficiente para cubrir
solo los déficits futuros que realmente merece la pena evitar.

Esto evita el comportamiento:

    SOC 60 % -> 45 % -> 85 %

si no existe una necesidad energética real para hacerlo.

Autor: Enrique M. Moreno Pérez
"""

import math


# ==========================================================
# Parámetros de sostenibilidad
# ==========================================================

# ----------------------------------------------------------
# Coste equivalente de degradación
# ----------------------------------------------------------
#
# Representa un coste interno ficticio por cada kWh descargado.
#
# No es un precio de mercado.
#
# Sirve para evitar utilizar batería por ahorros económicos
# marginales.
#
# Valor inicial provisional.

COSTE_DEGRADACION_EUR_KWH = 0.06


# ----------------------------------------------------------
# Margen adicional
# ----------------------------------------------------------
#
# Incluso después de descontar degradación se exige un pequeño
# margen económico antes de decidir descargar.

MARGEN_DESCARGA_EUR_KWH = 0.02


# ----------------------------------------------------------
# SOC preferente
# ----------------------------------------------------------

SOC_RESERVA_BASE = 0.40


# ----------------------------------------------------------
# SOC máximo predictivo
# ----------------------------------------------------------
#
# Aunque config.py permita llegar a 85 %, no queremos hacerlo
# automáticamente si el horizonte futuro no lo necesita.

SOC_MAX_PREDICTIVO = 0.80


# ----------------------------------------------------------
# SOC objetivo al final del día
# ----------------------------------------------------------
#
# Valor inicial.
#
# Posteriormente podrá depender de la previsión del día siguiente.

SOC_OBJETIVO_FIN_DIA = 0.55


# ==========================================================
# Utilidades
# ==========================================================

def limitar(
    valor,
    minimo,
    maximo,
):
    """
    Limita un valor a un intervalo.
    """

    return max(
        minimo,
        min(
            maximo,
            valor,
        ),
    )


# ==========================================================
# Eficiencias de batería
# ==========================================================

def obtener_eficiencias_bateria(
    bateria,
):
    """
    Separa la eficiencia de ciclo en carga y descarga.

    Si:

        eta_ciclo = eta_carga * eta_descarga

    y suponemos simetría:

        eta_carga = eta_descarga = sqrt(eta_ciclo)
    """

    eficiencia_ciclo = float(
        bateria.get(
            "eficiencia_ciclo",
            0.90,
        )
    )

    eficiencia = math.sqrt(
        eficiencia_ciclo
    )

    return (
        eficiencia,
        eficiencia,
    )


# ==========================================================
# Valor económico de descargar batería
# ==========================================================

def beneficio_descarga_por_kwh(
    precio_compra,
    eficiencia_descarga,
):
    """
    Calcula el beneficio económico aproximado de descargar
    batería para evitar una compra de red.

    Se descuenta:

        - pérdida energética;
        - coste equivalente de degradación.
    """

    valor_util = (
        precio_compra
        * eficiencia_descarga
    )

    beneficio = (
        valor_util
        - COSTE_DEGRADACION_EUR_KWH
    )

    return beneficio


def merece_descargar(
    precio_compra,
    eficiencia_descarga,
):
    """
    Decide si merece la pena descargar batería.

    La descarga solo se permite si el beneficio neto supera
    un margen mínimo.
    """

    beneficio = beneficio_descarga_por_kwh(
        precio_compra,
        eficiencia_descarga,
    )

    return (
        beneficio
        >= MARGEN_DESCARGA_EUR_KWH
    )


# ==========================================================
# Déficit futuro valioso
# ==========================================================

def calcular_deficit_futuro_valioso(
    balance,
    indice_actual,
    eficiencia_descarga,
):
    """
    Calcula la energía futura que potencialmente merece ser
    cubierta mediante batería.

    Solo se suman déficits futuros en horas en las que:

        precio_compra
        * eficiencia_descarga
        - coste_degradacion

    supera el margen sostenible.
    """

    energia = 0.0

    for registro in balance[
        indice_actual + 1:
    ]:

        deficit = float(
            registro.get(
                "energia_deficit_kwh",
                0.0,
            )
        )

        if deficit <= 0.0:
            continue

        precio = float(
            registro.get(
                "precio_compra",
                0.0,
            )
        )

        if merece_descargar(
            precio,
            eficiencia_descarga,
        ):

            energia += deficit

    return energia


# ==========================================================
# Precio máximo futuro
# ==========================================================

def obtener_precio_maximo_futuro(
    balance,
    indice_actual,
):
    """
    Obtiene el máximo precio de compra restante.
    """

    futuros = balance[
        indice_actual + 1:
    ]

    if not futuros:
        return None

    return max(
        float(
            r.get(
                "precio_compra",
                0.0,
            )
        )
        for r in futuros
    )


# ==========================================================
# Precio venta actual frente al valor futuro
# ==========================================================

def merece_almacenar_excedente(
    precio_venta_actual,
    precio_compra_futuro,
    eficiencia_ciclo,
):
    """
    Decide si almacenar un excedente tiene valor suficiente.

    Valor de vender ahora:

        V_venta = precio_venta

    Valor aproximado de conservarlo:

        V_futuro =
            precio_compra_futuro
            * eficiencia_ciclo

    Se descuenta además degradación.
    """

    if precio_compra_futuro is None:
        return False

    valor_futuro = (
        precio_compra_futuro
        * eficiencia_ciclo
        - COSTE_DEGRADACION_EUR_KWH
    )

    ventaja = (
        valor_futuro
        - precio_venta_actual
    )

    return (
        ventaja
        >= 0.0
    )


# ==========================================================
# SOC objetivo predictivo
# ==========================================================

def calcular_soc_objetivo(
    soc_actual,
    energia_nominal_kwh,
    energia_deficit_futuro_kwh,
    eficiencia_descarga,
    soc_min,
    soc_max,
):
    """
    Calcula el SOC que sería suficiente para cubrir el déficit
    futuro considerado valioso.

    Energía interna necesaria:

        E_int =
            E_deficit / eta_descarga

    SOC necesario:

        SOC_necesario =
            SOC_reserva
            + E_int / E_nominal

    El resultado se limita por:

        - SOC mínimo;
        - reserva sostenible;
        - SOC máximo predictivo;
        - SOC máximo técnico.
    """

    soc_reserva = max(
        soc_min,
        SOC_RESERVA_BASE,
    )

    energia_interna_necesaria = (
        energia_deficit_futuro_kwh
        / eficiencia_descarga
        if eficiencia_descarga > 0
        else 0.0
    )

    soc_necesario = (
        soc_reserva
        + energia_interna_necesaria
        / energia_nominal_kwh
    )

    soc_max_efectivo = min(
        soc_max,
        SOC_MAX_PREDICTIVO,
    )

    return limitar(
        soc_necesario,
        soc_reserva,
        soc_max_efectivo,
    )


# ==========================================================
# Reserva mínima dinámica
# ==========================================================

def calcular_soc_reserva_dinamica(
    indice_actual,
    total_horas,
    soc_min,
):
    """
    Reserva mínima dinámica.

    Durante buena parte del día se mantiene al menos la reserva
    base.

    Cerca del final del horizonte se intenta no terminar por debajo
    del SOC objetivo final.
    """

    soc_reserva = max(
        soc_min,
        SOC_RESERVA_BASE,
    )

    horas_restantes = (
        total_horas
        - indice_actual
        - 1
    )

    # Durante las últimas horas preservamos más SOC.
    if horas_restantes <= 3:

        soc_reserva = max(
            soc_reserva,
            SOC_OBJETIVO_FIN_DIA,
        )

    return soc_reserva


# ==========================================================
# Generación del plan sostenible predictivo
# ==========================================================

def generar_plan_sostenible_predictivo(
    balance,
    configuracion,
    soc_inicial,
):
    """
    Genera un plan horario sostenible-predictivo.

    La decisión se realiza secuencialmente pero utilizando
    información del horizonte futuro.
    """

    bateria = configuracion[
        "bateria"
    ]

    energia_nominal_kwh = float(
        bateria[
            "energia_total_kwh"
        ]
    )

    soc_min = float(
        bateria[
            "soc_min_normal"
        ]
    )

    soc_max = float(
        bateria[
            "soc_max_normal"
        ]
    )

    eficiencia_ciclo = float(
        bateria.get(
            "eficiencia_ciclo",
            0.90,
        )
    )

    (
        eficiencia_carga,
        eficiencia_descarga,
    ) = obtener_eficiencias_bateria(
        bateria
    )

    potencia_carga_max = float(
        bateria.get(
            "potencia_carga_preferida_kw",
            999.0,
        )
    )

    potencia_descarga_max = float(
        bateria.get(
            "potencia_descarga_preferida_kw",
            999.0,
        )
    )

    soc = limitar(
        float(soc_inicial),
        soc_min,
        soc_max,
    )

    plan = []

    total_horas = len(
        balance
    )

    # ======================================================
    # Simulación secuencial
    # ======================================================

    for indice, registro in enumerate(
        balance
    ):

        hora = registro[
            "hora"
        ]

        demanda = float(
            registro[
                "demanda_kw"
            ]
        )

        fv = float(
            registro[
                "fv_kw"
            ]
        )

        excedente = float(
            registro[
                "excedente_kw"
            ]
        )

        deficit = float(
            registro[
                "deficit_kw"
            ]
        )

        precio_compra = float(
            registro[
                "precio_compra"
            ]
        )

        precio_venta = float(
            registro[
                "precio_venta"
            ]
        )

        soc_inicio = soc

        autoconsumo = min(
            demanda,
            fv,
        )

        carga_bateria = 0.0
        descarga_bateria = 0.0
        compra_red = 0.0
        venta_red = 0.0

        acciones = []
        razones = []

        # ==================================================
        # Autoconsumo directo
        # ==================================================

        if autoconsumo > 0.0:

            acciones.append(
                "AUTOCONSUMO"
            )

        # ==================================================
        # Calcular horizonte futuro
        # ==================================================

        deficit_futuro_valioso = (
            calcular_deficit_futuro_valioso(
                balance,
                indice,
                eficiencia_descarga,
            )
        )

        soc_objetivo = calcular_soc_objetivo(
            soc_actual=soc,
            energia_nominal_kwh=energia_nominal_kwh,
            energia_deficit_futuro_kwh=deficit_futuro_valioso,
            eficiencia_descarga=eficiencia_descarga,
            soc_min=soc_min,
            soc_max=soc_max,
        )

        precio_maximo_futuro = (
            obtener_precio_maximo_futuro(
                balance,
                indice,
            )
        )

        # ==================================================
        # CASO A: excedente FV
        # ==================================================

        if excedente > 0.0:

            debe_almacenar = (
                merece_almacenar_excedente(
                    precio_venta_actual=precio_venta,
                    precio_compra_futuro=precio_maximo_futuro,
                    eficiencia_ciclo=eficiencia_ciclo,
                )
            )

            # ------------------------------------------------
            # Solo cargamos hasta SOC objetivo
            # ------------------------------------------------

            if (
                debe_almacenar
                and soc < soc_objetivo
            ):

                energia_interna_faltante = (
                    (
                        soc_objetivo
                        - soc
                    )
                    * energia_nominal_kwh
                )

                energia_entrada_necesaria = (
                    energia_interna_faltante
                    / eficiencia_carga
                )

                carga_bateria = min(
                    excedente,
                    energia_entrada_necesaria,
                    potencia_carga_max,
                )

                energia_guardada = (
                    carga_bateria
                    * eficiencia_carga
                )

                soc += (
                    energia_guardada
                    / energia_nominal_kwh
                )

                if carga_bateria > 0.0:

                    acciones.append(
                        "CARGAR_BATERIA"
                    )

                    razones.append(
                        "Se carga únicamente hasta el SOC "
                        "necesario para cubrir déficits futuros "
                        "económicamente justificables."
                    )

            # ------------------------------------------------
            # Excedente restante -> venta
            # ------------------------------------------------

            excedente_restante = (
                excedente
                - carga_bateria
            )

            if excedente_restante > 0.0:

                venta_red = (
                    excedente_restante
                )

                acciones.append(
                    "VENDER"
                )

                if soc >= soc_objetivo:

                    razones.append(
                        "La reserva energética prevista ya es "
                        "suficiente; se evita sobrecargar "
                        "innecesariamente la batería."
                    )

        # ==================================================
        # CASO B: déficit
        # ==================================================

        elif deficit > 0.0:

            soc_reserva = (
                calcular_soc_reserva_dinamica(
                    indice_actual=indice,
                    total_horas=total_horas,
                    soc_min=soc_min,
                )
            )

            descargar = merece_descargar(
                precio_compra,
                eficiencia_descarga,
            )

            energia_disponible_interna = max(
                0.0,
                (
                    soc
                    - soc_reserva
                )
                * energia_nominal_kwh
            )

            energia_salida_disponible = (
                energia_disponible_interna
                * eficiencia_descarga
            )

            if (
                descargar
                and energia_salida_disponible > 0.0
            ):

                descarga_bateria = min(
                    deficit,
                    energia_salida_disponible,
                    potencia_descarga_max,
                )

                energia_extraida = (
                    descarga_bateria
                    / eficiencia_descarga
                )

                soc -= (
                    energia_extraida
                    / energia_nominal_kwh
                )

                if descarga_bateria > 0.0:

                    acciones.append(
                        "DESCARGAR_BATERIA"
                    )

                    razones.append(
                        "El ahorro de compra supera el coste "
                        "equivalente de degradación y existe "
                        "SOC por encima de la reserva."
                    )

            deficit_restante = (
                deficit
                - descarga_bateria
            )

            if deficit_restante > 0.0:

                compra_red = (
                    deficit_restante
                )

                acciones.append(
                    "COMPRAR_RED"
                )

                if not descargar:

                    razones.append(
                        "El ahorro potencial no justifica "
                        "degradar la batería."
                    )

        # ==================================================
        # CASO C: equilibrio
        # ==================================================

        else:

            if not acciones:

                acciones.append(
                    "EQUILIBRIO"
                )

        # ==================================================
        # Seguridad SOC
        # ==================================================

        soc = limitar(
            soc,
            soc_min,
            soc_max,
        )

        # ==================================================
        # Economía
        # ==================================================

        coste_compra = (
            compra_red
            * precio_compra
        )

        ingreso_venta = (
            venta_red
            * precio_venta
        )

        coste_neto = (
            coste_compra
            - ingreso_venta
        )

        # ==================================================
        # Registro
        # ==================================================

        plan.append(
            {
                "hora": hora,

                "demanda_kw": round(
                    demanda,
                    4,
                ),

                "fv_kw": round(
                    fv,
                    4,
                ),

                "precio_compra": (
                    precio_compra
                ),

                "precio_venta": (
                    precio_venta
                ),

                "soc_inicio": round(
                    soc_inicio,
                    4,
                ),

                "soc_objetivo": round(
                    soc_objetivo,
                    4,
                ),

                "soc_fin": round(
                    soc,
                    4,
                ),

                "autoconsumo_kw": round(
                    autoconsumo,
                    4,
                ),

                "carga_bateria_kw": round(
                    carga_bateria,
                    4,
                ),

                "descarga_bateria_kw": round(
                    descarga_bateria,
                    4,
                ),

                "compra_red_kw": round(
                    compra_red,
                    4,
                ),

                "venta_red_kw": round(
                    venta_red,
                    4,
                ),

                "deficit_futuro_valioso_kwh": round(
                    deficit_futuro_valioso,
                    4,
                ),

                "accion": (
                    " + ".join(
                        acciones
                    )
                ),

                "razon": (
                    " ".join(
                        razones
                    )
                ),

                "coste_compra_eur": round(
                    coste_compra,
                    5,
                ),

                "ingreso_venta_eur": round(
                    ingreso_venta,
                    5,
                ),

                "coste_neto_eur": round(
                    coste_neto,
                    5,
                ),
            }
        )

    return plan


# ==========================================================
# Métricas
# ==========================================================

def calcular_metricas_plan(
    plan,
    configuracion,
):
    """
    Calcula las métricas agregadas del despacho.
    """

    bateria = configuracion[
        "bateria"
    ]

    energia_nominal = float(
        bateria[
            "energia_total_kwh"
        ]
    )

    energia_cargada = sum(
        r[
            "carga_bateria_kw"
        ]
        for r in plan
    )

    energia_descargada = sum(
        r[
            "descarga_bateria_kw"
        ]
        for r in plan
    )

    compra_red = sum(
        r[
            "compra_red_kw"
        ]
        for r in plan
    )

    venta_red = sum(
        r[
            "venta_red_kw"
        ]
        for r in plan
    )

    coste_compra = sum(
        r[
            "coste_compra_eur"
        ]
        for r in plan
    )

    ingreso_venta = sum(
        r[
            "ingreso_venta_eur"
        ]
        for r in plan
    )

    energia_ciclada = (
        energia_cargada
        + energia_descargada
    )

    ciclos_equivalentes = (
        energia_ciclada
        / (
            2.0
            * energia_nominal
        )
        if energia_nominal > 0
        else 0.0
    )

    soc_minimo = min(
        (
            r[
                "soc_fin"
            ]
            for r in plan
        ),
        default=None,
    )

    soc_maximo = max(
        (
            r[
                "soc_fin"
            ]
            for r in plan
        ),
        default=None,
    )

    return {
        "energia_cargada_bateria_kwh": round(
            energia_cargada,
            3,
        ),

        "energia_descargada_bateria_kwh": round(
            energia_descargada,
            3,
        ),

        "energia_ciclada_bateria_kwh": round(
            energia_ciclada,
            3,
        ),

        "ciclos_equivalentes": round(
            ciclos_equivalentes,
            4,
        ),

        "compra_red_kwh": round(
            compra_red,
            3,
        ),

        "venta_red_kwh": round(
            venta_red,
            3,
        ),

        "coste_compra_eur": round(
            coste_compra,
            4,
        ),

        "ingreso_venta_eur": round(
            ingreso_venta,
            4,
        ),

        "coste_neto_eur": round(
            coste_compra
            - ingreso_venta,
            4,
        ),

        "soc_final": (
            plan[-1][
                "soc_fin"
            ]
            if plan
            else None
        ),

        "soc_minimo": (
            soc_minimo
        ),

        "soc_maximo": (
            soc_maximo
        ),
    }


# ==========================================================
# Presentación
# ==========================================================

def mostrar_plan_horario(
    plan,
):
    """
    Muestra el plan horario.
    """

    print()
    print("Plan horario sostenible-predictivo")
    print("----------------------------------")

    print(
        f"{'Hora':<7}"
        f"{'FV':>7}"
        f"{'Dem':>7}"
        f"{'SOC':>8}"
        f"{'SOCobj':>8}"
        f"{'Red+':>8}"
        f"{'Red-':>8}"
        f"{'Bat+':>8}"
        f"{'Bat-':>8}"
        f"  Acción"
    )

    print(
        "-" * 98
    )

    for r in plan:

        print(
            f"{r['hora']:<7}"
            f"{r['fv_kw']:>7.2f}"
            f"{r['demanda_kw']:>7.2f}"
            f"{r['soc_fin'] * 100:>7.1f}%"
            f"{r['soc_objetivo'] * 100:>7.1f}%"
            f"{r['compra_red_kw']:>8.2f}"
            f"{r['venta_red_kw']:>8.2f}"
            f"{r['carga_bateria_kw']:>8.2f}"
            f"{r['descarga_bateria_kw']:>8.2f}"
            f"  {r['accion']}"
        )


def mostrar_resumen_plan(
    metricas,
):
    """
    Presenta las métricas del plan sostenible-predictivo.
    """

    print()
    print("Resumen del despacho sostenible")
    print("-------------------------------")

    print(
        f"Carga de batería          : "
        f"{metricas['energia_cargada_bateria_kwh']:.2f} kWh"
    )

    print(
        f"Descarga de batería       : "
        f"{metricas['energia_descargada_bateria_kwh']:.2f} kWh"
    )

    print(
        f"Energía ciclada           : "
        f"{metricas['energia_ciclada_bateria_kwh']:.2f} kWh"
    )

    print(
        f"Ciclos equivalentes       : "
        f"{metricas['ciclos_equivalentes']:.3f}"
    )

    print(
        f"Compra de red             : "
        f"{metricas['compra_red_kwh']:.2f} kWh"
    )

    print(
        f"Venta a red               : "
        f"{metricas['venta_red_kwh']:.2f} kWh"
    )

    print(
        f"Coste de compra           : "
        f"{metricas['coste_compra_eur']:.3f} €"
    )

    print(
        f"Ingreso por venta         : "
        f"{metricas['ingreso_venta_eur']:.3f} €"
    )

    print(
        f"Balance económico neto    : "
        f"{metricas['coste_neto_eur']:.3f} €"
    )

    if metricas[
        "soc_final"
    ] is not None:

        print(
            f"SOC final previsto        : "
            f"{metricas['soc_final'] * 100:.1f} %"
        )

    if metricas[
        "soc_minimo"
    ] is not None:

        print(
            f"SOC mínimo previsto       : "
            f"{metricas['soc_minimo'] * 100:.1f} %"
        )

    if metricas[
        "soc_maximo"
    ] is not None:

        print(
            f"SOC máximo previsto       : "
            f"{metricas['soc_maximo'] * 100:.1f} %"
        )
