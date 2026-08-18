# Mathematical Model and Energy Management Strategy

## Predictive Solar Energy Management — AEMET / PVGIS / ESIOS

[🇪🇸 Versión en español](MODEL.md)

---

This document describes the physical, energy, and economic model used by
**Predictive Solar Energy Management**.

The objective of the system is not only to maximize photovoltaic self-consumption
or minimize the instantaneous electricity cost. The algorithm attempts to coordinate:

- photovoltaic production;
- household demand;
- weather forecasting;
- hourly electricity prices;
- electrochemical storage;
- thermal storage;
- flexible loads;
- temperature-dependent services;
- surplus-energy export;
- and preservation of battery lifetime.

The general philosophy can be summarized as:

> **use solar energy directly whenever possible, shift consumption when feasible,
> and use the battery only when doing so is energetically or economically justified.**

---

# 1. Model architecture

The system can be represented by the following chain:

```text
                    ┌─────────────┐
                    │    AEMET    │
                    │   weather   │
                    └──────┬──────┘
                           │
                           ▼
┌───────────┐       ┌─────────────┐
│   PVGIS   │──────▶│  Solar model│
└───────────┘       └──────┬──────┘
                           │
                           ▼
                    PV production
                           │
                           ▼
┌───────────┐       ┌─────────────┐       ┌──────────────┐
│ Household │──────▶│   Energy    │◀──────│    ESIOS     │
│  demand   │       │   balance   │       │ prices €/kWh │
└───────────┘       └──────┬──────┘       └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Optimizer  │
                    └──────┬──────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Battery       Grid import    Flexible
                        and export     services
```

The model currently operates at two time scales:

1. **Weekly planning**, used to determine when certain services should preferably
   be provided.

2. **Hourly dispatch**, used to determine energy flows during the following
   24 hours.

---

# 2. Photovoltaic production

Photovoltaic production is obtained by combining a physical reference from PVGIS
with the AEMET weather forecast.

For each hour $h$, the predicted irradiance is defined as:

```math
G_h^{pred}
=
G_h^{PVGIS}\,F_h^{met}
```

where:

- $G_h^{PVGIS}$ is the reference irradiance;
- $F_h^{met}$ is the meteorological factor obtained from AEMET.

The meteorological factor modifies the PVGIS climatological profile according to
the forecast weather conditions.

---

# 3. Photovoltaic cell temperature

The power produced by a photovoltaic module depends on cell temperature.

In simplified form:

```math
T_{cell,h}
=
T_{amb,h}
+
\Delta T(G_h,v_h)
```

where:

- $T_{amb,h}$ is the forecast ambient temperature;
- $G_h$ is irradiance;
- $v_h$ is wind speed.

Cell temperature increases with irradiance and decreases with wind-induced cooling.

---

# 4. Thermal correction of PV power

DC photovoltaic power can be approximated as:

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

where:

- $P_{STC}$ is the installed nominal power;
- $G_h$ is expressed in W/m²;
- $\gamma$ is the temperature coefficient of power;
- $T_{cell,h}$ is cell temperature.

For modern modules, $\gamma$ is usually negative.

Therefore, high temperatures reduce the available photovoltaic power.

---

# 5. Inverter limitation

AC power cannot exceed the nominal inverter power:

```math
P_{FV,h}
=
\min
\left(
P_{AC,h},
P_{inv,max}
\right)
```

This represents inverter *clipping* when the available PV-array power exceeds
the inverter capacity.

---

# 6. Daily photovoltaic energy

For hourly intervals:

```math
E_{FV}
=
\sum_{h=0}^{23}
P_{FV,h}\Delta t
```

with:

```math
\Delta t = 1\ \mathrm{h}
```

and therefore:

```math
E_{FV}
=
\sum_{h=0}^{23}
P_{FV,h}
```

when power is expressed in kW and the interval is exactly one hour.

---

# 7. Demand model

Total demand is constructed from the different household loads:

```math
P_D(h)
=
P_{base}(h)
+
\sum_i P_i(h)
```

Loads are classified according to their management flexibility.

## Non-shiftable loads

These represent consumption that must occur when required.

## Shiftable loads

These can be moved to periods with more favourable energy conditions.

Examples:

- washing machine;
- electric oven;
- food processor.

## Thermal loads

Their use depends on weather conditions.

Examples:

- air conditioning;
- heat pump.

## Conditional loads

These are used only when another resource cannot provide the required service.

Example:

- electric water heater as backup for the solar thermal system.

## External constraints

Some services are not optimized exclusively according to electrical criteria.

Example:

- irrigation.

---

# 8. Hourly energy balance

For every hour:

```math
B_h
=
P_{FV,h}
-
P_{D,h}
```

If:

```math
B_h>0
```

there is a photovoltaic surplus:

```math
E_{exc,h}
=
\max(B_h,0)
```

If:

```math
B_h<0
```

there is a deficit:

```math
E_{def,h}
=
\max(-B_h,0)
```

---

# 9. Direct self-consumption

Photovoltaic energy used directly is:

```math
E_{auto,h}
=
\min
\left(
E_{FV,h},
E_{D,h}
\right)
```

and on a daily basis:

```math
E_{auto}
=
\sum_h E_{auto,h}
```

The self-consumption ratio can be defined as:

```math
R_{auto}
=
\frac{E_{auto}}
{E_{FV}}
```

whereas direct energy self-sufficiency is:

```math
R_{self}
=
\frac{E_{auto}}
{E_D}
```

These two quantities represent different concepts.

---

# 10. Battery model

The battery is represented through its state of charge:

```math
SOC_h
=
\frac{E_{bat,h}}
{E_{nom}}
```

where:

- $E_{bat,h}$ is stored energy;
- $E_{nom}$ is nominal capacity.

Its temporal evolution can be expressed as:

```math
E_{bat,h+1}
=
E_{bat,h}
+
\eta_c E_{charge,h}
-
\frac{E_{discharge,h}}{\eta_d}
```

where:

- $\eta_c$ is charging efficiency;
- $\eta_d$ is discharging efficiency.

---

# 11. Sustainable battery window

The entire nominal battery capacity is not necessarily used.

The operating constraint is:

```math
SOC_{min}
\leq
SOC_h
\leq
SOC_{max}
```

The usable energy within this window is:

```math
E_{usable}
=
E_{nom}
(SOC_{max}-SOC_{min})
```

This restriction protects the battery against unnecessary depth of discharge.

---

# 12. Equivalent cycles

An important metric is the total cycled energy:

```math
E_{cycle}
=
E_{charge}
+
E_{discharge}
```

An approximation to the number of equivalent full cycles is:

```math
N_{eq}
=
\frac{
E_{charge}+E_{discharge}
}{
2E_{nom}
}
```

This variable makes it possible to explicitly include battery wear in the
control strategy.

---

# 13. Cost of purchasing electricity

For every hour:

```math
C_h
=
E_{grid,h}^{buy}
p_h^{buy}
```

The daily cost is:

```math
C_{grid}
=
\sum_h
E_{grid,h}^{buy}
p_h^{buy}
```

---

# 14. Revenue from surplus energy

Exported energy generates:

```math
I_h
=
E_{grid,h}^{sell}
p_h^{sell}
```

and:

```math
I_{grid}
=
\sum_h I_h
```

The net economic balance is:

```math
C_{net}
=
C_{grid}
-
I_{grid}
```

---

# 15. Implicit cost of battery use

Battery discharge is not necessarily free.

Every cycle causes degradation.

An equivalent cost can be introduced:

```math
C_{bat}
=
c_{deg}
E_{throughput}
```

where $c_{deg}$ represents the estimated degradation cost per unit of processed
energy.

This leads to an important rule:

```math
\text{discharge battery}
\quad\text{only if}\quad
V_{energy}
>
C_{degradation}
```

Therefore, purchasing a small amount of inexpensive electricity may be preferable
to performing a low-value battery cycle.

---

# 16. Predictive target SOC

The algorithm does not rely only on fixed limits.

A target SOC dependent on future conditions can be defined:

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

If high solar production is expected, it is not necessary to keep the battery
excessively charged.

If low future production is expected, maintaining a larger energy reserve may
be advisable.

This turns the control strategy into a **predictive**, rather than merely
reactive, approach.

---

# 17. Flexible-load scheduling

For a flexible load $i$, the problem is to determine the starting time:

```math
t_i^*
=
\arg\max_t
S_i(t)
```

where $S_i(t)$ is a suitability function.

Conceptually, it may depend on:

```math
S_i(t)
=
w_s S_{solar}
+
w_p S_{price}
+
w_b S_{battery}
+
w_u S_{user}
```

with configurable weights.

Scheduling attempts to shift loads toward periods with available PV production
without violating service-use constraints.

---

# 18. Thermal management

Thermal loads have a different characteristic:

> their demand depends on the weather itself.

Therefore, the temperature forecast by AEMET is used to determine whether
climate control is required.

Cooling can be represented as:

```math
u_{cool}(t)
=
\begin{cases}
1, & T(t) > T_{cool}\\
0, & T(t) \leq T_{cool}
\end{cases}
```

and heating as:

```math
u_{heat}(t)
=
\begin{cases}
1, & T(t) < T_{heat}\\
0, & T(t) \geq T_{heat}
\end{cases}
```

where $u(t)$ represents the activation recommendation.

---

# 19. Hourly and daily forecasting

The model uses two meteorological resolutions.

## Near-term horizon

When an hourly AEMET forecast is available:

```math
T=T(h)
```

thermal decisions can be made hour by hour.

## Longer-term horizon

When only a daily forecast is available:

```math
T
\approx
\left(
T_{min},
T_{max}
\right)
```

Uncertainty increases with the forecast horizon.

The system therefore assigns qualitative confidence levels:

- high;
- medium;
- low.

---

# 20. Thermal storage before electrochemical storage

An important feature of the model is the recognition that certain loads can
indirectly store energy.

Examples include:

- heating domestic hot water during solar-production periods;
- precooling a building;
- conditioning the building during PV-production hours;
- cooking during maximum production.

In these cases, the building, water, or food partly acts as an energy-storage
medium.

The proposed hierarchy is:

```text
Direct PV
    ↓
Shiftable consumption
    ↓
Thermal storage
    ↓
Battery
    ↓
Grid export / import
```

The exact position of export, battery, and grid operation may vary depending on
electricity prices and the selected strategy.

---

# 21. General objective function

The complete problem can be formulated as a multi-objective optimization:

```math
\min J
```

with:

```math
J
=
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

where:

- $C_{grid}$: cost of purchased electricity;
- $I_{grid}$: revenue from exported electricity;
- $C_{battery}$: estimated battery degradation;
- $E_{waste}$: unused renewable energy;
- $P_{discomfort}$: penalty for loss of comfort;
- $P_{constraints}$: penalty for constraint violations.

The coefficients $\lambda_i$ allow the operating philosophy to be modified.

---

# 22. Sustainable predictive strategy

The currently implemented strategy prioritizes:

1. satisfying required demand;
2. using PV energy directly;
3. shifting flexible loads toward solar hours;
4. exploiting thermal storage;
5. avoiding marginal electrochemical cycles;
6. using the battery when a sufficient advantage exists;
7. purchasing electricity when it is more reasonable than degrading the battery;
8. exporting surplus energy when no more convenient local use exists.

The objective is not to maximize absolute daily economic profit.

The objective is to achieve a compromise among:

```math
\boxed{
\text{cost}
+
\text{self-consumption}
+
\text{battery lifetime}
+
\text{comfort}
+
\text{sustainability}
}
```

---

# 23. Weekly planning

For each day $d$, a solar indicator is constructed:

```math
S_d \in [0,1]
```

from:

- sky conditions;
- precipitation;
- temperature;
- forecast horizon.

The weekly scheduler uses this indicator to select the most suitable days for
shiftable loads.

Weekly planning answers:

> **When should each service preferably be provided during the next few days?**

Hourly dispatch answers a different question:

> **Where should the required energy come from during each hour?**

Both layers are complementary.

---

# 24. Complete decision flow

The conceptual algorithm flow is:

```text
AEMET forecast
       │
       ├───────────────┐
       ▼               ▼
    weather         temperature
       │               │
       ▼               ▼
    PV model       thermal loads
       │
       └───────┬───────┘
               ▼
        forecast demand
               │
               ▼
         hourly balance
               │
               ├──── ESIOS prices
               │
               ├──── battery state
               │
               └──── flexible loads
               │
               ▼
       predictive optimizer
               │
     ┌─────────┼───────────┐
     ▼         ▼           ▼
self-consume battery      grid
                         │
                    ┌────┴────┐
                    ▼         ▼
                  import     export
```

---

# 25. Current limitations

The model remains experimental.

Its main current simplifications include:

- partially theoretical household demand;
- absence of instantaneous real inverter measurements;
- absence of real SOC read directly from the BMS;
- imperfect cloud-cover prediction;
- simplified building thermal model;
- approximate battery-degradation model;
- rule-based user behaviour;
- absence of global mathematical optimization over the complete horizon.

Therefore, the resulting decisions should currently be regarded as
**predictive recommendations**, not certified control commands.

---

# 26. Experimental validation

The next phase of the project is to record real data from the installation.

Ideally:

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

with a known temporal resolution.

This will make it possible to compare:

```math
P_{FV}^{predicted}(t)
\quad\text{vs.}\quad
P_{FV}^{measured}(t)
```

and:

```math
E_{grid}^{predicted}
\quad\text{vs.}\quad
E_{grid}^{measured}
```

---

# 27. Validation metrics

For photovoltaic prediction, metrics such as the following can be used.

## MAE

```math
MAE
=
\frac{1}{N}
\sum_{i=1}^{N}
|P_i-\hat P_i|
```

## RMSE

```math
RMSE
=
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
(P_i-\hat P_i)^2
}
```

## Daily energy error

```math
\epsilon_E
=
\frac{
E_{pred}-E_{real}
}{
E_{real}
}
```

The following should also be evaluated:

- economic savings;
- reduction in purchased energy;
- increase in self-consumption;
- equivalent battery cycles;
- energy shifted through flexible loads.

---

# 28. Future evolution

The architecture is designed to evolve from a recommendation system toward a
control system.

A future version could incorporate:

```text
AEMET
PVGIS
ESIOS
   │
   ▼
OPTIMIZER
   │
   ▼
API / Modbus / MQTT
   │
   ▼
INVERTER + BMS + HOME AUTOMATION
```

This could automatically execute commands such as:

- charge battery;
- discharge battery;
- limit discharge;
- modify minimum SOC;
- export surplus energy;
- activate domestic hot water;
- operate HVAC;
- execute programmable loads.

---

# 29. Predictive control

The natural evolution of the project is toward a
**Model Predictive Control (MPC)** scheme.

At every instant:

1. the current state is acquired;
2. forecasts are updated;
3. the future horizon is calculated;
4. decisions are optimized;
5. only the first action is executed;
6. the process is repeated using new data.

Mathematically:

```math
\mathbf{u}^{*}
=
\arg\min_{\mathbf{u}}
J(\mathbf{x},\mathbf{u})
```

subject to:

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

and to the energy balance:

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

# 30. Scientific objective

The scientific interest of the project is not limited to predicting photovoltaic
production.

The main question is whether the combination of:

```math
\boxed{
\text{weather forecasting}
+
\text{PV forecasting}
+
\text{prices}
+
\text{demand flexibility}
+
\text{storage}
}
```

can simultaneously reduce:

- energy cost;
- grid consumption;
- unnecessary battery cycles;

while maintaining the required household services.

This hypothesis must be tested using experimental data obtained from a real
photovoltaic installation.

---

# 31. Project status

The software should currently be regarded as an experimental research platform.

The transition from simulation to real control requires:

1. continuous inverter-data acquisition;
2. historical data storage;
3. validation of the PV model;
4. validation of the demand model;
5. calibration of the battery model;
6. evaluation across different seasons;
7. comparison against reference strategies;
8. subsequent integration of remote control.

This separation between **prediction**, **optimization**, **validation**, and
**control** allows the project to evolve progressively without compromising
installation safety.
