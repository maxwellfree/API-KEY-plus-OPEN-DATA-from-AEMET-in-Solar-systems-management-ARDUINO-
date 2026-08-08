#!/usr/bin/env python3
"""
solar.py

Modelo físico-predictivo horario de generación fotovoltaica.

Versión 4.

================================================================
OBJETIVO
================================================================

Este módulo combina tres fuentes principales:

1. config.py

   Describe la instalación:

       - municipio;
       - provincia;
       - latitud y longitud si se conocen;
       - potencia FV instalada;
       - inclinación;
       - azimut;
       - coeficiente térmico del módulo;
       - potencia nominal del inversor.

2. PVGIS

   Proporciona una referencia climatológica horaria de:

       G(i)

   irradiancia incidente sobre el plano real de los módulos.

3. aemet_hourly.py

   Proporciona la meteorología prevista hora a hora:

       - temperatura;
       - estado del cielo;
       - precipitación;
       - viento;
       - factor meteorológico.

================================================================
CADENA FÍSICA
================================================================

La irradiancia prevista se obtiene mediante:

    G_pred(t) =
        G_PVGIS(t)
        * F_AEMET(t)

A partir de ella:

    T_cell(t) =
        T_amb(t)
        + DeltaT_1000
          * G_pred(t) / 1000

Después:

    P_DC(t) =
        P_STC
        * G_pred(t) / G_STC
        * [1 + gamma_P (T_cell - 25)]
        * F_DC

Finalmente:

    P_AC(t) =
        min(
            eta_inv * P_DC(t),
            P_inversor
        )

================================================================
JERARQUÍA DE DATOS METEOROLÓGICOS
================================================================

Prioridad 1:
    AEMET horario.

Prioridad 2:
    AEMET diario.

Prioridad 3:
    PVGIS climatológico sin corrección meteorológica.

Así, una caída temporal de AEMET no impide que el modelo
siga funcionando.

================================================================
IMPORTANTE
================================================================

PVGIS se utiliza fundamentalmente como fuente de irradiancia
sobre el plano:

    G(i)

La potencia P calculada por PVGIS se conserva solamente como
variable de diagnóstico y comparación.

Nuestro modelo calcula independientemente:

    irradiancia
        ->
    temperatura de célula
        ->
    potencia DC
        ->
    potencia AC.

Autor: Enrique M. Moreno Pérez
"""

# ==========================================================
# Importaciones
# ==========================================================

import json
import math

from datetime import datetime, timezone
from pathlib import Path
import pytz

import requests


# ==========================================================
# Servicios externos
# ==========================================================

PVGIS_URL = (
    "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
)

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)


# ==========================================================
# Zona horaria
# ==========================================================

ZONA_HORARIA_LOCAL = pytz.timezone(
    "Europe/Madrid"
)


# ==========================================================
# Directorios y caché
# ==========================================================

DIRECTORIO_PROYECTO = (
    Path(__file__).resolve().parent
)

CACHE_COORDENADAS = (
    DIRECTORIO_PROYECTO
    / ".solar_location_cache.json"
)

CACHE_PVGIS = (
    DIRECTORIO_PROYECTO
    / ".solar_pvgis_cache.json"
)


# ==========================================================
# Periodo histórico PVGIS
# ==========================================================

PVGIS_ANIO_INICIO = 2019

PVGIS_ANIO_FIN = 2023


# ==========================================================
# Constantes físicas
# ==========================================================

IRRADIANCIA_STC_WM2 = 1000.0

TEMPERATURA_STC_C = 25.0


# ----------------------------------------------------------
# Modelo térmico simplificado
# ----------------------------------------------------------
#
# A 1000 W/m² se supone inicialmente una diferencia aproximada
# de 20 °C entre célula y ambiente.
#
# Posteriormente podrá sustituirse por un modelo NOCT o por
# una formulación dependiente del viento.

INCREMENTO_TEMP_CELULA_1000_C = 20.0


# ----------------------------------------------------------
# Pérdidas DC
# ----------------------------------------------------------
#
# Engloba inicialmente:
#
#   - cableado;
#   - mismatch;
#   - suciedad;
#   - pequeñas pérdidas DC.
#
# La temperatura NO se incluye aquí porque se calcula
# explícitamente.

FACTOR_PERDIDAS_DC = 0.95


# ----------------------------------------------------------
# Eficiencia del inversor
# ----------------------------------------------------------

EFICIENCIA_INVERSOR = 0.97


# ==========================================================
# Utilidades
# ==========================================================

def limitar(
    valor,
    minimo,
    maximo,
):
    """
    Limita un número a un intervalo.
    """

    return max(
        minimo,
        min(
            maximo,
            valor,
        ),
    )


def cargar_json(
    ruta,
):
    """
    Lee un archivo JSON.

    Si no existe o no puede leerse devuelve {}.
    """

    if not ruta.exists():
        return {}

    try:

        with open(
            ruta,
            "r",
            encoding="utf-8",
        ) as archivo:

            return json.load(
                archivo
            )

    except (
        OSError,
        ValueError,
        TypeError,
    ):

        return {}


def guardar_json(
    ruta,
    datos,
):
    """
    Guarda datos en JSON.
    """

    with open(
        ruta,
        "w",
        encoding="utf-8",
    ) as archivo:

        json.dump(
            datos,
            archivo,
            indent=4,
            ensure_ascii=False,
        )


# ==========================================================
# Localización
# ==========================================================

def clave_localizacion(
    municipio,
    provincia,
):
    """
    Construye una clave estable de localización.
    """

    return (
        f"{municipio.strip().lower()}|"
        f"{provincia.strip().lower()}"
    )


def resolver_coordenadas(
    configuracion,
):
    """
    Obtiene latitud y longitud.

    Prioridad:

        1. config.py
        2. caché
        3. geocodificación automática
    """

    localizacion = configuracion[
        "localizacion"
    ]

    municipio = localizacion[
        "municipio"
    ]

    provincia = localizacion.get(
        "provincia",
        "",
    )

    latitud = localizacion.get(
        "latitud"
    )

    longitud = localizacion.get(
        "longitud"
    )

    # ------------------------------------------------------
    # Coordenadas introducidas manualmente
    # ------------------------------------------------------

    if (
        latitud is not None
        and longitud is not None
    ):

        return (
            float(latitud),
            float(longitud),
        )

    # ------------------------------------------------------
    # Caché local
    # ------------------------------------------------------

    cache = cargar_json(
        CACHE_COORDENADAS
    )

    clave = clave_localizacion(
        municipio,
        provincia,
    )

    if clave in cache:

        dato = cache[
            clave
        ]

        return (
            float(
                dato[
                    "latitud"
                ]
            ),
            float(
                dato[
                    "longitud"
                ]
            ),
        )

    # ------------------------------------------------------
    # Geocodificación
    # ------------------------------------------------------

    consulta = (
        f"{municipio}, "
        f"{provincia}, "
        f"España"
    )

    params = {
        "q": consulta,
        "format": "json",
        "limit": 1,
        "countrycodes": "es",
    }

    headers = {
        "User-Agent": (
            "GestionSolarAEMET/1.0 "
            "PV-research"
        )
    }

    respuesta = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=headers,
        timeout=20,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos:

        raise RuntimeError(
            "No se pudieron resolver coordenadas para "
            f"{consulta}."
        )

    latitud = float(
        datos[0][
            "lat"
        ]
    )

    longitud = float(
        datos[0][
            "lon"
        ]
    )

    cache[
        clave
    ] = {
        "municipio": municipio,
        "provincia": provincia,
        "latitud": latitud,
        "longitud": longitud,
    }

    guardar_json(
        CACHE_COORDENADAS,
        cache,
    )

    return (
        latitud,
        longitud,
    )


# ==========================================================
# Geometría FV
# ==========================================================

def obtener_geometria_paneles(
    configuracion,
):
    """
    Obtiene inclinación y azimut.

    Convención:

         0° = Sur
       -90° = Este
       +90° = Oeste
      ±180° = Norte
    """

    fv = configuracion[
        "fotovoltaica"
    ]

    inclinacion = float(
        fv.get(
            "inclinacion_grados",
            30.0,
        )
    )

    azimut = float(
        fv.get(
            "azimut_grados",
            0.0,
        )
    )

    if not 0.0 <= inclinacion <= 90.0:

        raise ValueError(
            "La inclinación debe estar entre "
            "0 y 90 grados."
        )

    if not -180.0 <= azimut <= 180.0:

        raise ValueError(
            "El azimut debe estar entre "
            "-180 y 180 grados."
        )

    return (
        inclinacion,
        azimut,
    )


# ==========================================================
# Clave PVGIS
# ==========================================================

def construir_clave_pvgis(
    latitud,
    longitud,
    inclinacion,
    azimut,
    potencia_kwp,
):
    """
    Crea una clave única para la caché PVGIS.
    """

    return (
        f"{latitud:.5f}|"
        f"{longitud:.5f}|"
        f"{inclinacion:.2f}|"
        f"{azimut:.2f}|"
        f"{potencia_kwp:.3f}|"
        f"{PVGIS_ANIO_INICIO}|"
        f"{PVGIS_ANIO_FIN}"
    )


# ==========================================================
# Consulta PVGIS
# ==========================================================

def consultar_pvgis(
    configuracion,
):
    """
    Obtiene la serie horaria histórica de PVGIS.

    La variable principal utilizada posteriormente será:

        G(i)

    irradiancia sobre el plano de los módulos.
    """

    latitud, longitud = resolver_coordenadas(
        configuracion
    )

    inclinacion, azimut = obtener_geometria_paneles(
        configuracion
    )

    potencia_kwp = float(
        configuracion[
            "fotovoltaica"
        ][
            "potencia_total_kwp"
        ]
    )

    clave = construir_clave_pvgis(
        latitud,
        longitud,
        inclinacion,
        azimut,
        potencia_kwp,
    )

    # ------------------------------------------------------
    # Intentar caché
    # ------------------------------------------------------

    cache = cargar_json(
        CACHE_PVGIS
    )

    if clave in cache:

        return cache[
            clave
        ]

    # ------------------------------------------------------
    # Consulta externa
    # ------------------------------------------------------

    params = {
        "lat": latitud,
        "lon": longitud,

        "startyear": PVGIS_ANIO_INICIO,
        "endyear": PVGIS_ANIO_FIN,

        "pvcalculation": 1,

        "peakpower": potencia_kwp,

        # No aplicamos pérdidas PVGIS porque nuestra potencia
        # se calculará independientemente.
        "loss": 0,

        "angle": inclinacion,
        "aspect": azimut,

        "outputformat": "json",
    }

    respuesta = requests.get(
        PVGIS_URL,
        params=params,
        timeout=60,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    try:

        serie = datos[
            "outputs"
        ][
            "hourly"
        ]

    except (
        KeyError,
        TypeError,
    ) as error:

        raise RuntimeError(
            "PVGIS devolvió un formato inesperado."
        ) from error

    if not serie:

        raise RuntimeError(
            "PVGIS no devolvió datos horarios."
        )

    cache[
        clave
    ] = serie

    guardar_json(
        CACHE_PVGIS,
        cache,
    )

    return serie


# ==========================================================
# Conversión horaria PVGIS
# ==========================================================

def interpretar_fecha_pvgis_utc(
    texto,
):
    """
    Interpreta la fecha PVGIS como UTC.
    """

    fecha_naive = datetime.strptime(
        texto,
        "%Y%m%d:%H%M",
    )

    return fecha_naive.replace(
        tzinfo=timezone.utc
    )


def convertir_a_hora_local(
    fecha_utc,
):
    """
    Convierte UTC a hora peninsular española.
    """

    return fecha_utc.astimezone(
        ZONA_HORARIA_LOCAL
    )


# ==========================================================
# Perfil climatológico PVGIS
# ==========================================================

def perfil_referencia_fecha(
    serie_pvgis,
    fecha,
):
    """
    Obtiene una curva climatológica horaria correspondiente
    al mismo día y mes de la fecha solicitada.

    Se promedian los años disponibles en PVGIS.

    La agrupación se realiza por HORA LOCAL.
    """

    acumulados = {
        hora: {
            "irradiancia": [],
            "temperatura": [],
            "viento": [],
            "potencia_pvgis": [],
        }
        for hora in range(24)
    }

    for registro in serie_pvgis:

        fecha_utc = (
            interpretar_fecha_pvgis_utc(
                registro[
                    "time"
                ]
            )
        )

        fecha_local = convertir_a_hora_local(
            fecha_utc
        )

        if (
            fecha_local.month != fecha.month
            or fecha_local.day != fecha.day
        ):

            continue

        hora = fecha_local.hour

        irradiancia = float(
            registro.get(
                "G(i)",
                0.0,
            )
        )

        temperatura = float(
            registro.get(
                "T2m",
                20.0,
            )
        )

        viento = float(
            registro.get(
                "WS10m",
                0.0,
            )
        )

        potencia_pvgis = float(
            registro.get(
                "P",
                0.0,
            )
        )

        acumulados[
            hora
        ][
            "irradiancia"
        ].append(
            irradiancia
        )

        acumulados[
            hora
        ][
            "temperatura"
        ].append(
            temperatura
        )

        acumulados[
            hora
        ][
            "viento"
        ].append(
            viento
        )

        acumulados[
            hora
        ][
            "potencia_pvgis"
        ].append(
            potencia_pvgis
        )

    perfil = []

    for hora in range(24):

        datos = acumulados[
            hora
        ]

        if datos[
            "irradiancia"
        ]:

            irradiancia = (
                sum(
                    datos[
                        "irradiancia"
                    ]
                )
                / len(
                    datos[
                        "irradiancia"
                    ]
                )
            )

            temperatura = (
                sum(
                    datos[
                        "temperatura"
                    ]
                )
                / len(
                    datos[
                        "temperatura"
                    ]
                )
            )

            viento = (
                sum(
                    datos[
                        "viento"
                    ]
                )
                / len(
                    datos[
                        "viento"
                    ]
                )
            )

            potencia_pvgis = (
                sum(
                    datos[
                        "potencia_pvgis"
                    ]
                )
                / len(
                    datos[
                        "potencia_pvgis"
                    ]
                )
            )

        else:

            irradiancia = 0.0
            temperatura = 20.0
            viento = 0.0
            potencia_pvgis = 0.0

        perfil.append(
            {
                "hora": (
                    f"{hora:02d}:00"
                ),

                "irradiancia_poa_referencia_wm2": (
                    irradiancia
                ),

                "temperatura_pvgis_c": (
                    temperatura
                ),

                "viento_pvgis_ms": (
                    viento
                ),

                # Solo diagnóstico.
                "potencia_pvgis_referencia_kw": (
                    potencia_pvgis
                    / 1000.0
                ),
            }
        )

    return perfil


# ==========================================================
# Indexación AEMET horaria
# ==========================================================

def indexar_aemet_horario(
    prevision_horaria,
    fecha,
):
    """
    Convierte la lista de AEMET horario en un diccionario:

        {
            0: registro,
            1: registro,
            ...
        }

    únicamente para la fecha solicitada.
    """

    resultado = {}

    if not prevision_horaria:
        return resultado

    for registro in prevision_horaria:

        if registro.get(
            "fecha"
        ) != fecha:

            continue

        hora_txt = registro.get(
            "hora",
            ""
        )

        try:

            hora = int(
                hora_txt[
                    :2
                ]
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        resultado[
            hora
        ] = registro

    return resultado


# ==========================================================
# Factor AEMET diario de respaldo
# ==========================================================

def factor_aemet_diario(
    prevision_diaria,
):
    """
    Construye el factor meteorológico de respaldo a partir
    del score diario.

    Solo se utiliza cuando no existe información horaria.
    """

    if not prevision_diaria:

        return 1.0

    score = float(
        prevision_diaria.get(
            "score",
            1.0,
        )
    )

    score = limitar(
        score,
        0.0,
        1.0,
    )

    # Corrección moderada.
    return (
        0.25
        + 0.75
        * score
    )


# ==========================================================
# Meteorología efectiva de cada hora
# ==========================================================

def obtener_meteorologia_hora(
    hora,
    aemet_horas,
    prevision_diaria,
    referencia_pvgis,
):
    """
    Determina meteorología efectiva para una hora.

    Jerarquía:

        AEMET horario
        AEMET diario
        PVGIS climatológico
    """

    # ======================================================
    # Caso 1: AEMET horario disponible
    # ======================================================

    if hora in aemet_horas:

        dato = aemet_horas[
            hora
        ]

        factor = dato.get(
            "factor_meteorologico"
        )

        temperatura = dato.get(
            "temperatura_c"
        )

        viento_kmh = dato.get(
            "viento_velocidad_kmh"
        )

        if factor is None:
            factor = 1.0

        if temperatura is None:

            temperatura = referencia_pvgis.get(
                "temperatura_pvgis_c",
                20.0,
            )

        if viento_kmh is None:

            viento_ms = referencia_pvgis.get(
                "viento_pvgis_ms",
                0.0,
            )

        else:

            viento_ms = (
                float(viento_kmh)
                / 3.6
            )

        return {
            "fuente": "AEMET_horario",

            "factor_meteorologico": limitar(
                float(factor),
                0.05,
                1.10,
            ),

            "temperatura_c": float(
                temperatura
            ),

            "viento_ms": float(
                viento_ms
            ),

            "estado_cielo": dato.get(
                "estado_cielo",
                "",
            ),
        }

    # ======================================================
    # Caso 2: AEMET diario
    # ======================================================

    if prevision_diaria:

        factor = factor_aemet_diario(
            prevision_diaria
        )

        tmax = prevision_diaria.get(
            "tmax"
        )

        if tmax is not None:

            temperatura = temperatura_horaria_desde_tmax(
                hora,
                float(tmax),
            )

        else:

            temperatura = referencia_pvgis.get(
                "temperatura_pvgis_c",
                20.0,
            )

        return {
            "fuente": "AEMET_diario",

            "factor_meteorologico": factor,

            "temperatura_c": temperatura,

            "viento_ms": referencia_pvgis.get(
                "viento_pvgis_ms",
                0.0,
            ),

            "estado_cielo": "",
        }

    # ======================================================
    # Caso 3: climatología PVGIS
    # ======================================================

    return {
        "fuente": "PVGIS",

        "factor_meteorologico": 1.0,

        "temperatura_c": referencia_pvgis.get(
            "temperatura_pvgis_c",
            20.0,
        ),

        "viento_ms": referencia_pvgis.get(
            "viento_pvgis_ms",
            0.0,
        ),

        "estado_cielo": "",
    }


# ==========================================================
# Temperatura horaria fallback
# ==========================================================

def temperatura_horaria_desde_tmax(
    hora,
    tmax,
):
    """
    Reconstrucción simple de temperatura horaria.

    Solo se utiliza cuando AEMET horario no está disponible.
    """

    amplitud = 7.0

    fase = (
        2.0
        * math.pi
        * (
            hora
            - 16.0
        )
        / 24.0
    )

    return (
        tmax
        - amplitud
        * (
            1.0
            - math.cos(
                fase
            )
        )
        / 2.0
    )


# ==========================================================
# Temperatura de célula
# ==========================================================

def estimar_temperatura_celula(
    temperatura_ambiente_c,
    irradiancia_wm2,
    viento_ms=0.0,
):
    """
    Estima la temperatura de célula.

    Modelo base:

        Tcell =
            Tamb
            + DeltaT
            * G / 1000

    Se introduce además una pequeña corrección por viento.

    El viento favorece la refrigeración del módulo.

    Esta formulación es todavía simplificada y podrá ser
    sustituida por un modelo NOCT/Faiman más completo.
    """

    fraccion_irradiancia = limitar(
        irradiancia_wm2
        / IRRADIANCIA_STC_WM2,
        0.0,
        1.2,
    )

    incremento = (
        INCREMENTO_TEMP_CELULA_1000_C
        * fraccion_irradiancia
    )

    # ------------------------------------------------------
    # Refrigeración por viento
    # ------------------------------------------------------
    #
    # Corrección inicial suave.
    #
    # Nunca permitimos que el viento reduzca más del 40 %
    # del incremento térmico calculado.

    factor_refrigeracion = (
        1.0
        / (
            1.0
            + 0.08
            * max(
                0.0,
                viento_ms,
            )
        )
    )

    factor_refrigeracion = limitar(
        factor_refrigeracion,
        0.60,
        1.0,
    )

    incremento *= (
        factor_refrigeracion
    )

    return (
        temperatura_ambiente_c
        + incremento
    )


# ==========================================================
# Potencia DC
# ==========================================================

def calcular_potencia_dc(
    potencia_stc_kwp,
    irradiancia_wm2,
    temperatura_celula_c,
    coef_temp_pmax,
):
    """
    Calcula la potencia DC.

    Pdc =
        Pstc
        * G/Gstc
        * [1 + gamma(Tcell-Tstc)]
        * F_DC
    """

    if irradiancia_wm2 <= 0.0:

        return 0.0

    factor_irradiancia = (
        irradiancia_wm2
        / IRRADIANCIA_STC_WM2
    )

    factor_temperatura = (
        1.0
        + coef_temp_pmax
        * (
            temperatura_celula_c
            - TEMPERATURA_STC_C
        )
    )

    factor_temperatura = limitar(
        factor_temperatura,
        0.70,
        1.10,
    )

    potencia = (
        potencia_stc_kwp
        * factor_irradiancia
        * factor_temperatura
        * FACTOR_PERDIDAS_DC
    )

    return max(
        0.0,
        potencia,
    )


# ==========================================================
# Potencia AC
# ==========================================================

def calcular_potencia_ac(
    potencia_dc_kw,
    potencia_inversor_kw,
):
    """
    Calcula potencia AC tras el inversor.
    """

    potencia = (
        potencia_dc_kw
        * EFICIENCIA_INVERSOR
    )

    return limitar(
        potencia,
        0.0,
        potencia_inversor_kw,
    )


# ==========================================================
# Perfil FV de 24 horas
# ==========================================================

def obtener_perfil_fv_24h(
    fecha,
    configuracion,
    prevision_horaria=None,
    prevision_diaria=None,
):
    """
    Calcula el perfil FV físico-predictivo de 24 horas.

    Parameters
    ----------
    fecha : datetime.date
        Día de cálculo.

    configuracion : dict
        Configuración física.

    prevision_horaria : list, optional
        Salida de aemet_hourly.obtener_prevision_horaria().

    prevision_diaria : dict, optional
        Predicción diaria procedente de aemet.py.

    Returns
    -------
    list
        Perfil horario FV.
    """

    # ------------------------------------------------------
    # PVGIS
    # ------------------------------------------------------

    serie_pvgis = consultar_pvgis(
        configuracion
    )

    referencia = perfil_referencia_fecha(
        serie_pvgis,
        fecha,
    )

    # ------------------------------------------------------
    # AEMET horario
    # ------------------------------------------------------

    aemet_horas = indexar_aemet_horario(
        prevision_horaria,
        fecha,
    )

    # ------------------------------------------------------
    # Sistema físico
    # ------------------------------------------------------

    fv = configuracion[
        "fotovoltaica"
    ]

    inversor = configuracion[
        "inversor"
    ]

    potencia_stc_kwp = float(
        fv[
            "potencia_total_kwp"
        ]
    )

    coef_temp_pmax = float(
        fv.get(
            "coef_temp_pmax",
            -0.0029,
        )
    )

    potencia_inversor_kw = float(
        inversor[
            "potencia_nominal_kw"
        ]
    )

    perfil = []

    # ======================================================
    # Cálculo horario
    # ======================================================

    for hora in range(
        24
    ):

        ref = referencia[
            hora
        ]

        irradiancia_ref = float(
            ref[
                "irradiancia_poa_referencia_wm2"
            ]
        )

        # --------------------------------------------------
        # Meteorología prevista
        # --------------------------------------------------

        meteo = obtener_meteorologia_hora(
            hora,
            aemet_horas,
            prevision_diaria,
            ref,
        )

        factor_meteo = float(
            meteo[
                "factor_meteorologico"
            ]
        )

        # --------------------------------------------------
        # Irradiancia prevista
        # --------------------------------------------------

        irradiancia_predicha = (
            irradiancia_ref
            * factor_meteo
        )

        irradiancia_predicha = max(
            0.0,
            irradiancia_predicha,
        )

        # --------------------------------------------------
        # Temperatura
        # --------------------------------------------------

        temperatura_ambiente = float(
            meteo[
                "temperatura_c"
            ]
        )

        viento_ms = float(
            meteo[
                "viento_ms"
            ]
        )

        temperatura_celula = (
            estimar_temperatura_celula(
                temperatura_ambiente,
                irradiancia_predicha,
                viento_ms,
            )
        )

        # --------------------------------------------------
        # Potencia DC
        # --------------------------------------------------

        potencia_dc = calcular_potencia_dc(
            potencia_stc_kwp,
            irradiancia_predicha,
            temperatura_celula,
            coef_temp_pmax,
        )

        # --------------------------------------------------
        # Potencia AC
        # --------------------------------------------------

        potencia_ac = calcular_potencia_ac(
            potencia_dc,
            potencia_inversor_kw,
        )

        # --------------------------------------------------
        # Registro
        # --------------------------------------------------

        perfil.append(
            {
                "hora": (
                    f"{hora:02d}:00"
                ),

                "irradiancia_referencia_wm2": round(
                    irradiancia_ref,
                    1,
                ),

                "factor_meteorologico": round(
                    factor_meteo,
                    3,
                ),

                "irradiancia_predicha_wm2": round(
                    irradiancia_predicha,
                    1,
                ),

                "temperatura_ambiente_c": round(
                    temperatura_ambiente,
                    1,
                ),

                "temperatura_celula_c": round(
                    temperatura_celula,
                    1,
                ),

                "viento_ms": round(
                    viento_ms,
                    2,
                ),

                "potencia_dc_kw": round(
                    potencia_dc,
                    4,
                ),

                "potencia_fv_kw": round(
                    potencia_ac,
                    4,
                ),

                "energia_fv_kwh": round(
                    potencia_ac,
                    4,
                ),

                "fuente_meteorologica": (
                    meteo[
                        "fuente"
                    ]
                ),

                "estado_cielo": (
                    meteo[
                        "estado_cielo"
                    ]
                ),

                # Comparación con PVGIS.
                "potencia_pvgis_referencia_kw": round(
                    ref[
                        "potencia_pvgis_referencia_kw"
                    ],
                    4,
                ),
            }
        )

    return perfil


# ==========================================================
# Energía diaria
# ==========================================================

def energia_fv_diaria(
    perfil,
):
    """
    Energía AC total estimada durante el día.
    """

    return sum(
        registro[
            "energia_fv_kwh"
        ]
        for registro in perfil
    )


# ==========================================================
# Pico de potencia
# ==========================================================

def obtener_pico_fv(
    perfil,
):
    """
    Devuelve la hora de máxima potencia FV.
    """

    if not perfil:

        return None

    return max(
        perfil,
        key=lambda registro: registro[
            "potencia_fv_kw"
        ],
    )


# ==========================================================
# Presentación
# ==========================================================

def mostrar_perfil_fv(
    perfil,
):
    """
    Muestra el perfil FV horario.
    """

    print()
    print("Perfil horario físico-predictivo FV")
    print("-----------------------------------")

    print(
        f"{'Hora':<7}"
        f"{'Gref':>8}"
        f"{'Fmet':>7}"
        f"{'Gpred':>9}"
        f"{'Tamb':>7}"
        f"{'Tcell':>8}"
        f"{'Pac':>8}"
        f"{'Fuente':>16}"
    )

    print(
        "-" * 70
    )

    for registro in perfil:

        print(
            f"{registro['hora']:<7}"
            f"{registro['irradiancia_referencia_wm2']:>8.1f}"
            f"{registro['factor_meteorologico']:>7.2f}"
            f"{registro['irradiancia_predicha_wm2']:>9.1f}"
            f"{registro['temperatura_ambiente_c']:>7.1f}"
            f"{registro['temperatura_celula_c']:>8.1f}"
            f"{registro['potencia_fv_kw']:>8.3f}"
            f"{registro['fuente_meteorologica']:>16}"
        )

    energia = energia_fv_diaria(
        perfil
    )

    pico = obtener_pico_fv(
        perfil
    )

    print()

    print(
        f"Generación FV diaria estimada : "
        f"{energia:.2f} kWh"
    )

    if pico:

        print(
            f"Pico FV AC estimado           : "
            f"{pico['hora']} — "
            f"{pico['potencia_fv_kw']:.2f} kW"
        )
