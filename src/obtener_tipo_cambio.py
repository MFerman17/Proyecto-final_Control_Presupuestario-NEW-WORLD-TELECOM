"""
Conexion a API externa via metodo GET.
Fuente: Frankfurter API (https://frankfurter.dev) - tipos de cambio historicos
del Banco Central Europeo. Es publica, gratuita y no requiere API key.

Objetivo de negocio: obtener el tipo de cambio EUR/USD de cada mes de 2025
para poder analizar el impacto cambiario en las categorias del presupuesto
que involucran compras en dolares (ej. Tecnologia e Infraestructura).
"""
import requests
import json
import os
import time

BASE_URL = "https://api.frankfurter.dev/v1"
MESES_2025 = [f"2025-{mes:02d}-01" for mes in range(1, 13)]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT_DIR, exist_ok=True)


def obtener_tipo_cambio(fecha: str, base: str = "EUR", destino: str = "USD") -> dict:
    """
    Realiza una peticion GET a la API para obtener el tipo de cambio
    de una fecha especifica. Devuelve el JSON de respuesta.
    """
    url = f"{BASE_URL}/{fecha}"
    params = {"base": base, "symbols": destino}

    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()  # lanza excepcion si el status code no es 2xx
    return respuesta.json()


def main():
    resultados = []

    for fecha in MESES_2025:
        try:
            data = obtener_tipo_cambio(fecha)
            tasa = data["rates"]["USD"]
            resultados.append({
                "fecha": data["date"],
                "base": data["base"],
                "eur_usd": tasa
            })
            print(f"{fecha} -> 1 EUR = {tasa} USD")
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar {fecha}: {e}")
        time.sleep(0.3)  # buena practica: no saturar la API con peticiones seguidas

    # Guardar resultado como JSON (uno de los formatos que necesitas para el repo)
    out_path = os.path.join(OUT_DIR, "tipo_cambio_eur_usd_2025.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n{len(resultados)} registros guardados en {out_path}")


if __name__ == "__main__":
    main()
