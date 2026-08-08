#!/usr/bin/env python3
"""
optimizer.py

Módulo de optimización para la gestión energética de una
instalación fotovoltaica con batería conectada a red.

Este módulo constituye el núcleo de decisión del sistema.

Recibe información procedente de:

    - AEMET:
        predicción meteorológica y disponibilidad solar.

    - ESIOS:
        precios horarios de compra y compensación de excedentes.

    - Sistema físico:
        características del inversor, paneles y baterías.

    - Usuario:
        demanda eléctrica, cargas flexibles y preferencias.

Y devuelve un plan de operación.

----------------------------------------------------------------
ESTRATEGIAS DISPONIBLES
----------------------------------------------------------------

1. economica
   Minimiza prioritariamente el coste económico.

2. autoconsumo
   Maximiza el aprovechamiento local de la energía fotovoltaica.

3. min_ciclos
   Reduce el uso y ciclado de la batería.

4. sostenible_jerarquica
   Aplica una jerarquía fija orientada a sostenibilidad.

5. sostenible_predictiva
   Estrategia principal del proyecto.

   Utiliza conjuntamente:

       - previsión solar;
       - precios futuros;
       - demanda prevista;
       - estado de carga;
       - degradación de batería;
       - disponibilidad futura de energía.

   Su objetivo principal es preservar la batería y utilizarla
   únicamente cuando su uso esté justificado desde el punto de
   vista energético, ambiental y económico.

----------------------------------------------------------------
FILOSOFÍA GENERAL
----------------------------------------------------------------

La optimización sostenible sigue aproximadamente esta jerarquía:

    1. Seguridad y restricciones técnicas.
    2. Satisfacción de cargas esenciales.
    3. Preservación de la vida útil de la batería.
    4. Autoconsumo solar directo.
    5. Programación de cargas flexibles.
    6. Reducción del coste de compra.
    7. Vertido de excedentes.

La batería NO se considera simplemente un recurso económico.

Cada ciclo tiene un coste físico y ambiental.

Por tanto, una operación económicamente rentable puede ser
rechazada si produce un desgaste innecesario de la batería.

Autor: Enrique M. Moreno Pérez
"""

# ==========================================================
# Importaciones
# ==========================================================

from typing import Any, Dict, List, Optional


# ==========================================================
# Nombres oficiales de las estrategias
# ==========================================================

ESTRATEGIA_ECONOMICA = "economica"

ESTRATEGIA_AUTOCONSUMO = "autoconsumo"

ESTRATEGIA_MIN_CICLOS = "min_ciclos"

ESTRATEGIA_SOSTENIBLE_JERARQUICA = (
    "sostenible_jerarquica"
)

ESTRATEGIA_SOSTENIBLE_PREDICTIVA = (
    "sostenible_predictiva"
)


ESTRATEGIAS_DISPONIBLES = [
    ESTRATEGIA_ECONOMICA,
    ESTRATEGIA_AUTOCONSUMO,
    ESTRATEGIA_MIN_CICLOS,
    ESTRATEGIA_SOSTENIBLE_JERARQUICA,
    ESTRATEGIA_SOSTENIBLE_PREDICTIVA,
]


# ==========================================================
# Estrategia predeterminada
# ==========================================================

# La estrategia sostenible predictiva se considera la estrategia
# principal del proyecto.
#
# El usuario podrá seleccionar cualquier otra, pero ésta será la
# opción utilizada por defecto.

ESTRATEGIA_DEFAULT = (
    ESTRATEGIA_SOSTENIBLE_PREDICTIVA
)


# ==========================================================
# Parámetros iniciales de sostenibilidad
# ==========================================================

# Estos parámetros son todavía valores generales del algoritmo.
#
# NO representan aún las especificaciones definitivas de una
# batería concreta.
#
# Más adelante serán sustituidos o sobrescritos por los valores
# definidos en config.py para cada instalación.


SOC_MIN_NORMAL = 0.20

SOC_MAX_NORMAL = 0.85

SOC_MIN_EMERGENCIA = 0.10

SOC_MAX_EMERGENCIA = 0.95


# Diferencia mínima de precio que debe existir antes de considerar
# que un arbitraje eléctrico podría ser interesante.
#
# El valor definitivo deberá considerar:
#
# - eficiencia de carga;
# - eficiencia de descarga;
# - degradación de batería;
# - estrategia seleccionada.

MARGEN_ECONOMICO_MINIMO = 0.02


# ==========================================================
# Validación de estrategia
# ==========================================================

def validar_estrategia(
    estrategia: str,
) -> str:
    """
    Comprueba que la estrategia solicitada existe.

    Parameters
    ----------
    estrategia : str
        Nombre de la estrategia.

    Returns
    -------
    str
        Nombre validado.

    Raises
    ------
    ValueError
        Si la estrategia no existe.
    """

    estrategia = str(
        estrategia
    ).strip().lower()

    if estrategia not in ESTRATEGIAS_DISPONIBLES:

        raise ValueError(
            f"Estrategia no válida: '{estrategia}'. "
            f"Estrategias disponibles: "
            f"{', '.join(ESTRATEGIAS_DISPONIBLES)}"
        )

    return estrategia


# ==========================================================
# Validación básica del estado del sistema
# ==========================================================

def obtener_soc(
    sistema: Dict[str, Any],
) -> Optional[float]:
    """
    Extrae el SOC de la batería desde el diccionario del sistema.

    El SOC debe expresarse como una fracción entre 0 y 1.

    Ejemplos
    --------
    0.20 -> 20 %
    0.75 -> 75 %

    Parameters
    ----------
    sistema : dict
        Estado actual del sistema energético.

    Returns
    -------
    float or None
        SOC si está disponible.
    """

    soc = sistema.get(
        "soc"
    )

    if soc is None:
        return None

    soc = float(
        soc
    )

    if not 0.0 <= soc <= 1.0:

        raise ValueError(
            "El SOC debe estar comprendido "
            "entre 0 y 1."
        )

    return soc


# ==========================================================
# Clasificación meteorológica
# ==========================================================

def clasificar_prevision_solar(
    prevision: Dict[str, Any],
) -> str:
    """
    Clasifica cualitativamente la previsión solar.

    Parameters
    ----------
    prevision : dict
        Predicción procesada por aemet.py.

    Returns
    -------
    str
        alta, media o baja.
    """

    score = float(
        prevision.get(
            "score",
            0.5,
        )
    )

    if score >= 0.75:
        return "alta"

    if score >= 0.50:
        return "media"

    return "baja"


# ==========================================================
# Análisis económico básico
# ==========================================================

def analizar_precios(
    precios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Extrae información económica básica de una serie horaria.

    Esta función NO decide qué debe hacer la batería.

    Únicamente obtiene datos que las estrategias podrán utilizar.

    Parameters
    ----------
    precios : list
        Tabla generada por esios.obtener_precios().

    Returns
    -------
    dict
        Información económica resumida.
    """

    if not precios:

        return {
            "hora_compra_minima": None,
            "hora_compra_maxima": None,
            "hora_venta_maxima": None,
            "spread_maximo": None,
        }

    compra_minima = min(
        precios,
        key=lambda registro: registro["compra"],
    )

    compra_maxima = max(
        precios,
        key=lambda registro: registro["compra"],
    )

    venta_maxima = max(
        precios,
        key=lambda registro: registro["venta"],
    )

    spread_maximo = max(
        precios,
        key=lambda registro: (
            registro["compra"]
            - registro["venta"]
        ),
    )

    return {
        "hora_compra_minima": compra_minima,
        "hora_compra_maxima": compra_maxima,
        "hora_venta_maxima": venta_maxima,
        "spread_maximo": spread_maximo,
    }

# ==========================================================
# Análisis de la demanda doméstica
# ==========================================================

def analizar_demanda(
    demanda: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Analiza la configuración doméstica procedente de demand.py.

    Extrae información general sobre las cargas de la vivienda
    y conserva también el perfil horario de 24 horas generado
    por demand.py.

    Parameters
    ----------
    demanda : dict, optional
        Configuración devuelta por
        demand.obtener_configuracion_demanda().

    Returns
    -------
    dict
        Resumen de las características de demanda.
    """

    # ------------------------------------------------------
    # Comprobación inicial
    # ------------------------------------------------------

    if not demanda:
        return {}

    # ------------------------------------------------------
    # Lista de cargas
    # ------------------------------------------------------

    cargas = demanda.get(
        "cargas",
        [],
    )

    # ------------------------------------------------------
    # Clasificación de cargas
    # ------------------------------------------------------

    cargas_flexibles = [
        carga
        for carga in cargas
        if carga.get(
            "flexible",
            False,
        )
    ]

    cargas_automaticas = [
        carga
        for carga in cargas
        if carga.get(
            "automatizable",
            False,
        )
    ]

    cargas_presencia = [
        carga
        for carga in cargas
        if carga.get(
            "requiere_presencia",
            False,
        )
    ]

    cargas_esenciales = [
        carga
        for carga in cargas
        if carga.get(
            "prioridad"
        ) == 1
    ]

    # ------------------------------------------------------
    # Construcción del resumen de demanda
    # ------------------------------------------------------

    return {
        "numero_cargas": len(
            cargas
        ),

        "cargas_flexibles": len(
            cargas_flexibles
        ),

        "cargas_automaticas": len(
            cargas_automaticas
        ),

        "cargas_con_presencia": len(
            cargas_presencia
        ),

        "cargas_esenciales": len(
            cargas_esenciales
        ),

        "potencia_base_kw": demanda.get(
            "potencia_base_kw",
            0.0,
        ),

        "prioridad_red_sobre_bateria": demanda.get(
            "prioridad_red_sobre_bateria",
            False,
        ),

        # --------------------------------------------------
        # Recursos energéticos alternativos
        # --------------------------------------------------

        "hornos_solares": demanda.get(
            "hornos_solares",
            {},
        ),

        "acs": demanda.get(
            "acs",
            {},
        ),

        # --------------------------------------------------
        # Política sostenible
        # --------------------------------------------------

        "politica_bateria": demanda.get(
            "politica_bateria",
            {},
        ),

        "jerarquia_sostenible": demanda.get(
            "jerarquia_sostenible",
            [],
        ),

        # --------------------------------------------------
        # Perfil horario de demanda
        # --------------------------------------------------

        "perfil_24h": demanda.get(
            "perfil_24h"
        ),

        "energia_diaria_teorica_kwh": demanda.get(
            "energia_diaria_teorica_kwh"
        ),

        "estacion": demanda.get(
            "estacion"
        ),

        "tipo_dia": demanda.get(
            "tipo_dia"
        ),
    }

# ==========================================================
# Estructura común de resultado
# ==========================================================

def crear_plan_base(
    estrategia: str,
) -> Dict[str, Any]:
    """
    Crea la estructura común utilizada por todas las estrategias.

    Returns
    -------
    dict
        Plan energético inicialmente vacío.
    """

    return {
        "estrategia": estrategia,

        # Acciones recomendadas.
        "acciones": [],

        # Información utilizada para justificar las decisiones.
        "razones": [],

        # Prioridad ambiental.
        "sostenibilidad": {},

        # Información económica relevante.
        "economia": {},

        # Información meteorológica.
        "meteorologia": {},

        # Demanda.
        "demanda": {},

        # En la siguiente fase contendrá las decisiones
        # correspondientes a cada intervalo temporal.
        "plan_horario": [],


        # Métricas que posteriormente se utilizarán para comparar
        # estrategias.
        "metricas": {
            "energia_demanda_kwh": None,
            "energia_fv_kwh": None,

            "energia_bateria_kwh": None,
            "ciclos_equivalentes": None,

            "coste_estimado": None,

            "energia_red_kwh": None,
            "energia_vertida_kwh": None,

            "autoconsumo_pct": None,
},
    }


# ==========================================================
# Estrategia 1: control económico puro
# ==========================================================

def estrategia_economica(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Estrategia orientada principalmente a minimizar el coste.

    Principio
    ---------
    La batería puede utilizarse para realizar arbitraje temporal:

        comprar/cargar cuando la energía es barata;

        descargar cuando la energía es cara.

    La degradación de la batería se considera una restricción
    secundaria.

    Esta estrategia servirá principalmente como referencia
    comparativa para el artículo.
    """

    plan = crear_plan_base(
        ESTRATEGIA_ECONOMICA
    )
    
    plan["demanda"] = analizar_demanda(
        demanda
    )

    analisis = analizar_precios(
        precios
    )

    demanda_info = analizar_demanda(
        demanda
    )

    plan["economia"] = analisis
    plan["demanda"] = demanda_info

    plan["acciones"].append(
        "Priorizar las horas de menor precio "
        "para consumo o carga."
    )

    plan["acciones"].append(
        "Priorizar la descarga de batería "
        "durante las horas de mayor precio."
    )

    plan["razones"].append(
        "La estrategia económica busca minimizar "
        "el coste neto de energía."
    )

    return plan


# ==========================================================
# Estrategia 2: maximización del autoconsumo
# ==========================================================

def estrategia_autoconsumo(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Estrategia orientada a maximizar el aprovechamiento local
    de la producción fotovoltaica.

    Jerarquía aproximada:

        FV -> consumo directo
        FV -> batería
        FV -> red

    Esta estrategia puede aumentar el ciclado de batería porque
    intenta evitar vertidos incluso cuando almacenarlos aporta
    poco beneficio.
    """

    plan = crear_plan_base(
        ESTRATEGIA_AUTOCONSUMO
    )

    calidad_solar = clasificar_prevision_solar(
        prevision
    )

    plan["meteorologia"][
        "calidad_solar"
    ] = calidad_solar

    plan["acciones"].append(
        "Cubrir primero la demanda directamente "
        "con producción fotovoltaica."
    )

    plan["acciones"].append(
        "Utilizar excedentes solares para cargar "
        "la batería."
    )

    plan["acciones"].append(
        "Verter a la red únicamente cuando no exista "
        "capacidad útil de almacenamiento."
    )

    plan["razones"].append(
        "La prioridad es maximizar el porcentaje "
        "de energía fotovoltaica utilizada localmente."
    )

    return plan


# ==========================================================
# Estrategia 3: minimización de ciclos
# ==========================================================

def estrategia_min_ciclos(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Estrategia orientada a minimizar el uso de la batería.

    Principio
    ---------
    La batería se utiliza solamente cuando existe una necesidad
    clara.

    Se evita:

        - cargar y descargar por diferencias económicas pequeñas;
        - almacenar excedentes que probablemente no se utilizarán;
        - realizar ciclos profundos innecesarios;
        - utilizar la batería cuando puede utilizarse directamente
          energía solar o de red.

    Esta estrategia será una referencia importante para estudiar
    la vida útil de la batería.
    """

    plan = crear_plan_base(
        ESTRATEGIA_MIN_CICLOS
    )

    soc = obtener_soc(
        sistema
    )

    plan["sostenibilidad"][
        "soc"
    ] = soc

    plan["acciones"].append(
        "Priorizar consumo fotovoltaico directo."
    )

    plan["acciones"].append(
        "Evitar cargar la batería si la energía "
        "almacenada no será necesaria."
    )

    plan["acciones"].append(
        "Evitar arbitraje de precios mediante batería "
        "salvo diferencias económicas claramente justificadas."
    )

    plan["razones"].append(
        "La estrategia minimiza la energía total "
        "procesada por la batería."
    )

    return plan


# ==========================================================
# Estrategia 4: sostenible jerárquica
# ==========================================================

def estrategia_sostenible_jerarquica(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Estrategia sostenible basada en una jerarquía fija.

    Orden de prioridad
    ------------------

    1. Seguridad.
    2. Cargas esenciales.
    3. Preservación de batería.
    4. Autoconsumo directo.
    5. Cargas flexibles.
    6. Economía.
    7. Vertido.

    A diferencia de la estrategia sostenible predictiva, esta
    versión no realiza todavía una optimización explícita del
    futuro.
    """

    plan = crear_plan_base(
        ESTRATEGIA_SOSTENIBLE_JERARQUICA
    )

    soc = obtener_soc(
        sistema
    )

    calidad_solar = clasificar_prevision_solar(
        prevision
    )

    plan["sostenibilidad"][
        "soc"
    ] = soc

    plan["meteorologia"][
        "calidad_solar"
    ] = calidad_solar

    plan["acciones"].append(
        "Mantener la batería dentro de una ventana "
        "de SOC conservadora."
    )

    plan["acciones"].append(
        "Priorizar consumo solar directo."
    )

    plan["acciones"].append(
        "Evitar ciclos que no aporten un beneficio "
        "energético significativo."
    )

    plan["acciones"].append(
        "Utilizar criterios económicos únicamente "
        "después de satisfacer los criterios de sostenibilidad."
    )

    plan["razones"].append(
        "La sostenibilidad de la batería tiene prioridad "
        "sobre la optimización económica."
    )

    return plan


def estrategia_sostenible_predictiva(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Estrategia principal del proyecto.

    Utiliza información futura para decidir si el uso de la
    batería está justificado.

    Variables previstas
    -------------------

    - producción fotovoltaica;
    - condiciones meteorológicas;
    - precio de compra;
    - precio de venta;
    - demanda;
    - estado de carga;
    - necesidades futuras;
    - degradación estimada de batería.

    Filosofía
    ---------

    No se pregunta únicamente:

        "¿Es rentable descargar ahora?"

    sino:

        "¿Necesitaré esta energía después?"

        "¿Habrá suficiente sol mañana?"

        "¿Compensa utilizar un ciclo de batería?"

        "¿Es mejor utilizar red y preservar batería?"

        "¿Debo reservar energía para una hora futura más cara?"

    La flexibilidad doméstica se utiliza antes de recurrir
    al almacenamiento electroquímico.

    Esta estrategia constituye el núcleo principal del trabajo.
    """

    # ------------------------------------------------------
    # Creación del plan
    # ------------------------------------------------------

    plan = crear_plan_base(
        ESTRATEGIA_SOSTENIBLE_PREDICTIVA
    )

    # ------------------------------------------------------
    # Estado de batería
    # ------------------------------------------------------

    soc = obtener_soc(
        sistema
    )

    # ------------------------------------------------------
    # Información meteorológica
    # ------------------------------------------------------

    calidad_solar = clasificar_prevision_solar(
        prevision
    )

    # ------------------------------------------------------
    # Información económica
    # ------------------------------------------------------

    analisis = analizar_precios(
        precios
    )

    # ------------------------------------------------------
    # Información de demanda doméstica
    # ------------------------------------------------------

    demanda_info = analizar_demanda(
        demanda
    )

    # ------------------------------------------------------
    # Almacenar información en el plan
    # ------------------------------------------------------

    plan["sostenibilidad"][
        "soc"
    ] = soc

    plan["meteorologia"][
        "calidad_solar"
    ] = calidad_solar

    plan["meteorologia"][
        "indice_solar"
    ] = prevision.get(
        "score"
    )

    plan["economia"] = analisis

    plan["demanda"] = demanda_info

    # ======================================================
    # Métricas iniciales de demanda
    # ======================================================
    #
    # demand.py ya proporciona un perfil horario de 24 horas.
    #
    # A partir de él podemos obtener dos primeras magnitudes:
    #
    #     - energía diaria teórica;
    #     - hora de máxima demanda.
    #
    # Todavía no existe balance FV-red-batería.
    # Por tanto, estas métricas describen únicamente la demanda.

    energia_demanda = demanda_info.get(
        "energia_diaria_teorica_kwh"
    )

    if energia_demanda is not None:

        plan["metricas"][
            "energia_demanda_kwh"
        ] = round(
            float(energia_demanda),
            3,
        )

    # ------------------------------------------------------
    # Pico horario de demanda
    # ------------------------------------------------------

    perfil_24h = demanda_info.get(
        "perfil_24h"
    )

    if perfil_24h:

        hora_pico = max(
            perfil_24h,
            key=lambda registro: registro[
                "potencia_total_kw"
            ],
        )

        plan["demanda"][
            "hora_pico_demanda"
        ] = hora_pico

    # ======================================================
    # Reglas meteorológicas preliminares
    # ======================================================

    if calidad_solar == "alta":

        plan["acciones"].append(
            "Esperar una producción fotovoltaica elevada."
        )

        plan["acciones"].append(
            "Priorizar autoconsumo directo."
        )

        plan["acciones"].append(
            "Concentrar las cargas flexibles "
            "en las horas de mayor disponibilidad solar."
        )

        plan["acciones"].append(
            "Evitar cargar desde red salvo necesidad "
            "energética justificada."
        )

    elif calidad_solar == "media":

        plan["acciones"].append(
            "Mantener una reserva moderada de batería."
        )

        plan["acciones"].append(
            "Desplazar, cuando sea posible, las cargas flexibles "
            "hacia las mejores horas solares."
        )

        plan["acciones"].append(
            "Combinar producción solar y red antes de recurrir "
            "a ciclos innecesarios de batería."
        )

    else:

        plan["acciones"].append(
            "No confiar en una elevada producción "
            "fotovoltaica durante el día."
        )

        plan["acciones"].append(
            "Priorizar la red frente a descargas de batería "
            "que no estén claramente justificadas."
        )

        plan["acciones"].append(
            "Evaluar carga desde red únicamente si existe "
            "una necesidad futura relevante."
        )

    # ======================================================
    # Gestión sostenible de la demanda doméstica
    # ======================================================

    if demanda_info:

        # --------------------------------------------------
        # Cargas flexibles
        # --------------------------------------------------

        numero_flexibles = demanda_info.get(
            "cargas_flexibles",
            0,
        )

        if numero_flexibles > 0:

            plan["acciones"].append(
                f"Se han identificado {numero_flexibles} "
                "cargas flexibles que pueden desplazarse "
                "hacia las horas solares."
            )

        # --------------------------------------------------
        # Hornos solares
        # --------------------------------------------------

        hornos_solares = demanda_info.get(
            "hornos_solares",
            {},
        )

        indice_minimo_hornos = hornos_solares.get(
            "indice_solar_minimo_recomendado",
            1.1,
        )

        indice_solar = float(
            prevision.get(
                "score",
                0.0,
            )
        )

        if (
            hornos_solares
            and indice_solar >= indice_minimo_hornos
        ):

            plan["acciones"].append(
                "Las condiciones solares permiten considerar "
                "el uso de los hornos solares en sustitución "
                "parcial de la cocina eléctrica."
            )

        # --------------------------------------------------
        # Agua caliente sanitaria
        # --------------------------------------------------

        acs = demanda_info.get(
            "acs",
            {},
        )

        solar_termico = acs.get(
            "solar_termico",
            {},
        )

        if solar_termico.get(
            "disponible",
            False,
        ):

            plan["acciones"].append(
                "Priorizar el sistema solar térmico y la bomba "
                "de intercambio antes de activar el termo "
                "eléctrico."
            )

        # --------------------------------------------------
        # Red frente a batería
        # --------------------------------------------------

        if demanda_info.get(
            "prioridad_red_sobre_bateria",
            False,
        ):

            plan["acciones"].append(
                "Cuando la producción solar sea insuficiente, "
                "priorizar la red frente a descargas de batería "
                "de escaso valor energético o económico."
            )

            plan["razones"].append(
                "El uso deliberado de la red puede reducir "
                "los ciclos equivalentes y prolongar la vida "
                "útil de la batería."
            )

    # ======================================================
    # Política de SOC
    # ======================================================

    if soc is not None:

        configuracion = sistema.get(
            "configuracion",
            {},
        )

        bateria = configuracion.get(
            "bateria",
            {},
        )

        soc_min_normal = bateria.get(
            "soc_min_normal",
            SOC_MIN_NORMAL,
        )

        soc_max_normal = bateria.get(
            "soc_max_normal",
            SOC_MAX_NORMAL,
        )

        if soc < soc_min_normal:

            plan["acciones"].append(
                "Evitar descargas adicionales de batería."
            )

            plan["razones"].append(
                "El SOC está por debajo de la ventana "
                "normal de operación sostenible."
            )

        elif soc > soc_max_normal:

            plan["acciones"].append(
                "Evitar mantener la batería durante periodos "
                "prolongados en SOC elevado."
            )

    # ======================================================
    # Filosofía ambiental
    # ======================================================

    plan["razones"].append(
        "La preservación de la vida útil de la batería "
        "tiene prioridad sobre beneficios económicos marginales."
    )

    plan["razones"].append(
        "La información meteorológica y económica futura "
        "se utiliza para evitar ciclos innecesarios."
    )

    plan["razones"].append(
        "Las cargas flexibles y el almacenamiento térmico "
        "deben aprovecharse antes que la batería."
    )

    return plan


# ==========================================================
# Selector general de estrategias
# ==========================================================

def optimizar(
    sistema: Dict[str, Any],
    prevision: Dict[str, Any],
    precios: List[Dict[str, Any]],
    demanda: Optional[List[Dict[str, Any]]] = None,
    estrategia: str = ESTRATEGIA_DEFAULT,
) -> Dict[str, Any]:
    """
    Ejecuta la estrategia seleccionada.

    Esta será la función principal utilizada por main.py.

    Parameters
    ----------
    sistema : dict
        Estado físico de la instalación.

    prevision : dict
        Información meteorológica de AEMET.

    precios : list
        Tabla horaria de ESIOS.

    demanda : list, optional
        Perfil previsto de consumo.

    estrategia : str
        Estrategia que se desea ejecutar.

    Returns
    -------
    dict
        Plan energético generado.
    """

    estrategia = validar_estrategia(
        estrategia
    )

    # ------------------------------------------------------
    # Control económico
    # ------------------------------------------------------

    if estrategia == ESTRATEGIA_ECONOMICA:

        return estrategia_economica(
            sistema,
            prevision,
            precios,
            demanda,
        )

    # ------------------------------------------------------
    # Maximización de autoconsumo
    # ------------------------------------------------------

    if estrategia == ESTRATEGIA_AUTOCONSUMO:

        return estrategia_autoconsumo(
            sistema,
            prevision,
            precios,
            demanda,
        )

    # ------------------------------------------------------
    # Minimización de ciclos
    # ------------------------------------------------------

    if estrategia == ESTRATEGIA_MIN_CICLOS:

        return estrategia_min_ciclos(
            sistema,
            prevision,
            precios,
            demanda,
        )

    # ------------------------------------------------------
    # Sostenibilidad jerárquica
    # ------------------------------------------------------

    if estrategia == ESTRATEGIA_SOSTENIBLE_JERARQUICA:

        return estrategia_sostenible_jerarquica(
            sistema,
            prevision,
            precios,
            demanda,
        )

    # ------------------------------------------------------
    # Sostenibilidad predictiva
    # ------------------------------------------------------

    if estrategia == ESTRATEGIA_SOSTENIBLE_PREDICTIVA:

        return estrategia_sostenible_predictiva(
            sistema,
            prevision,
            precios,
            demanda,
        )

    # Esta línea no debería alcanzarse porque la estrategia
    # ya ha sido validada.
    raise RuntimeError(
        "No se pudo seleccionar la estrategia."
    )
