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

## 🤖 Uso con Arduino y automatización mediante relés

Este proyecto puede ampliarse fácilmente para crear un sistema autónomo basado en microcontroladores como Arduino, ESP32 o Raspberry Pi, capaz de tomar decisiones energéticas en función de la predicción meteorológica.

La idea consiste en utilizar la salida del script (o una versión adaptada que genere señales simples) para controlar relés que activen o desactiven dispositivos eléctricos en momentos óptimos.

### ⚡ Aplicación práctica

Mediante un microcontrolador se pueden controlar:

- Lavadora
- Lavavajillas
- Termo eléctrico
- Sistemas de carga de baterías
- Otros consumos programables

El objetivo es:

- Aprovechar al máximo la producción solar ☀️
- Evitar consumos en momentos de baja generación
- Reducir ciclos innecesarios de las baterías
- Mantener las baterías como **respaldo**, no como fuente principal

---

## 🧠 Criterios inteligentes de control

El microcontrolador puede implementar lógica basada en la predicción:

### 🔋 Gestión de batería

- Si la predicción es **muy favorable (alto índice solar)**:
  - Permitir consumos directos desde producción solar
  - Activar cargas (lavadora, termo, etc.)
- Si la predicción es **intermedia**:
  - Priorizar autoconsumo, pero limitar cargas grandes
- Si la predicción es **desfavorable**:
  - Evitar consumos innecesarios
  - Reservar batería como respaldo

---

### ⏱️ Control por franjas horarias

Si se dispone de información más detallada:

- Activar dispositivos en horas centrales (ej: 12:00–16:00)
- Evitar primeras y últimas horas del día
- Ajustar dinámicamente según previsión diaria

---

## 💡 Uso de LEDs como indicadores

Un sistema sencillo pero muy útil es utilizar LEDs para indicar el estado del sistema:

- 🟢 LED verde → condiciones óptimas (activar consumos)
- 🟡 LED amarillo → condiciones intermedias (uso moderado)
- 🔴 LED rojo → condiciones desfavorables (evitar consumos)

Esto permite visualizar rápidamente el estado energético del sistema sin necesidad de interfaz compleja.

---

## 🔧 Ejemplo de lógica en Arduino (conceptual)

```cpp
int solar_score = obtenerPrediccion(); // valor simplificado

if (solar_score > 70) {
    digitalWrite(RELE, HIGH);   // activar dispositivo
    digitalWrite(LED_VERDE, HIGH);
}
else if (solar_score > 50) {
    digitalWrite(RELE, LOW);    // uso limitado
    digitalWrite(LED_AMARILLO, HIGH);
}
else {
    digitalWrite(RELE, LOW);    // no consumir
    digitalWrite(LED_ROJO, HIGH);
}

Lunes 20/04/2026
- Batería: Mejor no confiar en una buena carga solar.
- Lavadora: Mejor dejarla para otro momento.
- Mejor franja orientativa: sin una franja especialmente buena
- Comentario: Aprovechamiento solar limitado.
