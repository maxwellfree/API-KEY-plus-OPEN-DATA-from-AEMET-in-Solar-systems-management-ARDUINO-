#!/usr/bin/env python3
"""
balance.py

Balance horario entre:

    - demanda doméstica;
    - generación fotovoltaica;
    - precios eléctricos de compra;
    - precio de compensación de excedentes.

================================================================
OBJETIVO
================================================================

Este módulo construye el balance energético ANTES de introducir
la batería.

Así podemos conocer primero cuál sería el comportamiento natural
de la instalación:

    FV -> autoconsumo directo
    déficit -> red
    excedente -> vertido

Esta referencia será posteriormente comparada con las estrategias
que utilizan almacenamiento.

================================================================
BALANCE ENERGÉTICO
================================================================

Para cada hora:

    P_balance =
        P_FV
        - P_demanda

Si:

    P_balance > 0

existe excedente:

    P_excedente = P_balance

Si:

    P_balance < 0

existe déficit:

    P_deficit = -P_balance

El autoconsumo directo es:

    P_autoconsumo =
        min(
            P_FV,
            P_demanda
        )

Como el paso temporal actual es una hora:

    energía [kWh]
        =
    potencia media [kW] * 1 h

================================================================
BALANCE ECONÓMICO SIN BATERÍA
================================================================

El déficit se compra de la red:

    coste_red =
        E_deficit
        * precio_compra

El excedente se vende:

    ingreso_excedente =
        E_excedente
        * precio_venta

El coste neto horario es:

    coste_neto =
        coste_red
        - ingreso_excedente

================================================================
IMPORTANTE
================================================================

Este módulo NO decide todavía:

    - carga de batería;
    - descarga de batería;
    - arbitraje;
    - preservación del SOC;
    - desplazamiento óptimo de cargas.

Eso corresponde a optimizer.py.

balance.py proporciona simplemente la referencia física y
económica previa al almacenamiento.

Autor: Enrique M. Moreno Pérez
"""


# ==========================================================
# Construcción de índices horarios
# ==========================================================

def indexar_por_hora(
    registros,
):
    """
    Convierte una lista de registros horarios en un diccionario:

        {
            "00:00": registro,
            ...
            "23:00": registro
        }

    Parameters
    ----------
    registros : list

    Returns
    -------
    dict
    """

    resultado = {}

    for registro in registros or []:

        hora = registro.get(
            "hora"
        )

        if hora is None:
            continue

        resultado[
            hora
        ] = registro

    return resultado


# ==========================================================
# Balance horario
# ==========================================================

def calcular_balance_horario(
    perfil_demanda,
    perfil_fv,
    precios,
):
    """
    Cruza demanda, FV y precios.

    Parameters
    ----------
    perfil_demanda : list
        Perfil generado por demand.py.

    perfil_fv : list
        Perfil generado por solar.py.

    precios : list
        Precios horarios generados por esios.py.

    Returns
    -------
    list
        Balance horario de 24 horas.
    """

    demanda_horas = indexar_por_hora(
        perfil_demanda
    )

    fv_horas = indexar_por_hora(
        perfil_fv
    )

    precios_horas = indexar_por_hora(
        precios
    )

    balance = []

    # ======================================================
    # Recorrido de las 24 horas
    # ======================================================

    for hora_entera in range(24):

        hora = (
            f"{hora_entera:02d}:00"
        )

        # --------------------------------------------------
        # Demanda
        # --------------------------------------------------

        registro_demanda = demanda_horas.get(
            hora,
            {},
        )

        potencia_demanda = float(
            registro_demanda.get(
                "potencia_total_kw",
                0.0,
            )
        )

        # --------------------------------------------------
        # Generación FV
        # --------------------------------------------------

        registro_fv = fv_horas.get(
            hora,
            {},
        )

        potencia_fv = float(
            registro_fv.get(
                "potencia_fv_kw",
                0.0,
            )
        )

        # --------------------------------------------------
        # Precios
        # --------------------------------------------------

        registro_precio = precios_horas.get(
            hora,
            {},
        )

        precio_compra = float(
            registro_precio.get(
                "compra",
                0.0,
            )
        )

        precio_venta = float(
            registro_precio.get(
                "venta",
                0.0,
            )
        )

        # --------------------------------------------------
        # Balance físico
        # --------------------------------------------------

        potencia_balance = (
            potencia_fv
            - potencia_demanda
        )

        potencia_autoconsumo = min(
            potencia_fv,
            potencia_demanda,
        )

        potencia_excedente = max(
            0.0,
            potencia_balance,
        )

        potencia_deficit = max(
            0.0,
            -potencia_balance,
        )

        # --------------------------------------------------
        # Energías
        # --------------------------------------------------
        #
        # Paso temporal actual:
        #
        #     Delta t = 1 hora
        #
        # Por tanto numéricamente kW -> kWh.

        energia_demanda = (
            potencia_demanda
        )

        energia_fv = (
            potencia_fv
        )

        energia_autoconsumo = (
            potencia_autoconsumo
        )

        energia_excedente = (
            potencia_excedente
        )

        energia_deficit = (
            potencia_deficit
        )

        # --------------------------------------------------
        # Economía sin batería
        # --------------------------------------------------

        coste_compra_red = (
            energia_deficit
            * precio_compra
        )

        ingreso_excedentes = (
            energia_excedente
            * precio_venta
        )

        coste_neto = (
            coste_compra_red
            - ingreso_excedentes
        )

        # --------------------------------------------------
        # Valor del autoconsumo
        # --------------------------------------------------
        #
        # Cada kWh autoconsumido evita comprarlo a la red.

        valor_autoconsumo = (
            energia_autoconsumo
            * precio_compra
        )

        # --------------------------------------------------
        # Diferencia compra / venta
        # --------------------------------------------------
        #
        # Mide el valor económico potencial de conservar
        # localmente un kWh en lugar de venderlo.
        #
        # Todavía NO significa que deba cargarse la batería:
        # habrá que descontar eficiencia y degradación.

        diferencial = (
            precio_compra
            - precio_venta
        )

        # --------------------------------------------------
        # Registro final
        # --------------------------------------------------

        balance.append(
            {
                "hora": hora,

                # Física.
                "demanda_kw": round(
                    potencia_demanda,
                    4,
                ),

                "fv_kw": round(
                    potencia_fv,
                    4,
                ),

                "balance_kw": round(
                    potencia_balance,
                    4,
                ),

                "autoconsumo_kw": round(
                    potencia_autoconsumo,
                    4,
                ),

                "excedente_kw": round(
                    potencia_excedente,
                    4,
                ),

                "deficit_kw": round(
                    potencia_deficit,
                    4,
                ),

                # Energía.
                "energia_demanda_kwh": round(
                    energia_demanda,
                    4,
                ),

                "energia_fv_kwh": round(
                    energia_fv,
                    4,
                ),

                "energia_autoconsumo_kwh": round(
                    energia_autoconsumo,
                    4,
                ),

                "energia_excedente_kwh": round(
                    energia_excedente,
                    4,
                ),

                "energia_deficit_kwh": round(
                    energia_deficit,
                    4,
                ),

                # Economía.
                "precio_compra": (
                    precio_compra
                ),

                "precio_venta": (
                    precio_venta
                ),

                "diferencia_compra_venta": (
                    diferencial
                ),

                "coste_compra_red_eur": round(
                    coste_compra_red,
                    5,
                ),

                "ingreso_excedentes_eur": round(
                    ingreso_excedentes,
                    5,
                ),

                "coste_neto_eur": round(
                    coste_neto,
                    5,
                ),

                "valor_autoconsumo_eur": round(
                    valor_autoconsumo,
                    5,
                ),
            }
        )

    return balance


# ==========================================================
# Métricas diarias
# ==========================================================

def calcular_metricas_balance(
    balance,
):
    """
    Calcula métricas diarias del balance FV-demanda.

    Returns
    -------
    dict
    """

    energia_demanda = sum(
        r[
            "energia_demanda_kwh"
        ]
        for r in balance
    )

    energia_fv = sum(
        r[
            "energia_fv_kwh"
        ]
        for r in balance
    )

    autoconsumo = sum(
        r[
            "energia_autoconsumo_kwh"
        ]
        for r in balance
    )

    excedentes = sum(
        r[
            "energia_excedente_kwh"
        ]
        for r in balance
    )

    deficit = sum(
        r[
            "energia_deficit_kwh"
        ]
        for r in balance
    )

    coste_red = sum(
        r[
            "coste_compra_red_eur"
        ]
        for r in balance
    )

    ingreso_excedentes = sum(
        r[
            "ingreso_excedentes_eur"
        ]
        for r in balance
    )

    valor_autoconsumo = sum(
        r[
            "valor_autoconsumo_eur"
        ]
        for r in balance
    )

    coste_neto = (
        coste_red
        - ingreso_excedentes
    )

    # ------------------------------------------------------
    # Ratio de autoconsumo
    # ------------------------------------------------------
    #
    # Porcentaje de la generación FV consumida directamente.

    if energia_fv > 0.0:

        ratio_autoconsumo = (
            autoconsumo
            / energia_fv
        )

    else:

        ratio_autoconsumo = 0.0

    # ------------------------------------------------------
    # Autosuficiencia
    # ------------------------------------------------------
    #
    # Porcentaje de la demanda cubierta directamente por FV.

    if energia_demanda > 0.0:

        autosuficiencia = (
            autoconsumo
            / energia_demanda
        )

    else:

        autosuficiencia = 0.0

    return {
        "energia_demanda_kwh": round(
            energia_demanda,
            3,
        ),

        "energia_fv_kwh": round(
            energia_fv,
            3,
        ),

        "autoconsumo_directo_kwh": round(
            autoconsumo,
            3,
        ),

        "excedentes_kwh": round(
            excedentes,
            3,
        ),

        "deficit_kwh": round(
            deficit,
            3,
        ),

        "ratio_autoconsumo": round(
            ratio_autoconsumo,
            4,
        ),

        "autosuficiencia": round(
            autosuficiencia,
            4,
        ),

        "coste_red_eur": round(
            coste_red,
            4,
        ),

        "ingreso_excedentes_eur": round(
            ingreso_excedentes,
            4,
        ),

        "coste_neto_eur": round(
            coste_neto,
            4,
        ),

        "valor_autoconsumo_eur": round(
            valor_autoconsumo,
            4,
        ),
    }


# ==========================================================
# Presentación
# ==========================================================

def mostrar_balance(
    balance,
):
    """
    Muestra el balance horario FV-demanda-precios.
    """

    print()
    print("Balance horario FV - demanda - precios")
    print("--------------------------------------")

    print(
        f"{'Hora':<7}"
        f"{'Demanda':>9}"
        f"{'FV':>9}"
        f"{'Balance':>10}"
        f"{'Déficit':>9}"
        f"{'Exced.':>9}"
        f"{'Compra':>10}"
        f"{'Venta':>10}"
    )

    print(
        "-" * 73
    )

    for r in balance:

        print(
            f"{r['hora']:<7}"
            f"{r['demanda_kw']:>9.2f}"
            f"{r['fv_kw']:>9.2f}"
            f"{r['balance_kw']:>10.2f}"
            f"{r['deficit_kw']:>9.2f}"
            f"{r['excedente_kw']:>9.2f}"
            f"{r['precio_compra']:>10.4f}"
            f"{r['precio_venta']:>10.4f}"
        )


def mostrar_resumen_balance(
    metricas,
):
    """
    Presenta las métricas agregadas del día.
    """

    print()
    print("Resumen energético sin batería")
    print("------------------------------")

    print(
        f"Demanda total             : "
        f"{metricas['energia_demanda_kwh']:.2f} kWh"
    )

    print(
        f"Generación FV             : "
        f"{metricas['energia_fv_kwh']:.2f} kWh"
    )

    print(
        f"Autoconsumo FV directo    : "
        f"{metricas['autoconsumo_directo_kwh']:.2f} kWh"
    )

    print(
        f"Excedentes FV             : "
        f"{metricas['excedentes_kwh']:.2f} kWh"
    )

    print(
        f"Déficit cubierto por red  : "
        f"{metricas['deficit_kwh']:.2f} kWh"
    )

    print(
        f"Ratio de autoconsumo      : "
        f"{metricas['ratio_autoconsumo'] * 100:.1f} %"
    )

    print(
        f"Autosuficiencia directa   : "
        f"{metricas['autosuficiencia'] * 100:.1f} %"
    )

    print()
    print("Economía sin batería")
    print("--------------------")

    print(
        f"Coste de compras a red    : "
        f"{metricas['coste_red_eur']:.3f} €"
    )

    print(
        f"Ingreso por excedentes    : "
        f"{metricas['ingreso_excedentes_eur']:.3f} €"
    )

    print(
        f"Balance económico neto    : "
        f"{metricas['coste_neto_eur']:.3f} €"
    )

    print(
        f"Valor del autoconsumo     : "
        f"{metricas['valor_autoconsumo_eur']:.3f} €"
    )
