[🇪🇸 Versión en español](ARCHITECTURE.md)

---

# System Architecture

## Predictive Solar Energy Management — Modular Design and Information Flow

This document describes the software architecture of **Predictive Solar Energy Management**.

The system has been designed with an explicit separation between:

- physical configuration;
- external data acquisition;
- demand modelling;
- photovoltaic prediction;
- energy balance;
- battery and grid dispatch;
- weekly planning;
- result presentation;
- future hardware communication.

The purpose of this separation is to keep the project:

- modular;
- verifiable;
- reproducible;
- extensible;
- independent of the inverter manufacturer;
- ready for experimental validation.

---

# 1. Overview

The current architecture can be represented as follows:

```text
                         ┌────────────────────┐
                         │     config.py      │
                         │ configuración fija │
                         └─────────┬──────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
     ┌────────────┐         ┌────────────┐         ┌──────────────┐
     │ demand.py  │         │  aemet.py  │         │ aemet_hourly│
     │  demanda   │         │   diaria   │         │     .py      │
     └─────┬──────┘         └─────┬──────┘         └──────┬───────┘
           │                      │                       │
           │                      └──────────┬────────────┘
           │                                 │
           │                                 ▼
           │                          ┌────────────┐
           │                          │  solar.py  │
           │                          │ modelo FV  │
           │                          └─────┬──────┘
           │                                │
           │                                ▼
           │                         perfil FV 24 h
           │                                │
           └───────────────┬────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ balance.py  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ dispatch.py │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │optimizer.py │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ weekly.py   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  main.py    │
                    └─────────────┘
```

---

# 2. Separation of Responsibilities

Each module should have a specific responsibility.

The architecture prevents a single file from:

- querying APIs;
- modelling the physics;
- calculating prices;
- deciding battery usage;
- scheduling tasks;
- controlling hardware.

This facilitates:

- debugging;
- independent validation;
- unit testing;
- module replacement;
- scientific reuse.

---

# 3. `config.py`

`config.py` contains the relatively permanent parameters of the installation.

Por ejemplo:

```text
localización
municipio
provincia
latitud
longitud
número de paneles
potencia instalada
inclinación
azimut
modelo de inversor
potencia nominal
capacidad de batería
SOC mínimo
SOC máximo
```

Conceptualmente:

```text
config.py
    ↓
describe el sistema físico
```

No debería contener lógica compleja de optimización.

---

# 4. `demand.py`

`demand.py` represents household energy behaviour.

Contiene:

- ocupantes;
- perfil base;
- cargas;
- potencia;
- duración;
- frecuencia;
- flexibilidad;
- presencia;
- automatización;
- ventanas horarias;
- comportamiento estacional.

Produce:

```text
perfil_24h
```

y una estructura de servicios utilizada posteriormente por `weekly.py`.

---

# 5. Load Types

La arquitectura distingue:

```text
tarea
termica
condicional
restriccion_externa
```

Esto es importante porque no todas las cargas admiten el mismo algoritmo.

Por ejemplo:

```text
lavadora -> tarea
```

```text
bomba de calor -> termica
```

```text
termo eléctrico -> condicional
```

```text
riego -> restriccion_externa
```

---

# 6. `aemet.py`

`aemet.py` handles the daily weather forecast.

Su responsabilidad es:

```text
AEMET
    ↓
datos meteorológicos
    ↓
estructura interna normalizada
```

Puede proporcionar:

- fecha;
- temperatura máxima;
- temperatura mínima;
- precipitación;
- estado del cielo;
- índice solar;
- penalizaciones meteorológicas.

No debe decidir:

- carga de batería;
- compra eléctrica;
- funcionamiento del inversor.

---

# 7. `aemet_hourly.py`

This module provides the hourly version of the forecast.

Su horizonte es aproximadamente:


```math
48\ \mathrm{h}
```


y puede proporcionar:

```text
datetime
temperatura
humedad
estado del cielo
precipitación
viento
factor de nubosidad
factor meteorológico
```

Su función es mejorar:

- producción FV;
- planificación térmica;
- decisiones próximas.

---

# 8. Difference Between Daily and Hourly AEMET

La arquitectura utiliza ambas resoluciones:

```text
AEMET horario
    ↓
corto plazo
    ↓
alta resolución

AEMET diario
    ↓
resto de semana
    ↓
menor resolución
```

Esto permite mantener un horizonte largo sin asumir una precisión horaria
irrealista.

---

# 9. `solar.py`

`solar.py` transforms:

```text
PVGIS
+
AEMET
+
configuración FV
```

en:

```text
perfil FV horario
```

Conceptualmente:


```math
P_{FV}(h)
=
f
\left(
G_{PVGIS},
F_{met},
T_{amb},
T_{cell},
P_{STC},
P_{inv}
\right)
```


---

# 10. PVGIS as a Physical Reference

PVGIS proporciona una referencia climatológica y geométrica.

AEMET modifica esa referencia según las condiciones previstas.

La arquitectura es:

```text
PVGIS
  │
  ▼
perfil físico de referencia
  │
  ▼
AEMET horario
  │
  ▼
corrección meteorológica
  │
  ▼
producción FV prevista
```

---

# 11. Weather-Source Hierarchy in `solar.py`

Puede utilizarse una jerarquía:

```text
1. AEMET horario
2. AEMET diario
3. PVGIS climatológico
```

Si falla la fuente más precisa, el sistema mantiene capacidad de cálculo con
una fuente de respaldo.

---

# 12. `esios.py`

The economic module retrieves electricity prices.

Produce series como:

```text
precio SPOT
precio de compra PVPC
precio de excedentes
```

Conceptualmente:

```text
ESIOS
  ↓
precios horarios
  ↓
balance económico
```

No debe contener lógica de despacho.

---

# 13. `balance.py`

`balance.py` combines:

```text
FV
+
demanda
+
precios
```

Para cada hora:


```math
B_h
=
P_{FV,h}
-
P_{D,h}
```


y calcula:

- autoconsumo;
- déficit;
- excedente;
- coste potencial;
- ingreso potencial.

---

# 14. Separation Between Balance and Dispatch

This distinction is fundamental.

`balance.py` responde:

> Is there a surplus or deficit?

`dispatch.py` responde:

> What should be done with that surplus or deficit?

---

# 15. `dispatch.py`

This module decides the energy flow.

Recibe:

```text
balance horario
SOC inicial
límites de batería
precios
```

y devuelve:

```text
SOC
carga batería
descarga batería
compra
venta
acción
```

---

# 16. Energy Flow

El sistema físico puede representarse así:

```text
                  ┌────────────┐
                  │     FV     │
                  └─────┬──────┘
                        │
                        ▼
                  ┌────────────┐
                  │  vivienda  │
                  └─────┬──────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      batería          red         excedente
          │             │             │
          │             │             ▼
          │             │           venta
          │             │
          ▼             ▼
       carga /        compra
       descarga
```

---

# 17. `optimizer.py`

`optimizer.py` contains the high-level strategy.

La estrategia actual principal es:

```text
sostenible_predictiva
```

Su papel es interpretar:

- previsión meteorológica;
- información económica;
- demanda;
- estado de batería;
- resultados del balance.

y generar:

- recomendaciones;
- justificación;
- métricas.

---

# 18. `weekly.py`

`weekly.py` operates at a higher time scale.

No decide únicamente flujo de energía.

Decide:

```text
cuándo conviene prestar servicios
```

como:

- lavadora;
- horno;
- robot de cocina;
- climatización;
- ACS;
- riego;
- cocina solar.

---

# 19. Time-Scale Architecture

Existen tres escalas principales:

```text
segundos/minutos
    ↓
futuro control real

horas
    ↓
dispatch

días
    ↓
weekly
```

---

# 20. Hourly Scale

En el nivel horario:

```text
FV(t)
demanda(t)
SOC(t)
precio(t)
```

producen:

```text
acción(t)
```

---

# 21. Weekly Scale

En el nivel semanal:

```text
meteorología
presencia
flexibilidad
temperatura
```

producen:

```text
calendario de servicios
```

---

# 22. Pending Interaction Between `weekly.py` and `demand.py`

Actualmente la planificación semanal puede generar una recomendación:

```text
Lavadora
domingo
13:30–15:00
```

pero el objetivo arquitectónico es que esa decisión modifique automáticamente:

```text
perfil_24h
```

de `demand.py`.

La arquitectura futura será:

```text
weekly.py
    ↓
plan
    ↓
demand.py
    ↓
perfil actualizado
    ↓
balance.py
    ↓
dispatch.py
```

---

# 23. Future Optimization Loop

Una versión más avanzada podrá iterar:

```text
crear demanda
    ↓
planificar servicios
    ↓
modificar demanda
    ↓
calcular dispatch
    ↓
evaluar
    ↓
replanificar
```

---

# 24. `main.py`

`main.py` is the orchestrator.

Su responsabilidad es:

1. cargar configuración;
2. cargar demanda;
3. consultar AEMET;
4. consultar ESIOS;
5. calcular FV;
6. calcular balance;
7. generar dispatch;
8. generar planificación semanal;
9. mostrar resultados.

No debería concentrar la lógica física de los módulos.

---

# 25. Current Execution Flow

Conceptualmente:

```text
main.py
  │
  ├── config
  │
  ├── demand
  │
  ├── AEMET diario
  │
  ├── AEMET horario
  │
  ├── ESIOS
  │
  ├── weekly
  │
  ├── solar
  │
  ├── balance
  │
  ├── dispatch
  │
  └── optimizer
```

---

# 26. Data Reuse

An important architectural rule is:

> the same external query should be reused across modules.

Por ejemplo:

```text
AEMET horario
```

se obtiene una vez en `main.py` y puede utilizarse en:

```text
solar.py
weekly.py
```

Esto reduce:

- llamadas a API;
- latencia;
- errores 429;
- inconsistencias temporales.

---

# 27. Acquisition Layer

La arquitectura puede dividirse en capas.

## Layer 1 — Acquisition

```text
AEMET
PVGIS
ESIOS
inversor
sensores
```

---

# 28. Modelling Layer

```text
solar.py
demand.py
modelo batería
modelo térmico
```

---

# 29. Decision Layer

```text
balance.py
dispatch.py
optimizer.py
weekly.py
```

---

# 30. Presentation Layer

```text
main.py
consola
archivo de salida
dashboard
app
```

---

# 31. Future Control Layer

```text
Modbus
MQTT
REST
Home Assistant
SolarAssistant
API fabricante
```

Esta capa todavía debe permanecer separada del núcleo científico.

---

# 32. Complete Target Architecture

```text
                  DATOS EXTERNOS
      ┌────────────┬────────────┬────────────┐
      │            │            │            │
    AEMET        PVGIS        ESIOS       sensores
      │            │            │            │
      └──────┬─────┴─────┬──────┴──────┬─────┘
             │           │             │
             ▼           ▼             ▼
        ┌───────────────────────────────┐
        │       CAPA DE MODELOS         │
        │                               │
        │ solar / demand / battery /    │
        │ thermal                       │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │       CAPA DE DECISIÓN        │
        │                               │
        │ balance / weekly / dispatch / │
        │ optimizer                     │
        └───────────────┬───────────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
 ┌────────────────┐          ┌────────────────┐
 │    USUARIO     │          │   CONTROL      │
 │ app/dashboard  │          │ inversor/HEMS  │
 └────────────────┘          └────────────────┘
```

---

# 33. Separation Between Recommendation and Control

Debe mantenerse una frontera clara:

```text
RECOMENDACIÓN
```

no es igual a:

```text
ORDEN
```

Actualmente el sistema está principalmente en modo:

```text
recomendación
```

Una futura capa de ejecución deberá validar nuevamente cualquier orden.

---

# 34. Inverter Control

En una arquitectura futura:

```text
dispatch.py
    ↓
consigna abstracta
    ↓
adapter de hardware
    ↓
inversor
```

Ejemplo:

```text
SET_SOC_MIN = 40 %
```

El núcleo científico no debería contener directamente registros Modbus
específicos del fabricante.

---

# 35. Adapter Pattern

Para soportar diferentes inversores puede utilizarse:

```text
InverterAdapter
```

con implementaciones:

```text
DeyeAdapter
VictronAdapter
HuaweiAdapter
GoodWeAdapter
...
```

El optimizador utilizaría una interfaz común.

---

# 36. Abstract Interface

Conceptualmente:

```python
class InverterAdapter:

    def read_soc(self):
        ...

    def read_pv_power(self):
        ...

    def read_grid_power(self):
        ...

    def set_charge_limit(self, value):
        ...

    def set_soc_min(self, value):
        ...
```

---

# 37. Advantages of Hardware Decoupling

Esto permite que:

```text
optimizer.py
```

sea independiente de:

```text
Deye
Victron
Huawei
...
```

y mejora:

- reutilización;
- testabilidad;
- publicación científica;
- seguridad.

---

# 38. Architecture with Home Assistant

Una posible implementación futura es:

```text
Gestion Solar Predictiva
        │
        ▼
      MQTT
        │
        ▼
Home Assistant
        │
        ▼
SolarAssistant / Modbus
        │
        ▼
      Deye
```

---

# 39. Alternative Direct Architecture

También puede utilizarse:

```text
Python
  │
  ▼
Modbus TCP / RS485
  │
  ▼
inversor
```

pero esto aumenta la responsabilidad del software propio.

---

# 40. Mobile Application

La app no debería contener la lógica científica principal.

Una arquitectura preferible sería:

```text
backend Python
      │
      ▼
 API REST / MQTT
      │
      ▼
   Android
```

La aplicación sería principalmente una interfaz.

---

# 41. Application Functions

La aplicación puede mostrar:

- SOC;
- producción FV;
- demanda;
- compra;
- venta;
- previsión;
- plan semanal;
- alertas;
- recomendaciones.

---

# 42. User Messages

Ejemplos:

```text
Ahora es buen momento para poner la lavadora.
```

```text
Se recomienda usar el horno solar entre 12:00 y 16:00.
```

```text
Hoy no es necesario utilizar el termo eléctrico.
```

```text
Se espera elevada producción FV mañana.
```

---

# 43. Gradual Automation

La evolución recomendable es:

```text
fase 1
solo recomendaciones

fase 2
automatización de cargas no críticas

fase 3
shadow mode del inversor

fase 4
control limitado

fase 5
control predictivo completo
```

---

# 44. Shadow mode

En esta fase:

```text
algoritmo
    ↓
calcula acciones
```

pero:

```text
no las ejecuta
```

Se comparan:

```text
acción propuesta
vs.
operación real
```

---

# 45. Control Mode

Solo después de validación:

```text
acción propuesta
    ↓
safety layer
    ↓
orden
    ↓
inversor
```

---

# 46. Safety Layer

Debe existir una capa independiente que compruebe:

- límites SOC;
- potencia máxima;
- temperatura;
- alarmas;
- estado BMS;
- estado inversor;
- comunicación.

---

# 47. Fallback

Si falla:

```text
Internet
AEMET
ESIOS
MQTT
Modbus
```

el sistema debe caer a una estrategia local segura.

Por ejemplo:

```text
modo autoconsumo estándar
```

---

# 48. Watchdog

Un sistema real debería incorporar:

```text
watchdog
```

capaz de detectar:

- proceso detenido;
- datos obsoletos;
- pérdida de conexión;
- valores imposibles.

---

# 49. Freshness de datos

Cada dato debería tener:

```text
timestamp
```

y una edad máxima permitida:


```math
t_{now}-t_{data}
<
\Delta t_{max}
```


Si no se cumple:

```text
dato inválido
```

---

# 50. Persistence

Para validación será necesario almacenar:

```text
predicciones
medidas
acciones
resultados
```

---

# 51. Future Data Architecture

```text
sensors
   │
   ▼
collector
   │
   ▼
database
   │
   ├── raw
   ├── predictions
   ├── plans
   └── results
```

---

# 52. CSV Versus Database

Durante una primera fase puede utilizarse:

```text
CSV
```

por simplicidad.

Para operación continua será mejor:

```text
SQLite
```

o posteriormente:

```text
PostgreSQL / TimescaleDB
```

---

# 53. Raw/Processed Separation

La arquitectura experimental debería mantener:

```text
raw
```

datos sin modificar,

y:

```text
processed
```

datos sincronizados y preparados.

---

# 54. Experiment Identification

Cada ejecución debería tener:

```text
run_id
```

y almacenar:

```text
fecha
commit
configuración
estrategia
SOC inicial
forecast
resultado
```

---

# 55. Reproducibility

La arquitectura debe permitir reconstruir:

> qué información tenía el algoritmo cuando tomó una decisión.

Por eso es importante guardar:

- forecast utilizado;
- precio utilizado;
- estado inicial;
- commit del código.

---

# 56. Git and Versioning

Cada resultado experimental debería poder asociarse a:

```text
git commit hash
```

por ejemplo:

```text
3a4e12f
```

Esto permite repetir exactamente una simulación.

---

# 57. Testability

La separación modular permite testear independientemente:

```text
solar.py
```

con datos meteorológicos artificiales,

```text
dispatch.py
```

con perfiles sintéticos,

```text
weekly.py
```

con semanas meteorológicas controladas.

---

# 58. Synthetic Data

Ejemplo de prueba:

```text
FV = 0
demanda = 1 kW
SOC = 50 %
precio = alto
```

y comprobar que la acción obtenida es físicamente coherente.

---

# 59. Energy-Conservation Test

Todo despacho debería satisfacer:


```math
P_{FV}
+
P_{buy}
+
P_{dis}
-
P_D
-
P_{ch}
-
P_{sell}
\approx0
```


Este test debe automatizarse.

---

# 60. SOC Test

Debe cumplirse siempre:


```math
SOC_{min}
\leq SOC
\leq SOC_{max}
```


---

# 61. Power Test

También:


```math
P_{charge}
\leq
P_{charge,max}
```



```math
P_{discharge}
\leq
P_{discharge,max}
```


---

# 62. Non-Simultaneity Test

Idealmente:


```math
P_{buy}P_{sell}=0
```


y:


```math
P_{charge}P_{discharge}=0
```


---

# 63. Cache

Las APIs externas pueden tener:

- límites de uso;
- latencia;
- errores temporales.

Por ello puede utilizarse cache local para:

```text
PVGIS
AEMET
ESIOS
```

---

# 64. PVGIS cache

PVGIS es especialmente adecuado para cache porque muchos datos de referencia
no cambian rápidamente.

---

# 65. AEMET cache

La predicción AEMET debe incluir:

```text
forecast_generated_at
```

para saber cuándo se obtuvo.

---

# 66. ESIOS cache

Los precios horarios también pueden guardarse para:

- reproducibilidad;
- análisis histórico;
- reducción de llamadas.

---

# 67. Error Handling

Las excepciones deben distinguir entre:

```text
error temporal
error de configuración
error de datos
error de autenticación
error físico
```

---

# 68. Rate limiting

Cuando AEMET devuelve:

```text
HTTP 429
```

la arquitectura puede utilizar:

```text
retry
+
backoff
```

pero evitando repetir llamadas desde varios módulos.

---

# 69. Credential Configuration

Las API keys deben permanecer fuera del código.

Por ejemplo:

```text
mytoken.env
```

o variables de entorno.

Nunca deben almacenarse en Git.

---

# 70. Repository Security

Debe incluirse en `.gitignore`:

```text
mytoken.env
.env
*.env
__pycache__/
*.pyc
```

---

# 71. Secret-Independent Architecture

Los módulos deben recibir credenciales desde una capa de configuración y no
incluirlas directamente.

---

# 72. Evolution Towards a Backend Service

Una futura arquitectura puede ejecutar el núcleo como servicio:

```text
systemd
   │
   ▼
Python backend
   │
   ├── scheduler
   ├── optimizer
   ├── API
   └── database
```

---

# 73. Scheduler

El sistema podría ejecutar:

```text
00:05
actualizar precios

06:00
actualizar AEMET

cada hora
reoptimizar

cada minuto
leer inversor
```

---

# 74. MPC futuro

La evolución natural es:

```text
medir
  ↓
actualizar estado
  ↓
predecir
  ↓
optimizar
  ↓
ejecutar primera acción
  ↓
repetir
```

---

# 75. MPC Architecture

```text
                 ┌───────────────┐
                 │   sensores    │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ estado actual │
                 └───────┬───────┘
                         │
                         ▼
       forecast ──► ┌───────────────┐
                    │     MPC       │
       prices ─────►│               │
                    └───────┬───────┘
                            │
                            ▼
                       primera acción
                            │
                            ▼
                         sistema
```

---

# 76. MPC States

Una futura variable de estado podría ser:


```math
\mathbf{x}
=
[
SOC,
T_{in},
T_{ACS},
P_{load}
]
```


---

# 77. Control Variables


```math
\mathbf{u}
=
[
P_{battery},
P_{grid},
P_{HVAC},
P_{ACS}
]
```


---

# 78. Exogenous Variables


```math
\mathbf{w}
=
[
G,
T_{out},
p_{buy},
p_{sell},
ocupacion
]
```


---

# 79. Scientific Architecture

Desde el punto de vista de una publicación, el sistema puede dividirse en:

```text
Prediction Layer
Planning Layer
Dispatch Layer
Validation Layer
Control Layer
```

---

# 80. Prediction Layer

Incluye:

```text
AEMET
PVGIS
solar.py
```

---

# 81. Planning Layer

Incluye:

```text
weekly.py
demand.py
```

---

# 82. Dispatch Layer

Incluye:

```text
balance.py
dispatch.py
optimizer.py
```

---

# 83. Validation Layer

Incluye:

```text
dataset
métricas
comparación experimental
```

---

# 84. Control Layer

Futura:

```text
adapter inversor
MQTT
Modbus
Home Assistant
```

---

# 85. Scientific Advantages of the Architecture

La separación permite estudiar independientemente:

- precisión de predicción;
- valor de flexibilidad;
- valor de batería;
- efecto de precios;
- degradación;
- control.

---

# 86. Conceptual Diagram for Publication

```text
Weather forecast ──────┐
                       │
PVGIS ─────────────────┤
                       ▼
                PV prediction
                       │
                       │
Load model ────────────┼──────────┐
                       │          │
Electricity prices ────┘          ▼
                              Optimizer
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
              Battery          Grid            Flexible
              dispatch       exchange           loads
                 │                │                │
                 └────────────────┼────────────────┘
                                  ▼
                             Residential
                              energy system
```

---

# 87. Design for Extensibility

Nuevos módulos podrían incorporarse sin modificar el núcleo.

Ejemplos:

```text
ev.py
```

para vehículo eléctrico,

```text
heatpump.py
```

para modelo térmico detallado,

```text
water.py
```

para ACS,

```text
forecast_ml.py
```

para predicción basada en aprendizaje automático.

---

# 88. Electric Vehicle

Una futura carga EV puede modelarse como:

```text
energía requerida
hora de salida
potencia de cargador
SOC vehículo
```

y planificarse como una tarea flexible de gran capacidad.

---

# 89. Other Resources

También podrían añadirse:

- aerotermia;
- piscina;
- bombeo;
- almacenamiento adicional;
- generador;
- tarifas dinámicas alternativas.

---

# 90. Interoperability

El núcleo debe trabajar con magnitudes físicas normalizadas:

```text
kW
kWh
°C
€/kWh
SOC [0,1]
```

independientemente del fabricante.

---

# 91. Unit Separation

La conversión desde unidades específicas de APIs o hardware debe realizarse en
la capa de adquisición.

Ejemplo:

```text
€/MWh
    ↓
€/kWh
```

antes de llegar al optimizador.

---

# 92. Design Principle

Una regla útil para el proyecto es:

> **Los módulos de adquisición describen el mundo; los módulos de decisión
> deciden qué hacer con él.**

---

# 93. Second Rule

> **Los modelos físicos no deben conocer el hardware de comunicación.**

`solar.py` no debería saber cómo se escribe un registro Modbus.

---

# 94. Third Rule

> **El controlador físico no debe redefinir la lógica científica.**

La capa Modbus debe ejecutar consignas, no decidir la estrategia energética.

---

# 95. Fourth Rule

> **Toda decisión debe poder reproducirse posteriormente.**

Esto requiere almacenar:

```text
estado
forecast
precios
configuración
versión de código
acción
```

---

# 96. Current Maturity

Actualmente existen:

```text
configuración
demanda
AEMET diario
AEMET horario
PVGIS
modelo FV
precios
balance
dispatch
plan semanal
```

---

# 97. Blocks Still Pending

Quedan por desarrollar plenamente:

```text
adquisición automática del inversor
base de datos experimental
acoplamiento weekly-demand
modelo térmico interior
control real
adapter de hardware
app
```

---

# 98. Minimum Architecture for the Next Phase

La siguiente ampliación recomendable es:

```text
            inversor
               │
               ▼
          collector.py
               │
               ▼
          data/raw/
               │
               ▼
         validator.py
               │
               ▼
      comparación modelo-real
```

---

# 99. Experimental Architecture

```text
                  ┌───────────────┐
                  │    inversor   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ data logger   │
                  └───────┬───────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
            raw                     model
            data                  prediction
              │                       │
              └───────────┬───────────┘
                          ▼
                    validation
```

---

# 100. Final Objective

La arquitectura pretende evolucionar hacia:


```math
\boxed{
\text{HEMS predictivo}
}
```


capaz de integrar:


```math
\boxed{
\text{meteorología}
+
\text{FV}
+
\text{demanda}
+
\text{precios}
+
\text{batería}
+
\text{flexibilidad}
+
\text{control}
}
```


manteniendo una separación clara entre:

- predicción;
- optimización;
- ejecución;
- seguridad;
- validación.

Esta separación permitirá utilizar el mismo núcleo tanto para investigación
científica como para una futura aplicación doméstica de control energético.
