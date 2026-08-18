# Experimental Validation

## Predictive Solar Energy Management — Validation Protocol

[🇪🇸 Spanish version](VALIDATION.md)

---

This document defines the experimental protocol for validating **Predictive Solar Energy Management** using real data from a residential photovoltaic installation.

The objective is to quantitatively assess:

- photovoltaic forecasting accuracy;
- demand-model accuracy;
- predicted SOC evolution;
- energy import and export;
- actual battery behaviour;
- usefulness of weekly planning;
- economic impact of the strategy;
- reduction of electrochemical cycling.

Experimental validation is required to move the project from a simulation and planning platform to a scientifically validated tool.

---

# 1. General objective

The system generates predictions

```math
\hat P_{FV}(t),\qquad
\hat P_D(t),\qquad
\widehat{SOC}(t),\qquad
\hat P_{grid}(t)
```

which must be compared with real measurements

```math
P_{FV}(t),\qquad
P_D(t),\qquad
SOC(t),\qquad
P_{grid}(t).
```

The objective is to quantify:

```math
\text{prediction}
\quad\text{vs.}\quad
\text{experiment}
```

---

# 2. Experimental installation

The residential installation used for validation must be documented in sufficient detail. At minimum:

```text
location
installed PV power
number of modules
module model
tilt
azimuth
inverter model
rated inverter power
battery type
nominal capacity
SOC limits
maximum charging power
maximum discharging power
electricity contract type
surplus-energy compensation scheme
```

Possible conditioning factors should also be recorded:

- shading;
- multiple orientations;
- wiring losses;
- inverter limitations;
- curtailment;
- inverter temperature;
- BMS behaviour.

---

# 3. Experimental variables

Ideally, at each instant $t$:

```math
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
```

Additional variables supplied by the inverter may also be stored.

---

# 4. Meteorological variables

The following should be stored together with the energy data:

```text
timestamp
AEMET temperature
sky conditions
meteorological factor
precipitation
wind
humidity
daily forecast
hourly forecast
```

It is essential to store **the forecast exactly as it was known before the experimental interval**, rather than reconstructing it afterwards. This prevents future information from leaking into the validation.

---

# 5. Economic variables

For each interval:

```math
p_{buy}(t)
```

is the electricity purchase price, and

```math
p_{sell}(t)
```

is the compensation/export price.

The following may also be stored:

```text
SPOT price
PVPC
surplus-energy price
```

---

# 6. Recommended dataset format

A simple CSV structure may be:

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

# 7. Sign convention

A single convention must be fixed and used consistently. For example:

```text
P_grid > 0     -> grid import
P_grid < 0     -> export

P_battery > 0  -> discharge
P_battery < 0  -> charge
```

Any other convention is acceptable provided that it remains unchanged throughout the study.

---

# 8. Acquisition frequency

A resolution of

```math
1-5\ \text{min}
```

is suitable for detailed characterization.

For comparison with the hourly model, data may subsequently be aggregated to

```math
\Delta t=1\ \mathrm{h}.
```

The original acquisition should not be limited directly to one hour if the inverter allows a higher resolution.

---

# 9. Energy from power measurements

For uniformly sampled measurements:

```math
E
=
\sum_i P_i\Delta t
```

If the sampling frequency is not uniform:

```math
E
=
\sum_i
P_i(t_i)
(t_{i+1}-t_i)
```

---

# 10. Validation of photovoltaic production

The first validation compares:

```math
\hat P_{FV}(t)
```

with:

```math
P_{FV}(t).
```

The instantaneous error is:

```math
e_{FV}(t)
=
P_{FV}(t)
-
\hat P_{FV}(t)
```

---

# 11. Mean absolute error

```math
MAE
=
\frac{1}{N}
\sum_{i=1}^{N}
|P_i-\hat P_i|
```

MAE retains the units of power. For example:

```text
MAE = 0.34 kW
```

---

# 12. Root mean square error

```math
RMSE
=
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
(P_i-\hat P_i)^2
}
```

RMSE penalizes large errors more strongly.

---

# 13. Normalized error

To compare days with different production levels:

```math
nRMSE
=
\frac{RMSE}{P_{rated}}
```

Alternatively, normalization may use the observed mean or maximum power. The selected definition must be stated explicitly.

---

# 14. MAPE

Mean absolute percentage error is:

```math
MAPE
=
\frac{100}{N}
\sum_i
\left|
\frac{P_i-\hat P_i}{P_i}
\right|
```

For PV generation this metric is problematic when

```math
P_i\approx0,
```

for example around sunrise or sunset. It should therefore not be used as the only metric.

---

# 15. Daily energy error

A particularly useful metric is:

```math
\epsilon_E
=
\frac{\hat E_{FV}-E_{FV}}{E_{FV}}
```

or, as a percentage:

```math
\epsilon_E[\%]
=
100
\frac{\hat E_{FV}-E_{FV}}{E_{FV}}
```

---

# 16. Bias

Mean bias error can be calculated as:

```math
MBE
=
\frac{1}{N}
\sum_i
(\hat P_i-P_i)
```

This reveals a systematic tendency to overestimate or underestimate.

---

# 17. Validation by weather conditions

PV error should not be analysed only globally. Results should be separated into categories such as:

```text
clear
mostly clear
partly cloudy
cloudy
overcast
rain
```

Prediction may be highly accurate on clear days and poorer under variable conditions.

---

# 18. Validation by forecast horizon

Results should also be separated by forecast horizon:

```math
H=0-24\ \mathrm{h}
```

```math
H=24-48\ \mathrm{h}
```

```math
H>48\ \mathrm{h}
```

This quantifies the value of the multiresolution strategy.

---

# 19. Hourly versus daily AEMET validation

A useful comparison is:

```math
MAE_{hourly}
```

versus:

```math
MAE_{daily}
```

to determine whether hourly information actually improves PV estimation.

---

# 20. Demand-model validation

Predicted demand:

```math
\hat P_D(t)
```

must be compared with actual demand:

```math
P_D(t).
```

Useful metrics include:

```math
MAE_D,\qquad RMSE_D
```

and the energy error:

```math
\epsilon_{E,D}
=
\frac{\hat E_D-E_D}{E_D}
```

---

# 21. Deterministic and stochastic demand

Residential demand contains two components.

## Deterministic

Examples:

- scheduled HVAC;
- electric water heater;
- washing machine;
- base loads.

## Stochastic

Examples:

- actual cooking;
- lighting;
- small appliances;
- behavioural changes.

Validation should separate both types whenever possible.

---

# 22. SOC validation

Compare:

```math
\widehat{SOC}(t)
```

with actual:

```math
SOC(t).
```

The error is:

```math
e_{SOC}(t)
=
SOC(t)-\widehat{SOC}(t)
```

and may be measured using:

```math
MAE_{SOC}
=
\frac{1}{N}
\sum_i
|SOC_i-\widehat{SOC}_i|
```

expressed in percentage points.

---

# 23. Cumulative SOC error

A small error in battery efficiency may produce progressive drift. Therefore:

```math
\Delta SOC(t)
```

should be monitored over several days.

Increasing drift would indicate that charging efficiency, discharging efficiency, or usable capacity requires recalibration.

---

# 24. Battery-power validation

If automatic setpoints are eventually executed, compare:

```math
\hat P_{battery}(t)
```

with:

```math
P_{battery}(t).
```

During the initial phase, the analysis may instead compare what the algorithm would have done with the observed real operation.

---

# 25. Shadow mode

Before physically controlling the inverter, the algorithm should operate in **shadow mode**:

```text
the algorithm calculates
what it would have done
```

but:

```text
does not modify the inverter
```

Store simultaneously:

```text
proposed action
actual action
actual result
```

This validates the controller without operational risk.

---

# 26. Comparison strategies

Scientific validation should compare at least three strategies.

## Strategy A — reference

Conventional operation:

```text
PV
↓
consumption
↓
battery
↓
grid
```

without forecasting.

## Strategy B — economic optimization

```math
\min(C_{buy}-I_{sell})
```

## Strategy C — sustainable predictive

Approximate objective:

```math
\min
(
C_{buy}
-
I_{sell}
+
C_{deg}
)
```

with additional comfort and flexibility criteria.

---

# 27. Fair comparison

Strategies must be evaluated using the same:

- days;
- weather;
- demand;
- prices;
- initial SOC.

Otherwise, the comparison would be biased.

---

# 28. Experimental replay

A powerful methodology is to record real data first and subsequently run different strategies over the same day:

```text
real day
   ↓
same PV / prices / demand
   ↓
strategy A
strategy B
strategy C
```

This permits comparison without physically repeating the day.

---

# 29. Daily energy cost

For each strategy:

```math
C_{day}
=
\sum_h E_{buy,h}p_{buy,h}
-
\sum_h E_{sell,h}p_{sell,h}
```

---

# 30. Savings relative to the reference

```math
Saving
=
C_{reference}
-
C_{strategy}
```

and:

```math
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
```

---

# 31. Imported energy

```math
E_{import}
=
\sum_h E_{grid,h}^{buy}
```

---

# 32. Exported energy

```math
E_{export}
=
\sum_h E_{grid,h}^{sell}
```

---

# 33. Self-consumption

```math
R_{auto}
=
\frac{E_{FV,used}}{E_{FV,total}}
```

---

# 34. Self-sufficiency

```math
R_{self}
=
\frac{E_{load}-E_{grid}^{buy}}{E_{load}}
```

---

# 35. Equivalent cycles

```math
N_{eq}
=
\frac{
E_{charge}+E_{discharge}
}{
2E_{nom}
}
```

This is one of the principal metrics of the study.

---

# 36. Cycling reduction

Relative to the reference strategy:

```math
\Delta N_{eq}
=
N_{eq}^{ref}
-
N_{eq}^{strategy}
```

and, as a percentage:

```math
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
```

---

# 37. Economic value per avoided cycle

An informative metric is:

```math
V_{cycle}
=
\frac{\Delta C}{\Delta N_{eq}}
```

This quantifies the economic cost exchanged for reduced battery wear.

---

# 38. Weekly-planning validation

For each recommendation, record:

```text
service
recommended time
actual time
predicted energy
actual energy
```

---

# 39. Recommendation acceptance

Define:

```math
R_{accept}
=
\frac{N_{accepted}}{N_{recommended}}
```

This measures how compatible the plan is with the user's real-life requirements.

---

# 40. Shifted energy

```math
E_{shift}
=
\sum_i E_i^{shifted}
```

The fraction of available flexibility used is:

```math
R_{shift}
=
\frac{E_{shift}}{E_{flex,total}}
```

---

# 41. Self-consumption gain from flexibility

```math
\Delta E_{auto}
=
E_{auto}^{flex}
-
E_{auto}^{base}
```

---

# 42. Battery savings from flexibility

If a load is shifted from night-time to a solar-production period, a battery discharge may be avoided:

```math
\Delta E_{battery}
=
E_{battery}^{base}
-
E_{battery}^{flex}
```

---

# 43. Thermal validation

For HVAC, record:

```text
forecast outdoor temperature
actual outdoor temperature
indoor temperature
HVAC state
HVAC power
```

---

# 44. Indoor temperature

When available:

```math
T_{in}(t)
```

allows evaluation of whether recommendations maintain comfort.

---

# 45. Thermal error

```math
e_T(t)
=
T_{set}
-
T_{in}(t)
```

---

# 46. Hours outside the comfort range

```math
H_{discomfort}
=
\sum_t
\mathbf{1}
\left(
|T_{in}(t)-T_{set}|>\Delta T
\right)
\Delta t
```

---

# 47. Thermal cost

Measure:

```math
E_{HVAC}
```

consumed by HVAC during the day.

The strategy should compare:

```text
HVAC energy
vs.
comfort
vs.
self-consumption
```

---

# 48. Domestic hot-water validation

At an advanced stage, record:

```math
T_{DHW}(t)
```

together with:

- electric water-heater activation;
- electrical energy used;
- available solar-thermal energy.

---

# 49. DHW electricity savings

```math
E_{DHW,saved}
=
E_{DHW,reference}
-
E_{DHW,solar}
```

---

# 50. Missing data

Real datasets will probably contain:

- connection losses;
- restarts;
- null values;
- impossible values.

These data must be explicitly flagged and must never be silently filled.

---

# 51. Quality flags

Each record may include:

```text
quality_ok
missing
interpolated
outlier
communication_error
```

---

# 52. Outliers

Extreme values should be detected but not automatically removed.

For example:

```math
P_{FV}>P_{physical,max}
```

may indicate:

- reading error;
- incorrect scale;
- incorrect units.

---

# 53. Time synchronization

All data must share:

```text
timezone
timestamp
interval
```

Preferably:

```text
Europe/Madrid
```

or internal UTC storage with explicit conversion.

---

# 54. Daylight-saving time

Summer/winter time changes require careful treatment. Some days contain:

```math
23\ \mathrm{h}
```

and others:

```math
25\ \mathrm{h}.
```

A day must not always be assumed to contain exactly 24 hourly records.

---

# 55. Temporal integrity

Verify:

```math
t_{i+1}>t_i
```

and detect gaps:

```math
t_{i+1}-t_i
>
\Delta t_{expected}
```

---

# 56. Raw and processed datasets

Maintain two levels:

```text
data/raw/
```

for unmodified original data, and:

```text
data/processed/
```

for synchronized, aggregated, validated, analysis-ready data.

The raw dataset must never be overwritten.

---

# 57. Recommended structure

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

# 58. Suggested daily file

For example:

```text
2026-08-09.csv
```

with:

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

# 59. Metadata

`installation.json` may store:

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

# 60. Reproducibility

Each experiment should also store:

```text
code version
Git commit
execution date
configuration
strategy
parameters
```

---

# 61. Version identification

It is advisable to store:

```text
git_commit
```

with every simulation so that the exact algorithm used can be reproduced.

---

# 62. Forecast freezing

Whenever an AEMET forecast is obtained, it should be stored immediately, including:

```text
forecast_generated_at
forecast_target_time
```

This allows error to be studied as a function of forecast horizon.

---

# 63. Forecast lead time

Define:

```math
L
=
t_{target}
-
t_{forecast}
```

and analyse error as:

```math
MAE(L)
```

---

# 64. Seasonal validation

The dataset should cover:

```text
summer
autumn
winter
spring
```

because irradiance, temperature, HVAC demand, total demand and PV performance change significantly.

---

# 65. Minimum experimental duration

A first publication may use several weeks, but robust validation should span several months.

Ideally:

```math
T_{exp}\geq1\ \text{year}
```

to cover full seasonality.

---

# 66. First publishable study

An initial phase may use:

```math
30-60\ \text{days}
```

provided it includes sufficient meteorological variability.

This would allow validation of PV production, dispatch, battery behaviour, prices and planning.

---

# 67. Calibration–validation separation

The same data must not be used for calibration and validation.

For example:

```text
60 % calibration
20 % validation
20 % test
```

or an equivalent temporal split.

---

# 68. Calibration

Parameters that may be adjusted include:

- meteorological factor;
- PV losses;
- effective thermal coefficient;
- battery efficiency;
- usable capacity;
- thermal thresholds;
- base load.

---

# 69. Independent test

The final test set must not be used during model fitting.

Only at the end should the following be calculated:

```math
MAE_{test}
```

```math
RMSE_{test}
```

```math
Savings_{test}
```

---

# 70. Comparison with a PV baseline

In addition to the complete model, a simple reference should exist. For example:

```math
P_{FV}^{baseline}
=
P_{PVGIS}
```

without meteorological correction.

Then compare:

```math
RMSE_{PVGIS}
```

with:

```math
RMSE_{AEMET+PVGIS}
```

---

# 71. Skill score

Define:

```math
Skill
=
1
-
\frac{RMSE_{model}}{RMSE_{baseline}}
```

If:

```math
Skill>0
```

the new model improves upon the baseline.

---

# 72. Control baseline

A battery-control baseline should also be defined, for example:

```text
charge with any surplus
discharge for any deficit
```

---

# 73. Value of predictive control

Improvement can be measured through:

```math
\Delta C,\qquad
\Delta N_{eq},\qquad
\Delta E_{grid}
```

relative to the baseline.

---

# 74. Statistical significance

When sufficient experimental days are available, comparisons should include:

- mean;
- standard deviation;
- median;
- percentiles;
- confidence intervals.

---

# 75. Paired daily comparison

Because strategies can be run on the same day through replay:

```math
\Delta C_d
=
C_{A,d}
-
C_{B,d}
```

can be calculated day by day, reducing the influence of weather variability.

---

# 76. Distribution of results

Do not report only:

```text
mean savings
```

Also report, for example:

```text
P10
P50
P90
```

or boxplots.

---

# 77. Extreme cases

Specific cases should include:

- completely clear day;
- very cloudy day;
- heat wave;
- low-production day;
- low battery SOC;
- nearly full battery;
- negative prices;
- high prices.

---

# 78. Robustness to weather-forecast error

Sensitivity can be studied by perturbing:

```math
G(t)
```

and:

```math
T(t).
```

---

# 79. Sensitivity

For example:

```math
G'=G(1+\delta_G)
```

with:

```math
\delta_G
=
\pm5\%,
\pm10\%,
\pm20\%
```

and observe:

```math
\Delta C
```

and:

```math
\Delta SOC.
```

---

# 80. Sensitivity to degradation cost

Vary:

```math
c_{deg}
```

and observe how:

```math
N_{eq}
```

and:

```math
C_{net}
```

change.

---

# 81. Pareto curve

A relationship can be obtained between:

```math
\text{economic cost}
```

and:

```math
\text{battery cycling}
```

to produce a Pareto frontier. This is particularly relevant scientifically.

---

# 82. Combined indicator

A combined metric may be defined as:

```math
J^\*
=
C_{net}
+
\lambda N_{eq}
```

for different values of:

```math
\lambda.
```

---

# 83. Validation in shadow mode

The first phase of real operation should be:

```text
WEEK 1-N
--------
read inverter
read battery
read grid
read AEMET
read ESIOS
calculate plan
DO NOT send commands
```

This validates the logic without risk.

---

# 84. Second phase

Afterwards, use:

```text
partial control
```

for example only:

- user notifications;
- scheduling of non-critical loads.

---

# 85. Third phase

Only after sufficient validation:

```text
inverter control
```

with independent safety limits.

---

# 86. Safety indicators

Record:

```text
number of rejected setpoints
communication errors
SOC outside target
inverter alarms
BMS alarms
```

---

# 87. Success criterion

The sustainable strategy may be considered better if:

```math
C_{strategy}
\leq
C_{reference}
+
\epsilon
```

and simultaneously:

```math
N_{eq,strategy}
<
N_{eq,reference}
```

with small:

```math
\epsilon.
```

That is, cycling is significantly reduced without a relevant economic penalty.

---

# 88. Hypothesis H1

```math
H_1:
```

Incorporating hourly weather forecasts reduces PV-production error relative to a climatological model without forecasting.

---

# 89. Hypothesis H2

```math
H_2:
```

Flexible-load scheduling increases direct self-consumption.

---

# 90. Hypothesis H3

```math
H_3:
```

The sustainable predictive strategy reduces equivalent battery cycles relative to a conventional self-consumption strategy.

---

# 91. Hypothesis H4

```math
H_4:
```

Cycling reduction can be achieved without significantly increasing total energy cost.

---

# 92. Hypothesis H5

```math
H_5:
```

The combination of thermal planning and PV production reduces energy extracted from the battery during HVAC periods.

---

# 93. Recommended figures for publication

A publication should include at least:

```text
Figure 1
System architecture

Figure 2
PV prediction vs. measurement

Figure 3
Predicted SOC vs. actual SOC

Figure 4
PV / demand / battery / grid over 24 h

Figure 5
Economic comparison of strategies

Figure 6
Equivalent cycles

Figure 7
PV error by forecast horizon

Figure 8
Cost vs. degradation Pareto frontier
```

---

# 94. Recommended tables

```text
Table 1
Installation characteristics

Table 2
Model parameters

Table 3
Prediction errors

Table 4
Strategy comparison

Table 5
Seasonal results
```

---

# 95. Example results table

| Strategy | Cost €/day | Import kWh | Export kWh | Eq. cycles | Self-consumption |
|---|---:|---:|---:|---:|---:|
| Conventional | — | — | — | — | — |
| Economic | — | — | — | — | — |
| Sustainable predictive | — | — | — | — | — |

Values must be obtained experimentally.

---

# 96. Dataset publication

If privacy permits, an anonymized version of the dataset should preferably be published.

It should not include:

- credentials;
- private identifiers;
- IP addresses;
- personal data;
- sensitive household information.

---

# 97. Public reproducibility

Ideally, the scientific article should provide:

```text
GitHub
+
dataset
+
experimental configuration
+
analysis scripts
```

allowing the results to be reproduced.

---

# 98. Execution log

Each simulation may produce a file:

```text
run_YYYYMMDD_HHMMSS.json
```

containing:

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

# 99. PV-model validation criterion

An arbitrary acceptance threshold should not yet be imposed.

First, real performance must be measured. Then an acceptable error can be defined from:

- the literature;
- baselines;
- system uncertainty.

---

# 100. Final validation objective

Validation seeks to answer experimentally:

```math
\boxed{
\text{Does predictive energy management actually provide value?}
}
```

That value must be demonstrated in terms of:

```math
\boxed{
\text{prediction}
+
\text{cost}
+
\text{self-consumption}
+
\text{battery cycles}
+
\text{comfort}
}
```

and not only through theoretical simulation.

---

# 101. Expected result

At the end of validation, real data should make it possible to state:

```text
how accurate the PV forecast is
```

```text
how much self-consumption increases
```

```text
how much grid purchasing is reduced
```

```text
how many battery cycles are avoided
```

```text
how much economic saving is achieved
```

```text
what impact the strategy has on comfort
```

and:

```text
whether the sustainable predictive strategy
outperforms the reference strategies
```

These results will constitute the experimental basis for a future scientific publication.
