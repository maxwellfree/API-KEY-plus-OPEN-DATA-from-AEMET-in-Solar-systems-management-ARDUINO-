# Instalación y configuración

## Gestión Solar Predictiva — Guía de puesta en marcha

Este documento explica cómo preparar el entorno de ejecución de **Gestión Solar Predictiva**, instalar sus dependencias y configurar el acceso a los servicios externos utilizados por el proyecto.

El sistema utiliza actualmente:

- **AEMET OpenData** para predicción meteorológica;
- **PVGIS** para la referencia solar y climatológica;
- **ESIOS** para información económica del sistema eléctrico;
- opcionalmente, **Home Assistant** como futura capa de integración, visualización y control.

---

# 1. Requisitos

Se recomienda utilizar:

```text
Python 3
pip
conexión a Internet
cuenta de correo para solicitar la API key de AEMET
token de ESIOS si los endpoints utilizados lo requieren
```

Comprobar Python:

```bash
python3 --version
```

Comprobar `pip`:

```bash
python3 -m pip --version
```

---

# 2. Obtener el código

Clonar el repositorio:

```bash
git clone https://github.com/maxwellfree/Gestion-Solar-AEMET-ESIOS.git
```

Entrar en la carpeta:

```bash
cd Gestion-Solar-AEMET-ESIOS
```

---

# 3. Entorno virtual recomendado

Es recomendable crear un entorno virtual:

```bash
python3 -m venv .venv
```

Activarlo en Linux:

```bash
source .venv/bin/activate
```

En Windows:

```text
.venv\Scripts\activate
```

---

# 4. Instalar dependencias

Instalar las dependencias definidas en:

```text
requirements.txt
```

mediante:

```bash
python3 -m pip install -r requirements.txt
```

Las dependencias externas principales son actualmente:

```text
requests
python-dotenv
```

---

# 5. Servicios externos

El programa depende de varias fuentes externas.

Cada una cumple una función diferente:

```text
AEMET  → meteorología prevista
PVGIS  → referencia física y climatológica solar
ESIOS  → precios e información económica
```

Las credenciales personales nunca deben incluirse en GitHub.

---

# 6. AEMET OpenData

## 6.1 Función en el proyecto

AEMET proporciona la información meteorológica utilizada por:

```text
aemet.py
aemet_hourly.py
solar.py
weekly.py
```

El proyecto utiliza información como:

- temperatura;
- temperatura máxima y mínima;
- estado del cielo;
- precipitación;
- predicción diaria;
- predicción horaria;
- variables empleadas para construir el factor meteorológico.

AEMET OpenData dispone de endpoints específicos para predicción municipal diaria y horaria.

## 6.2 Web oficial

Portal:

```text
https://opendata.aemet.es/
```

Información del servicio:

```text
https://opendata.aemet.es/centrodedescargas/info
```

Documentación para desarrolladores:

```text
https://opendata.aemet.es/centrodedescargas/AEMETApi
```

Swagger / API:

```text
https://opendata.aemet.es/dist/
```

## 6.3 Obtener una API key

AEMET OpenData requiere una **API key**.

Puede solicitarse desde:

```text
https://opendata.aemet.es/centrodedescargas/altaUsuario
```

El procedimiento consiste en introducir una dirección de correo electrónico y seguir las instrucciones de AEMET.

AEMET permite solicitar más de una API key asociada a una misma dirección de correo.

## 6.4 Configuración local

La clave no debe escribirse directamente en los archivos publicados.

Una opción es usar:

```text
mytoken.env
```

con:

```text
AEMET_API_KEY=TU_CLAVE_AEMET
```

También puede utilizarse una variable de entorno:

```bash
export AEMET_API_KEY="TU_CLAVE_AEMET"
```

Desde Python:

```python
import os

AEMET_API_KEY = os.getenv("AEMET_API_KEY")
```

Si la versión concreta de `aemet.py` utiliza otro nombre de variable, debe conservarse el nombre esperado por ese módulo.

## 6.5 Endpoints utilizados conceptualmente

AEMET ofrece, entre otros:

```text
/api/prediccion/especifica/municipio/diaria/{municipio}

/api/prediccion/especifica/municipio/horaria/{municipio}
```

El proyecto utiliza ambas resoluciones:

```text
horizonte próximo → predicción horaria
resto de semana   → predicción diaria
```

---

# 7. Límites temporales de AEMET

AEMET puede responder temporalmente con limitación de peticiones.

Por ejemplo:

```text
HTTP 429
```

El código puede implementar:

```text
retry
+
espera incremental
+
reutilización de datos ya descargados
```

Debe evitarse que distintos módulos realicen de forma independiente la misma consulta.

La arquitectura recomendada es:

```text
main.py
   ↓
consulta AEMET una vez
   ↓
reutiliza la respuesta
   ├── solar.py
   └── weekly.py
```

---

# 8. PVGIS

## 8.1 Función en el proyecto

PVGIS proporciona la referencia física y climatológica utilizada por `solar.py`.

El proyecto combina:

```text
PVGIS
  +
AEMET
  ↓
predicción FV
```

Conceptualmente:

```math
G_{\mathrm{pred}}(t)
=
G_{\mathrm{PVGIS}}(t)
F_{\mathrm{met}}(t)
```

## 8.2 Web oficial

Herramienta web:

```text
https://re.jrc.ec.europa.eu/pvg_tools/en/
```

API:

```text
https://re.jrc.ec.europa.eu/api/
```

PVGIS es mantenido por el **Joint Research Centre de la Comisión Europea**.

## 8.3 Credenciales

Para las consultas públicas habituales de PVGIS utilizadas por este proyecto no es necesario almacenar una contraseña personal.

Por ello, normalmente:

```text
PVGIS → sin token
```

## 8.4 Caché

Es recomendable almacenar localmente respuestas que no necesitan solicitarse repetidamente.

El proyecto puede utilizar archivos de caché, por ejemplo:

```text
.solar_pvgis_cache.json
.solar_location_cache.json
```

Estos archivos reducen:

- llamadas innecesarias;
- tiempo de ejecución;
- dependencia temporal del servicio.

---

# 9. ESIOS

## 9.1 Función en el proyecto

`esios.py` obtiene información utilizada para construir:

- precios horarios de compra;
- precios de venta o compensación;
- información económica del mercado eléctrico.

Esta información se cruza posteriormente con:

```text
FV
+
demanda
+
batería
```

para generar el despacho horario.

## 9.2 Web oficial

Portal ESIOS:

```text
https://www.esios.ree.es/
```

Documentación de la API:

```text
https://api.esios.ree.es/
```

## 9.3 Token

La documentación oficial de la API ESIOS incluye un procedimiento de solicitud de **token personal**.

El token debe mantenerse fuera del repositorio.

Por ejemplo:

```text
ESIOS_API_KEY=TU_TOKEN_ESIOS
```

en:

```text
mytoken.env
```

o mediante:

```bash
export ESIOS_API_KEY="TU_TOKEN_ESIOS"
```

Desde Python:

```python
import os

ESIOS_API_KEY = os.getenv("ESIOS_API_KEY")
```

Si `esios.py` utiliza actualmente otro nombre para la variable, debe conservarse el esperado por el código.

---

# 10. Archivo local de credenciales

Una configuración posible es:

```text
mytoken.env
```

con:

```text
AEMET_API_KEY=TU_CLAVE_AEMET
ESIOS_API_KEY=TU_TOKEN_ESIOS
```

No debe subirse a GitHub.

El `.gitignore` debería incluir:

```gitignore
mytoken.env
.env
*.env
__pycache__/
*.pyc
```

---

# 11. Comprobar que no se publican secretos

Antes de hacer un commit:

```bash
git status
```

Buscar posibles secretos:

```bash
grep -RniE \
    'api[_-]?key|token|password|passwd|secret|authorization' \
    . \
    --exclude-dir=.git
```

Si una clave real se ha publicado alguna vez en Git, no basta con borrarla del archivo actual.

Debe:

```text
revocarse
o
regenerarse
```

---

# 12. Configuración de la instalación

La instalación física se define en:

```text
config.py
```

Debe revisarse al menos:

```text
municipio
provincia
latitud / longitud
número de paneles
potencia FV instalada
inclinación
azimut
potencia del inversor
modelo de batería
capacidad nominal
SOC mínimo
SOC máximo
```

Ejemplo conceptual:

```python
"localizacion": {
    "municipio": "Maracena",
    "provincia": "Granada",
}
```

El municipio se utiliza para resolver las consultas meteorológicas.

---

# 13. Configuración de demanda

El comportamiento doméstico se define principalmente en:

```text
demand.py
```

Puede incluir:

- ocupantes;
- potencia base;
- cargas flexibles;
- cargas automatizables;
- cargas térmicas;
- presencia;
- frecuencia semanal;
- horarios permitidos;
- ACS;
- riego;
- cocina solar.

Debe adaptarse a cada vivienda antes de interpretar los resultados como representativos.

---

# 14. Primera prueba

Una vez configuradas las credenciales y la instalación:

```bash
python3 main.py --soc 0.60
```

Una ejecución más completa:

```bash
python3 main.py \
    --soc 0.60 \
    --mostrar-semanal \
    --mostrar-precios \
    --mostrar-solar \
    --mostrar-balance \
    --mostrar-plan-horario
```

---

# 15. Prueba independiente de la planificación semanal

```bash
python3 weekly.py
```

La salida debería mostrar:

```text
plan semanal
calidad solar
confianza
tareas desplazables
gestión térmica
ACS
riego
cocina solar
```

---

# 16. Comprobación de AEMET

Puede comprobarse primero que la API key funciona utilizando los módulos del proyecto.

Ejemplo conceptual:

```python
from config import obtener_configuracion_sistema
from aemet import obtener_prevision_solar

config = obtener_configuracion_sistema()

municipio = config["localizacion"]["municipio"]

datos = obtener_prevision_solar(municipio)

print(datos)
```

---

# 17. Comprobación de AEMET horario

Ejemplo:

```python
from config import obtener_configuracion_sistema
from aemet_hourly import obtener_prevision_horaria

config = obtener_configuracion_sistema()

municipio = config["localizacion"]["municipio"]

datos = obtener_prevision_horaria(municipio)

print(datos)
```

---

# 18. Comprobación del modelo FV

Una prueba típica del modelo solar puede utilizar:

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

# 19. Home Assistant — integración opcional

Home Assistant no es necesario para ejecutar actualmente el modelo.

Puede utilizarse en una fase posterior como:

- interfaz;
- dashboard;
- sistema de notificaciones;
- adquisición de datos reales;
- automatización de cargas;
- futura capa de control del inversor.

## 19.1 Web oficial

```text
https://www.home-assistant.io/
```

Instalación:

```text
https://www.home-assistant.io/installation/
```

Home Assistant recomienda actualmente **Home Assistant Operating System** para la mayoría de instalaciones domésticas.

También puede ejecutarse mediante:

```text
Home Assistant Container
```

en sistemas Linux administrados por el usuario.

## 19.2 Arquitectura prevista

```text
AEMET + PVGIS + ESIOS
          │
          ▼
Gestión Solar Predictiva
          │
          ▼
    Home Assistant
      ┌───┼────┐
      ▼   ▼    ▼
 sensores app automatizaciones
              │
              ▼
         inversor / cargas
```

El núcleo científico debe permanecer separado de Home Assistant.

---

# 20. Deye y Home Assistant

La futura integración del inversor debe plantearse como una capa independiente.

Conceptualmente:

```text
Deye
  │
  ▼
Modbus / integración local
  │
  ▼
Home Assistant
  │
  ▼
datos reales
  │
  ▼
Gestión Solar Predictiva
```

En una primera fase se recomienda utilizar Home Assistant únicamente para:

```text
lectura
visualización
registro
notificaciones
```

Antes de permitir:

```text
escritura de registros
cambio de SOC
cambio de modos
órdenes de carga
órdenes de descarga
```

debe realizarse validación experimental y añadir una capa independiente de seguridad.

---

# 21. Modo experimental recomendado

La evolución recomendada es:

```text
FASE 1
simulación

FASE 2
datos reales sin control

FASE 3
shadow mode
el algoritmo calcula decisiones pero no las ejecuta

FASE 4
automatización de cargas no críticas

FASE 5
control limitado del inversor

FASE 6
control predictivo cerrado
```

---

# 22. Problemas frecuentes

## `ModuleNotFoundError`

Ejecutar:

```bash
python3 -m pip install -r requirements.txt
```

y comprobar que está activo el entorno virtual correcto.

## Error de API key de AEMET

Comprobar:

```bash
echo "$AEMET_API_KEY"
```

o revisar:

```text
mytoken.env
```

sin mostrar públicamente el contenido.

## AEMET limita las peticiones

Esperar y volver a intentar.

No lanzar múltiples consultas idénticas desde módulos diferentes.

## ESIOS no devuelve datos

Comprobar:

- token;
- endpoint;
- fechas solicitadas;
- formato de las cabeceras;
- disponibilidad del indicador utilizado.

## Municipio incorrecto

Comprobar:

```text
config.py
```

y la resolución del identificador municipal utilizado por AEMET.

## Predicción FV extraña

Revisar:

- localización;
- inclinación;
- azimut;
- potencia instalada;
- potencia máxima del inversor;
- fuente meteorológica;
- caché PVGIS.

---

# 23. Reproducibilidad

Para cualquier experimento deben conservarse:

```text
versión del código
commit Git
configuración
fecha
SOC inicial
forecast utilizado
precios utilizados
estrategia
resultado
```

Esto permite reconstruir posteriormente las condiciones exactas en las que el algoritmo tomó una decisión.

---

# 24. Documentación relacionada

La documentación técnica del proyecto se divide en:

```text
docs/
├── INSTALLATION.md
├── MODEL.md
├── DISPATCH.md
├── WEEKLY.md
├── VALIDATION.md
└── ARCHITECTURE.md
```

- `INSTALLATION.md`: instalación, APIs y credenciales;
- `MODEL.md`: modelo físico y energético;
- `DISPATCH.md`: batería, red y despacho;
- `WEEKLY.md`: planificación semanal;
- `VALIDATION.md`: protocolo experimental;
- `ARCHITECTURE.md`: organización software y evolución futura.

---

# 25. Seguridad

Este proyecto es experimental.

Las API keys y tokens deben considerarse secretos.

La futura integración con un inversor real no debe sustituir:

- protecciones eléctricas;
- BMS;
- límites internos del inversor;
- protecciones AC/DC;
- mecanismos de seguridad del fabricante.

Las decisiones del optimizador deben mantenerse siempre dentro de los límites físicos y operativos del sistema.
