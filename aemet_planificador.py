import os
import sys
import argparse
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

AEMET_API_KEY = os.getenv("AEMET_API_KEY")
BASE_URL = "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/{municipio}"


import time

def get_json(url: str, params=None, retries=3):
    for intento in range(retries):
        resp = requests.get(url, params=params, timeout=20)

        if resp.status_code == 429:
            espera = 5 * (intento + 1)
            print(f"Demasiadas peticiones. Esperando {espera}s...")
            time.sleep(espera)
            continue

        resp.raise_for_status()
        return resp.json()

    raise RuntimeError("Demasiados intentos fallidos por límite de API")


def fetch_forecast(municipio_id: str, api_key: str) -> List[Dict[str, Any]]:
    url = BASE_URL.format(municipio=municipio_id)
    first = get_json(url, params={"api_key": api_key})
    data_url = first.get("datos")
    if not data_url:
        raise RuntimeError(f"No se recibió URL de datos: {first}")

    forecast = get_json(data_url)
    if not isinstance(forecast, list) or not forecast:
        raise RuntimeError("Formato inesperado en predicción.")

    dias = forecast[0].get("prediccion", {}).get("dia", [])
    if not dias:
        raise RuntimeError("No hay días de predicción.")

    return dias


def avg_precip(prob_precip_list: List[Dict[str, Any]]) -> float:
    vals = []
    for item in prob_precip_list or []:
        v = item.get("value")
        if v in ("", None):
            continue
        try:
            vals.append(float(v))
        except (ValueError, TypeError):
            pass
    return sum(vals) / len(vals) if vals else 0.0


def sky_score(estado_cielo_list: List[Dict[str, Any]]) -> float:
    if not estado_cielo_list:
        return 0.5

    text = " ".join(
        ((item.get("descripcion") or "") + " " + str(item.get("value") or ""))
        for item in estado_cielo_list
    ).lower()

    if "despejado" in text:
        return 1.0
    if "poco nuboso" in text:
        return 0.8
    if "intervalos nubosos" in text:
        return 0.6
    if "nuboso" in text and "muy nuboso" not in text:
        return 0.35
    if "muy nuboso" in text or "cubierto" in text:
        return 0.15
    if "tormenta" in text:
        return 0.05
    return 0.5


def day_solar_score(day: Dict[str, Any]) -> Dict[str, Any]:
    precip_avg = avg_precip(day.get("probPrecipitacion", []))
    cielo = sky_score(day.get("estadoCielo", []))

    temp = day.get("temperatura", {})
    tmax = temp.get("maxima")

    bonus = 0.0
    try:
        tmax_num = float(tmax)
        if tmax_num >= 20:
            bonus = 0.05
        elif tmax_num < 10:
            bonus = -0.05
    except (ValueError, TypeError):
        pass

    score = (cielo * 0.75) + (((100 - min(max(precip_avg, 0), 100)) / 100) * 0.25) + bonus
    score = max(0.0, min(1.0, score))

    fecha_txt = day.get("fecha", "")[:10]
    fecha = datetime.strptime(fecha_txt, "%Y-%m-%d").date()

    return {
        "fecha": fecha,
        "score": round(score, 2),
        "precip": round(precip_avg, 1),
        "tmax": tmax,
    }

def next_monday(from_date):
    days_ahead = (7 - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def next_monday(from_date):
    days_ahead = (7 - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def filter_days(analyzed, modo: str):
    hoy = datetime.now().date()

    if modo == "hoy":
        inicio = hoy
    elif modo == "manana":
        inicio = hoy + timedelta(days=1)
    elif modo == "proximo_lunes":
        inicio = next_monday(hoy)
    else:
        raise ValueError("Modo no válido")

    fin = inicio + timedelta(days=7)
    return [d for d in analyzed if inicio <= d["fecha"] < fin]


def nombre_dia(fecha):
    nombres = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    return nombres[fecha.weekday()]


def franja_aproximada(score: float) -> str:
    if score >= 0.80:
        return "12:00 a 16:00"
    if score >= 0.65:
        return "12:00 a 15:00"
    if score >= 0.50:
        return "13:00 a 15:00"
    return "sin una franja especialmente buena"


def decision_bateria(score: float) -> str:
    if score >= 0.75:
        return "Sí, recomendable cargar batería."
    if score >= 0.55:
        return "Podría compensar cargar, pero no será de los mejores días."
    return "Mejor no confiar en una buena carga solar."


def decision_lavadora(score: float, precip: float) -> str:
    if score >= 0.65 and precip < 25:
        return "Buen día para poner lavadora."
    if score >= 0.50 and precip < 40:
        return "Aceptable para lavadora si te conviene."
    return "Mejor dejar la lavadora para otro momento."


def comentario_general(score: float, precip: float) -> str:
    if score >= 0.75:
        return "Día favorable para aprovechar energía solar."
    if score >= 0.55:
        return "Día razonable, aunque no especialmente fuerte."
    if precip > 50:
        return "Pinta flojo por nubosidad o lluvia."
    return "Aprovechamiento solar limitado."


def print_human_report(days: List[Dict[str, Any]], modo: str):
    titulo = "hoy" if modo == "hoy" else "el próximo lunes"
    print(f"\nPlanificación tomando como inicio {titulo}\n")

    if not days:
        print("No hay días disponibles en la predicción para ese rango.")
        return

    for d in days:
        dia = nombre_dia(d["fecha"])
        fecha_txt = d["fecha"].strftime("%d/%m/%Y")
        franja = franja_aproximada(d["score"])

        print(f"{dia.capitalize()} {fecha_txt}")
        print(f"- Batería: {decision_bateria(d['score'])}")
        print(f"- Lavadora: {decision_lavadora(d['score'], d['precip'])}")
        print(f"- Mejor franja orientativa: {franja}")
        print(f"- Comentario: {comentario_general(d['score'], d['precip'])}")
        print("")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--municipio", required=True, help="Código de municipio AEMET, por ejemplo 28079")
    parser.add_argument("--modo", choices=["hoy", "proximo_lunes"], default="hoy")
    args = parser.parse_args()

    if not AEMET_API_KEY:
        print("Falta AEMET_API_KEY como variable de entorno.", file=sys.stderr)
        sys.exit(1)

    dias_raw = fetch_forecast(args.municipio, AEMET_API_KEY)
    dias_analizados = [day_solar_score(d) for d in dias_raw]
    dias_filtrados = filter_days(dias_analizados, args.modo)
    print_human_report(dias_filtrados, args.modo)


if __name__ == "__main__":
    main()
