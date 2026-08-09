# Modelo matemático y estrategia de gestión energética

## Gestión Solar Predictiva — AEMET / PVGIS / ESIOS

Este documento describe el modelo físico, energético y económico utilizado por
**Gestión Solar Predictiva**.

El objetivo del sistema no es únicamente maximizar el autoconsumo fotovoltaico
ni minimizar el coste eléctrico instantáneo. El algoritmo intenta coordinar:

- producción fotovoltaica,
- demanda doméstica,
- predicción meteorológica,
- precios horarios de electricidad,
- almacenamiento electroquímico,
- almacenamiento térmico,
- cargas flexibles,
- servicios dependientes de la temperatura,
- venta de excedentes,
- y conservación de la vida útil de la batería.

La filosofía general puede resumirse como:

> **utilizar primero la energía solar directamente, desplazar consumos cuando
> sea posible y utilizar la batería solamente cuando su uso esté
> energéticamente o económicamente justificado.**

---

# 1. Arquitectura del modelo

El sistema puede representarse mediante la cadena:

```text
                    ┌─────────────┐
                    │    AEMET    │
                    │ meteorología│
                    └──────┬──────┘
                           │
                           ▼
┌───────────┐       ┌─────────────┐
│   PVGIS   │──────▶│ Modelo solar│
└───────────┘       └──────┬──────┘
                           │
                           ▼
                    Producción FV
                           │
                           ▼
┌───────────┐       ┌─────────────┐       ┌──────────────┐
│  Demanda  │──────▶│   Balance   │◀──────│    ESIOS     │
│ doméstica │       │  energético │       │ precios €/kWh│
└───────────┘       └──────┬──────┘       └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Optimizador │
                    └──────┬──────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Batería       Compra/red     Servicios
                         y venta        flexibles
```

El modelo opera actualmente en dos escalas temporales:

1. **Planificación semanal**, utilizada para decidir cuándo conviene prestar
   determinados servicios.

2. **Despacho horario**, utilizado para decidir el flujo energético durante
   las siguientes 24 horas.

---

# 2. Producción fotovoltaica

La producción fotovoltaica se obtiene combinando una referencia física
procedente de PVGIS con la predicción meteorológica de AEMET.

Para cada hora $h$, se define una irradiancia prevista:


```math
G_h^{pred} =
G_h^{PVGIS}\,F_h^{met}
```


donde:

- $G_h^{PVGIS}$ es la irradiancia de referencia,
- $F_h^{met}$ es el factor meteorológico obtenido a partir de AEMET.

El factor meteorológico permite modificar el perfil climatológico de PVGIS
utilizando las condiciones meteorológicas previstas.

---

# 3. Temperatura de la célula fotovoltaica

La potencia de un panel depende de la temperatura de sus células.

De forma simplificada:


```math
T_{cell,h}
=
T_{amb,h}
+
\Delta T(G_h,v_h)
```


donde:

- $T_{amb,h}$ es la temperatura ambiente prevista,
- $G_h$ es la irradiancia,
- $v_h$ es la velocidad del viento.

La temperatura de la célula aumenta con la irradiancia y disminuye con la
refrigeración producida por el viento.

---

# 4. Corrección térmica de la potencia FV

La potencia fotovoltaica DC puede aproximarse mediante:


```math
P_{DC,h}
=
P_{STC}
\frac{G_h}{1000}
\left[
1+\gamma
(T_{cell,h}-25)
\right]
```


donde:

- $P_{STC}$ es la potencia nominal instalada,
- $G_h$ está expresada en W/m²,
- $\gamma$ es el coeficiente térmico de potencia,
- $T_{cell,h}$ es la temperatura de la célula.

Para módulos modernos, $\gamma$ suele ser negativo.

Por tanto, temperaturas elevadas reducen la potencia disponible.

---

# 5. Limitación del inversor

La potencia AC no puede superar la potencia nominal del inversor:


```math
P_{FV,h}
=
\min
\left(
P_{AC,h},
P_{inv,max}
\right)
```


Esto permite representar el *clipping* del inversor cuando la potencia
disponible del campo fotovoltaico supera su capacidad.

---

# 6. Energía fotovoltaica diaria

Con intervalos horarios:


```math
E_{FV}
=
\sum_{h=0}^{23}
P_{FV,h}\Delta t
```


con:


```math
\Delta t = 1\ \mathrm{h}
```


por lo que:


```math
E_{FV}
=
\sum_{h=0}^{23}
P_{FV,h}
```


cuando la potencia se expresa en kW y el intervalo es exactamente una hora.

---

# 7. Modelo de demanda

La demanda total se construye a partir de las diferentes cargas domésticas:


```math
P_D(h)
=
P_{base}(h)
+
\sum_i P_i(h)
```


Las cargas se clasifican según su capacidad de gestión.

## Cargas no desplazables

Representan consumos que deben producirse cuando son necesarios.

## Cargas desplazables

Pueden trasladarse hacia periodos con mejores condiciones energéticas.

Ejemplos:

- lavadora,
- horno,
- robot de cocina.

## Cargas térmicas

Su utilización depende de las condiciones meteorológicas.

Ejemplos:

- aire acondicionado,
- bomba de calor.

## Cargas condicionales

Se utilizan únicamente cuando otro recurso no puede proporcionar el servicio.

Ejemplo:

- termo eléctrico como apoyo al sistema solar térmico.

## Restricciones externas

Algunos servicios no se optimizan únicamente mediante criterios eléctricos.

Ejemplo:

- riego.

---

# 8. Balance energético horario

Para cada hora:


```math
B_h
=
P_{FV,h}
-
P_{D,h}
```


Si:


```math
B_h>0
```


existe excedente fotovoltaico:


```math
E_{exc,h}
=
\max(B_h,0)
```


Si:


```math
B_h<0
```


existe déficit:


```math
E_{def,h}
=
\max(-B_h,0)
```


---

# 9. Autoconsumo directo

La energía fotovoltaica utilizada directamente es:


```math
E_{auto,h}
=
\min
\left(
E_{FV,h},
E_{D,h}
\right)
```


y diariamente:


```math
E_{auto}
=
\sum_h E_{auto,h}
```


El ratio de autoconsumo puede definirse como:


```math
R_{auto}
=
\frac{E_{auto}}
{E_{FV}}
```


mientras que la autosuficiencia energética directa es:


```math
R_{self}
=
\frac{E_{auto}}
{E_D}
```


Estas dos magnitudes representan conceptos diferentes.

---

# 10. Modelo de batería

La batería se representa mediante su estado de carga:


```math
SOC_h =
\frac{E_{bat,h}}
{E_{nom}}
```


donde:

- $E_{bat,h}$ es la energía almacenada,
- $E_{nom}$ es la capacidad nominal.

La evolución temporal puede expresarse como:


```math
E_{bat,h+1}
=
E_{bat,h}
+
\eta_c E_{carga,h}
-
\frac{E_{descarga,h}}{\eta_d}
```


donde:

- $\eta_c$ es la eficiencia de carga,
- $\eta_d$ es la eficiencia de descarga.

---

# 11. Ventana sostenible de batería

No se utiliza necesariamente toda la capacidad nominal.

Se define:


```math
SOC_{min}
\leq
SOC_h
\leq
SOC_{max}
```


La energía utilizable dentro de esta ventana es:


```math
E_{usable}
=
E_{nom}
(SOC_{max}-SOC_{min})
```


Esta restricción protege la batería frente a profundidades de descarga
innecesarias.

---

# 12. Ciclos equivalentes

Una métrica importante es la energía total ciclada:


```math
E_{cycle}
=
E_{charge}
+
E_{discharge}
```


Una aproximación a los ciclos completos equivalentes es:


```math
N_{eq}
=
\frac{
E_{charge}+E_{discharge}
}{
2E_{nom}
}
```


Esta variable permite introducir explícitamente el desgaste de la batería en
la estrategia de control.

---

# 13. Coste de comprar electricidad

Para cada hora:


```math
C_h
=
E_{grid,h}^{buy}
p_h^{buy}
```


El coste diario es:


```math
C_{grid}
=
\sum_h
E_{grid,h}^{buy}
p_h^{buy}
```


---

# 14. Ingreso por excedentes

La energía exportada genera:


```math
I_h
=
E_{grid,h}^{sell}
p_h^{sell}
```


y:


```math
I_{grid}
=
\sum_h I_h
```


El balance económico neto es:


```math
C_{net}
=
C_{grid}
-
I_{grid}
```


---

# 15. Coste implícito de utilizar la batería

Una descarga de batería no es necesariamente gratuita.

Cada ciclo produce degradación.

Puede introducirse un coste equivalente:


```math
C_{bat}
=
c_{deg}
E_{throughput}
```


donde $c_{deg}$ representa el coste estimado de degradación por unidad de
energía procesada.

Esto conduce a una regla importante:


```math
\text{descargar batería}
\quad\text{solo si}\quad
V_{energia}
>
C_{degradacion}
```


Por tanto, comprar una pequeña cantidad de electricidad barata puede ser
preferible a realizar un ciclo de batería de escaso valor.

---

# 16. SOC objetivo predictivo

El algoritmo no utiliza únicamente límites fijos.

Puede establecer un SOC objetivo dependiente del futuro:


```math
SOC_h^{obj}
=
f
\left(
E_{FV}^{future},
E_D^{future},
p^{future},
SOC_{min},
SOC_{max}
\right)
```


Si se espera elevada producción solar, no es necesario conservar una batería
excesivamente cargada.

Si se espera baja producción futura, puede resultar conveniente conservar una
reserva energética mayor.

Esto convierte el control en una estrategia **predictiva**, no meramente
reactiva.

---

# 17. Planificación de cargas flexibles

Para una carga flexible $i$, el problema consiste en determinar el instante
de inicio:


```math
t_i^*
=
\arg\max_t
S_i(t)
```


donde $S_i(t)$ es una función de conveniencia.

Conceptualmente puede depender de:


```math
S_i(t)
=
w_s S_{solar}
+
w_p S_{precio}
+
w_b S_{bateria}
+
w_u S_{usuario}
```


con pesos configurables.

La planificación intenta desplazar cargas hacia periodos donde exista
producción FV disponible sin violar las restricciones de utilización del
servicio.

---

# 18. Gestión térmica

Las cargas térmicas presentan una característica diferente:

> su demanda depende del propio tiempo meteorológico.

Por ello, la temperatura prevista por AEMET se utiliza para decidir si existe
necesidad de climatización.

Puede representarse mediante:


```math
u_{cool}(t)
=
\begin{cases}
1, & T(t) > T_{cool}\\
0, & T(t) \leq T_{cool}
\end{cases}
```


y para calefacción:


```math
u_{heat}(t)
=
\begin{cases}
1, & T(t) < T_{heat}\\
0, & T(t) \geq T_{heat}
\end{cases}
```


donde $u(t)$ representa la recomendación de activación.

---

# 19. Predicción horaria y diaria

El modelo utiliza dos resoluciones meteorológicas.

## Horizonte próximo

Cuando existe predicción horaria AEMET:


```math
T=T(h)
```


y las decisiones térmicas pueden realizarse hora a hora.

## Horizonte lejano

Cuando únicamente existe predicción diaria:


```math
T \approx
\left(
T_{min},
T_{max}
\right)
```


La incertidumbre aumenta con el horizonte temporal.

Por ello, el sistema asigna niveles cualitativos de confianza:

- alta,
- media,
- baja.

---

# 20. Almacenamiento térmico antes que electroquímico

Una característica importante del modelo es considerar que determinados
consumos pueden almacenar indirectamente energía.

Por ejemplo:

- calentar ACS durante producción solar,
- enfriar previamente una vivienda,
- climatizar durante horas FV,
- cocinar durante máxima producción.

En estos casos el edificio, el agua o los alimentos actúan parcialmente como
almacenamiento energético.

La jerarquía propuesta es:

```text
FV directa
    ↓
consumo desplazable
    ↓
almacenamiento térmico
    ↓
batería
    ↓
venta / compra de red
```

La posición exacta de venta, batería y red puede variar dependiendo del precio
y de la estrategia seleccionada.

---

# 21. Función objetivo general

El problema completo puede formularse como una optimización multiobjetivo:


```math
\min J
```


con:


```math
J =
C_{grid}
-
I_{grid}
+
C_{battery}
+
\lambda_1 E_{waste}
+
\lambda_2 P_{discomfort}
+
\lambda_3 P_{constraints}
```


donde:

- $C_{grid}$: coste de electricidad comprada,
- $I_{grid}$: ingreso por electricidad vendida,
- $C_{battery}$: degradación estimada de batería,
- $E_{waste}$: energía renovable desaprovechada,
- $P_{discomfort}$: penalización por pérdida de confort,
- $P_{constraints}$: penalización por incumplimiento de restricciones.

Los coeficientes $\lambda_i$ permiten modificar la filosofía de operación.

---

# 22. Estrategia sostenible predictiva

La estrategia actualmente implementada prioriza:

1. satisfacer la demanda necesaria;
2. utilizar FV directamente;
3. desplazar cargas flexibles hacia horas solares;
4. aprovechar almacenamiento térmico;
5. evitar ciclos electroquímicos marginales;
6. utilizar batería cuando exista una ventaja suficiente;
7. comprar electricidad cuando resulte más razonable que degradar la batería;
8. vender excedentes cuando no exista un uso local más conveniente.

El objetivo no es maximizar de forma absoluta el beneficio económico diario.

El objetivo es obtener un compromiso entre:


```math
\boxed{
\text{coste}
+
\text{autoconsumo}
+
\text{vida de batería}
+
\text{confort}
+
\text{sostenibilidad}
}
```


---

# 23. Planificación semanal

Para cada día $d$ se construye un indicador solar:


```math
S_d \in [0,1]
```


A partir de:

- estado del cielo,
- precipitación,
- temperatura,
- horizonte de predicción.

El planificador semanal utiliza este indicador para seleccionar los días más
adecuados para cargas desplazables.

La planificación semanal responde a la pregunta:

> **¿Cuándo conviene prestar cada servicio durante los próximos días?**

El despacho horario responde a una pregunta diferente:

> **¿De dónde debe proceder la energía necesaria en cada hora?**

Ambas capas son complementarias.

---

# 24. Flujo completo de decisión

El flujo conceptual del algoritmo es:

```text
Predicción AEMET
       │
       ├───────────────┐
       ▼               ▼
 meteorología       temperatura
       │               │
       ▼               ▼
    modelo FV     cargas térmicas
       │
       └───────┬───────┘
               ▼
          demanda prevista
               │
               ▼
         balance horario
               │
               ├──── precios ESIOS
               │
               ├──── estado batería
               │
               └──── cargas flexibles
               │
               ▼
       optimizador predictivo
               │
     ┌─────────┼───────────┐
     ▼         ▼           ▼
 autoconsumo batería      red
                         │
                    ┌────┴────┐
                    ▼         ▼
                  compra     venta
```

---

# 25. Limitaciones actuales

El modelo sigue siendo experimental.

Entre las principales simplificaciones actuales se encuentran:

- demanda doméstica parcialmente teórica;
- ausencia de medida instantánea real del inversor;
- ausencia de SOC real leído directamente del BMS;
- predicción imperfecta de nubosidad;
- simplificación del modelo térmico del edificio;
- degradación de batería todavía aproximada;
- comportamiento del usuario modelado mediante reglas;
- ausencia de optimización matemática global del horizonte completo.

Por tanto, las decisiones obtenidas deben considerarse actualmente
**recomendaciones predictivas**, no órdenes de control certificadas.

---

# 26. Validación experimental

La siguiente fase del proyecto consiste en registrar datos reales de la
instalación.

Idealmente:


```math
\{
P_{FV},
P_{load},
P_{grid},
P_{battery},
SOC,
T,
G,
p_{buy},
p_{sell}
\}
```


con resolución temporal conocida.

Esto permitirá comparar:


```math
P_{FV}^{predicho}(t)
\quad\text{vs.}\quad
P_{FV}^{medido}(t)
```


y:


```math
E_{grid}^{predicho}
\quad\text{vs.}\quad
E_{grid}^{medido}
```


---

# 27. Métricas de validación

Para la predicción fotovoltaica pueden utilizarse métricas como:

## MAE


```math
MAE =
\frac{1}{N}
\sum_{i=1}^{N}
|P_i-\hat P_i|
```


## RMSE


```math
RMSE =
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
(P_i-\hat P_i)^2
}
```


## Error energético diario


```math
\epsilon_E
=
\frac{
E_{pred}-E_{real}
}{
E_{real}
}
```


También deberían evaluarse:

- ahorro económico,
- reducción de energía comprada,
- incremento de autoconsumo,
- ciclos equivalentes de batería,
- energía desplazada mediante cargas flexibles.

---

# 28. Evolución futura

La arquitectura está diseñada para evolucionar desde un sistema de
recomendación hacia un sistema de control.

Una futura versión podría incorporar:

```text
AEMET
PVGIS
ESIOS
   │
   ▼
OPTIMIZADOR
   │
   ▼
API / Modbus / MQTT
   │
   ▼
INVERSOR + BMS + DOMÓTICA
```

Esto permitiría ejecutar automáticamente órdenes como:

- cargar batería,
- descargar batería,
- limitar descarga,
- modificar SOC mínimo,
- vender excedentes,
- activar ACS,
- climatizar,
- ejecutar cargas programables.

---

# 29. Control predictivo

La evolución natural del proyecto es hacia un esquema de
**Model Predictive Control (MPC)**.

En cada instante:

1. se adquiere el estado actual;
2. se actualizan las predicciones;
3. se calcula el horizonte futuro;
4. se optimizan las decisiones;
5. se ejecuta únicamente la primera acción;
6. se repite el proceso con nuevos datos.

Matemáticamente:


```math
\mathbf{u}^{*}
=
\arg\min_{\mathbf{u}}
J(\mathbf{x},\mathbf{u})
```


sujeto a:


```math
SOC_{min}
\leq SOC(t)
\leq SOC_{max}
```



```math
0
\leq
P_{charge}(t)
\leq
P_{charge,max}
```



```math
0
\leq
P_{discharge}(t)
\leq
P_{discharge,max}
```


y al balance:


```math
P_{FV}
+
P_{grid}^{buy}
+
P_{battery}^{dis}
=
P_D
+
P_{battery}^{charge}
+
P_{grid}^{sell}
```


---

# 30. Objetivo científico

El interés del proyecto no reside únicamente en predecir la producción
fotovoltaica.

La cuestión principal es estudiar si la combinación de:


```math
\boxed{
\text{predicción meteorológica}
+
\text{predicción FV}
+
\text{precios}
+
\text{flexibilidad de demanda}
+
\text{almacenamiento}
}
```


permite reducir simultáneamente:

- coste energético,
- consumo de red,
- ciclos innecesarios de batería,

manteniendo los servicios domésticos requeridos.

Esta hipótesis deberá comprobarse mediante datos experimentales obtenidos de
una instalación fotovoltaica real.

---

# 31. Estado del proyecto

El software debe considerarse actualmente una plataforma experimental de
investigación.

La transición desde simulación hacia control real requiere:

1. adquisición continua de datos del inversor;
2. almacenamiento histórico;
3. validación del modelo FV;
4. validación del modelo de demanda;
5. calibración del modelo de batería;
6. evaluación durante diferentes estaciones;
7. comparación frente a estrategias de referencia;
8. incorporación posterior del control remoto.

Esta separación entre **predicción**, **optimización**, **validación** y
**control** permite evolucionar el proyecto progresivamente sin comprometer la
seguridad de la instalación.
