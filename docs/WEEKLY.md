# Planificación semanal de servicios

## Gestión Solar Predictiva — `weekly.py`

Este documento describe la lógica de planificación semanal utilizada por
**Gestión Solar Predictiva**.

Mientras que `dispatch.py` responde a la pregunta:

> **¿De dónde debe proceder la energía en cada hora?**

`weekly.py` responde a:

> **¿Cuándo conviene prestar cada servicio durante los próximos días?**

La planificación semanal utiliza:

- previsión meteorológica de AEMET;
- resolución horaria para el horizonte próximo;
- resolución diaria para el resto de la semana;
- disponibilidad solar;
- temperatura prevista;
- presencia del usuario;
- flexibilidad de las cargas;
- frecuencia semanal;
- restricciones físicas;
- simultaneidad;
- necesidades térmicas;
- disponibilidad de recursos solares alternativos.

---

# 1. Horizonte semanal

El horizonte básico es:

\[
H = 7\ \text{días}
\]

La planificación no considera todos los días con la misma precisión.

Se utiliza un enfoque multirresolución:

\[
\text{predicción}(t)
=
\begin{cases}
\text{AEMET horario}, & t \lesssim 48\ \text{h}\\[4pt]
\text{AEMET diario}, & t > 48\ \text{h}
\end{cases}
\]

La idea es utilizar la máxima resolución disponible sin atribuir precisión
horaria a predicciones meteorológicas lejanas.

---

# 2. Confianza de la planificación

La confianza disminuye con el horizonte.

Conceptualmente:

```text
hoy / mañana
    ↓
confianza alta

días intermedios
    ↓
confianza media

final de semana
    ↓
confianza baja
```

Por tanto, una recomendación para mañana puede considerarse más robusta que una
recomendación para dentro de seis días.

---

# 3. Clasificación de servicios

No todas las cargas deben gestionarse del mismo modo.

`weekly.py` separa los servicios en varias categorías físicas.

## 3.1 Tareas desplazables

Son cargas que deben ejecutarse durante un tiempo determinado, pero cuyo
instante puede modificarse.

Ejemplos:

- lavadora;
- horno eléctrico;
- robot de cocina.

La variable principal es el instante de inicio:

\[
t_i
\]

y la tarea ocupa una duración:

\[
\tau_i
\]

por lo que:

\[
[t_i,\ t_i+\tau_i]
\]

debe permanecer dentro de una ventana admisible.

---

# 4. Cargas térmicas

Las cargas térmicas no deben tratarse como simples tareas.

Ejemplos:

- bomba de calor de planta superior;
- bomba de calor de planta inferior;
- aire acondicionado de despensa.

Su utilización depende de la temperatura exterior prevista y, en futuras
versiones, también de la temperatura interior y de la inercia térmica del
edificio.

---

# 5. Cargas condicionales

Son servicios que no deben activarse automáticamente solo porque exista
electricidad disponible.

El ejemplo principal es:

```text
termo eléctrico de ACS
```

La lógica correcta es:

```text
captación solar térmica
        ↓
bomba de intercambio
        ↓
temperatura del acumulador
        ↓
¿ACS suficiente?
   │             │
  sí            no
   │             │
   ▼             ▼
no usar      apoyo eléctrico
termo
```

Por tanto, el termo eléctrico es una carga de respaldo.

---

# 6. Restricciones externas

Algunos servicios están gobernados por criterios que no son principalmente
eléctricos.

El ejemplo principal es el riego.

En este caso deben considerarse:

- necesidades de las plantas;
- temperatura;
- precipitación;
- evaporación;
- horario adecuado;
- frecuencia semanal.

La optimización eléctrica es secundaria.

---

# 7. Alternativas solares

El modelo contempla recursos que reducen directamente la demanda eléctrica.

El ejemplo principal son los hornos solares.

Cuando el índice solar es suficientemente elevado:

\[
S_d \geq S_{min}
\]

se propone una ventana de utilización.

Esto no genera electricidad:

\[
P_{FV}
\]

sino que reduce:

\[
P_D
\]

---

# 8. Índice solar diario

Para cada día se utiliza un indicador:

\[
S_d \in [0,1]
\]

que resume las condiciones meteorológicas relevantes para la disponibilidad
solar.

Puede depender de:

- estado del cielo;
- precipitación;
- temperatura;
- penalizaciones meteorológicas.

Este índice no sustituye al modelo físico horario de `solar.py`.

Su función en `weekly.py` es principalmente comparar días entre sí.

---

# 9. Clasificación cualitativa del día

A partir de \(S_d\), el sistema puede generar categorías como:

```text
excelente
bueno
aceptable
malo
```

Esto facilita la interpretación humana del plan semanal.

---

# 10. Tareas desplazables

Para una tarea \(i\), se busca una ventana compatible con:

\[
W_i
=
[t_{min,i},t_{max,i}]
\]

y con duración:

\[
\tau_i
\]

La tarea debe satisfacer:

\[
t_i \geq t_{min,i}
\]

y:

\[
t_i+\tau_i
\leq t_{max,i}
\]

---

# 11. Presencia

Algunas cargas requieren presencia física.

Si:

\[
P_{user}(t)=0
\]

la tarea no puede asignarse a ese intervalo.

Por tanto, la ventana efectiva es:

\[
W_i^{eff}
=
W_i
\cap
W_{presence}
\]

Esto es especialmente relevante para:

- lavadora;
- horno;
- robot de cocina;
- determinadas operaciones manuales.

---

# 12. Frecuencia semanal

No todas las tareas deben ejecutarse todos los días.

Puede existir una frecuencia:

\[
f_i
\]

por ejemplo:

```text
lavadora:
4 usos/semana
```

El planificador distribuye estas ejecuciones entre los días disponibles.

---

# 13. Simultaneidad

Aunque dos tareas sean flexibles, puede ser poco conveniente ejecutarlas
simultáneamente.

Se controla:

\[
P_{tasks}(t)
=
\sum_i P_i(t)
\]

para evitar picos innecesarios.

Una condición general sería:

\[
P_{tasks}(t)
\leq
P_{flex,max}
\]

---

# 14. Función de conveniencia

Conceptualmente, cada posible ventana puede recibir una puntuación:

\[
Q_i(d,t)
\]

dependiente de:

\[
Q_i
=
f
\left(
S_d,
P_{FV},
precio,
presencia,
simultaneidad,
confianza
\right)
\]

Una forma genérica sería:

\[
Q_i
=
w_s Q_{solar}
+
w_p Q_{precio}
+
w_u Q_{usuario}
-
w_c Q_{concurrencia}
\]

La versión actual puede implementar esta lógica mediante reglas discretas en
lugar de una función objetivo continua.

---

# 15. Gestión térmica en verano

Para refrigeración, la planificación utiliza la temperatura exterior prevista.

En el horizonte próximo:

\[
T = T(h)
\]

con resolución horaria.

Para días posteriores:

\[
T \approx T_{max}
\]

La lógica conceptual es:

\[
u_{cool}(h)
=
\begin{cases}
1, & T(h)\geq T_{on}\\
0, & T(h)<T_{on}
\end{cases}
\]

donde \(u_{cool}\) representa la recomendación de climatizar.

---

# 16. Umbral estival

En la versión actual se utilizan umbrales iniciales distintos para la vivienda
y la despensa.

Conceptualmente:

```text
vivienda
T >= 30 °C
→ refrigeración

despensa
T >= 27 °C
→ refrigeración
```

Estos valores deben entenderse como parámetros de control iniciales y no como
umbrales universales.

En una versión futura deben trasladarse a `config.py`.

---

# 17. Ventana operativa de verano

La vivienda utiliza una estrategia doméstica conocida:

```text
noche
↓
ventilación natural

mañana
↓
cerrar ventanas

mediodía/tarde
↓
climatización si la temperatura lo requiere

18:00 aprox.
↓
apagado
```

Por ello, incluso si AEMET predice temperatura elevada a las 10:00, el sistema
puede restringir la operación del aire acondicionado a la ventana doméstica
admisible.

---

# 18. Agrupación de horas térmicas

Si AEMET predice:

```text
12:00   28 °C
13:00   29 °C
14:00   31 °C
15:00   34 °C
16:00   35 °C
17:00   32 °C
```

y:

\[
T_{on}=30^\circ C
\]

las horas activas son:

```text
14
15
16
17
```

que se agrupan en una única ventana:

```text
14:00–18:00
```

---

# 19. Nivel de climatización

La recomendación térmica puede clasificarse cualitativamente como:

```text
suave
media
alta
```

según la temperatura prevista.

Esto permite informar al usuario no solo de la ventana, sino también de la
intensidad térmica esperada.

---

# 20. Gestión térmica en invierno

Para calefacción, la variable más representativa es:

\[
T_{min}
\]

especialmente para decidir la necesidad térmica de primera hora.

Cuando existe predicción horaria:

\[
T=T(h)
\]

y pueden analizarse ventanas específicas:

```text
mañana
07:00–09:00

tarde
18:00–22:00
```

---

# 21. Umbral de calefacción

Conceptualmente:

\[
u_{heat}(h)
=
\begin{cases}
1,&T(h)\leq T_{heat}\\
0,&T(h)>T_{heat}
\end{cases}
\]

El valor inicial utilizado puede ser, por ejemplo:

\[
T_{heat}\approx12^\circ C
\]

como criterio exterior aproximado.

Este parámetro deberá calibrarse experimentalmente.

---

# 22. Tmin y Tmax

Para días sin información horaria suficientemente detallada:

- en verano se utiliza principalmente \(T_{max}\);
- en invierno se utiliza preferentemente \(T_{min}\).

Si \(T_{min}\) no está disponible, puede utilizarse temporalmente:

\[
T_{max}
\]

como indicador de respaldo.

La salida debe identificar que se trata de un *fallback*.

---

# 23. Fuente meteorológica de la decisión

La planificación térmica distingue explícitamente entre:

```text
AEMET_horario
```

y:

```text
AEMET_diario
```

Esto es importante para interpretar la calidad de la recomendación.

Una ventana derivada de datos horarios próximos tiene mayor resolución que una
ventana estimada mediante una máxima diaria de dentro de varios días.

---

# 24. Planificación híbrida

La lógica de la versión 4 puede resumirse como:

\[
\boxed{
\text{Alta resolución cerca}
+
\text{baja resolución lejos}
}
\]

Esto permite mantener un horizonte largo sin fingir una precisión inexistente.

---

# 25. ACS

El ACS se planifica separadamente de la climatización.

Se intenta aprovechar primero:

\[
E_{solar,thermal}
\]

antes que:

\[
E_{electric}
\]

La recomendación depende del recurso solar del día.

---

# 26. Días de alta disponibilidad solar para ACS

Si:

\[
S_d
\]

es elevado, el sistema recomienda:

```text
Priorizar captación solar térmica
y bomba de intercambio.
```

El termo eléctrico solo debería intervenir si:

\[
T_{ACS}<T_{min,ACS}
\]

---

# 27. Días de baja disponibilidad solar

Cuando el recurso solar es bajo, puede preverse:

```text
posible apoyo eléctrico
```

En ese caso el termo debería programarse considerando:

- precio de compra;
- producción FV disponible;
- temperatura real del acumulador.

---

# 28. Riego

La planificación del riego prioriza horarios agronómicamente razonables.

Por ejemplo:

```text
06:00–08:00
```

en lugar del máximo solar.

Esto ilustra una característica importante:

> **el mínimo coste eléctrico no es siempre el criterio principal.**

---

# 29. Precipitación

En futuras versiones puede introducirse una regla:

\[
P_{rain}(d) > P_{threshold}
\]

o:

\[
R_d > R_{min}
\]

para cancelar o reducir el riego previsto.

---

# 30. Cocina solar

Cuando:

\[
S_d \geq S_{solar\_oven}
\]

se propone una ventana como:

```text
12:00–16:00
```

La cocina solar puede sustituir parcial o totalmente:

- horno eléctrico;
- robot de cocina;
- otras cargas culinarias.

---

# 31. Planificación y demanda eléctrica

El plan semanal no debería permanecer separado del perfil eléctrico.

Si se decide:

```text
lavadora
13:30–15:00
```

entonces el perfil de demanda debe modificarse.

Formalmente:

\[
P_D^{new}(t)
=
P_D^{base}(t)
+
P_{washer}(t)
\]

---

# 32. Acoplamiento con dispatch

La arquitectura objetivo es:

```text
weekly.py
    ↓
plan de servicios
    ↓
perfil de demanda modificado
    ↓
balance.py
    ↓
dispatch.py
```

El despacho debe recalcularse una vez desplazadas las cargas.

---

# 33. Iteración conjunta

Una evolución más avanzada podría hacer:

```text
1. calcular plan semanal
2. generar demanda
3. calcular dispatch
4. evaluar coste/ciclos
5. modificar plan
6. repetir
```

Matemáticamente:

\[
Q^{(k+1)}
=
F(Q^{(k)})
\]

hasta alcanzar una solución suficientemente estable.

---

# 34. Flexibilidad del usuario

Las ventanas admisibles deben ser configurables.

El usuario puede proporcionar:

\[
W_{home}(d)
\]

que representa cuándo se encuentra en casa.

Ejemplo:

```text
lunes-viernes
07:00–08:30
18:00–22:00

sábado-domingo
08:00–22:00
```

Esto modifica directamente la flexibilidad real.

---

# 35. Automatización

No todas las cargas requieren presencia.

Las cargas automatizables pueden ejecutarse sin intervención directa.

Esto permite diferenciar:

\[
W_i^{auto}
\]

de:

\[
W_i^{presence}
\]

---

# 36. Recomendaciones al usuario

La planificación puede transformarse en mensajes.

Ejemplos:

```text
Buen momento para poner la lavadora:
domingo 13:30–15:00.
```

```text
Hoy no es necesario utilizar el termo eléctrico.
```

```text
Se recomienda climatizar entre 14:00 y 18:00.
```

```text
Hoy conviene utilizar el horno solar.
```

---

# 37. Uso móvil

Una futura interfaz móvil podría mostrar:

```text
HOY

13:30 Lavadora
14:00 Refrigeración
14:30 Robot de cocina

SOC objetivo: 55 %
FV prevista: alta
```

y generar notificaciones.

---

# 38. Plan semanal versus control automático

Es importante diferenciar:

```text
planificación
```

de:

```text
ejecución
```

`weekly.py` produce recomendaciones y horarios.

Un futuro sistema de control deberá verificar inmediatamente antes de ejecutar:

- estado del inversor;
- SOC real;
- temperatura real;
- presencia;
- conectividad;
- precios actualizados;
- restricciones de seguridad.

---

# 39. Actualización continua

Un plan semanal no debe considerarse definitivo.

Cada día:

\[
Forecast_{new}
\]

sustituye a:

\[
Forecast_{old}
\]

por lo que el plan puede recalcularse.

Idealmente:

```text
cada mañana
↓
actualizar AEMET
↓
actualizar precios
↓
recalcular plan
```

---

# 40. Replanificación por cambios meteorológicos

Si una previsión cambia significativamente:

\[
|S_d^{new}-S_d^{old}|
>
\Delta S_{threshold}
\]

puede ser conveniente recalcular automáticamente las tareas flexibles.

---

# 41. Replanificación térmica

La climatización es especialmente sensible a cambios de temperatura.

Si:

\[
T^{new}(h)
\neq
T^{old}(h)
\]

la ventana térmica debe recalcularse.

Esto hace que las primeras 24–48 horas deban actualizarse con mayor frecuencia.

---

# 42. Incertidumbre

Las predicciones meteorológicas contienen incertidumbre.

Por ello, la planificación debería evolucionar hacia:

\[
P(T_h)
\]

y:

\[
P(G_h)
\]

en lugar de utilizar únicamente valores deterministas.

Una futura función objetivo podría incluir:

\[
E[J]
\]

o penalizaciones de riesgo.

---

# 43. Planificación robusta

Una estrategia robusta podría evitar programar una carga crítica en una ventana
que solo resulta viable bajo una predicción muy optimista.

Conceptualmente:

\[
Q_{robust}
=
Q
-
\lambda \sigma
\]

donde \(\sigma\) representa incertidumbre.

---

# 44. Modelo térmico futuro

La versión actual utiliza temperatura exterior como variable de decisión.

Una formulación más física deberá incluir un estado interior:

\[
T_{in}(t)
\]

con una ecuación simplificada tipo RC:

\[
C
\frac{dT_{in}}{dt}
=
\frac{
T_{out}-T_{in}
}{R}
+
Q_{solar}
+
Q_{internal}
+
Q_{HVAC}
\]

donde:

- \(R\) representa resistencia térmica efectiva;
- \(C\) capacidad térmica;
- \(Q_{HVAC}\) aporte térmico de climatización.

---

# 45. Preenfriamiento predictivo

Con un modelo térmico puede decidirse:

\[
T_{in}(t)<T_{set}
\]

durante horas de exceso FV para reducir consumo posterior.

Esto permite trasladar energía en el tiempo mediante la masa térmica del
edificio.

---

# 46. ACS como almacenamiento térmico

El acumulador de agua puede modelarse mediante:

\[
E_{ACS}
=
m c_p
(T_{ACS}-T_{ref})
\]

Esto permitiría comparar directamente:

```text
cargar batería
```

frente a:

```text
calentar agua
```

durante horas de excedente.

---

# 47. Función objetivo semanal

El problema completo puede representarse mediante:

\[
\max
\sum_{d,t,i}
Q_i(d,t)x_i(d,t)
\]

sujeto a:

\[
\sum_{d,t}x_i(d,t)=f_i
\]

para cada tarea \(i\),

junto con restricciones de:

- presencia;
- duración;
- potencia;
- simultaneidad;
- temperatura;
- frecuencia.

---

# 48. Variable binaria

Para tareas discretas puede utilizarse:

\[
x_{i,d,t}
\in
\{0,1\}
\]

donde:

\[
x_{i,d,t}=1
\]

significa que la tarea \(i\) comienza en el día \(d\) a la hora \(t\).

Esto permitiría transformar `weekly.py` en un problema de programación entera.

---

# 49. Programación matemática futura

La evolución natural puede utilizar:

- Linear Programming;
- Mixed Integer Linear Programming;
- Dynamic Programming;
- Model Predictive Control.

Especialmente:

\[
MILP
\]

es adecuado para representar tareas discretas con horarios.

---

# 50. Relación con MPC

`weekly.py` puede proporcionar el horizonte superior de un sistema MPC.

Por ejemplo:

```text
weekly
    ↓
restricciones / preferencias
    ↓
MPC 24–48 h
    ↓
consignas horarias
```

La planificación semanal actuaría como capa estratégica y el MPC como capa
operativa.

---

# 51. Validación de la planificación

La planificación también debe validarse experimentalmente.

Pueden compararse:

```text
horario recomendado
vs.
horario realmente utilizado
```

y medir:

- energía desplazada;
- ahorro;
- autoconsumo adicional;
- reducción de ciclado;
- aceptación del usuario.

---

# 52. Métrica de energía desplazada

Puede definirse:

\[
E_{shift}
=
\sum_i
E_i^{moved}
\]

y el porcentaje:

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

# 53. Ganancia por flexibilidad

Una métrica interesante es comparar:

\[
C_{fixed}
\]

con:

\[
C_{flex}
\]

y definir:

\[
\Delta C_{flex}
=
C_{fixed}
-
C_{flex}
\]

---

# 54. Ganancia de autoconsumo

También:

\[
\Delta E_{auto}
=
E_{auto}^{flex}
-
E_{auto}^{fixed}
\]

Esto permitirá medir científicamente el valor de la planificación doméstica.

---

# 55. Interacción con batería

Una buena planificación semanal puede reducir la necesidad de almacenamiento.

Si una carga puede trasladarse desde la noche al mediodía:

\[
E_{battery}
\downarrow
\]

sin reducir el servicio prestado.

Esta es una de las ideas centrales del proyecto:

> **la flexibilidad de demanda puede sustituir parcialmente al almacenamiento
> electroquímico.**

---

# 56. Jerarquía energética

La planificación sostenible intenta aproximadamente:

```text
1. servicio necesario
2. FV directa
3. desplazamiento temporal
4. almacenamiento térmico
5. batería
6. red / exportación
```

El orden exacto puede variar en función de precios y restricciones.

---

# 57. Estado actual

La versión 4 de `weekly.py` implementa:

- horizonte de siete días;
- clasificación de servicios;
- tareas desplazables;
- ACS;
- riego;
- cocina solar;
- gestión térmica;
- AEMET horario para el horizonte próximo;
- AEMET diario para el resto;
- confianza dependiente del horizonte.

---

# 58. Limitaciones actuales

Entre las principales limitaciones:

- ausencia de temperatura interior;
- umbrales térmicos todavía manuales;
- flexibilidad doméstica basada en reglas;
- planificación semanal todavía no completamente acoplada a `dispatch.py`;
- ausencia de optimización MILP;
- ausencia de probabilidades meteorológicas explícitas;
- ausencia de realimentación de comportamiento real del usuario.

---

# 59. Próximos pasos

Los siguientes desarrollos naturales son:

1. trasladar umbrales térmicos a `config.py`;
2. incorporar temperatura mínima diaria;
3. incorporar temperatura interior medida;
4. modificar automáticamente el perfil de `demand.py`;
5. recalcular `dispatch.py` después de planificar;
6. extender precios y FV a 48–96 h;
7. incorporar incertidumbre;
8. generar notificaciones;
9. integrar domótica;
10. validar experimentalmente.

---

# 60. Objetivo final

El objetivo de `weekly.py` es transformar:

\[
\boxed{
\text{meteorología}
+
\text{flexibilidad}
+
\text{presencia}
+
\text{necesidades domésticas}
}
\]

en:

\[
\boxed{
\text{un calendario energético útil para el usuario}
}
\]

y utilizar posteriormente ese calendario para construir una demanda eléctrica
más inteligente que pueda ser optimizada por `dispatch.py`.
