[README.md](https://github.com/user-attachments/files/30863394/README.md)
# Gestión Solar Predictiva

Sistema experimental en Python para **planificar y optimizar el consumo
energético de una vivienda con instalación fotovoltaica, baterías y
conexión a red**.

El proyecto combina previsión meteorológica, estimación física de
generación fotovoltaica, precios horarios de electricidad, un modelo
doméstico de demanda y un algoritmo de despacho para decidir, hora a
hora, cuándo conviene:

-   autoconsumir energía fotovoltaica;
-   cargar o descargar la batería;
-   comprar electricidad de la red;
-   vender excedentes;
-   desplazar consumos flexibles hacia las mejores horas;
-   preservar la vida útil de las baterías;
-   planificar servicios domésticos a lo largo de la semana.

> **Estado del proyecto:** en desarrollo. Actualmente genera un plan
> semanal de servicios y un despacho energético detallado para el día
> actual. La siguiente etapa es extender el despacho físico-económico
> detallado a las primeras 48--96 horas.

------------------------------------------------------------------------

## Filosofía del proyecto

El objetivo no es maximizar únicamente el beneficio económico
instantáneo.

La estrategia `sostenible_predictiva` sigue aproximadamente esta
jerarquía:

1.  satisfacer las necesidades de la vivienda;
2.  respetar presencia y restricciones físicas;
3.  aprovechar directamente la producción fotovoltaica;
4.  desplazar cargas flexibles hacia horas solares;
5.  evitar ciclos innecesarios de batería;
6.  utilizar la red para consumos marginales cuando resulte razonable;
7.  vender excedentes;
8.  optimizar finalmente el resultado económico.

La preservación de la batería tiene, por tanto, prioridad frente a
pequeños arbitrajes económicos.

------------------------------------------------------------------------

## Instalación de referencia

La configuración actualmente utilizada como ejemplo corresponde a:

  Elemento                                         Configuración
  ------------------------------- ------------------------------
  Paneles FV                                                  10
  Potencia instalada                                    6.05 kWp
  Inversor                          Deye SUN-6K-SG05LP1-EU-AM2-P
  Potencia del inversor                                  6.00 kW
  Baterías                                     2 × SE-G5.1 Pro-B
  Energía nominal                                      10.24 kWh
  SOC operativo normal                                  20--85 %
  Ventana energética sostenible                        6.656 kWh

Estos parámetros son configurables y no constituyen requisitos del
programa.

------------------------------------------------------------------------

## Modelo doméstico de demanda

El modelo de referencia representa una vivienda unifamiliar ocupada por
cinco personas.

Incluye, entre otras cargas:

-   iluminación;
-   cocina de inducción;
-   horno eléctrico;
-   microondas;
-   robot de cocina;
-   cafetera;
-   termo eléctrico;
-   sistema solar térmico para ACS con bomba de intercambio;
-   lavadora;
-   climatización mediante bombas de calor;
-   climatización estival de una despensa;
-   riego automático mediante electroválvulas;
-   lámpara UV asociada al consumo de agua de cocina;
-   consumos eléctricos de base.

También se consideran **hornos solares**, que pueden sustituir
parcialmente el consumo eléctrico de cocina cuando las condiciones
solares son favorables.

El modelo distingue cargas flexibles, automatizables, condicionadas,
térmicas y cargas que requieren presencia física.

------------------------------------------------------------------------

## Arquitectura

El proyecto se ha dividido en módulos para separar la física, los datos
externos y las decisiones de control.

``` text
config.py
   │
   ├── configuración FV, batería, inversor y localización
   │
demand.py
   │
   ├── vivienda, presencia, cargas y perfil de demanda
   │
aemet.py ─────────────── previsión meteorológica diaria
aemet_hourly.py ──────── previsión meteorológica horaria
   │
solar.py
   │
   ├── modelo físico-predictivo de generación FV
   │
prices / ESIOS
   │
   ├── precios horarios de compra y excedentes
   │
balance.py
   │
   ├── cruce FV + demanda + precios
   │
dispatch.py
   │
   ├── batería + red + autoconsumo + venta
   │
optimizer.py
   │
   ├── estrategia sostenible_predictiva
   │
weekly.py
   │
   └── planificación semanal de servicios
   │
main.py
   └── integración, ejecución y presentación
```

`weekly.py` responde específicamente a la pregunta **«¿cuándo conviene
prestar cada servicio durante la semana?»** y considera disponibilidad
solar, presencia, frecuencia, potencia, simultaneidad y restricciones
físicas.

------------------------------------------------------------------------

## Datos externos

### AEMET OpenData

La meteorología procede de **AEMET OpenData**.

Se emplean datos diarios y horarios para estimar, entre otras
magnitudes:

-   estado del cielo;
-   nubosidad;
-   precipitación;
-   temperatura;
-   calidad solar prevista.

Para utilizar AEMET OpenData se necesita una **API Key personal**. La
clave se solicita al propio servicio AEMET OpenData.

Documentación oficial:

https://opendata.aemet.es/

La clave **no debe publicarse en GitHub**.

### ESIOS / Red Eléctrica

Los datos económicos proceden de **e·sios**, el sistema de información
de Red Eléctrica.

El proyecto utiliza precios horarios para construir magnitudes como:

-   precio de compra;
-   precio de excedentes;
-   horas económicas;
-   horas de mayor valor de exportación;
-   coste de importación;
-   ingreso por excedentes.

La API de e·sios utiliza autenticación mediante una clave enviada en las
peticiones.

Documentación oficial:

https://api.esios.ree.es/

Las credenciales personales **no forman parte del repositorio**.

------------------------------------------------------------------------

## Credenciales y seguridad

Este repositorio deliberadamente **no contiene contraseñas, API keys ni
tokens privados**.

Cada usuario debe obtener sus propias credenciales de los proveedores
correspondientes.

Una forma recomendable de gestionarlas es mediante variables de entorno:

``` bash
export AEMET_API_KEY="TU_CLAVE_AEMET"
export ESIOS_API_KEY="TU_CLAVE_ESIOS"
```

Y recuperarlas desde Python, por ejemplo:

``` python
import os

AEMET_API_KEY = os.getenv("AEMET_API_KEY")
ESIOS_API_KEY = os.getenv("ESIOS_API_KEY")
```

También puede utilizarse un archivo local `.env`, siempre que esté
excluido del repositorio.

Ejemplo de `.gitignore`:

``` gitignore
.env
.env.*
secrets.py
credentials.py
__pycache__/
*.pyc
```

Puede añadirse al repositorio un archivo `.env.example` sin secretos:

``` text
AEMET_API_KEY=INTRODUCIR_CLAVE_AEMET
ESIOS_API_KEY=INTRODUCIR_CLAVE_ESIOS
```

**Nunca se deben copiar al repositorio las claves reales**, ni siquiera
temporalmente: Git conserva el historial de los commits.

------------------------------------------------------------------------

## Ejecución

Ejemplo básico:

``` bash
python3 main.py --soc 0.60
```

El municipio y las características físicas de la instalación pueden
almacenarse en `config.py`, evitando introducir repetidamente parámetros
que pertenecen a la instalación.

Para mostrar todos los bloques de análisis disponibles:

``` bash
python3 main.py \
    --soc 0.60 \
    --mostrar-semanal \
    --mostrar-precios \
    --mostrar-solar \
    --mostrar-balance \
    --mostrar-plan-horario
```

------------------------------------------------------------------------

## Ejemplo de resultado

En una ejecución de referencia con SOC inicial del 60 %, el programa
identifica:

``` text
Sistema fotovoltaico
--------------------
Potencia FV instalada : 6.05 kWp
Potencia inversor     : 6.00 kW
Energía nominal       : 10.24 kWh
SOC normal            : 20–85 %

Modelo de demanda
-----------------
Ocupantes              : 5
Cargas modeladas       : 15
Cargas flexibles       : 8
Cargas automatizables  : 7
Potencia base estimada : 0.180 kW
Demanda diaria teórica : 22.50 kWh
```

El planificador semanal genera un horizonte de siete días y asigna una
confianza decreciente conforme aumenta el horizonte de predicción.

Ejemplo:

``` text
Día         Solar     Calidad      Confianza
sábado       0.95     excelente    alta
domingo      0.92     excelente    alta
lunes        0.72     bueno        media
martes       0.62     aceptable    media
miércoles    0.57     aceptable    baja
jueves       0.51     aceptable    baja
viernes      0.47     malo         baja
```

El programa puede recomendar horarios para lavadora, cocina, ACS,
climatización y riego, teniendo en cuenta la presencia y las
restricciones propias de cada servicio.

------------------------------------------------------------------------

## Modelo fotovoltaico

`solar.py` no utiliza únicamente una curva solar artificial.

El módulo construye una estimación física-predictiva horaria teniendo en
cuenta la geometría solar y las condiciones meteorológicas disponibles.

La salida horaria incluye magnitudes como:

``` text
Hora   Gref   Fmet   Gpred   Tamb   Tcell   Pac
```

donde, conceptualmente:

-   `Gref` representa la irradiancia de referencia calculada;
-   `Fmet` introduce la corrección meteorológica;
-   `Gpred` es la irradiancia prevista empleada por el modelo;
-   `Tamb` es la temperatura ambiente;
-   `Tcell` es la temperatura estimada de célula;
-   `Pac` es la potencia fotovoltaica AC estimada.

En una ejecución de referencia se obtuvo:

``` text
Energía FV diaria : 33.55 kWh
Pico FV previsto  : 14:00 — 5.23 kW
```

Estos valores son **predicciones**, no medidas reales del inversor.

------------------------------------------------------------------------

## Balance energético

El sistema cruza para cada hora:

``` text
FV(t)
demanda(t)
precio_compra(t)
precio_venta(t)
```

y calcula:

``` text
balance(t) = FV(t) - demanda(t)
```

Antes de introducir la batería puede obtenerse un balance como:

-   autoconsumo FV directo;
-   excedente;
-   déficit;
-   compra necesaria;
-   venta posible;
-   coste de compra;
-   ingreso por excedentes;
-   autosuficiencia.

Posteriormente `dispatch.py` decide cómo utilizar batería y red.

------------------------------------------------------------------------

## Despacho de batería

El despacho horario genera variables como:

``` text
Hora
FV
Demanda
SOC
Compra de red
Venta a red
Carga de batería
Descarga de batería
Acción
```

Las acciones pueden incluir combinaciones como:

``` text
AUTOCONSUMO
AUTOCONSUMO + CARGAR_BATERIA
AUTOCONSUMO + VENDER
DESCARGAR_BATERIA
COMPRAR_RED
AUTOCONSUMO + DESCARGAR_BATERIA + COMPRAR_RED
```

La estrategia sostenible evita utilizar sistemáticamente la batería para
cubrir cualquier pequeño déficit. El coste económico de la electricidad
se compara con el valor de preservar ciclos de batería.

------------------------------------------------------------------------

## Planificación semanal

`weekly.py` implementa actualmente un horizonte de siete días.

Los servicios se separan conceptualmente en:

### Tareas desplazables

Por ejemplo:

-   lavadora;
-   horno;
-   robot de cocina.

Tienen duración determinada y pueden desplazarse dentro de una ventana
temporal compatible con la presencia.

### Cargas térmicas

Por ejemplo:

-   climatización;
-   bombas de calor;
-   ACS.

No deben modelarse simplemente como una tarea puntual de una hora, sino
mediante ventanas y, en versiones futuras, mediante estado térmico.

### Cargas condicionales

Por ejemplo, el termo eléctrico.

Solo debería activarse cuando exista una necesidad física, como
temperatura insuficiente del acumulador solar.

### Servicios con restricciones externas

El riego es el ejemplo principal.

La sostenibilidad del agua y las necesidades de las plantas tienen
prioridad sobre el pequeño beneficio de desplazar el consumo eléctrico
hasta el máximo fotovoltaico.

------------------------------------------------------------------------

## ACS solar

La vivienda de referencia dispone de captación solar térmica conectada
al sistema de ACS.

La lógica de planificación da prioridad a:

``` text
captación solar térmica
        ↓
bomba de intercambio
        ↓
comprobación de temperatura
        ↓
termo eléctrico solamente si es necesario
```

Por ello, una buena predicción fotovoltaica no implica automáticamente
encender el termo eléctrico.

------------------------------------------------------------------------

## Cocina solar

Cuando la predicción meteorológica es suficientemente favorable, el
sistema informa de ventanas adecuadas para utilizar hornos solares.

La cocina solar se considera una sustitución directa de parte de la
demanda eléctrica y no una fuente de generación eléctrica.

------------------------------------------------------------------------

## Objetivo de desarrollo

La arquitectura pretende evolucionar hacia un controlador energético
doméstico predictivo.

El siguiente paso importante consiste en extender a las primeras
**48--96 horas** el cálculo conjunto de:

``` text
P_FV(t)
demanda(t)
precio_compra(t)
precio_venta(t)
SOC(t)
```

Esto permitirá que la planificación semanal deje de basarse
principalmente en un índice solar diario y utilice excedentes
energéticos reales previstos.

A más largo plazo, el plan podrá convertirse en consignas para el
inversor o para un sistema domótico, siempre con límites de seguridad
independientes.

------------------------------------------------------------------------

## Limitaciones actuales

El proyecto todavía debe considerarse experimental.

Entre las limitaciones actuales:

-   la demanda doméstica es un modelo teórico y no una medición en
    tiempo real;
-   la generación FV es una predicción;
-   la incertidumbre meteorológica aumenta con el horizonte;
-   algunos servicios térmicos todavía requieren un modelo dinámico de
    temperatura;
-   el estado real del acumulador de ACS todavía no se mide;
-   no se modelan sombras locales detalladas;
-   el despacho calculado no debe considerarse por sí solo una orden
    segura para actuar sobre hardware;
-   antes del control automático del inversor deben añadirse
    validaciones, límites eléctricos, estados de fallo y mecanismos de
    *fallback*.

------------------------------------------------------------------------

## Estructura recomendada del repositorio

``` text
GestionSolarAEMET/
├── main.py
├── config.py
├── demand.py
├── aemet.py
├── aemet_hourly.py
├── solar.py
├── balance.py
├── dispatch.py
├── optimizer.py
├── weekly.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

Dependiendo de la versión actual del proyecto pueden existir módulos
adicionales para la descarga y tratamiento de precios.

------------------------------------------------------------------------

## Autor

**Enrique M. Moreno Pérez**

Proyecto experimental de gestión energética residencial, predicción
fotovoltaica y optimización sostenible.

------------------------------------------------------------------------

## Licencia

MIT License

Copyright (c) 2026 Enrique M. Moreno Pérez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------

## Aviso

Este software se encuentra en desarrollo y sus resultados son
estimaciones de planificación energética.

No sustituye las protecciones eléctricas, los límites configurados en el
inversor, el BMS de las baterías ni los dispositivos de seguridad de la
instalación. Cualquier futura conexión automática con hardware debe
conservar mecanismos independientes de protección y funcionamiento
seguro.
