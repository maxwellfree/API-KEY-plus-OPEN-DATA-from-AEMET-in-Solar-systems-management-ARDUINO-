# Energy Dispatch and Battery Management

## Predictive Solar Energy Management — Hourly Operating Logic

[🇪🇸 Versión en español](DISPATCH.md)

---

This document describes the logic used to transform the photovoltaic–household energy balance into an hourly operating strategy.

For each hour, the dispatch module receives:

- forecast photovoltaic production;
- forecast demand;
- electricity purchase price;
- electricity sale price;
- initial battery state of charge;
- system operating limits;
- battery-preservation criteria.

From these inputs, it decides how energy should be distributed among:

- direct self-consumption;
- battery charging;
- battery discharging;
- grid import;
- surplus export.

---

# 1. Main variables

For each hourly interval $h$, the following variables are used:

```math
P_{FV,h}
```

available photovoltaic power,

```math
P_{D,h}
```

household demand,

```math
P_{ch,h}
```

battery charging power,

```math
P_{dis,h}
```

battery discharging power,

```math
P_{grid,h}^{buy}
```

power imported from the grid,

```math
P_{grid,h}^{sell}
```

power exported to the grid.

Battery state of charge is represented by:

```math
SOC_h
```

---

# 2. Power balance

For every hour, the following balance should approximately hold:

```math
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
```

This equation is the fundamental dispatch constraint.

---

# 3. Balance before battery operation

Before deciding how storage should be used, the net balance is calculated:

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

there is a photovoltaic surplus.

If:

```math
B_h<0
```

there is a deficit.

We define:

```math
P_{exc,h}
=
\max(B_h,0)
```

and:

```math
P_{def,h}
=
\max(-B_h,0)
```

---

# 4. Direct self-consumption

The first use of photovoltaic generation is to directly meet household demand.

```math
P_{auto,h}
=
\min
\left(
P_{FV,h},
P_{D,h}
\right)
```

Direct self-consumption avoids:

- additional conversion losses;
- battery cycling;
- electricity purchases;
- dependence on surplus compensation.

It is therefore the first energy priority.

---

# 5. State of charge

The state of charge is defined as:

```math
SOC_h
=
\frac{E_{bat,h}}{E_{nom}}
```

where:

- $E_{bat,h}$ is the energy stored in the battery;
- $E_{nom}$ is the nominal battery capacity.

Its update may be written as:

```math
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
```

where:

- $\eta_c$ is the charging efficiency;
- $\eta_d$ is the discharging efficiency.

---

# 6. SOC limits

The battery should not operate freely between 0 and 100%.

An operating window is defined:

```math
SOC_{min}
\leq
SOC_h
\leq
SOC_{max}
```

For the reference installation:

```text
normal SOC : 20–85 %
```

The algorithm may nevertheless use more conservative internal limits depending on the selected strategy.

---

# 7. Battery reserve

A central part of the strategy is to avoid discharging the battery merely because a temporary deficit exists.

A target SOC is introduced:

```math
SOC_h^{obj}
```

representing the amount of energy that should preferably be retained after considering future hours.

Conceptually:

```math
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
```

If strong PV production is expected a few hours later:

```math
SOC_h^{obj}
\downarrow
```

because the battery can be recharged afterwards.

If low future generation is expected:

```math
SOC_h^{obj}
\uparrow
```

so that additional reserve is retained.

---

# 8. Photovoltaic deficit

When:

```math
P_{D,h}>P_{FV,h}
```

the deficit is:

```math
P_{def,h}
=
P_{D,h}
-
P_{FV,h}
```

The system must then choose between:

```math
\text{battery}
```

and:

```math
\text{grid}
```

or a combination of both.

---

# 9. Available discharge

The energy available for discharge depends on the current SOC.

If:

```math
SOC_h > SOC_{min}
```

there is available energy margin.

It may be defined as:

```math
E_{available,h}
=
E_{nom}
\left(
SOC_h-SOC_{min}
\right)
```

Not all this energy should necessarily be used.

The strategy may retain an additional reserve associated with $SOC_h^{obj}$.

---

# 10. Sustainable discharge

A conceptual formulation is:

```math
P_{dis,h}
=
\min
\left[
P_{def,h},
P_{dis,max},
P_{available,h}
\right]
```

but only when sufficient justification exists.

The algorithm avoids a simplistic rule such as:

```text
if there is a deficit -> always discharge
```

because such a policy would tend to maximize battery cycling.

---

# 11. Battery preservation

The sustainable strategy introduces an implicit penalty associated with battery cycling.

It may be represented by:

```math
C_{deg,h}
=
c_{deg}
E_{throughput,h}
```

where:

```math
E_{throughput,h}
=
E_{ch,h}
+
E_{dis,h}
```

and $c_{deg}$ represents an equivalent degradation cost.

Although the current implementation may express this principle using rules and thresholds, this formulation provides a mathematical representation of the strategy.

---

# 12. Battery-versus-grid decision

When a deficit exists, the conceptual comparison is between:

```math
C_{grid,h}
=
p_{buy,h}
E_{def,h}
```

and:

```math
C_{battery,h}
=
C_{deg,h}
```

If:

```math
C_{grid,h}
<
C_{battery,h}
```

buying electricity may be preferable.

If:

```math
C_{grid,h}
>
C_{battery,h}
```

and sufficient SOC is available, battery discharge may be justified.

This leads to a fundamental policy:

> **Stored battery energy is not considered free.**

---

# 13. Photovoltaic surplus

When:

```math
P_{FV,h}>P_{D,h}
```

the surplus is:

```math
P_{exc,h}
=
P_{FV,h}
-
P_{D,h}
```

This surplus can:

1. charge the battery;
2. be exported to the grid;
3. supply flexible loads;
4. supply thermal storage;
5. be curtailed if no other option exists.

---

# 14. Battery charging

Charging power is constrained by:

```math
P_{ch,h}
\leq
P_{ch,max}
```

and by the available battery capacity:

```math
SOC_h < SOC_{max}
```

The maximum storable energy is approximately:

```math
E_{cap,h}
=
E_{nom}
\left(
SOC_{max}
-
SOC_h
\right)
```

Therefore:

```math
P_{ch,h}
=
\min
\left[
P_{exc,h},
P_{ch,max},
P_{cap,h}
\right]
```

---

# 15. Surplus export

Once the following have been satisfied:

- household demand;
- desired battery charging;
- flexible loads;
- thermal needs;

the remaining surplus can be exported.

```math
P_{grid,h}^{sell}
=
\max
\left[
P_{exc,h}
-
P_{ch,h},
0
\right]
```

The corresponding income is:

```math
I_h
=
P_{grid,h}^{sell}
p_{sell,h}
\Delta t
```

---

# 16. Grid import

Grid energy is used when:

- PV generation is insufficient;
- battery discharge is not convenient;
- the battery has reached its minimum SOC;
- energy should be preserved for future hours.

```math
P_{grid,h}^{buy}
=
P_{def,h}
-
P_{dis,h}
```

with:

```math
P_{grid,h}^{buy}\geq0
```

---

# 17. Ideal non-simultaneity

An ideal formulation should avoid situations such as:

```math
P_{grid}^{buy}>0
\quad\text{and}\quad
P_{grid}^{sell}>0
```

at the same time.

Likewise:

```math
P_{ch}>0
\quad\text{and}\quad
P_{dis}>0
```

except where particular hardware conditions require otherwise.

These constraints avoid unnecessary circulation of energy.

---

# 18. Hourly actions

The system translates energy flows into readable operating labels.

Examples:

```text
SELF_CONSUMPTION
```

```text
SELF_CONSUMPTION + CHARGE_BATTERY
```

```text
SELF_CONSUMPTION + EXPORT
```

```text
SELF_CONSUMPTION + DISCHARGE_BATTERY
```

```text
IMPORT_GRID
```

```text
SELF_CONSUMPTION + IMPORT_GRID
```

```text
SELF_CONSUMPTION + DISCHARGE_BATTERY + IMPORT_GRID
```

These labels make the calculated dispatch easy to interpret.

The current Python implementation may continue to emit the original Spanish labels; this English documentation translates their meaning without changing the software interface.

---

# 19. Equivalent cycles

The total energy processed by the battery is:

```math
E_{cycled}
=
E_{charge}
+
E_{discharge}
```

The approximate number of equivalent full cycles is:

```math
N_{eq}
=
\frac{
E_{charge}
+
E_{discharge}
}{
2E_{nom}
}
```

This metric is particularly useful when comparing strategies.

A strategy that saves only a few cents per day while doubling the number of battery cycles may be unattractive in the long term.

---

# 20. Daily dispatch metrics

The module computes aggregated quantities such as:

```text
Battery charge
Battery discharge
Cycled energy
Equivalent cycles
Grid import
Grid export
Purchase cost
Export revenue
Net economic balance
Final SOC
Minimum SOC
Maximum SOC
```

These metrics enable different operating policies to be compared.

---

# 21. Economic balance

The purchase cost is:

```math
C_{buy}
=
\sum_h
E_{grid,h}^{buy}
p_{buy,h}
```

Export revenue is:

```math
I_{sell}
=
\sum_h
E_{grid,h}^{sell}
p_{sell,h}
```

The net economic balance is:

```math
C_{net}
=
C_{buy}
-
I_{sell}
```

A negative value represents export revenue greater than the purchase cost.

---

# 22. Purely economic optimization

A purely economic strategy would tend to solve:

```math
\min
\left[
C_{buy}
-
I_{sell}
\right]
```

However, this objective ignores battery degradation.

It may therefore lead to:

- excessive charging;
- excessive discharging;
- frequent daily arbitrage;
- reduced battery lifetime.

---

# 23. Sustainable objective function

A more complete formulation is:

```math
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
```

where:

- $C_{deg}$ penalizes battery degradation;
- $P_{SOC}$ penalizes deviations from the desired SOC range;
- $P_{comfort}$ represents household comfort constraints.

The current algorithm implements this philosophy through predictive rules and target SOC.

---

# 24. Predictive strategy

Dispatch should not treat each hour completely independently.

Suppose a deficit of:

```math
0.4\ \mathrm{kWh}
```

exists at 08:00, but from 09:00 onward:

```math
P_{FV} \gg P_D
```

is expected.

The battery may be partially used because it is expected to recharge shortly afterwards.

Conversely, if a long night with low future generation is approaching, preserving SOC may be preferable.

---

# 25. Time horizon

Dispatch is currently calculated at hourly resolution.

For a horizon:

```math
H=24
```

one may define:

```math
\mathbf{u}
=
[
u_0,u_1,\ldots,u_{23}
]
```

where every $u_h$ contains the decisions:

```math
u_h
=
\{
P_{ch},
P_{dis},
P_{buy},
P_{sell}
\}
```

A future development is to extend the horizon to:

```math
48-96\ \mathrm{h}
```

---

# 26. Relationship with weekly planning

`dispatch.py` answers:

> Where should the energy come from during each hour?

`weekly.py` answers:

> When should each service preferably be operated?

Therefore:

```text
weekly.py
    ↓
modifies future demand
    ↓
dispatch.py
    ↓
decides the energy source
```

At present, these two layers are not yet fully coupled.

Their integration is one of the next development steps.

---

# 27. Interaction with flexible loads

If `weekly.py` moves a washing-machine cycle from:

```text
20:00
```

to:

```text
13:30
```

the demand profile changes:

```math
P_D^{new}(h)
\neq
P_D^{old}(h)
```

Dispatch must therefore be recalculated using the updated profile.

The process can become iterative:

```text
weekly plan
    ↓
new demand profile
    ↓
dispatch
    ↓
new cost
    ↓
evaluation
```

---

# 28. Interaction with HVAC

HVAC operation also modifies dispatch.

If AEMET indicates that air conditioning should operate during:

```math
12{:}00-18{:}00
```

the thermal demand must be added to the electrical load profile during that window.

This can reduce:

- surplus energy;
- exported energy;

while increasing:

- direct self-consumption;
- implicit thermal storage;
- comfort.

---

# 29. Possible precooling

In buildings with significant thermal inertia, it may be convenient to use:

```math
P_{cool}(t)>0
```

during periods of high PV production even before the maximum indoor temperature is reached.

The building then acts as a form of thermal storage.

A future strategy could compare:

```math
\text{charge battery}
```

against:

```math
\text{precool building}
```

---

# 30. Power constraints

In addition to SOC, limits such as the following must be respected:

```math
P_{ch}\leq P_{ch,max}
```

```math
P_{dis}\leq P_{dis,max}
```

```math
P_{grid}^{buy}\leq P_{grid,max}
```

```math
P_{grid}^{sell}\leq P_{export,max}
```

and:

```math
P_{AC}\leq P_{inverter,max}
```

These limits must always correspond to the actual hardware constraints.

---

# 31. Safety

The dispatch algorithm must not replace the physical protections of the system.

Safety limits must remain independently implemented in:

- the inverter;
- the BMS;
- AC protection;
- DC protection;
- the control system.

The optimizer should only issue setpoints within the permitted operating range.

---

# 32. Fallback operation

A future real-control system must define safe operating modes when any of the following fail:

- AEMET;
- ESIOS;
- Internet access;
- inverter communication;
- data acquisition.

For example:

```text
if forecasting fails
    ↓
use a conservative local strategy
```

or:

```text
if communication fails
    ↓
retain a safe inverter configuration
```

---

# 33. Relationship with Model Predictive Control

A future formulation can be expressed as a Model Predictive Control problem.

At every instant $k$:

```math
\mathbf{u}^*
=
\arg\min_{\mathbf{u}}
J
```

subject to:

```math
\mathbf{x}_{k+1}
=
f(
\mathbf{x}_k,
\mathbf{u}_k
)
```

where the state may include:

```math
\mathbf{x}
=
[
SOC,
T_{indoor},
T_{DHW},
\ldots
]
```

and the control variables:

```math
\mathbf{u}
=
[
P_{charge},
P_{discharge},
P_{grid},
P_{HVAC},
\ldots
]
```

---

# 34. Reoptimization

In a real MPC implementation, the entire 24-hour plan would not be executed without modification.

The operating loop would be:

```text
measure
  ↓
forecast
  ↓
optimize
  ↓
execute next action
  ↓
wait
  ↓
measure again
```

The advantage is that forecast errors can be continuously corrected.

---

# 35. Strategy comparison

Experimental validation should compare at least three operating policies.

## Strategy A — conventional

```text
PV -> demand -> battery -> grid
```

without forecasting.

## Strategy B — economic

Minimizes:

```math
C_{buy}-I_{sell}
```

## Strategy C — sustainable predictive

Approximately minimizes:

```math
C_{buy}
-
I_{sell}
+
C_{deg}
```

while also respecting household constraints.

---

# 36. Comparison indicators

The three strategies should be compared using:

```math
C_{net}
```

net economic cost,

```math
N_{eq}
```

equivalent battery cycles,

```math
E_{grid}^{buy}
```

imported energy,

```math
E_{grid}^{sell}
```

exported energy,

```math
R_{self}
```

self-sufficiency,

```math
R_{auto}
```

self-consumption ratio.

---

# 37. Scientific hypothesis

The main hypothesis behind sustainable dispatch can be stated as follows:

> A predictive strategy that explicitly accounts for the cost associated with battery cycling can reduce storage degradation without causing a significant increase in total energy cost.

This hypothesis must be experimentally validated.

---

# 38. Current status

The dispatch module already generates the following information for each hour:

```text
Hour
PV
Demand
SOC
Target SOC
Import
Export
Charge
Discharge
Action
```

and provides daily operating metrics.

The next development steps are:

1. incorporate the weekly plan into the actual demand profile;
2. extend the optimization horizon to several days;
3. use real inverter measurements;
4. calibrate the degradation cost;
5. close the control loop.

---

# 39. Conceptual surplus example

Suppose:

```math
P_{FV}=3.0\ \mathrm{kW}
```

and:

```math
P_D=2.0\ \mathrm{kW}
```

Then:

```math
P_{exc}=1.0\ \mathrm{kW}
```

If:

```math
SOC<SOC^{obj}
```

the system may choose:

```math
P_{ch}=1.0\ \mathrm{kW}
```

and:

```math
P_{sell}=0
```

If the battery is already sufficiently charged:

```math
P_{ch}=0
```

and:

```math
P_{sell}=1.0\ \mathrm{kW}
```

---

# 40. Conceptual deficit example

Suppose:

```math
P_{FV}=0.5\ \mathrm{kW}
```

and:

```math
P_D=1.5\ \mathrm{kW}
```

The deficit is:

```math
P_{def}=1.0\ \mathrm{kW}
```

If the battery has sufficient SOC but the grid purchase price is very low, the system may choose:

```math
P_{dis}=0
```

```math
P_{buy}=1.0\ \mathrm{kW}
```

If the grid price is high and the battery has sufficient reserve:

```math
P_{dis}=1.0\ \mathrm{kW}
```

```math
P_{buy}=0
```

This decision illustrates the difference between predictive dispatch and conventional self-consumption logic.

---

# 41. Final objective

The purpose of `dispatch.py` is to transform:

```math
\boxed{
\text{PV}
+
\text{demand}
+
\text{SOC}
+
\text{prices}
+
\text{future forecast}
}
```

into:

```math
\boxed{
\text{physically feasible hourly actions}
}
```

while simultaneously minimizing:

- energy cost;
- battery degradation;
- unnecessary grid consumption;

without compromising:

- comfort;
- safety;
- energy availability.
