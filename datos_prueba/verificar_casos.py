"""Verifica que el sistema da lo mismo que los ejercicios resueltos en clase.

Lee `casos_clase.json` (entradas del ejercicio + resultado esperado, tomado del Excel o de las
diapositivas del curso), llama a la API REAL por HTTP y compara campo por campo.

Uso (con el servidor corriendo):
    .venv\\Scripts\\python.exe datos_prueba\\verificar_casos.py
    .venv\\Scripts\\python.exe datos_prueba\\verificar_casos.py --url http://127.0.0.1:8000/api/v1
    .venv\\Scripts\\python.exe datos_prueba\\verificar_casos.py --solo FR-01 FR-02

Tolerancia: el Excel trabaja sin redondear y el sistema redondea montos a 2 decimales y tasas a
7, por eso cada valor esperado trae su propia tolerancia (normalmente 1 céntimo).
Termina con código 1 si algún campo no coincide.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

ARCHIVO = Path(__file__).with_name("casos_clase.json")


def llamar(url_base: str, endpoint: str, entrada: dict) -> dict:
    peticion = urllib.request.Request(
        url_base + endpoint,
        data=json.dumps(entrada).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return {"__error__": f"HTTP {error.code}: {error.read().decode('utf-8')[:200]}"}
    except urllib.error.URLError as error:
        sys.exit(f"No se pudo conectar con la API ({error.reason}). ¿Está corriendo uvicorn?")


def extraer(datos, ruta: str):
    """'cronograma.0.interes' -> datos['cronograma'][0]['interes']"""
    actual = datos
    for parte in ruta.split("."):
        actual = actual[int(parte)] if isinstance(actual, list) else actual[parte]
    return actual


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:8000/api/v1")
    ap.add_argument("--solo", nargs="*", help="ids de casos a correr (por defecto todos)")
    args = ap.parse_args()

    casos = json.loads(ARCHIVO.read_text(encoding="utf-8"))["casos"]
    if args.solo:
        casos = [c for c in casos if c["id"] in args.solo]

    total = coinciden = 0
    casos_con_diferencia = []
    for caso in casos:
        print(f"\n[{caso['id']}] {caso['titulo']}")
        print(f"    fuente: {caso['fuente']}")
        respuesta = llamar(args.url.rstrip("/"), caso["endpoint"], caso["entrada"])
        if "__error__" in respuesta:
            print(f"    ERROR {respuesta['__error__']}")
            casos_con_diferencia.append(caso["id"])
            total += len(caso["esperado"])
            continue
        caso_ok = True
        for esp in caso["esperado"]:
            total += 1
            obtenido = Decimal(str(extraer(respuesta, esp["campo"])))
            esperado = Decimal(esp["valor"])
            diferencia = abs(obtenido - esperado)
            ok = diferencia <= Decimal(esp["tol"])
            coinciden += ok
            caso_ok &= ok
            marca = "OK " if ok else "DIF"
            print(f"    {marca} {esp['campo']:<28} sistema={obtenido:>18}  clase={esperado:>18}  dif={diferencia:.7f}")
            if esp.get("nota"):
                print(f"        nota: {esp['nota']}")
        if not caso_ok:
            casos_con_diferencia.append(caso["id"])

    print("\n" + "=" * 70)
    print(f"{coinciden} de {total} valores coinciden con la clase ({len(casos)} ejercicios).")
    if casos_con_diferencia:
        print("Con diferencias:", ", ".join(casos_con_diferencia))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
