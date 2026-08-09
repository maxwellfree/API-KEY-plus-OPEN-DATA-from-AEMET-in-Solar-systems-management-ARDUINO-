# Validación experimental

## Gestión Solar Predictiva — Protocolo de validación

Este documento define el protocolo experimental para validar el sistema
**Gestión Solar Predictiva** utilizando datos reales de una instalación
fotovoltaica residencial.

El objetivo es comprobar cuantitativamente:

- precisión de la predicción fotovoltaica;
- precisión del modelo de demanda;
- evolución prevista del SOC;
- importación y exportación de energía;
- comportamiento real de la batería;
- utilidad de la planificación semanal;
- impacto económico de la estrategia;
- reducción del ciclado electroquímico.

La validación experimental es necesaria para convertir el proyecto desde una
plataforma de simulación y planificación en una herramienta científicamente
contrastada.

---

# 1. Objetivo general

El sistema genera predicciones:

\[
\hat P_{FV}(t)
\]

\[
\hat P_D(t)
\]

\[
\widehat{SOC}(t)
\]

\[
\hat P_{grid}(t)
\]

que deben compararse con medidas reales:

\[
P_{FV}(t)
\]

\[
P_D(t)
\]

\[
SOC(t)
\]

\[
P_{grid}(t)
\]

El objetivo es cuantificar:

\[
\text{predicción}
\quad\text{vs.}\quad
\text{experimento}
\]

---

# 2. Instalación experimental

La instalación residencial utilizada para la validación debe documentarse con
suficiente detalle.

Como mínimo:

```text
localización
potencia FV instalada
número de paneles
modelo de panel
inclinación
azimut
modelo de inversor
potencia nominal del inversor
tipo de batería
capacidad nominal
límites de SOC
potencia máxima de carga
potencia máxima de descarga
tipo de contrato eléctrico
sistema de compensación de excedentes
```

También deben registrarse posibles condicionantes:

- sombras;
- orientación múltiple;
- pérdidas de cableado;
- limitaciones del inversor;
- curtailment;
- temperatura del inversor;
- comportamiento del BMS.

---

# 3. Variables experimentales

Idealmente, en cada instante \(t\) deben registrarse:

\[
\mathbf{x}(t)
=
\{
P_{FV},
P_{load},
P_{grid},
P_{battery},
SOC,
V_{battery},
I_{battery},
T_{battery}
\}
\]

Si el inversor proporciona más variables, también pueden almacenarse.

---

# 4. Variables meteorológicas

Deben almacenarse junto con los datos energéticos:

```text
timestamp
temperatura AEMET
estado del cielo
factor meteorológico
precipitación
viento
humedad
predicción diaria
predicción horaria
```

Es importante guardar **la predicción tal como era conocida antes del
intervalo experimental**, no reconstruirla posteriormente.

Esto evita introducir información futura en la validación.

---

# 5. Variables económicas

Para cada intervalo:

\[
p_{buy}(t)
\]

precio de compra,

y:

\[
p_{sell}(t)
\]

precio de compensación/exportación.

También puede almacenarse:

```text
precio SPOT
PVPC
precio excedentes
```

---

# 6. Formato recomendado del dataset

Una estructura CSV sencilla puede ser:

```text
timestamp,
pv_pred_kw,
pv_real_kw,
load_pred_kw,
load_real_kw,
soc_pred,
soc_real,
battery_power_kw,
grid_power_kw,
price_buy_eur_kwh,
price_sell_eur_kwh,
temperature_aemet_c,
cloud_factor,
strategy,
action_predicted
```

---

# 7. Convención de signos

Es fundamental fijar una convención única.

Por ejemplo:

```text
P_grid > 0  -> compra de red
P_grid < 0  -> exportación

P_battery > 0 -> descarga
P_battery < 0 -> carga
```

o cualquier otra.

La convención debe permanecer constante durante todo el estudio.

---

# 8. Frecuencia de adquisición

Una resolución de:

\[
1-5\ \text{min}
\]

sería adecuada para caracterización detallada.

Para comparar con el modelo horario, los datos pueden posteriormente agregarse
a:

\[
\Delta t=1\ \mathrm{h}
\]

La adquisición original no debería limitarse directamente a una hora si el
inversor permite mayor resolución.

---

# 9. Energía a partir de potencia

A partir de medidas discretas:

\[
E
=
\sum_i
P_i\Delta t
\]

Si la frecuencia de medida no es uniforme, debe utilizarse:

\[
E
=
\sum_i
P_i(t_i)
(t_{i+1}-t_i)
\]

---

# 10. Validación de producción fotovoltaica

La primera validación consiste en comparar:

\[
\hat P_{FV}(t)
\]

con:

\[
P_{FV}(t)
\]

El error instantáneo es:

\[
e_{FV}(t)
=
P_{FV}(t)
-
\hat P_{FV}(t)
\]

---

# 11. Error absoluto medio

\[
MAE
=
\frac{1}{N}
\sum_{i=1}^{N}
|P_i-\hat P_i|
\]

El MAE mantiene las unidades de potencia.

Por ejemplo:

```text
MAE = 0.34 kW
```

---

# 12. Error cuadrático medio

\[
RMSE
=
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
(P_i-\hat P_i)^2
}
\]

El RMSE penaliza especialmente los errores grandes.

---

# 13. Error normalizado

Para comparar días con distinta producción puede utilizarse:

\[
nRMSE
=
\frac{RMSE}
{P_{rated}}
\]

o normalizar respecto a la potencia media o máxima observada.

La definición utilizada debe indicarse expresamente.

---

# 14. MAPE

El error porcentual absoluto medio es:

\[
MAPE
=
\frac{100}{N}
\sum_i
\left|
\frac{P_i-\hat P_i}{P_i}
\right|
\]

Sin embargo, en generación FV presenta problemas cuando:

\[
P_i\approx0
\]

por ejemplo al amanecer o anochecer.

Por ello no debería utilizarse como única métrica.

---

# 15. Error energético diario

Una métrica especialmente útil es:

\[
\epsilon_E
=
\frac{
\hat E_{FV}
-
E_{FV}
}{
E_{FV}
}
\]

en porcentaje:

\[
\epsilon_E[\%]
=
100
\frac{
\hat E_{FV}
-
E_{FV}
}{
E_{FV}
}
\]

---

# 16. Bias

El sesgo medio puede calcularse como:

\[
MBE
=
\frac{1}{N}
\sum_i
(\hat P_i-P_i)
\]

Esto permite detectar una tendencia sistemática a:

- sobreestimar;
- subestimar.

---

# 17. Validación por condiciones meteorológicas

El error FV no debe analizarse únicamente de forma global.

Debe separarse por categorías:

```text
despejado
poco nuboso
intervalos nubosos
nuboso
cubierto
lluvia
```

La predicción puede ser muy precisa en días despejados y peor en condiciones
variables.

---

# 18. Validación por horizonte

También debe separarse según horizonte:

\[
H=0-24\ \mathrm{h}
\]

\[
H=24-48\ \mathrm{h}
\]

\[
H>48\ \mathrm{h}
\]

Esto permitirá cuantificar el valor de la estrategia multirresolución.

---

# 19. Validación de AEMET horario frente a diario

Una comparación interesante es:

\[
MAE_{hourly}
\]

frente a:

\[
MAE_{daily}
\]

para comprobar si la información horaria mejora realmente la estimación FV.

---

# 20. Validación del modelo de demanda

La demanda prevista:

\[
\hat P_D(t)
\]

debe compararse con:

\[
P_D(t)
\]

real.

Se pueden calcular:

\[
MAE_D
\]

\[
RMSE_D
\]

y error energético:

\[
\epsilon_{E,D}
=
\frac{
\hat E_D-E_D
}{
E_D
}
\]

---

# 21. Demanda determinista y estocástica

La demanda doméstica contiene dos componentes.

## Determinista

Ejemplos:

- climatización programada;
- termo;
- lavadora;
- cargas base.

## Estocástica

Ejemplos:

- cocina real;
- iluminación;
- pequeños aparatos;
- cambios de comportamiento.

La validación debería separar ambos tipos cuando sea posible.

---

# 22. Validación del SOC

Debe compararse:

\[
\widehat{SOC}(t)
\]

con:

\[
SOC(t)
\]

real.

El error:

\[
e_{SOC}(t)
=
SOC(t)
-
\widehat{SOC}(t)
\]

Puede medirse mediante:

\[
MAE_{SOC}
=
\frac{1}{N}
\sum_i
|SOC_i-\widehat{SOC}_i|
\]

expresado en puntos porcentuales.

---

# 23. Error acumulativo del SOC

Un error pequeño en eficiencia de batería puede producir deriva progresiva.

Por ello debe observarse:

\[
\Delta SOC(t)
\]

a lo largo de varios días.

Una deriva creciente indicaría que:

- eficiencia de carga;
- eficiencia de descarga;
- capacidad útil;

necesitan recalibración.

---

# 24. Validación de potencia de batería

Se comparará:

\[
\hat P_{battery}(t)
\]

con:

\[
P_{battery}(t)
\]

si el sistema llega a ejecutar automáticamente las consignas.

Durante la fase inicial, la comparación puede limitarse a analizar qué habría
hecho el algoritmo frente a la operación real observada.

---

# 25. Shadow mode

Antes de controlar físicamente el inversor, el algoritmo debería ejecutarse en
**modo sombra**.

Esto significa:

```text
el algoritmo calcula
qué habría hecho
```

pero:

```text
no modifica el inversor
```

Se almacenan simultáneamente:

```text
acción propuesta
acción real
resultado real
```

Esta fase permite validar el controlador sin riesgo operativo.

---

# 26. Estrategias de comparación

La validación científica debería comparar varias estrategias.

Como mínimo:

## Estrategia A — referencia

Funcionamiento convencional.

Por ejemplo:

```text
FV
↓
consumo
↓
batería
↓
red
```

sin predicción.

## Estrategia B — optimización económica

Objetivo:

\[
\min
(C_{buy}-I_{sell})
\]

## Estrategia C — sostenible predictiva

Objetivo aproximado:

\[
\min
(
C_{buy}
-
I_{sell}
+
C_{deg}
)
\]

con criterios adicionales de confort y flexibilidad.

---

# 27. Comparación justa

Las estrategias deben evaluarse sobre:

- mismos días;
- mismo clima;
- misma demanda;
- mismos precios;
- mismo SOC inicial.

De lo contrario la comparación estaría sesgada.

---

# 28. Replay experimental

Una metodología especialmente potente consiste en registrar primero los datos
reales y posteriormente ejecutar diferentes estrategias sobre el mismo día.

Esto permite hacer:

```text
día real
    ↓
mismos FV / precios / demanda
    ↓
estrategia A
estrategia B
estrategia C
```

y comparar resultados sin necesidad de repetir físicamente el día.

---

# 29. Coste energético diario

Para cada estrategia:

\[
C_{day}
=
\sum_h
E_{buy,h}p_{buy,h}
-
\sum_h
E_{sell,h}p_{sell,h}
\]

---

# 30. Ahorro respecto a referencia

\[
Saving
=
C_{reference}
-
C_{strategy}
\]

y:

\[
Saving[\%]
=
100
\frac{
C_{reference}
-
C_{strategy}
}{
C_{reference}
}
\]

---

# 31. Energía importada

\[
E_{import}
=
\sum_h
E_{grid,h}^{buy}
\]

---

# 32. Energía exportada

\[
E_{export}
=
\sum_h
E_{grid,h}^{sell}
\]

---

# 33. Autoconsumo

\[
R_{auto}
=
\frac{
E_{FV,used}
}{
E_{FV,total}
}
\]

---

# 34. Autosuficiencia

\[
R_{self}
=
\frac{
E_{load}-E_{grid}^{buy}
}{
E_{load}
}
\]

---

# 35. Ciclos equivalentes

Se calculará:

\[
N_{eq}
=
\frac{
E_{charge}
+
E_{discharge}
}{
2E_{nom}
}
\]

Esta es una de las métricas principales del estudio.

---

# 36. Reducción de ciclado

Respecto a la estrategia de referencia:

\[
\Delta N_{eq}
=
N_{eq}^{ref}
-
N_{eq}^{strategy}
\]

Puede expresarse en porcentaje:

\[
R_{cycle}
=
100
\frac{
N_{eq}^{ref}
-
N_{eq}^{strategy}
}{
N_{eq}^{ref}
}
\]

---

# 37. Valor económico por ciclo evitado

Una métrica interesante puede ser:

\[
V_{cycle}
=
\frac{
\Delta C
}{
\Delta N_{eq}
}
\]

Esto permite estudiar cuánto coste económico se intercambia por reducción de
desgaste.

---

# 38. Validación de la planificación semanal

Para cada recomendación se puede registrar:

```text
servicio
hora recomendada
hora real
energía prevista
energía real
```

---

# 39. Aceptación de recomendaciones

Puede definirse:

\[
R_{accept}
=
\frac{
N_{accepted}
}{
N_{recommended}
}
\]

Esto mide hasta qué punto el plan es compatible con la vida real del usuario.

---

# 40. Energía desplazada

\[
E_{shift}
=
\sum_i E_i^{shifted}
\]

El porcentaje de flexibilidad utilizada:

\[
R_{shift}
=
\frac{
E_{shift}
}{
E_{flex,total}
}
\]

---

# 41. Ganancia de autoconsumo por flexibilidad

\[
\Delta E_{auto}
=
E_{auto}^{flex}
-
E_{auto}^{base}
\]

---

# 42. Ahorro de batería por flexibilidad

Si una carga se desplaza de la noche al periodo solar, puede evitarse una
descarga de batería.

Puede medirse:

\[
\Delta E_{battery}
=
E_{battery}^{base}
-
E_{battery}^{flex}
\]

---

# 43. Validación térmica

Para climatización deben registrarse:

```text
temperatura exterior prevista
temperatura exterior real
temperatura interior
estado HVAC
potencia HVAC
```

---

# 44. Temperatura interior

Cuando esté disponible:

\[
T_{in}(t)
\]

permitirá evaluar si las recomendaciones mantienen el confort.

---

# 45. Error térmico

Puede definirse:

\[
e_T(t)
=
T_{set}
-
T_{in}(t)
\]

---

# 46. Horas fuera de confort

Una métrica sencilla:

\[
H_{discomfort}
=
\sum_t
\mathbf{1}
\left(
|T_{in}(t)-T_{set}|>\Delta T
\right)
\Delta t
\]

---

# 47. Coste térmico

Puede medirse:

\[
E_{HVAC}
\]

consumida por climatización durante el día.

La estrategia debe comparar:

```text
energía HVAC
vs.
confort
vs.
autoconsumo
```

---

# 48. Validación de ACS

En una fase avanzada se registrará:

\[
T_{ACS}(t)
\]

junto con:

- activación del termo;
- energía eléctrica utilizada;
- energía solar térmica disponible.

---

# 49. Ahorro eléctrico de ACS

\[
E_{ACS,saved}
=
E_{ACS,reference}
-
E_{ACS,solar}
\]

---

# 50. Datos faltantes

Los datasets reales contendrán probablemente:

- pérdidas de conexión;
- reinicios;
- valores nulos;
- valores imposibles.

Estos datos deben marcarse explícitamente.

Nunca deben rellenarse silenciosamente.

---

# 51. Flags de calidad

Cada registro puede incluir:

```text
quality_ok
missing
interpolated
outlier
communication_error
```

---

# 52. Outliers

Los valores extremos deben detectarse pero no eliminarse automáticamente.

Por ejemplo:

\[
P_{FV}>P_{physical,max}
\]

puede indicar:

- error de lectura;
- escala incorrecta;
- unidad equivocada.

---

# 53. Sincronización temporal

Todos los datos deben compartir:

```text
timezone
timestamp
intervalo
```

Preferiblemente:

```text
Europe/Madrid
```

o almacenamiento interno en UTC con conversión explícita.

---

# 54. Cambio horario

El cambio verano/invierno debe tratarse cuidadosamente.

Existen días con:

\[
23\ \mathrm{h}
\]

y:

\[
25\ \mathrm{h}
\]

No debe asumirse siempre que un día tiene exactamente 24 registros horarios.

---

# 55. Integridad temporal

Debe verificarse:

\[
t_{i+1}>t_i
\]

y detectar huecos:

\[
t_{i+1}-t_i
>
\Delta t_{expected}
\]

---

# 56. Dataset bruto y procesado

Conviene conservar dos niveles.

```text
data/raw/
```

Datos originales sin modificar.

```text
data/processed/
```

Datos:

- sincronizados;
- agregados;
- validados;
- preparados para análisis.

Nunca debe sobrescribirse el dataset bruto.

---

# 57. Estructura recomendada

```text
data/
├── raw/
│   ├── inverter/
│   ├── aemet/
│   ├── esios/
│   └── sensors/
│
├── processed/
│   ├── hourly/
│   └── daily/
│
└── metadata/
    └── installation.json
```

---

# 58. Archivo diario sugerido

Por ejemplo:

```text
2026-08-09.csv
```

con:

```text
timestamp
pv_kw
load_kw
grid_kw
battery_kw
soc
temperature_c
price_buy
price_sell
```

---

# 59. Metadatos

`installation.json` puede almacenar:

```json
{
    "pv_kwp": 6.05,
    "inverter_kw": 6.0,
    "battery_kwh": 10.24,
    "soc_min": 0.20,
    "soc_max": 0.85
}
```

---

# 60. Reproducibilidad

Cada experimento debería almacenar también:

```text
versión del código
commit Git
fecha de ejecución
configuración
estrategia
parámetros
```

---

# 61. Identificación de versión

Es recomendable almacenar:

```text
git_commit
```

junto a cada simulación.

Así puede reproducirse exactamente el algoritmo utilizado.

---

# 62. Congelación de predicciones

Cuando se obtiene una predicción AEMET debe almacenarse inmediatamente.

Por ejemplo:

```text
forecast_generated_at
forecast_target_time
```

Esto permite estudiar error según horizonte.

---

# 63. Forecast lead time

Definimos:

\[
L
=
t_{target}
-
t_{forecast}
\]

El error puede analizarse como función:

\[
MAE(L)
\]

---

# 64. Validación estacional

El dataset debería cubrir:

```text
verano
otoño
invierno
primavera
```

porque:

- irradiancia;
- temperatura;
- climatización;
- demanda;
- rendimiento FV;

cambian significativamente.

---

# 65. Duración mínima experimental

Una primera publicación podría utilizar varias semanas, pero una validación
más robusta debería intentar abarcar varios meses.

Idealmente:

\[
T_{exp}\geq1\ \text{año}
\]

para cubrir toda la estacionalidad.

---

# 66. Primer estudio publicable

Una primera fase puede utilizar:

\[
30-60\ \text{días}
\]

si incluye suficiente variabilidad meteorológica.

Esto permitiría validar:

- producción FV;
- despacho;
- batería;
- precios;
- planificación.

---

# 67. Separación calibración-validación

No deben utilizarse los mismos datos para calibrar y validar.

Por ejemplo:

```text
60 % calibración
20 % validación
20 % test
```

o separación temporal equivalente.

---

# 68. Calibración

Los parámetros que pueden ajustarse incluyen:

- factor meteorológico;
- pérdidas FV;
- coeficiente térmico efectivo;
- eficiencia de batería;
- capacidad útil;
- umbrales térmicos;
- carga base.

---

# 69. Test independiente

El conjunto final de test no debe utilizarse durante el ajuste del modelo.

Solo al final se calcula:

\[
MAE_{test}
\]

\[
RMSE_{test}
\]

\[
Savings_{test}
\]

---

# 70. Comparación con baseline FV

Además del modelo completo, debe existir una referencia simple.

Por ejemplo:

\[
P_{FV}^{baseline}
=
P_{PVGIS}
\]

sin corrección meteorológica.

Después se compara:

\[
RMSE_{PVGIS}
\]

con:

\[
RMSE_{AEMET+PVGIS}
\]

---

# 71. Skill score

Puede definirse:

\[
Skill
=
1
-
\frac{
RMSE_{model}
}{
RMSE_{baseline}
}
\]

Si:

\[
Skill>0
\]

el nuevo modelo mejora el baseline.

---

# 72. Baseline de control

También debe existir un baseline para batería.

Por ejemplo:

```text
cargar con cualquier excedente
descargar ante cualquier déficit
```

---

# 73. Valor del control predictivo

La mejora puede medirse mediante:

\[
\Delta C
\]

\[
\Delta N_{eq}
\]

\[
\Delta E_{grid}
\]

respecto a ese baseline.

---

# 74. Significancia estadística

Cuando existan suficientes días experimentales, las comparaciones deben
acompañarse de:

- media;
- desviación estándar;
- mediana;
- percentiles;
- intervalos de confianza.

---

# 75. Comparación diaria pareada

Como las estrategias pueden ejecutarse sobre el mismo día mediante replay,
puede utilizarse:

\[
\Delta C_d
=
C_{A,d}
-
C_{B,d}
\]

día a día.

Esto reduce el efecto de la variabilidad meteorológica.

---

# 76. Distribución de resultados

No debe presentarse únicamente:

```text
ahorro medio
```

También conviene mostrar:

```text
P10
P50
P90
```

o boxplots.

---

# 77. Casos extremos

Debe estudiarse específicamente:

- día completamente despejado;
- día muy nuboso;
- ola de calor;
- día con baja producción;
- batería con SOC bajo;
- batería casi llena;
- precios negativos;
- precios elevados.

---

# 78. Robustez ante error meteorológico

Puede realizarse una prueba perturbando:

\[
G(t)
\]

y:

\[
T(t)
\]

para estudiar sensibilidad.

---

# 79. Sensibilidad

Por ejemplo:

\[
G' = G(1+\delta_G)
\]

con:

\[
\delta_G
=
\pm5\%,
\pm10\%,
\pm20\%
\]

y observar:

\[
\Delta C
\]

\[
\Delta SOC
\]

---

# 80. Sensibilidad al coste de degradación

También puede variarse:

\[
c_{deg}
\]

para observar cómo cambia:

\[
N_{eq}
\]

y:

\[
C_{net}
\]

---

# 81. Curva de Pareto

Puede obtenerse una relación entre:

\[
\text{coste económico}
\]

y:

\[
\text{ciclado de batería}
\]

produciendo una frontera de Pareto.

Esto sería especialmente interesante científicamente.

---

# 82. Indicador combinado

Podría definirse:

\[
J^\*
=
C_{net}
+
\lambda N_{eq}
\]

para diferentes valores de:

\[
\lambda
\]

---

# 83. Validación en shadow mode

La primera fase de operación real debería ser:

```text
SEMANA 1-N
---------
leer inversor
leer batería
leer red
leer AEMET
leer ESIOS
calcular plan
NO enviar órdenes
```

Esto permite validar la lógica sin riesgo.

---

# 84. Segunda fase

Después:

```text
control parcial
```

por ejemplo únicamente:

- notificaciones al usuario;
- programación de cargas no críticas.

---

# 85. Tercera fase

Solo después de validación suficiente:

```text
control de inversor
```

con límites independientes de seguridad.

---

# 86. Indicadores de seguridad

Debe registrarse:

```text
número de consignas rechazadas
errores de comunicación
SOC fuera de objetivo
alarmas del inversor
alarmas BMS
```

---

# 87. Criterio de éxito

La estrategia sostenible podría considerarse mejor si:

\[
C_{strategy}
\leq
C_{reference}
+
\epsilon
\]

y simultáneamente:

\[
N_{eq,strategy}
<
N_{eq,reference}
\]

con:

\[
\epsilon
\]

pequeño.

Es decir, si se reduce significativamente el ciclado sin penalización económica
relevante.

---

# 88. Hipótesis H1

\[
H_1:
\]

La incorporación de predicción meteorológica horaria reduce el error de
producción FV respecto a un modelo climatológico sin predicción.

---

# 89. Hipótesis H2

\[
H_2:
\]

La planificación de cargas flexibles incrementa el autoconsumo directo.

---

# 90. Hipótesis H3

\[
H_3:
\]

La estrategia sostenible predictiva reduce los ciclos equivalentes de batería
frente a una estrategia de autoconsumo convencional.

---

# 91. Hipótesis H4

\[
H_4:
\]

La reducción de ciclado puede obtenerse sin aumentar significativamente el
coste energético total.

---

# 92. Hipótesis H5

\[
H_5:
\]

La combinación de planificación térmica y producción FV reduce la energía
extraída de batería durante periodos de climatización.

---

# 93. Figuras recomendadas para publicación

Una publicación debería incluir al menos:

```text
Figura 1
Arquitectura del sistema

Figura 2
Predicción FV vs medida

Figura 3
SOC previsto vs SOC real

Figura 4
FV / demanda / batería / red durante 24 h

Figura 5
Comparación económica de estrategias

Figura 6
Ciclos equivalentes

Figura 7
Error FV según horizonte

Figura 8
Pareto coste vs degradación
```

---

# 94. Tablas recomendadas

```text
Tabla 1
Características de la instalación

Tabla 2
Parámetros del modelo

Tabla 3
Errores de predicción

Tabla 4
Comparación de estrategias

Tabla 5
Resultados estacionales
```

---

# 95. Ejemplo de tabla de resultados

| Estrategia | Coste €/día | Compra kWh | Venta kWh | Ciclos eq. | Autoconsumo |
|---|---:|---:|---:|---:|---:|
| Convencional | — | — | — | — | — |
| Económica | — | — | — | — | — |
| Sostenible predictiva | — | — | — | — | — |

Los valores deben obtenerse experimentalmente.

---

# 96. Publicación del dataset

Si no existen problemas de privacidad, sería recomendable publicar una versión
anonimizada del dataset.

No debería incluir:

- credenciales;
- identificadores privados;
- IP;
- datos personales;
- información sensible de la vivienda.

---

# 97. Reproducibilidad pública

Idealmente el artículo debería proporcionar:

```text
GitHub
+
dataset
+
configuración experimental
+
scripts de análisis
```

Esto permitiría reproducir los resultados.

---

# 98. Registro de ejecución

Cada simulación puede producir un fichero:

```text
run_YYYYMMDD_HHMMSS.json
```

con:

```text
commit
config
forecast
prices
soc_initial
strategy
results
```

---

# 99. Criterio de validación del modelo FV

No debe fijarse todavía un umbral arbitrario de aceptación.

Primero debe medirse el comportamiento real.

Después, a partir de:

- literatura;
- baselines;
- incertidumbre del sistema;

podrá definirse qué error resulta aceptable.

---

# 100. Objetivo final de validación

La validación pretende responder experimentalmente a la pregunta:

\[
\boxed{
\text{¿Aporta realmente valor la gestión predictiva?}
}
\]

Ese valor debe demostrarse en términos de:

\[
\boxed{
\text{predicción}
+
\text{coste}
+
\text{autoconsumo}
+
\text{ciclos de batería}
+
\text{confort}
}
\]

y no únicamente mediante una simulación teórica.

---

# 101. Resultado esperado

Al finalizar la validación debería ser posible afirmar, con datos reales:

```text
qué precisión tiene la predicción FV
```

```text
cuánto aumenta el autoconsumo
```

```text
cuánto reduce la compra de red
```

```text
cuántos ciclos de batería evita
```

```text
qué ahorro económico produce
```

```text
qué impacto tiene sobre el confort
```

y:

```text
si la estrategia sostenible predictiva
es superior a las estrategias de referencia
```

Ese conjunto de resultados constituirá la base experimental para una futura
publicación científica.
