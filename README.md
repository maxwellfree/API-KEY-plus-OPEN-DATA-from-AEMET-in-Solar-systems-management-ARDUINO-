# ☀️ Planificador Solar con AEMET (Python)

Este proyecto permite tomar decisiones prácticas basadas en la predicción meteorológica de la Agencia Estatal de Meteorología (AEMET), como:

- Cuándo **cargar baterías solares**
- Cuándo **poner la lavadora o lavavajillas**
- Cuándo **evitar consumos eléctricos importantes**

La idea es usar la previsión del tiempo para anticiparse y optimizar el uso de energía, especialmente en instalaciones con autoconsumo.

---

## 🔑 ¿Qué es la API de AEMET OpenData?

AEMET ofrece un servicio llamado **OpenData**, que permite acceder a datos meteorológicos mediante una API.

Para utilizar este script necesitas una **API key**, que es una clave personal que identifica tus peticiones.

---

## 📨 Cómo obtener la API key

1. Accede a:
   👉 https://opendata.aemet.es/

2. Solicita acceso (registro o email).

3. Recibirás una clave similar a esta:
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJlbS5tb3Jlbm9AdXBtLmVzIiwianRpIjoiYjU1ZTVlNDctOGU4NS00NTBlLTlmM2ItZDE2MWMwMjQ1OTU3IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NzYwNTg3MTAsInVzZXJJZCI6ImI1NWU1ZTQ3LThlODUtNDUwZS05ZjNiLWQxNjFjMDI0NTk1NyIsInJvbGUiOiIifQ.9VgtxhVERLeLVpK_OFO8-3UDsVZoOAEW96-uTZE3H4s

export AEMET_API_KEY="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJlbS5tb3Jlbm9AdXBtLmVzIiwianRpIjoiYjU1ZTVlNDctOGU4NS00NTBlLTlmM2ItZDE2MWMwMjQ1OTU3IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NzYwNTg3MTAsInVzZXJJZCI6ImI1NWU1ZTQ3LThlODUtNDUwZS05ZjNiLWQxNjFjMDI0NTk1NyIsInJvbGUiOiIifQ.9VgtxhVERLeLVpK_OFO8-3UDsVZoOAEW96-uTZE3H4s"
▶️ Uso del script

El script se ejecuta desde terminal:

python3 aemet_planificador.py --municipio CODIGO --modo MODO
Parámetros
--municipio → código de municipio de AEMET
--modo → define desde cuándo empieza la planificación:
hoy → desde el día actual
proximo_lunes → desde el próximo lunes

Ejemplo de salida:

Planificación tomando como inicio hoy

Sábado 18/04/2026
- Batería: Sí, recomendable cargar batería.
- Lavadora: Buen día para poner lavadora.
- Mejor franja orientativa: 12:00 a 15:00
- Comentario: Día favorable para aprovechar energía solar.

Domingo 19/04/2026
- Batería: Podría compensar cargar, pero no será de los mejores días.
- Lavadora: Aceptable si te conviene.
- Mejor franja orientativa: 13:00 a 15:00
- Comentario: Día razonable, aunque no especialmente fuerte.

Lunes 20/04/2026
- Batería: Mejor no confiar en una buena carga solar.
- Lavadora: Mejor dejarla para otro momento.
- Mejor franja orientativa: sin una franja especialmente buena
- Comentario: Aprovechamiento solar limitado.
