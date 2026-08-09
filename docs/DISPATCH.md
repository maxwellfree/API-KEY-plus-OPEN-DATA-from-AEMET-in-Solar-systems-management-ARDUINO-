# Dispatch energético y gestión de batería

## Gestión Solar Predictiva — Lógica horaria de operación

Este documento describe la lógica utilizada para transformar el balance
fotovoltaico-doméstico en una estrategia horaria de operación.

El módulo de despacho recibe, para cada hora:

- producción fotovoltaica prevista;
- demanda prevista;
- precio de compra;
- precio de venta;
- estado de carga inicial de la batería;
- límites operativos del sistema;
- criterios de preservación de batería.

A partir de estos datos decide cómo repartir la energía entre:

- autoconsumo;
- carga de batería;
- descarga de batería;
- compra a red;
- venta de excedentes.

---

# 1. Variables principales

Para cada intervalo horario \(h\) se utilizan las siguientes variables:

\[
P_{FV,h}
\]

potencia fotovoltaica disponible,

\[
P_{D,h}
\]

demanda doméstica,

\[
P_{ch,h}
\]

potencia de carga de batería,

\[
P_{dis,h}
\]

potencia de descarga,

\[
P_{grid,h}^{buy}
\]

potencia importada de red,

\[
P_{grid,h}^{sell}
\]

potencia exportada.

El estado de carga de batería se representa mediante:

\[
SOC_h
\]

---

# 2. Balance de potencia

En cada hora debe cumplirse aproximadamente:

\[
P_{FV,h}
+
P_{grid,h}^{buy}
+
P_{dis,h}
=
P_{D,h}
+
P_{ch,h}
+
P_{grid,h}^{sell}
\]

Esta ecuación constituye la restricción fundamental del despacho.

---

# 3. Balance previo a la batería

Antes de decidir el uso del almacenamiento se calcula:

\[
B_h
=
P_{FV,h}
-
P_{D,h}
\]

Si:

\[
B_h>0
\]

existe excedente fotovoltaico.

Si:

\[
B_h<0
\]

existe déficit.

Se definen:

\[
P_{exc,h}
=
\max(B_h,0)
\]

y:

\[
P_{def,h}
=
\max(-B_h,0)
\]

---

# 4. Autoconsumo directo

La primera utilización de la producción FV es satisfacer directamente la
demanda.

\[
P_{auto,h}
=
\min
\left(
P_{FV,h},
P_{D,h}
\right)
\]

El autoconsumo directo evita:

- pérdidas de conversión adicionales;
- ciclos de batería;
- compra de electricidad;
- dependencia de compensación por excedentes.

Por ello constituye la primera prioridad energética.

---

# 5. Estado de carga

El estado de carga se define como:

\[
SOC_h
=
\frac{E_{bat,h}}{E_{nom}}
\]

donde:

- \(E_{bat,h}\) es la energía almacenada;
- \(E_{nom}\) es la capacidad nominal.

La actualización puede expresarse como:

\[
SOC_{h+1}
=
SOC_h
+
\frac{
\eta_c E_{ch,h}
}{
E_{nom}
}
-
\frac{
E_{dis,h}
}{
\eta_d E_{nom}
}
\]

donde:

- \(\eta_c\) es la eficiencia de carga;
- \(\eta_d\) es la eficiencia de descarga.

---

# 6. Límites de SOC

La batería no debe operar libremente entre 0 y 100 %.

Se define una ventana:

\[
SOC_{min}
\leq
SOC_h
\leq
SOC_{max}
\]

En la instalación de referencia:

```text
SOC normal : 20–85 %
```

Aunque el algoritmo puede emplear límites operativos internos más
conservadores dependiendo de la estrategia.

---

# 7. Reserva de batería

Una parte importante de la estrategia es evitar descargar la batería solo
porque exista un déficit puntual.

Se introduce un SOC objetivo:

\[
SOC_h^{obj}
\]

que representa la cantidad de energía que conviene conservar teniendo en
cuenta las horas futuras.

Conceptualmente:

\[
SOC_h^{obj}
=
f
\left(
P_{FV}^{future},
P_D^{future},
p_{buy}^{future},
SOC_{min},
SOC_{max}
\right)
\]

Si se espera fuerte producción FV unas horas más tarde:

\[
SOC_h^{obj}
\downarrow
\]

porque la batería podrá recargarse posteriormente.

Si se espera baja producción:

\[
SOC_h^{obj}
\uparrow
\]

para conservar reserva.

---

# 8. Déficit fotovoltaico

Cuando:

\[
P_{D,h}>P_{FV,h}
\]

el déficit es:

\[
P_{def,h}
=
P_{D,h}
-
P_{FV,h}
\]

El sistema debe decidir entre:

\[
\text{batería}
\]

y:

\[
\text{red}
\]

o una combinación de ambas.

---

# 9. Descarga disponible

La energía disponible para descargar depende del SOC actual.

Si:

\[
SOC_h > SOC_{min}
\]

existe margen energético.

Puede definirse:

\[
E_{available,h}
=
E_{nom}
\left(
SOC_h-SOC_{min}
\right)
\]

No toda esta energía debe necesariamente utilizarse.

La estrategia puede conservar una reserva adicional asociada a
\(SOC_h^{obj}\).

---

# 10. Descarga sostenible

Una aproximación conceptual es:

\[
P_{dis,h}
=
\min
\left[
P_{def,h},
P_{dis,max},
P_{available,h}
\right]
\]

pero solamente cuando exista justificación suficiente.

El algoritmo evita una regla simplista del tipo:

```text
si hay déficit -> descargar siempre
```

porque esto maximizaría el número de ciclos.

---

# 11. Preservación de batería

La filosofía sostenible introduce una penalización implícita al ciclado.

Puede representarse mediante:

\[
C_{deg,h}
=
c_{deg}
E_{throughput,h}
\]

donde:

\[
E_{throughput,h}
=
E_{ch,h}
+
E_{dis,h}
\]

y \(c_{deg}\) representa un coste equivalente asociado al desgaste.

Aunque el modelo actual puede implementar esta idea mediante reglas y umbrales,
esta formulación permite expresar matemáticamente la estrategia.

---

# 12. Decisión batería frente a red

Cuando existe déficit se compara conceptualmente:

\[
C_{grid,h}
=
p_{buy,h}
E_{def,h}
\]

con:

\[
C_{battery,h}
=
C_{deg,h}
\]

Si:

\[
C_{grid,h}
<
C_{battery,h}
\]

puede resultar preferible comprar energía.

Si:

\[
C_{grid,h}
>
C_{battery,h}
\]

y existe suficiente SOC, puede justificarse la descarga.

Esto conduce a una política:

> **la energía almacenada no se considera gratuita.**

---

# 13. Excedente fotovoltaico

Cuando:

\[
P_{FV,h}>P_{D,h}
\]

el excedente es:

\[
P_{exc,h}
=
P_{FV,h}
-
P_{D,h}
\]

Este excedente puede:

1. cargar la batería;
2. venderse a red;
3. alimentar cargas flexibles;
4. alimentar almacenamiento térmico;
5. desperdiciarse si no existe ninguna alternativa.

---

# 14. Carga de batería

La potencia de carga está limitada por:

\[
P_{ch,h}
\leq
P_{ch,max}
\]

y por la capacidad disponible:

\[
SOC_h < SOC_{max}
\]

La energía máxima que puede almacenarse es aproximadamente:

\[
E_{cap,h}
=
E_{nom}
\left(
SOC_{max}
-
SOC_h
\right)
\]

Por tanto:

\[
P_{ch,h}
=
\min
\left[
P_{exc,h},
P_{ch,max},
P_{cap,h}
\right]
\]

---

# 15. Venta de excedentes

Una vez satisfechas:

- demanda;
- carga de batería deseada;
- cargas flexibles;
- necesidades térmicas;

el excedente restante puede venderse.

\[
P_{grid,h}^{sell}
=
\max
\left[
P_{exc,h}
-
P_{ch,h},
0
\right]
\]

El ingreso correspondiente es:

\[
I_h
=
P_{grid,h}^{sell}
p_{sell,h}
\Delta t
\]

---

# 16. Compra de red

La energía comprada se utiliza cuando:

- no existe suficiente FV;
- no conviene descargar batería;
- el SOC ha alcanzado el mínimo;
- se desea preservar energía para horas futuras.

\[
P_{grid,h}^{buy}
=
P_{def,h}
-
P_{dis,h}
\]

con:

\[
P_{grid,h}^{buy}\geq0
\]

---

# 17. No simultaneidad ideal

En una formulación ideal deben evitarse situaciones como:

\[
P_{grid}^{buy}>0
\quad\text{y}\quad
P_{grid}^{sell}>0
\]

simultáneamente.

También:

\[
P_{ch}>0
\quad\text{y}\quad
P_{dis}>0
\]

salvo condiciones especiales del hardware.

Estas restricciones evitan circulación energética innecesaria.

---

# 18. Acciones horarias

El sistema traduce los flujos energéticos a etiquetas comprensibles.

Ejemplos:

```text
AUTOCONSUMO
```

```text
AUTOCONSUMO + CARGAR_BATERIA
```

```text
AUTOCONSUMO + VENDER
```

```text
AUTOCONSUMO + DESCARGAR_BATERIA
```

```text
COMPRAR_RED
```

```text
AUTOCONSUMO + COMPRAR_RED
```

```text
AUTOCONSUMO + DESCARGAR_BATERIA + COMPRAR_RED
```

Estas etiquetas permiten interpretar fácilmente el despacho calculado.

---

# 19. Ciclos equivalentes

La energía total procesada por la batería se calcula como:

\[
E_{cycled}
=
E_{charge}
+
E_{discharge}
\]

El número aproximado de ciclos completos equivalentes es:

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

Esta métrica es especialmente útil para comparar estrategias.

Una estrategia que ahorre unos pocos céntimos diarios a costa de duplicar el
número de ciclos puede ser poco conveniente a largo plazo.

---

# 20. Métricas diarias de despacho

El módulo calcula magnitudes agregadas como:

```text
Carga de batería
Descarga de batería
Energía ciclada
Ciclos equivalentes
Compra de red
Venta a red
Coste de compra
Ingreso por venta
Balance económico neto
SOC final
SOC mínimo
SOC máximo
```

Estas métricas permiten comparar diferentes políticas de operación.

---

# 21. Balance económico

El coste de compra es:

\[
C_{buy}
=
\sum_h
E_{grid,h}^{buy}
p_{buy,h}
\]

El ingreso por venta:

\[
I_{sell}
=
\sum_h
E_{grid,h}^{sell}
p_{sell,h}
\]

El balance económico neto:

\[
C_{net}
=
C_{buy}
-
I_{sell}
\]

Un valor negativo representaría un ingreso neto superior al coste de compra.

---

# 22. Optimización puramente económica

Una estrategia puramente económica tendería a resolver:

\[
\min
\left[
C_{buy}
-
I_{sell}
\right]
\]

Sin embargo, esta función objetivo ignora la degradación de batería.

Por ello podría producir:

- carga excesiva;
- descarga excesiva;
- arbitraje diario frecuente;
- reducción de vida útil.

---

# 23. Función objetivo sostenible

Una formulación más completa es:

\[
J
=
C_{buy}
-
I_{sell}
+
C_{deg}
+
P_{SOC}
+
P_{comfort}
\]

donde:

- \(C_{deg}\) penaliza el desgaste de batería;
- \(P_{SOC}\) penaliza desviaciones del rango deseado;
- \(P_{comfort}\) representa restricciones domésticas.

El algoritmo actual implementa esta filosofía mediante reglas predictivas y
SOC objetivo.

---

# 24. Estrategia predictiva

El despacho no debe considerar cada hora de forma completamente aislada.

Supongamos que a las 08:00 existe un déficit de:

\[
0.4\ \mathrm{kWh}
\]

pero a partir de las 09:00 se espera:

\[
P_{FV} \gg P_D
\]

La batería puede utilizarse parcialmente sabiendo que será recargada poco
después.

Por el contrario, si se aproxima una noche larga con baja producción prevista,
puede ser preferible conservar SOC.

---

# 25. Horizonte temporal

El despacho actualmente se calcula con resolución horaria.

Para un horizonte:

\[
H=24
\]

puede definirse:

\[
\mathbf{u}
=
[
u_0,u_1,\ldots,u_{23}
]
\]

donde cada \(u_h\) contiene las decisiones de:

\[
u_h
=
\{
P_{ch},
P_{dis},
P_{buy},
P_{sell}
\}
\]

Una evolución futura consistirá en extender este horizonte a:

\[
48-96\ \mathrm{h}
\]

---

# 26. Relación con la planificación semanal

`dispatch.py` responde a:

> ¿De dónde debe proceder la energía en cada hora?

`weekly.py` responde a:

> ¿Cuándo conviene realizar cada servicio?

Por tanto:

```text
weekly.py
    ↓
modifica demanda futura
    ↓
dispatch.py
    ↓
decide origen de la energía
```

Actualmente ambas capas todavía no están completamente acopladas.

Ese acoplamiento es uno de los siguientes pasos del proyecto.

---

# 27. Interacción con cargas flexibles

Si `weekly.py` desplaza una lavadora desde:

```text
20:00
```

hasta:

```text
13:30
```

entonces el perfil de demanda cambia:

\[
P_D^{new}(h)
\neq
P_D^{old}(h)
\]

El despacho debe recalcularse con el nuevo perfil.

Este proceso puede convertirse en una iteración:

```text
plan semanal
    ↓
nuevo perfil de demanda
    ↓
dispatch
    ↓
nuevo coste
    ↓
evaluación
```

---

# 28. Interacción con climatización

La climatización también modifica el despacho.

Si AEMET determina que el aire acondicionado debe funcionar:

\[
12:00-18:00
\]

la demanda térmica debe añadirse al perfil eléctrico durante esa ventana.

Esto puede reducir:

- excedentes;
- energía exportada;

pero aumentar:

- autoconsumo directo;
- almacenamiento térmico implícito;
- confort.

---

# 29. Posible preenfriamiento

En edificios con buena inercia térmica puede resultar conveniente:

\[
P_{cool}(t)>0
\]

durante horas de alta producción FV incluso antes del máximo de temperatura
interior.

Esto convierte al edificio en una forma de almacenamiento térmico.

Una estrategia futura podría comparar:

\[
\text{cargar batería}
\]

frente a:

\[
\text{preenfriar edificio}
\]

---

# 30. Restricciones de potencia

Además del SOC deben respetarse límites como:

\[
P_{ch}\leq P_{ch,max}
\]

\[
P_{dis}\leq P_{dis,max}
\]

\[
P_{grid}^{buy}\leq P_{grid,max}
\]

\[
P_{grid}^{sell}\leq P_{export,max}
\]

y:

\[
P_{AC}\leq P_{inverter,max}
\]

Estas restricciones deberán corresponder siempre con los límites reales del
hardware.

---

# 31. Seguridad

El algoritmo de despacho no debe sustituir las protecciones físicas del
sistema.

Los límites de seguridad deben permanecer implementados independientemente en:

- inversor;
- BMS;
- protecciones AC;
- protecciones DC;
- sistema de control.

El optimizador solo debe proporcionar consignas dentro del rango permitido.

---

# 32. Fallback

Un futuro sistema de control real deberá definir modos de operación seguros
cuando falle:

- AEMET;
- ESIOS;
- Internet;
- comunicación con inversor;
- adquisición de datos.

Por ejemplo:

```text
si falla predicción
    ↓
usar estrategia conservadora local
```

o:

```text
si falla comunicación
    ↓
mantener configuración segura del inversor
```

---

# 33. Relación con control predictivo MPC

La formulación futura puede expresarse como un problema de Model Predictive
Control.

En cada instante \(k\):

\[
\mathbf{u}^*
=
\arg\min_{\mathbf{u}}
J
\]

sujeto a:

\[
\mathbf{x}_{k+1}
=
f(
\mathbf{x}_k,
\mathbf{u}_k
)
\]

donde el estado puede incluir:

\[
\mathbf{x}
=
[
SOC,
T_{interior},
T_{ACS},
\ldots
]
\]

y las acciones:

\[
\mathbf{u}
=
[
P_{charge},
P_{discharge},
P_{grid},
P_{HVAC},
\ldots
]
\]

---

# 34. Reoptimización

En un MPC real no se ejecutaría el plan completo de 24 horas sin cambios.

El ciclo sería:

```text
medir
  ↓
predecir
  ↓
optimizar
  ↓
ejecutar próxima acción
  ↓
esperar
  ↓
volver a medir
```

La ventaja es que los errores de predicción se corrigen continuamente.

---

# 35. Comparación de estrategias

Para validación experimental deberían compararse al menos tres políticas.

## Estrategia A — convencional

```text
FV -> consumo -> batería -> red
```

sin predicción.

## Estrategia B — económica

Minimiza:

\[
C_{buy}-I_{sell}
\]

## Estrategia C — sostenible predictiva

Minimiza aproximadamente:

\[
C_{buy}
-
I_{sell}
+
C_{deg}
\]

manteniendo además restricciones domésticas.

---

# 36. Indicadores de comparación

Las tres estrategias deberían compararse mediante:

\[
C_{net}
\]

coste económico,

\[
N_{eq}
\]

ciclos equivalentes,

\[
E_{grid}^{buy}
\]

energía comprada,

\[
E_{grid}^{sell}
\]

energía exportada,

\[
R_{self}
\]

autosuficiencia,

\[
R_{auto}
\]

autoconsumo.

---

# 37. Hipótesis científica

La hipótesis principal del despacho sostenible puede formularse como:

> Una estrategia predictiva que incorpore explícitamente el coste asociado al
> ciclado de batería puede reducir el desgaste del almacenamiento sin producir
> un incremento significativo del coste energético total.

Esto deberá validarse experimentalmente.

---

# 38. Estado actual

El módulo de despacho ya permite generar para cada hora:

```text
Hora
FV
Demanda
SOC
SOC objetivo
Compra
Venta
Carga
Descarga
Acción
```

y obtener métricas diarias de comportamiento.

La siguiente evolución consiste en:

1. incorporar el plan semanal al perfil real de demanda;
2. extender el horizonte a varios días;
3. utilizar medidas reales del inversor;
4. calibrar el coste de degradación;
5. cerrar el lazo de control.

---

# 39. Ejemplo conceptual

Supongamos:

\[
P_{FV}=3.0\ \mathrm{kW}
\]

\[
P_D=2.0\ \mathrm{kW}
\]

Entonces:

\[
P_{exc}=1.0\ \mathrm{kW}
\]

Si:

\[
SOC<SOC^{obj}
\]

puede decidirse:

\[
P_{ch}=1.0\ \mathrm{kW}
\]

y:

\[
P_{sell}=0
\]

Si la batería ya se encuentra suficientemente cargada:

\[
P_{ch}=0
\]

y:

\[
P_{sell}=1.0\ \mathrm{kW}
\]

---

# 40. Ejemplo con déficit

Supongamos:

\[
P_{FV}=0.5\ \mathrm{kW}
\]

\[
P_D=1.5\ \mathrm{kW}
\]

El déficit es:

\[
P_{def}=1.0\ \mathrm{kW}
\]

Si la batería tiene suficiente SOC pero el precio de compra es muy bajo, puede
resultar:

\[
P_{dis}=0
\]

\[
P_{buy}=1.0\ \mathrm{kW}
\]

Si el precio es elevado y la batería tiene suficiente margen:

\[
P_{dis}=1.0\ \mathrm{kW}
\]

\[
P_{buy}=0
\]

Esta decisión es precisamente la que diferencia un sistema predictivo de una
estrategia de autoconsumo convencional.

---

# 41. Objetivo final

El propósito de `dispatch.py` es transformar:

\[
\boxed{
\text{FV}
+
\text{demanda}
+
\text{SOC}
+
\text{precios}
+
\text{predicción futura}
}
\]

en:

\[
\boxed{
\text{acciones horarias físicamente viables}
}
\]

minimizando simultáneamente:

- coste energético;
- degradación de batería;
- consumo innecesario de red;

sin comprometer:

- confort;
- seguridad;
- disponibilidad energética.
