# Installation and Configuration

## Predictive Solar Energy Management — Setup Guide

[🇪🇸 Versión en español](INSTALLATION.md)

---

This document explains how to prepare the execution environment for **Predictive Solar Energy Management**, install its dependencies, and configure access to the external services used by the project.

The system currently uses:

- **AEMET OpenData** for weather forecasting;
- **PVGIS** for solar and climatological reference data;
- **ESIOS** for economic information from the Spanish electricity system;
- optionally, **Home Assistant** as a future integration, visualization, and control layer.

---

# 1. Requirements

The recommended environment includes:

```text
Python 3
pip
Internet connection
email account to request an AEMET API key
ESIOS token if required by the endpoints being used
```

Check Python:

```bash
python3 --version
```

Check `pip`:

```bash
python3 -m pip --version
```

---

# 2. Get the Source Code

Clone the repository:

```bash
git clone https://github.com/maxwellfree/Gestion-Solar-AEMET-ESIOS.git
```

Enter the project directory:

```bash
cd Gestion-Solar-AEMET-ESIOS
```

---

# 3. Recommended Virtual Environment

It is recommended to create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on Linux:

```bash
source .venv/bin/activate
```

On Windows:

```text
.venv\Scripts\activate
```

---

# 4. Install Dependencies

Install the dependencies defined in:

```text
requirements.txt
```

using:

```bash
python3 -m pip install -r requirements.txt
```

The main external dependencies currently are:

```text
requests
python-dotenv
```

---

# 5. External Services

The program depends on several external data sources.

Each one has a different role:

```text
AEMET  → weather forecasts
PVGIS  → physical and climatological solar reference
ESIOS  → prices and economic information
```

Personal credentials must never be included in the GitHub repository.

---

# 6. AEMET OpenData

## 6.1 Role in the Project

AEMET provides the weather information used by:

```text
aemet.py
aemet_hourly.py
solar.py
weekly.py
```

The project uses information such as:

- temperature;
- minimum and maximum temperature;
- sky conditions;
- precipitation;
- daily forecasts;
- hourly forecasts;
- variables used to construct the meteorological correction factor.

AEMET OpenData provides specific endpoints for daily and hourly municipal forecasts.

## 6.2 Official Website

Portal:

```text
https://opendata.aemet.es/
```

Service information:

```text
https://opendata.aemet.es/centrodedescargas/info
```

Developer documentation:

```text
https://opendata.aemet.es/centrodedescargas/AEMETApi
```

Swagger / API:

```text
https://opendata.aemet.es/dist/
```

## 6.3 Obtain an API Key

AEMET OpenData requires an **API key**.

It can be requested from:

```text
https://opendata.aemet.es/centrodedescargas/altaUsuario
```

The procedure consists of entering an email address and following the instructions provided by AEMET.

AEMET allows more than one API key to be requested for the same email address.

## 6.4 Local Configuration

The key should not be written directly into files published in the repository.

One option is to use:

```text
mytoken.env
```

with:

```text
AEMET_API_KEY=YOUR_AEMET_KEY
```

An environment variable can also be used:

```bash
export AEMET_API_KEY="YOUR_AEMET_KEY"
```

From Python:

```python
import os

AEMET_API_KEY = os.getenv("AEMET_API_KEY")
```

If the specific version of `aemet.py` uses a different variable name, keep the name expected by that module.

## 6.5 Conceptually Used Endpoints

AEMET provides, among others:

```text
/api/prediccion/especifica/municipio/diaria/{municipio}

/api/prediccion/especifica/municipio/horaria/{municipio}
```

The project uses both time resolutions:

```text
near-term horizon → hourly forecast
rest of the week  → daily forecast
```

---

# 7. Temporary AEMET Rate Limits

AEMET may temporarily limit the number of requests.

For example:

```text
HTTP 429
```

The code may implement:

```text
retry
+
incremental backoff
+
reuse of already downloaded data
```

Different modules should avoid independently performing the same request.

The recommended architecture is:

```text
main.py
   ↓
query AEMET once
   ↓
reuse the response
   ├── solar.py
   └── weekly.py
```

---

# 8. PVGIS

## 8.1 Role in the Project

PVGIS provides the physical and climatological reference used by `solar.py`.

The project combines:

```text
PVGIS
  +
AEMET
  ↓
PV prediction
```

Conceptually:

```math
G_{\mathrm{pred}}(t)
=
G_{\mathrm{PVGIS}}(t)
F_{\mathrm{met}}(t)
```

## 8.2 Official Website

Web tool:

```text
https://re.jrc.ec.europa.eu/pvg_tools/en/
```

API:

```text
https://re.jrc.ec.europa.eu/api/
```

PVGIS is maintained by the **Joint Research Centre of the European Commission**.

## 8.3 Credentials

For the usual public PVGIS requests used by this project, no personal password needs to be stored.

Therefore, normally:

```text
PVGIS → no token
```

## 8.4 Cache

It is recommended to locally store responses that do not need to be requested repeatedly.

The project may use cache files such as:

```text
.solar_pvgis_cache.json
.solar_location_cache.json
```

These files reduce:

- unnecessary requests;
- execution time;
- temporary dependence on the remote service.

---

# 9. ESIOS

## 9.1 Role in the Project

`esios.py` obtains information used to build:

- hourly electricity purchase prices;
- sale or surplus-compensation prices;
- economic information from the electricity market.

This information is later combined with:

```text
PV
+
demand
+
battery
```

to generate the hourly dispatch.

## 9.2 Official Website

ESIOS portal:

```text
https://www.esios.ree.es/
```

API documentation:

```text
https://api.esios.ree.es/
```

## 9.3 Token

The official ESIOS API documentation includes a procedure for requesting a **personal token**.

The token must remain outside the repository.

For example:

```text
ESIOS_API_KEY=YOUR_ESIOS_TOKEN
```

inside:

```text
mytoken.env
```

or by using:

```bash
export ESIOS_API_KEY="YOUR_ESIOS_TOKEN"
```

From Python:

```python
import os

ESIOS_API_KEY = os.getenv("ESIOS_API_KEY")
```

If `esios.py` currently uses another variable name, keep the one expected by the code.

---

# 10. Local Credentials File

One possible configuration is:

```text
mytoken.env
```

containing:

```text
AEMET_API_KEY=YOUR_AEMET_KEY
ESIOS_API_KEY=YOUR_ESIOS_TOKEN
```

This file must not be uploaded to GitHub.

The `.gitignore` file should include:

```gitignore
mytoken.env
.env
*.env
__pycache__/
*.pyc
```

---

# 11. Check That Secrets Are Not Published

Before creating a commit:

```bash
git status
```

Search for possible secrets:

```bash
grep -RniE \
    'api[_-]?key|token|password|passwd|secret|authorization' \
    . \
    --exclude-dir=.git
```

If a real key has ever been published in Git, deleting it from the current file is not sufficient.

It must be:

```text
revoked
or
regenerated
```

---

# 12. Installation Configuration

The physical installation is defined in:

```text
config.py
```

At minimum, review:

```text
municipality
province
latitude / longitude
number of PV modules
installed PV power
tilt
azimuth
inverter power
battery model
nominal battery capacity
minimum SOC
maximum SOC
```

Conceptual example:

```python
"localizacion": {
    "municipio": "Maracena",
    "provincia": "Granada",
}
```

The municipality is used to resolve meteorological queries.

The names of configuration keys are intentionally kept as they appear in the current Python implementation.

---

# 13. Demand Configuration

Household behaviour is mainly defined in:

```text
demand.py
```

It may include:

- occupants;
- base consumption;
- flexible loads;
- automatable loads;
- thermal loads;
- presence;
- weekly frequency;
- allowed time windows;
- domestic hot water;
- irrigation;
- solar cooking.

This configuration should be adapted to each household before interpreting the results as representative.

---

# 14. First Test

Once the credentials and installation have been configured:

```bash
python3 main.py --soc 0.60
```

A more complete execution:

```bash
python3 main.py \
    --soc 0.60 \
    --mostrar-semanal \
    --mostrar-precios \
    --mostrar-solar \
    --mostrar-balance \
    --mostrar-plan-horario
```

The command-line option names are kept in Spanish because they are part of the current software interface.

---

# 15. Independent Weekly-Planning Test

```bash
python3 weekly.py
```

The output should show information such as:

```text
weekly plan
solar quality
confidence
shiftable tasks
thermal management
DHW
irrigation
solar cooking
```

The current application may display these labels in Spanish.

---

# 16. AEMET Check

The AEMET API key can first be tested using the project modules.

Conceptual example:

```python
from config import obtener_configuracion_sistema
from aemet import obtener_prevision_solar

config = obtener_configuracion_sistema()

municipio = config["localizacion"]["municipio"]

datos = obtener_prevision_solar(municipio)

print(datos)
```

Function names and dictionary keys are preserved exactly as implemented in the Python source code.

---

# 17. Hourly AEMET Check

Example:

```python
from config import obtener_configuracion_sistema
from aemet_hourly import obtener_prevision_horaria

config = obtener_configuracion_sistema()

municipio = config["localizacion"]["municipio"]

datos = obtener_prevision_horaria(municipio)

print(datos)
```

---

# 18. PV-Model Check

A typical solar-model test can use:

```python
from datetime import datetime

from config import obtener_configuracion_sistema
from aemet import obtener_prevision_solar
from aemet_hourly import obtener_prevision_horaria
from solar import obtener_perfil_fv_24h, mostrar_perfil_fv

config = obtener_configuracion_sistema()

municipio = config["localizacion"]["municipio"]

fecha = datetime.now().date()

diaria = obtener_prevision_solar(municipio)

prevision_dia = next(
    d for d in diaria
    if d["fecha"] == fecha
)

horaria = obtener_prevision_horaria(municipio)

perfil = obtener_perfil_fv_24h(
    fecha=fecha,
    configuracion=config,
    prevision_horaria=horaria,
    prevision_diaria=prevision_dia,
)

mostrar_perfil_fv(perfil)
```

---

# 19. Home Assistant — Optional Integration

Home Assistant is not required to run the current predictive model.

It may be used at a later stage as:

- user interface;
- dashboard;
- notification system;
- real-data acquisition layer;
- load-automation platform;
- future inverter-control layer.

## 19.1 Official Website

```text
https://www.home-assistant.io/
```

Installation:

```text
https://www.home-assistant.io/installation/
```

Home Assistant OS is suitable for a dedicated domestic Home Assistant installation.

Home Assistant Container may also be used on Linux systems managed by the user.

The specific installation method should be selected according to the host system and the current Home Assistant documentation.

## 19.2 Planned Architecture

```text
AEMET + PVGIS + ESIOS
          │
          ▼
Predictive Solar Energy Management
          │
          ▼
    Home Assistant
      ┌───┼────┐
      ▼   ▼    ▼
 sensors app automations
              │
              ▼
         inverter / loads
```

The scientific core should remain separated from Home Assistant.

---

# 20. Deye and Home Assistant

Future inverter integration should be implemented as an independent layer.

Conceptually:

```text
Deye
  │
  ▼
Modbus / local integration
  │
  ▼
Home Assistant
  │
  ▼
real measurements
  │
  ▼
Predictive Solar Energy Management
```

During an initial phase, Home Assistant should preferably be used only for:

```text
reading
visualization
logging
notifications
```

Before allowing:

```text
register writes
SOC changes
operating-mode changes
charge commands
discharge commands
```

the system should undergo experimental validation and include an independent safety layer.

---

# 21. Recommended Experimental Progression

The recommended evolution is:

```text
PHASE 1
simulation

PHASE 2
real data without control

PHASE 3
shadow mode
the algorithm calculates decisions but does not execute them

PHASE 4
automation of non-critical loads

PHASE 5
limited inverter control

PHASE 6
closed-loop predictive control
```

---

# 22. Common Problems

## `ModuleNotFoundError`

Run:

```bash
python3 -m pip install -r requirements.txt
```

and verify that the correct virtual environment is active.

## AEMET API-Key Error

Check:

```bash
echo "$AEMET_API_KEY"
```

or inspect:

```text
mytoken.env
```

without exposing its contents publicly.

## AEMET Rate Limits Requests

Wait and try again.

Avoid launching multiple identical queries from different modules.

## ESIOS Returns No Data

Check:

- token;
- endpoint;
- requested dates;
- header format;
- availability of the indicator being used.

## Incorrect Municipality

Check:

```text
config.py
```

and the resolution of the municipal identifier used by AEMET.

## Unusual PV Prediction

Review:

- location;
- tilt;
- azimuth;
- installed power;
- inverter maximum power;
- meteorological source;
- PVGIS cache.

---

# 23. Reproducibility

For every experiment, preserve:

```text
code version
Git commit
configuration
date
initial SOC
forecast used
prices used
strategy
result
```

This makes it possible to reconstruct the exact conditions under which the algorithm made a decision.

---

# 24. Related Documentation

The project documentation is divided into:

```text
docs/
├── INSTALLATION.md
├── INSTALLATIONen.md
├── MODEL.md
├── DISPATCH.md
├── WEEKLY.md
├── VALIDATION.md
└── ARCHITECTURE.md
```

Spanish documents currently use their original filenames.

English companion documents may use the `en` suffix, for example:

```text
ARCHITECTUREen.md
DISPATCHen.md
INSTALLATIONen.md
```

The documentation set covers:

- `INSTALLATION.md`: installation, APIs, credentials, and setup;
- `MODEL.md`: physical and energy model;
- `DISPATCH.md`: battery, grid, and dispatch;
- `WEEKLY.md`: weekly planning;
- `VALIDATION.md`: experimental protocol;
- `ARCHITECTURE.md`: software organization and future development.

---

# 25. Safety

This project is experimental.

API keys and tokens must be treated as secrets.

Any future integration with a real inverter must not replace:

- electrical protections;
- the BMS;
- internal inverter limits;
- AC/DC protections;
- manufacturer safety mechanisms.

Optimizer decisions must always remain within the physical and operational limits of the system.
