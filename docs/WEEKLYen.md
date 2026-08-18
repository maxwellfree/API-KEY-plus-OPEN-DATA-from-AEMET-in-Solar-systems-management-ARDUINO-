# Weekly Service Planning

## Predictive Solar Energy Management — `weekly.py`

[🇪🇸 Versión en español](WEEKLY.md)

---

This document describes the weekly planning logic used by **Predictive Solar Energy Management**.

While `dispatch.py` answers:

> **Where should the energy come from during each hour?**

`weekly.py` answers:

> **When should each service preferably be provided during the coming days?**

Weekly planning uses:

- AEMET weather forecasts;
- hourly resolution for the near-term horizon;
- daily resolution for the rest of the week;
- solar availability;
- forecast temperature;
- user presence;
- load flexibility;
- weekly frequency;
- physical constraints;
- simultaneity constraints;
- thermal requirements;
- availability of alternative solar resources.

---

# 1. Weekly horizon

The basic horizon is:

```math
H = 7\ \text{days}
```

Not all days are treated with the same forecasting precision.

A multiresolution approach is used:

```math
\text{forecast}(t)
=
\begin{cases}
\text{hourly AEMET}, & t \lesssim 48\ \text{h}\\[4pt]
\text{daily AEMET}, & t > 48\ \text{h}
\end{cases}
```

The idea is to use the highest available resolution without assigning artificial hourly precision to distant forecasts.

---

# 2. Planning confidence

Confidence decreases with the forecasting horizon.

Conceptually:

```text
today / tomorrow
      ↓
high confidence

intermediate days
      ↓
medium confidence

end of week
      ↓
low confidence
```

A recommendation for tomorrow can therefore be considered more robust than a recommendation for six days ahead.

---

# 3. Service classification

Not all loads should be managed in the same way.

`weekly.py` separates services into several physical categories.

## 3.1 Shiftable tasks

These are loads that must operate for a certain duration but whose start time can be moved.

Examples:

- washing machine;
- electric oven;
- food processor.

The main variable is the starting time:

```math
t_i
```

and the task occupies a duration:

```math
\tau_i
```

therefore:

```math
[t_i,\ t_i+\tau_i]
```

must remain inside an admissible time window.

---

# 4. Thermal loads

Thermal loads should not be treated as simple tasks.

Examples:

- upper-floor heat pump;
- lower-floor heat pump;
- pantry air conditioner.

Their operation depends on the forecast outdoor temperature and, in future versions, also on indoor temperature and building thermal inertia.

---

# 5. Conditional loads

These are services that should not be activated automatically merely because electricity is available.

The main example is:

```text
electric DHW heater
```

The correct logic is:

```text
solar thermal collection
        ↓
heat-exchange pump
        ↓
storage-tank temperature
        ↓
DHW sufficient?
   │             │
  yes            no
   │             │
   ▼             ▼
do not use   electric backup
heater
```

Therefore, the electric water heater is a backup load.

---

# 6. External constraints

Some services are governed by criteria that are not primarily electrical.

The main example is irrigation.

The following should be considered:

- plant requirements;
- temperature;
- precipitation;
- evaporation;
- suitable time of day;
- weekly frequency.

Electrical optimization is secondary.

---

# 7. Solar alternatives

The model also considers resources that directly reduce electricity demand.

The main example is solar cooking.

When the solar index is sufficiently high:

```math
S_d \geq S_{min}
```

a suitable usage window can be proposed.

This does not increase:

```math
P_{FV}
```

but instead reduces:

```math
P_D
```

---

# 8. Daily solar index

For every day, an indicator is used:

```math
S_d \in [0,1]
```

which summarizes meteorological conditions relevant to solar availability.

It may depend on:

- sky conditions;
- precipitation;
- temperature;
- meteorological penalties.

This index does not replace the physical hourly model in `solar.py`.

Its main purpose in `weekly.py` is to compare days with one another.

---

# 9. Qualitative day classification

From $S_d$, the system can generate categories such as:

```text
excellent
good
acceptable
poor
```

This makes the weekly plan easier for the user to interpret.

---

# 10. Shiftable tasks

For a task $i$, the planner searches for a window compatible with:

```math
W_i
=
[t_{min,i},t_{max,i}]
```

and with duration:

```math
\tau_i
```

The task must satisfy:

```math
t_i \geq t_{min,i}
```

and:

```math
t_i+\tau_i
\leq t_{max,i}
```

---

# 11. Presence

Some loads require physical user presence.

If:

```math
P_{user}(t)=0
```

the task cannot be assigned to that interval.

The effective window is therefore:

```math
W_i^{eff}
=
W_i
\cap
W_{presence}
```

This is particularly relevant for:

- washing machine;
- oven;
- food processor;
- certain manual operations.

---

# 12. Weekly frequency

Not every task must be executed every day.

A frequency may be defined:

```math
f_i
```

for example:

```text
washing machine:
4 uses/week
```

The scheduler distributes these executions among the available days.

---

# 13. Simultaneity

Even when two tasks are flexible, running them simultaneously may be undesirable.

The system controls:

```math
P_{tasks}(t)
=
\sum_i P_i(t)
```

to avoid unnecessary peaks.

A general condition would be:

```math
P_{tasks}(t)
\leq
P_{flex,max}
```

---

# 14. Suitability function

Conceptually, each possible window may receive a score:

```math
Q_i(d,t)
```

depending on:

```math
Q_i
=
f
\left(
S_d,
P_{FV},
\text{price},
\text{presence},
\text{simultaneity},
\text{confidence}
\right)
```

A generic form would be:

```math
Q_i
=
w_s Q_{solar}
+
w_p Q_{price}
+
w_u Q_{user}
-
w_c Q_{concurrency}
```

The current version may implement this logic using discrete rules instead of a continuous objective function.

---

# 15. Thermal management in summer

For cooling, planning uses the forecast outdoor temperature.

In the near-term horizon:

```math
T=T(h)
```

with hourly resolution.

For later days:

```math
T\approx T_{max}
```

The conceptual logic is:

```math
u_{cool}(h)
=
\begin{cases}
1, & T(h)\geq T_{on}\\
0, & T(h)<T_{on}
\end{cases}
```

where $u_{cool}$ represents the recommendation to operate cooling.

---

# 16. Summer threshold

The current version uses different initial thresholds for the dwelling and the pantry.

Conceptually:

```text
dwelling
T >= 30 °C
→ cooling

pantry
T >= 27 °C
→ cooling
```

These values should be understood as initial control parameters, not universal thresholds.

In a future version they should be moved to `config.py`.

---

# 17. Summer operating window

The dwelling follows a known household strategy:

```text
night
↓
natural ventilation

morning
↓
close windows

midday/afternoon
↓
cooling if temperature requires it

around 18:00
↓
switch off
```

Therefore, even if AEMET forecasts a high temperature at 10:00, the system may restrict air-conditioning operation to the admissible household window.

---

# 18. Grouping of thermal hours

If AEMET predicts:

```text
12:00   28 °C
13:00   29 °C
14:00   31 °C
15:00   34 °C
16:00   35 °C
17:00   32 °C
```

and:

```math
T_{on}=30^\circ C
```

the active hours are:

```text
14
15
16
17
```

which are grouped into a single window:

```text
14:00–18:00
```

---

# 19. Cooling intensity level

The thermal recommendation may be classified qualitatively as:

```text
mild
medium
high
```

according to forecast temperature.

This allows the user to receive not only the operating window but also an indication of expected thermal intensity.

---

# 20. Thermal management in winter

For heating, the most representative variable is:

```math
T_{min}
```

especially when deciding whether heating is needed early in the day.

When hourly forecasting is available:

```math
T=T(h)
```

specific windows can be analysed:

```text
morning
07:00–09:00

evening
18:00–22:00
```

---

# 21. Heating threshold

Conceptually:

```math
u_{heat}(h)
=
\begin{cases}
1,&T(h)\leq T_{heat}\\
0,&T(h)>T_{heat}
\end{cases}
```

An initial value may be, for example:

```math
T_{heat}\approx12^\circ C
```

as an approximate outdoor criterion.

This parameter should be calibrated experimentally.

---

# 22. Tmin and Tmax

For days without sufficiently detailed hourly information:

- in summer, $T_{max}$ is used mainly;
- in winter, $T_{min}$ is preferred.

If $T_{min}$ is unavailable, the system may temporarily use:

```math
T_{max}
```

as a fallback indicator.

The output should identify that a fallback is being used.

---

# 23. Weather source used for the decision

Thermal planning explicitly distinguishes between:

```text
AEMET_hourly
```

and:

```text
AEMET_daily
```

This is important when interpreting recommendation quality.

A window derived from near-term hourly data has greater resolution than a window estimated from a daily maximum several days ahead.

---

# 24. Hybrid planning

The logic of version 4 can be summarized as:

```math
\boxed{
\text{High resolution nearby}
+
\text{low resolution farther away}
}
```

This makes it possible to maintain a long planning horizon without pretending to have precision that does not exist.

---

# 25. DHW

Domestic hot water is planned separately from space conditioning.

The system attempts to use first:

```math
E_{solar,thermal}
```

before:

```math
E_{electric}
```

The recommendation depends on the solar resource available that day.

---

# 26. High solar-availability days for DHW

If:

```math
S_d
```

is high, the system recommends:

```text
Prioritize solar thermal collection
and the heat-exchange pump.
```

The electric heater should intervene only if:

```math
T_{DHW}<T_{min,DHW}
```

---

# 27. Low solar-availability days

When solar availability is low, the plan may anticipate:

```text
possible electric backup
```

In that case, the electric heater should be scheduled considering:

- purchase price;
- available PV production;
- actual storage-tank temperature.

---

# 28. Irrigation

Irrigation planning prioritizes agronomically reasonable times.

For example:

```text
06:00–08:00
```

rather than the period of maximum solar production.

This illustrates an important feature:

> **minimum electricity cost is not always the primary criterion.**

---

# 29. Precipitation

Future versions may introduce a rule such as:

```math
P_{rain}(d)>P_{threshold}
```

or:

```math
R_d>R_{min}
```

to cancel or reduce scheduled irrigation.

---

# 30. Solar cooking

When:

```math
S_d\geq S_{solar\_oven}
```

a window such as:

```text
12:00–16:00
```

is proposed.

Solar cooking may partially or fully replace:

- electric oven;
- food processor;
- other cooking loads.

---

# 31. Planning and electrical demand

The weekly plan should not remain separated from the electrical demand profile.

If the plan decides:

```text
washing machine
13:30–15:00
```

the demand profile must be modified.

Formally:

```math
P_D^{new}(t)
=
P_D^{base}(t)
+
P_{washer}(t)
```

---

# 32. Coupling with dispatch

The target architecture is:

```text
weekly.py
    ↓
service plan
    ↓
modified demand profile
    ↓
balance.py
    ↓
dispatch.py
```

Dispatch must be recalculated once the loads have been shifted.

---

# 33. Joint iteration

A more advanced evolution could perform:

```text
1. calculate weekly plan
2. generate demand
3. calculate dispatch
4. evaluate cost/cycles
5. modify plan
6. repeat
```

Mathematically:

```math
Q^{(k+1)}
=
F(Q^{(k)})
```

until a sufficiently stable solution is reached.

---

# 34. User flexibility

Admissible windows should be configurable.

The user may provide:

```math
W_{home}(d)
```

representing when they are at home.

Example:

```text
Monday-Friday
07:00–08:30
18:00–22:00

Saturday-Sunday
08:00–22:00
```

This directly modifies real flexibility.

---

# 35. Automation

Not all loads require presence.

Automatable loads may run without direct intervention.

This makes it possible to distinguish:

```math
W_i^{auto}
```

from:

```math
W_i^{presence}
```

---

# 36. User recommendations

Planning can be converted into messages.

Examples:

```text
Good time to run the washing machine:
Sunday 13:30–15:00.
```

```text
Today it is not necessary to use the electric water heater.
```

```text
Cooling is recommended between 14:00 and 18:00.
```

```text
Today is a good day to use the solar oven.
```

---

# 37. Mobile use

A future mobile interface could display:

```text
TODAY

13:30 Washing machine
14:00 Cooling
14:30 Food processor

Target SOC: 55 %
Forecast PV: high
```

and generate notifications.

---

# 38. Weekly planning versus automatic control

It is important to distinguish:

```text
planning
```

from:

```text
execution
```

`weekly.py` produces recommendations and schedules.

A future control system should verify immediately before execution:

- inverter state;
- actual SOC;
- actual temperature;
- presence;
- connectivity;
- updated prices;
- safety constraints.

---

# 39. Continuous updating

A weekly plan should not be considered final.

Every day:

```math
Forecast_{new}
```

replaces:

```math
Forecast_{old}
```

so the plan can be recalculated.

Ideally:

```text
every morning
↓
update AEMET
↓
update prices
↓
recalculate plan
```

---

# 40. Replanning after meteorological changes

If a forecast changes significantly:

```math
|S_d^{new}-S_d^{old}|
>
\Delta S_{threshold}
```

it may be appropriate to automatically reschedule flexible tasks.

---

# 41. Thermal replanning

HVAC planning is especially sensitive to temperature changes.

If:

```math
T^{new}(h)
\neq
T^{old}(h)
```

the thermal window should be recalculated.

This means that the first 24–48 hours should be updated more frequently.

---

# 42. Uncertainty

Weather forecasts contain uncertainty.

Therefore, planning should evolve toward:

```math
P(T_h)
```

and:

```math
P(G_h)
```

instead of using only deterministic values.

A future objective function could include:

```math
E[J]
```

or risk penalties.

---

# 43. Robust planning

A robust strategy could avoid scheduling a critical load in a window that is only feasible under an overly optimistic forecast.

Conceptually:

```math
Q_{robust}
=
Q
-
\lambda\sigma
```

where $\sigma$ represents uncertainty.

---

# 44. Future thermal model

The current version uses outdoor temperature as a decision variable.

A more physical formulation should include an indoor state:

```math
T_{in}(t)
```

with a simplified RC-type equation:

```math
C
\frac{dT_{in}}{dt}
=
\frac{T_{out}-T_{in}}{R}
+
Q_{solar}
+
Q_{internal}
+
Q_{HVAC}
```

where:

- $R$ represents effective thermal resistance;
- $C$ is thermal capacitance;
- $Q_{HVAC}$ is the HVAC thermal contribution.

---

# 45. Predictive precooling

With a thermal model, it may be possible to choose:

```math
T_{in}(t)<T_{set}
```

during hours of PV surplus in order to reduce later consumption.

This shifts energy in time using the thermal mass of the building.

---

# 46. DHW as thermal storage

The hot-water storage tank can be modelled as:

```math
E_{DHW}
=
m c_p
(T_{DHW}-T_{ref})
```

This would allow a direct comparison between:

```text
charge battery
```

and:

```text
heat water
```

during surplus periods.

---

# 47. Weekly objective function

The full problem can be represented as:

```math
\max
\sum_{d,t,i}
Q_i(d,t)x_i(d,t)
```

subject to:

```math
\sum_{d,t}x_i(d,t)=f_i
```

for every task $i$,

together with constraints on:

- presence;
- duration;
- power;
- simultaneity;
- temperature;
- frequency.

---

# 48. Binary variable

For discrete tasks:

```math
x_{i,d,t}
\in
\{0,1\}
```

where:

```math
x_{i,d,t}=1
```

means that task $i$ starts on day $d$ at time $t$.

This would allow `weekly.py` to be transformed into an integer-programming problem.

---

# 49. Future mathematical programming

The natural evolution may use:

- Linear Programming;
- Mixed Integer Linear Programming;
- Dynamic Programming;
- Model Predictive Control.

In particular:

```math
MILP
```

is well suited to discrete time-scheduled tasks.

---

# 50. Relationship with MPC

`weekly.py` may provide the upper planning horizon of an MPC system.

For example:

```text
weekly
    ↓
constraints / preferences
    ↓
MPC 24–48 h
    ↓
hourly setpoints
```

Weekly planning would act as the strategic layer and MPC as the operational layer.

---

# 51. Planning validation

Planning should also be validated experimentally.

The comparison can include:

```text
recommended schedule
vs.
actual schedule
```

and measure:

- shifted energy;
- savings;
- additional self-consumption;
- cycling reduction;
- user acceptance.

---

# 52. Shifted-energy metric

Define:

```math
E_{shift}
=
\sum_i
E_i^{moved}
```

and the percentage:

```math
R_{shift}
=
\frac{E_{shift}}{E_{flex,total}}
```

---

# 53. Benefit of flexibility

A useful metric is to compare:

```math
C_{fixed}
```

with:

```math
C_{flex}
```

and define:

```math
\Delta C_{flex}
=
C_{fixed}
-
C_{flex}
```

---

# 54. Self-consumption gain

Also:

```math
\Delta E_{auto}
=
E_{auto}^{flex}
-
E_{auto}^{fixed}
```

This makes it possible to scientifically quantify the value of household scheduling.

---

# 55. Interaction with the battery

Good weekly planning can reduce the need for storage.

If a load can be shifted from night to midday:

```math
E_{battery}
\downarrow
```

without reducing the service provided.

This is one of the central ideas of the project:

> **demand flexibility can partially replace electrochemical storage.**

---

# 56. Energy hierarchy

Sustainable planning approximately attempts to follow:

```text
1. required service
2. direct PV
3. temporal shifting
4. thermal storage
5. battery
6. grid / export
```

The exact order may vary depending on prices and constraints.

---

# 57. Current status

Version 4 of `weekly.py` implements:

- seven-day horizon;
- service classification;
- shiftable tasks;
- DHW;
- irrigation;
- solar cooking;
- thermal management;
- hourly AEMET for the near-term horizon;
- daily AEMET for the rest;
- confidence dependent on forecast horizon.

---

# 58. Current limitations

The main limitations include:

- no indoor-temperature measurement;
- thermal thresholds still defined manually;
- household flexibility based on rules;
- weekly planning not yet fully coupled to `dispatch.py`;
- no MILP optimization;
- no explicit meteorological probabilities;
- no feedback from actual user behaviour.

---

# 59. Next steps

The next natural developments are:

1. move thermal thresholds to `config.py`;
2. incorporate daily minimum temperature;
3. incorporate measured indoor temperature;
4. automatically modify the `demand.py` profile;
5. recalculate `dispatch.py` after planning;
6. extend prices and PV forecasts to 48–96 h;
7. incorporate uncertainty;
8. generate notifications;
9. integrate home automation;
10. validate experimentally.

---

# 60. Final objective

The purpose of `weekly.py` is to transform:

```math
\boxed{
\text{weather}
+
\text{flexibility}
+
\text{presence}
+
\text{household requirements}
}
```

into:

```math
\boxed{
\text{a useful energy schedule for the user}
}
```

and then use this schedule to construct a more intelligent electrical-demand profile that can be optimized by `dispatch.py`.
