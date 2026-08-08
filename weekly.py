#!/usr/bin/env python3
"""
weekly.py

Planificador semanal sostenible de servicios energéticos.

Versión 2.

================================================================
OBJETIVO
================================================================

Este módulo responde a la pregunta:

    ¿Cuándo conviene prestar cada servicio durante la semana?

A diferencia de la versión 1, los servicios NO se planifican
independientemente.

Se considera:

    - disponibilidad solar;
    - presencia;
    - frecuencia semanal;
    - potencia de las cargas;
    - simultaneidad;
    - tipo físico del servicio;
    - restricciones térmicas;
    - restricciones externas;
    - sostenibilidad.

================================================================
TIPOS DE SERVICIO
================================================================

1. TAREA DESPLAZABLE

   Ejemplos:

       lavadora
       horno
       robot de cocina

   Tiene duración definida y puede desplazarse dentro de una
   ventana temporal.

2. CARGA TÉRMICA

   Ejemplos:

       climatización
       ACS

   No debe interpretarse como una tarea puntual de una hora.

   Se controla mediante ventanas de funcionamiento o estados
   térmicos.

3. CARGA CONDICIONAL

   Ejemplo:

       termo eléctrico

   Solo se activa si existe una necesidad física:

       temperatura ACS insuficiente.

4. SERVICIO CON RESTRICCIÓN EXTERNA

   Ejemplo:

       riego

   La sostenibilidad del recurso agua tiene prioridad frente
   al pequeño beneficio eléctrico de ejecutar el servicio
   durante el máximo solar.

================================================================
FILOSOFÍA
================================================================

Orden de prioridad:

    1. satisfacer el servicio;
    2. respetar presencia y restricciones físicas;
    3. aprovechar FV directa;
    4. evitar simultaneidad innecesaria;
    5. evitar batería;
    6. utilizar red para consumos marginales;
    7. economía.

================================================================
LIMITACIÓN ACTUAL
================================================================

Esta versión sigue utilizando principalmente la predicción
AEMET diaria para distribuir servicios entre los 7 días.

La siguiente fase incorporará para las primeras 48 horas:

    P_FV(t)
    demanda(t)
    precio_compra(t)
    precio_venta(t)

y permitirá elegir las horas usando excedentes reales.

Autor: Enrique M. Moreno Pérez
"""

from datetime import datetime, timedelta


# ==========================================================
# Parámetros generales
# ==========================================================

HORIZONTE_DIAS_DEFAULT = 7


# ----------------------------------------------------------
# Clasificación solar
# ----------------------------------------------------------

INDICE_SOLAR_EXCELENTE = 0.85
INDICE_SOLAR_BUENO = 0.70
INDICE_SOLAR_ACEPTABLE = 0.50


# ----------------------------------------------------------
# Límites de planificación
# ----------------------------------------------------------
#
# No es el límite físico del inversor.
#
# Es un límite operativo para evitar concentrar demasiadas
# cargas flexibles simultáneamente.

POTENCIA_SERVICIOS_SIMULTANEA_MAX_KW = 3.0


# ----------------------------------------------------------
# Resolución temporal
# ----------------------------------------------------------

PASO_PLANIFICACION_H = 0.5


# ----------------------------------------------------------
# Ventana solar general
# ----------------------------------------------------------

VENTANA_SOLAR_GENERAL = (
    "10:00",
    "18:00",
)


# ----------------------------------------------------------
# Ventana solar central
# ----------------------------------------------------------

VENTANA_SOLAR_CENTRAL = (
    "12:00",
    "16:00",
)


# ----------------------------------------------------------
# Riego
# ----------------------------------------------------------

VENTANAS_RIEGO_PREFERIDAS = [
    (
        "06:00",
        "08:00",
    ),
    (
        "20:00",
        "22:00",
    ),
]


# ==========================================================
# Utilidades temporales
# ==========================================================

def nombre_dia_semana(
    fecha,
):
    """
    Devuelve el día de la semana en castellano.
    """

    nombres = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    return nombres[
        fecha.weekday()
    ]


def hora_a_decimal(
    hora_txt,
):
    """
    Convierte HH:MM en hora decimal.
    """

    horas, minutos = hora_txt.split(
        ":"
    )

    return (
        int(horas)
        + int(minutos) / 60.0
    )


def decimal_a_hora(
    valor,
):
    """
    Convierte hora decimal en HH:MM.
    """

    valor = valor % 24.0

    hora = int(
        valor
    )

    minutos = int(
        round(
            (
                valor
                - hora
            )
            * 60.0
        )
    )

    if minutos >= 60:

        hora = (
            hora
            + 1
        ) % 24

        minutos = 0

    return (
        f"{hora:02d}:"
        f"{minutos:02d}"
    )


# ==========================================================
# Calidad solar
# ==========================================================

def clasificar_dia_solar(
    score,
):
    """
    Clasifica cualitativamente el recurso solar.
    """

    score = float(
        score
    )

    if score >= INDICE_SOLAR_EXCELENTE:
        return "excelente"

    if score >= INDICE_SOLAR_BUENO:
        return "bueno"

    if score >= INDICE_SOLAR_ACEPTABLE:
        return "aceptable"

    return "malo"


# ==========================================================
# Confianza
# ==========================================================

def confianza_por_horizonte(
    indice_dia,
):
    """
    Clasificación aproximada de confianza.
    """

    if indice_dia <= 1:
        return "alta"

    if indice_dia <= 3:
        return "media"

    return "baja"


# ==========================================================
# Presencia
# ==========================================================

def obtener_ventanas_presencia(
    demanda,
    fecha,
    estacion,
):
    """
    Obtiene las ventanas de presencia del día.
    """

    nombre_dia = nombre_dia_semana(
        fecha
    )

    presencia = demanda.get(
        "presencia",
        {},
    )

    por_estacion = presencia.get(
        estacion,
        {},
    )

    return por_estacion.get(
        nombre_dia,
        [],
    )


def intervalo_dentro_de_ventana(
    inicio,
    fin,
    ventana,
):
    """
    Comprueba si un intervalo está completamente contenido
    en una ventana.
    """

    inicio_d = hora_a_decimal(
        inicio
    )

    fin_d = hora_a_decimal(
        fin
    )

    inicio_v = hora_a_decimal(
        ventana[
            0
        ]
    )

    fin_v = hora_a_decimal(
        ventana[
            1
        ]
    )

    return (
        inicio_d >= inicio_v
        and fin_d <= fin_v
    )


def hay_presencia_en_intervalo(
    ventanas,
    inicio,
    fin,
):
    """
    Comprueba presencia durante todo el servicio.
    """

    for ventana in ventanas:

        if intervalo_dentro_de_ventana(
            inicio,
            fin,
            ventana,
        ):
            return True

    return False


# ==========================================================
# Clasificación de servicios
# ==========================================================

def determinar_tipo_servicio(
    carga,
):
    """
    Clasifica automáticamente una carga.

    Se permite además definir explícitamente:

        tipo_servicio

    dentro de demand.py.
    """

    tipo_explicitado = carga.get(
        "tipo_servicio"
    )

    if tipo_explicitado:

        return tipo_explicitado

    nombre = (
        carga.get(
            "nombre",
            ""
        )
        .lower()
    )

    if (
        "riego" in nombre
        or "electroválvula" in nombre
    ):
        return "restriccion_externa"

    if (
        "termo eléctrico" in nombre
        or "termo electrico" in nombre
    ):
        return "condicional"

    if (
        "aire acondicionado" in nombre
        or "bomba de calor" in nombre
        or "climatización" in nombre
        or "climatizacion" in nombre
    ):
        return "termica"

    if "acs" in nombre:
        return "termica"

    return "tarea"


# ==========================================================
# Frecuencia semanal
# ==========================================================

def frecuencia_semanal_servicio(
    carga,
):
    """
    Obtiene la frecuencia semanal.

    Si demand.py todavía no especifica una frecuencia,
    se utilizan valores iniciales razonables.
    """

    frecuencia = carga.get(
        "frecuencia_semanal"
    )

    if frecuencia is not None:

        return max(
            0,
            int(
                frecuencia
            ),
        )

    nombre = (
        carga.get(
            "nombre",
            ""
        )
        .lower()
    )

    if "lavadora" in nombre:
        return 4

    if "riego" in nombre:
        return 3

    if (
        "horno" in nombre
        or "robot" in nombre
    ):
        return 2

    # Climatización y ACS se tratan por día,
    # no mediante frecuencia de tareas.

    return 1


# ==========================================================
# Extracción de servicios
# ==========================================================

def extraer_servicios(
    demanda,
):
    """
    Extrae las cargas flexibles del modelo doméstico.
    """

    servicios = []

    for carga in demanda.get(
        "cargas",
        [],
    ):

        if not carga.get(
            "flexible",
            False,
        ):
            continue

        tipo = determinar_tipo_servicio(
            carga
        )

        servicios.append(
            {
                "nombre": carga.get(
                    "nombre",
                    "servicio",
                ),

                "descripcion": carga.get(
                    "descripcion",
                    carga.get(
                        "nombre",
                        "servicio",
                    ),
                ),

                "tipo": tipo,

                "potencia_kw": float(
                    carga.get(
                        "potencia_kw",
                        0.0,
                    )
                    or 0.0
                ),

                "duracion_h": float(
                    carga.get(
                        "duracion_h",
                        1.0,
                    )
                    or 1.0
                ),

                "requiere_presencia": carga.get(
                    "requiere_presencia",
                    False,
                ),

                "automatizable": carga.get(
                    "automatizable",
                    False,
                ),

                "prioridad": int(
                    carga.get(
                        "prioridad",
                        3,
                    )
                ),

                "estacional": carga.get(
                    "estacional",
                    "todo",
                ),

                "frecuencia_semanal": (
                    frecuencia_semanal_servicio(
                        carga
                    )
                ),

                "max_aplazamiento_h": float(
                    carga.get(
                        "max_aplazamiento_h",
                        168.0,
                    )
                    or 168.0
                ),
            }
        )

    return servicios


# ==========================================================
# Estacionalidad
# ==========================================================

def servicio_activo_en_estacion(
    servicio,
    estacion,
):
    """
    Comprueba compatibilidad estacional.
    """

    valor = servicio.get(
        "estacional",
        "todo",
    )

    if valor in (
        None,
        "todo",
    ):
        return True

    return (
        valor == estacion
    )


# ==========================================================
# Agenda de potencia
# ==========================================================

def crear_agenda_potencia(
    prevision,
):
    """
    Crea una agenda de potencia flexible programada.

    Estructura:

        agenda[fecha][hora_decimal] = potencia_kw
    """

    agenda = {}

    for dia in prevision:

        fecha = dia[
            "fecha"
        ]

        agenda[
            fecha
        ] = {}

        hora = 0.0

        while hora < 24.0:

            agenda[
                fecha
            ][
                round(
                    hora,
                    2,
                )
            ] = 0.0

            hora += (
                PASO_PLANIFICACION_H
            )

    return agenda


def comprobar_potencia_disponible(
    agenda,
    fecha,
    inicio_h,
    duracion_h,
    potencia_kw,
):
    """
    Comprueba que añadir una carga no supere el límite
    de simultaneidad programada.
    """

    t = inicio_h

    fin = (
        inicio_h
        + duracion_h
    )

    while t < fin:

        clave = round(
            t,
            2,
        )

        potencia_existente = (
            agenda[
                fecha
            ].get(
                clave,
                0.0,
            )
        )

        if (
            potencia_existente
            + potencia_kw
            >
            POTENCIA_SERVICIOS_SIMULTANEA_MAX_KW
        ):
            return False

        t += (
            PASO_PLANIFICACION_H
        )

    return True


def reservar_potencia(
    agenda,
    fecha,
    inicio_h,
    duracion_h,
    potencia_kw,
):
    """
    Reserva potencia para un servicio.
    """

    t = inicio_h

    fin = (
        inicio_h
        + duracion_h
    )

    while t < fin:

        clave = round(
            t,
            2,
        )

        agenda[
            fecha
        ][
            clave
        ] = (
            agenda[
                fecha
            ].get(
                clave,
                0.0,
            )
            + potencia_kw
        )

        t += (
            PASO_PLANIFICACION_H
        )


# ==========================================================
# Generación de intervalos candidatos
# ==========================================================

def generar_intervalos(
    ventana,
    duracion_h,
):
    """
    Genera posibles horas de inicio dentro de una ventana.
    """

    inicio = hora_a_decimal(
        ventana[
            0
        ]
    )

    fin = hora_a_decimal(
        ventana[
            1
        ]
    )

    resultados = []

    t = inicio

    while (
        t
        + duracion_h
        <= fin
        + 1e-9
    ):

        resultados.append(
            (
                t,
                t + duracion_h,
            )
        )

        t += (
            PASO_PLANIFICACION_H
        )

    return resultados


# ==========================================================
# Puntuación solar horaria aproximada
# ==========================================================

def factor_hora_solar(
    hora,
):
    """
    Factor aproximado dentro del día.

    Todavía no utiliza P_FV(t).

    Se utiliza solamente para días en los que tenemos
    predicción diaria pero no perfil horario detallado.
    """

    if hora < 8.0:
        return 0.05

    if hora < 10.0:
        return 0.35

    if hora < 12.0:
        return 0.75

    if hora <= 16.0:
        return 1.0

    if hora <= 18.0:
        return 0.75

    if hora <= 20.0:
        return 0.30

    return 0.05


# ==========================================================
# Puntuación de tarea
# ==========================================================

def puntuar_tarea(
    servicio,
    dia,
    indice_dia,
    inicio_h,
    presencia_valida,
    potencia_programada_kw,
):
    """
    Puntúa una tarea candidata.
    """

    score_solar = float(
        dia.get(
            "score",
            0.5,
        )
    )

    centro_servicio = (
        inicio_h
        + servicio[
            "duracion_h"
        ] / 2.0
    )

    factor_horario = factor_hora_solar(
        centro_servicio
    )

    puntuacion = (
        score_solar
        * factor_horario
        * 100.0
    )

    # ------------------------------------------------------
    # Presencia
    # ------------------------------------------------------

    if servicio[
        "requiere_presencia"
    ]:

        if not presencia_valida:

            return -1e9

        puntuacion += 20.0

    # ------------------------------------------------------
    # Confianza
    # ------------------------------------------------------

    confianza = confianza_por_horizonte(
        indice_dia
    )

    if confianza == "alta":

        puntuacion += 10.0

    elif confianza == "media":

        puntuacion += 4.0

    # ------------------------------------------------------
    # Penalización por simultaneidad
    # ------------------------------------------------------

    puntuacion -= (
        potencia_programada_kw
        * 8.0
    )

    # ------------------------------------------------------
    # Prioridad
    # ------------------------------------------------------

    puntuacion += max(
        0.0,
        5.0
        - servicio[
            "prioridad"
        ],
    )

    return puntuacion


# ==========================================================
# Planificación de tareas
# ==========================================================

def planificar_tareas(
    servicios,
    prevision,
    demanda,
    estacion,
    agenda,
):
    """
    Planifica tareas desplazables conjuntamente.
    """

    resultado = []

    tareas = [
        servicio
        for servicio in servicios
        if servicio[
            "tipo"
        ] == "tarea"
    ]

    # ------------------------------------------------------
    # Primero cargas de mayor potencia/prioridad.
    # ------------------------------------------------------

    tareas.sort(
        key=lambda s: (
            s[
                "prioridad"
            ],
            -s[
                "potencia_kw"
            ],
        )
    )

    for servicio in tareas:

        frecuencia = min(
            servicio[
                "frecuencia_semanal"
            ],
            len(
                prevision
            ),
        )

        dias_utilizados = set()

        for repeticion in range(
            frecuencia
        ):

            candidatos = []

            for indice_dia, dia in enumerate(
                prevision
            ):

                fecha = dia[
                    "fecha"
                ]

                # Evitar concentrar todas las repeticiones
                # del mismo servicio en un único día.

                if fecha in dias_utilizados:
                    continue

                ventanas_presencia = (
                    obtener_ventanas_presencia(
                        demanda,
                        fecha,
                        estacion,
                    )
                )

                intervalos = generar_intervalos(
                    VENTANA_SOLAR_GENERAL,
                    servicio[
                        "duracion_h"
                    ],
                )

                for (
                    inicio_h,
                    fin_h,
                ) in intervalos:

                    inicio_txt = decimal_a_hora(
                        inicio_h
                    )

                    fin_txt = decimal_a_hora(
                        fin_h
                    )

                    presencia_valida = (
                        hay_presencia_en_intervalo(
                            ventanas_presencia,
                            inicio_txt,
                            fin_txt,
                        )
                    )

                    if (
                        servicio[
                            "requiere_presencia"
                        ]
                        and not presencia_valida
                    ):
                        continue

                    if not comprobar_potencia_disponible(
                        agenda,
                        fecha,
                        inicio_h,
                        servicio[
                            "duracion_h"
                        ],
                        servicio[
                            "potencia_kw"
                        ],
                    ):
                        continue

                    potencia_actual = max(
                        agenda[
                            fecha
                        ].get(
                            round(
                                inicio_h,
                                2,
                            ),
                            0.0,
                        ),
                        0.0,
                    )

                    puntuacion = puntuar_tarea(
                        servicio,
                        dia,
                        indice_dia,
                        inicio_h,
                        presencia_valida,
                        potencia_actual,
                    )

                    candidatos.append(
                        {
                            "fecha": fecha,

                            "indice_dia": indice_dia,

                            "inicio_h": inicio_h,

                            "fin_h": fin_h,

                            "inicio": inicio_txt,

                            "fin": fin_txt,

                            "puntuacion": (
                                puntuacion
                            ),

                            "score_solar": float(
                                dia.get(
                                    "score",
                                    0.5,
                                )
                            ),
                        }
                    )

            if not candidatos:
                continue

            mejor = max(
                candidatos,
                key=lambda c: c[
                    "puntuacion"
                ],
            )

            reservar_potencia(
                agenda,
                mejor[
                    "fecha"
                ],
                mejor[
                    "inicio_h"
                ],
                servicio[
                    "duracion_h"
                ],
                servicio[
                    "potencia_kw"
                ],
            )

            dias_utilizados.add(
                mejor[
                    "fecha"
                ]
            )

            resultado.append(
                {
                    "servicio": servicio[
                        "nombre"
                    ],

                    "descripcion": servicio[
                        "descripcion"
                    ],

                    "tipo": "tarea",

                    "fecha": mejor[
                        "fecha"
                    ],

                    "dia_semana": nombre_dia_semana(
                        mejor[
                            "fecha"
                        ]
                    ),

                    "hora_inicio": mejor[
                        "inicio"
                    ],

                    "hora_fin": mejor[
                        "fin"
                    ],

                    "potencia_kw": servicio[
                        "potencia_kw"
                    ],

                    "score_solar": mejor[
                        "score_solar"
                    ],

                    "confianza": confianza_por_horizonte(
                        mejor[
                            "indice_dia"
                        ]
                    ),

                    "numero_ejecucion": (
                        repeticion
                        + 1
                    ),

                    "motivo": (
                        "Servicio colocado en una ventana "
                        "solar evitando concentrar cargas "
                        "flexibles simultáneamente."
                    ),
                }
            )

    return resultado


# ==========================================================
# Planificación de climatización
# ==========================================================

def planificar_cargas_termicas(
    servicios,
    prevision,
    estacion,
):
    """
    Genera ventanas orientativas para climatización.

    La climatización no se trata como una tarea puntual.
    """

    resultado = []

    servicios_termicos = [
        s
        for s in servicios
        if s[
            "tipo"
        ] == "termica"
    ]

    for servicio in servicios_termicos:

        nombre = servicio[
            "nombre"
        ].lower()

        # ACS se gestiona separadamente.
        if (
            "acs" in nombre
            or "termo" in nombre
        ):
            continue

        for indice, dia in enumerate(
            prevision
        ):

            fecha = dia[
                "fecha"
            ]

            score = float(
                dia.get(
                    "score",
                    0.5,
                )
            )

            if estacion == "verano":

                inicio = "12:00"
                fin = "18:00"

                estrategia = (
                    "Climatizar durante la ventana solar. "
                    "Aprovechar FV directa y evitar funcionamiento "
                    "nocturno siempre que el confort lo permita."
                )

            else:

                inicio = "18:00"
                fin = "22:00"

                estrategia = (
                    "Utilizar la bomba de calor en la ventana "
                    "habitual de ocupación. Considerar "
                    "precalentamiento solar si existe excedente."
                )

            resultado.append(
                {
                    "servicio": servicio[
                        "nombre"
                    ],

                    "descripcion": servicio[
                        "descripcion"
                    ],

                    "tipo": "termica",

                    "fecha": fecha,

                    "dia_semana": nombre_dia_semana(
                        fecha
                    ),

                    "hora_inicio": inicio,

                    "hora_fin": fin,

                    "score_solar": score,

                    "confianza": confianza_por_horizonte(
                        indice
                    ),

                    "motivo": estrategia,
                }
            )

    return resultado


# ==========================================================
# ACS
# ==========================================================

def planificar_acs(
    demanda,
    prevision,
):
    """
    Planifica la estrategia ACS.

    El termo eléctrico NO se programa de forma automática.
    """

    acs = demanda.get(
        "acs",
        {},
    )

    if not acs:
        return []

    resultado = []

    for indice, dia in enumerate(
        prevision
    ):

        fecha = dia[
            "fecha"
        ]

        score = float(
            dia.get(
                "score",
                0.5,
            )
        )

        if score >= INDICE_SOLAR_BUENO:

            accion = (
                "Priorizar captación solar térmica y bomba "
                "de intercambio. No activar termo eléctrico "
                "salvo temperatura insuficiente."
            )

            termo = "condicional"

        elif score >= INDICE_SOLAR_ACEPTABLE:

            accion = (
                "Comprobar temperatura del acumulador solar. "
                "Usar termo eléctrico únicamente como apoyo."
            )

            termo = "posible"

        else:

            accion = (
                "Probable necesidad de apoyo eléctrico para ACS. "
                "Preferir una hora de bajo precio o producción FV."
            )

            termo = "probable"

        resultado.append(
            {
                "servicio": "ACS",

                "tipo": "condicional",

                "fecha": fecha,

                "dia_semana": nombre_dia_semana(
                    fecha
                ),

                "hora_inicio": "12:00",

                "hora_fin": "17:00",

                "score_solar": score,

                "confianza": confianza_por_horizonte(
                    indice
                ),

                "estado_termo_electrico": termo,

                "motivo": accion,
            }
        )

    return resultado


# ==========================================================
# Riego
# ==========================================================

def planificar_riego(
    servicios,
    prevision,
):
    """
    Planifica el riego fuera de las horas centrales.

    Se prioriza eficiencia hídrica frente al pequeño ahorro
    eléctrico potencial.
    """

    resultado = []

    servicios_riego = [
        s
        for s in servicios
        if s[
            "tipo"
        ] == "restriccion_externa"
    ]

    for servicio in servicios_riego:

        frecuencia = min(
            servicio[
                "frecuencia_semanal"
            ],
            len(
                prevision
            ),
        )

        # --------------------------------------------------
        # Se prefieren días con menor probabilidad de lluvia.
        # --------------------------------------------------

        dias_ordenados = sorted(
            enumerate(
                prevision
            ),
            key=lambda elemento: (
                float(
                    elemento[
                        1
                    ].get(
                        "precip",
                        0.0,
                    )
                    or 0.0
                ),
                elemento[
                    0
                ],
            ),
        )

        for numero, (
            indice,
            dia,
        ) in enumerate(
            dias_ordenados[
                :frecuencia
            ]
        ):

            fecha = dia[
                "fecha"
            ]

            ventana = (
                VENTANAS_RIEGO_PREFERIDAS[
                    0
                ]
            )

            resultado.append(
                {
                    "servicio": servicio[
                        "nombre"
                    ],

                    "descripcion": servicio[
                        "descripcion"
                    ],

                    "tipo": "restriccion_externa",

                    "fecha": fecha,

                    "dia_semana": nombre_dia_semana(
                        fecha
                    ),

                    "hora_inicio": ventana[
                        0
                    ],

                    "hora_fin": ventana[
                        1
                    ],

                    "potencia_kw": servicio[
                        "potencia_kw"
                    ],

                    "confianza": confianza_por_horizonte(
                        indice
                    ),

                    "numero_ejecucion": (
                        numero
                        + 1
                    ),

                    "motivo": (
                        "Se prioriza eficiencia hídrica y baja "
                        "probabilidad de precipitación frente "
                        "al aprovechamiento del máximo solar."
                    ),
                }
            )

    return resultado


# ==========================================================
# Hornos solares
# ==========================================================

def planificar_hornos_solares(
    demanda,
    prevision,
):
    """
    Identifica oportunidades de cocina solar.
    """

    configuracion = demanda.get(
        "hornos_solares",
        {},
    )

    if not configuracion:
        return []

    umbral = float(
        configuracion.get(
            "indice_solar_minimo_recomendado",
            0.75,
        )
    )

    resultado = []

    for indice, dia in enumerate(
        prevision
    ):

        score = float(
            dia.get(
                "score",
                0.0,
            )
        )

        if score < umbral:
            continue

        fecha = dia[
            "fecha"
        ]

        resultado.append(
            {
                "servicio": "hornos_solares",

                "tipo": "alternativa_solar",

                "fecha": fecha,

                "dia_semana": nombre_dia_semana(
                    fecha
                ),

                "hora_inicio": "12:00",

                "hora_fin": "16:00",

                "score_solar": score,

                "confianza": confianza_por_horizonte(
                    indice
                ),

                "motivo": (
                    "Puede sustituirse parcial o totalmente "
                    "la cocina eléctrica por cocina solar."
                ),
            }
        )

    return resultado


# ==========================================================
# Resumen meteorológico semanal
# ==========================================================

def construir_resumen_dias(
    prevision,
):
    """
    Construye el resumen de los días.
    """

    resultado = []

    for indice, dia in enumerate(
        prevision
    ):

        resultado.append(
            {
                "fecha": dia[
                    "fecha"
                ],

                "dia_semana": nombre_dia_semana(
                    dia[
                        "fecha"
                    ]
                ),

                "score_solar": float(
                    dia.get(
                        "score",
                        0.5,
                    )
                ),

                "calidad_solar": clasificar_dia_solar(
                    dia.get(
                        "score",
                        0.5,
                    )
                ),

                "precipitacion": dia.get(
                    "precip"
                ),

                "temperatura_max": dia.get(
                    "tmax"
                ),

                "confianza": confianza_por_horizonte(
                    indice
                ),
            }
        )

    return resultado


# ==========================================================
# Plan semanal completo
# ==========================================================

def generar_plan_semanal(
    demanda,
    prevision_semanal,
    estacion=None,
    horizonte_dias=HORIZONTE_DIAS_DEFAULT,
):
    """
    Genera un plan semanal coordinado de servicios.
    """

    if not prevision_semanal:

        raise ValueError(
            "No existe predicción semanal."
        )

    prevision = prevision_semanal[
        :horizonte_dias
    ]

    # ------------------------------------------------------
    # Estación
    # ------------------------------------------------------

    if estacion is None:

        estacion = demanda.get(
            "estacion"
        )

    if estacion is None:

        mes = prevision[
            0
        ][
            "fecha"
        ].month

        if mes in (
            5,
            6,
            7,
            8,
            9,
        ):

            estacion = "verano"

        else:

            estacion = "invierno"

    # ------------------------------------------------------
    # Servicios
    # ------------------------------------------------------

    servicios = extraer_servicios(
        demanda
    )

    servicios = [
        s
        for s in servicios
        if servicio_activo_en_estacion(
            s,
            estacion,
        )
    ]

    # ------------------------------------------------------
    # Agenda conjunta de potencia
    # ------------------------------------------------------

    agenda = crear_agenda_potencia(
        prevision
    )

    # ------------------------------------------------------
    # Tareas desplazables
    # ------------------------------------------------------

    tareas = planificar_tareas(
        servicios=servicios,
        prevision=prevision,
        demanda=demanda,
        estacion=estacion,
        agenda=agenda,
    )

    # ------------------------------------------------------
    # Cargas térmicas
    # ------------------------------------------------------

    termicas = planificar_cargas_termicas(
        servicios=servicios,
        prevision=prevision,
        estacion=estacion,
    )

    # ------------------------------------------------------
    # ACS
    # ------------------------------------------------------

    acs = planificar_acs(
        demanda,
        prevision,
    )

    # ------------------------------------------------------
    # Riego
    # ------------------------------------------------------

    riego = planificar_riego(
        servicios,
        prevision,
    )

    # ------------------------------------------------------
    # Hornos solares
    # ------------------------------------------------------

    hornos = planificar_hornos_solares(
        demanda,
        prevision,
    )

    return {
        "version": 2,

        "estacion": estacion,

        "horizonte_dias": len(
            prevision
        ),

        "dias": construir_resumen_dias(
            prevision
        ),

        "tareas": tareas,

        "termicas": termicas,

        "acs": acs,

        "riego": riego,

        "hornos_solares": hornos,

        "agenda_potencia": agenda,
    }


# ==========================================================
# Presentación
# ==========================================================

def mostrar_plan_semanal(
    plan,
):
    """
    Presenta el plan semanal.
    """

    print()
    print("Plan semanal sostenible de servicios")
    print("------------------------------------")

    print(
        f"Versión                : "
        f"{plan['version']}"
    )

    print(
        f"Estación               : "
        f"{plan['estacion']}"
    )

    print(
        f"Horizonte              : "
        f"{plan['horizonte_dias']} días"
    )

    # ======================================================
    # Meteorología
    # ======================================================

    print()
    print("Resumen semanal")
    print("---------------")

    print(
        f"{'Día':<12}"
        f"{'Fecha':<12}"
        f"{'Solar':>8}"
        f"{'Calidad':>12}"
        f"{'Confianza':>12}"
    )

    print(
        "-" * 56
    )

    for dia in plan[
        "dias"
    ]:

        print(
            f"{dia['dia_semana']:<12}"
            f"{dia['fecha'].strftime('%d/%m/%Y'):<12}"
            f"{dia['score_solar']:>8.2f}"
            f"{dia['calidad_solar']:>12}"
            f"{dia['confianza']:>12}"
        )

    # ======================================================
    # Tareas
    # ======================================================

    print()
    print("Tareas desplazables")
    print("-------------------")

    if not plan[
        "tareas"
    ]:

        print(
            "No existen tareas desplazables programadas."
        )

    else:

        tareas_ordenadas = sorted(
            plan[
                "tareas"
            ],
            key=lambda x: (
                x[
                    "fecha"
                ],
                x[
                    "hora_inicio"
                ],
            ),
        )

        for tarea in tareas_ordenadas:

            print(
                f"{tarea['dia_semana']} "
                f"{tarea['fecha'].strftime('%d/%m/%Y')} "
                f"{tarea['hora_inicio']}–"
                f"{tarea['hora_fin']} | "
                f"{tarea['descripcion']} "
                f"({tarea['potencia_kw']:.2f} kW)"
            )

    # ======================================================
    # Climatización
    # ======================================================

    if plan[
        "termicas"
    ]:

        print()
        print("Gestión térmica")
        print("---------------")

        for entrada in plan[
            "termicas"
        ]:

            print(
                f"{entrada['dia_semana']} "
                f"{entrada['fecha'].strftime('%d/%m/%Y')} | "
                f"{entrada['servicio']} | "
                f"{entrada['hora_inicio']}–"
                f"{entrada['hora_fin']}"
            )

    # ======================================================
    # ACS
    # ======================================================

    if plan[
        "acs"
    ]:

        print()
        print("ACS")
        print("---")

        for entrada in plan[
            "acs"
        ]:

            print(
                f"{entrada['dia_semana']} "
                f"{entrada['fecha'].strftime('%d/%m/%Y')}: "
                f"{entrada['motivo']}"
            )

    # ======================================================
    # Riego
    # ======================================================

    if plan[
        "riego"
    ]:

        print()
        print("Riego")
        print("-----")

        for entrada in plan[
            "riego"
        ]:

            print(
                f"{entrada['dia_semana']} "
                f"{entrada['fecha'].strftime('%d/%m/%Y')} "
                f"{entrada['hora_inicio']}–"
                f"{entrada['hora_fin']} | "
                f"{entrada['servicio']}"
            )

    # ======================================================
    # Hornos solares
    # ======================================================

    if plan[
        "hornos_solares"
    ]:

        print()
        print("Cocina solar")
        print("------------")

        for entrada in plan[
            "hornos_solares"
        ]:

            print(
                f"{entrada['dia_semana']} "
                f"{entrada['fecha'].strftime('%d/%m/%Y')} "
                f"{entrada['hora_inicio']}–"
                f"{entrada['hora_fin']} | "
                f"índice solar "
                f"{entrada['score_solar']:.2f}"
            )


# ==========================================================
# Prueba independiente
# ==========================================================

if __name__ == "__main__":

    from config import (
        obtener_configuracion_sistema,
    )

    from demand import (
        obtener_configuracion_demanda,
    )

    from aemet import (
        obtener_prevision_solar,
    )

    configuracion = (
        obtener_configuracion_sistema()
    )

    municipio = configuracion[
        "localizacion"
    ][
        "municipio"
    ]

    hoy = datetime.now().date()

    demanda = obtener_configuracion_demanda(
        fecha=hoy
    )

    prevision = obtener_prevision_solar(
        municipio
    )

    plan = generar_plan_semanal(
        demanda=demanda,
        prevision_semanal=prevision,
    )

    mostrar_plan_semanal(
        plan
    )
