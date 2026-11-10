"""
Arena TTS: suma los votos de varios evaluadores y calcula la clasificación.

Uso:
    python clasificacion.py resultados
    python clasificacion.py resultados votos_de_otra_persona.csv --min-votos 35 --salida clasificacion

Acepta ficheros CSV y carpetas (de una carpeta se leen todos los votos_*.csv).
Si el mismo fichero aparece dos veces, solo se cuenta una.

Reglas:
  - Una "pareja" es un par de modelos dentro de un mismo idioma y perfil
    (p. ej. m1 vs m2 en CASTELLANO / VOZ JOVEN), sumando todas las frases y evaluadores.
  - Una pareja solo cuenta para el ranking si tiene al menos --min-votos
    participaciones (votos con ganador + abstenciones). Por defecto, 35.
  - Porcentaje de victorias = victorias / (victorias + derrotas), usando solo
    las parejas válidas. Las abstenciones se registran pero no cuentan en el %.
  - Ranking por perfil y ranking general por idioma (todas las parejas válidas
    de todos los perfiles de ese idioma).

Salidas en la carpeta --salida:
  suma_votos_parejas.csv   suma global de votos por pareja de modelos (idioma, perfil)
  ranking_por_perfil.csv   clasificación de cada idioma y perfil
  ranking_general.csv      clasificación de cada idioma, sumando todos los perfiles
  resumen.json             ficheros usados, parámetros y ganadores

Solo usa la biblioteca estándar de Python (>= 3.9).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from arena import ABSTENCIONES, AMBOS_BIEN, AMBOS_MAL, CODIFICACION, SIN_VOTO, leer_votos

TODOS = "TODOS"  # valor de la columna "perfil" en el ranking general


def recoger_ficheros(entradas: list[str]) -> list[Path]:
    """Expande carpetas a sus votos_*.csv y elimina duplicados."""
    ficheros: dict[Path, None] = {}
    for e in entradas:
        ruta = Path(e)
        if ruta.is_dir():
            for f in sorted(ruta.glob("votos_*.csv")):
                ficheros[f.resolve()] = None
        elif ruta.is_file():
            ficheros[ruta.resolve()] = None
        else:
            print(f"Aviso: no existe {ruta}, se ignora.", file=sys.stderr)
    return list(ficheros)


def sumar_votos(ficheros: list[Path]) -> dict[tuple[str, str, str, str], dict[str, int]]:
    """Suma los votos de todos los ficheros por (idioma, perfil, modelo_a, modelo_b)."""
    suma: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"victorias_a": 0, "victorias_b": 0, AMBOS_BIEN: 0, AMBOS_MAL: 0})
    for f in ficheros:
        for pareja, resultado in leer_votos(f):
            if resultado in ("", SIN_VOTO):
                continue
            clave = (pareja.idioma, pareja.perfil, pareja.modelo_a, pareja.modelo_b)
            if resultado == pareja.modelo_a:
                suma[clave]["victorias_a"] += 1
            elif resultado == pareja.modelo_b:
                suma[clave]["victorias_b"] += 1
            elif resultado in ABSTENCIONES:
                suma[clave][resultado] += 1
            else:
                print(f"Aviso: {f.name}: resultado desconocido '{resultado}' en {pareja}, se ignora.",
                      file=sys.stderr)
    return suma


def participaciones(c: dict[str, int]) -> int:
    return c["victorias_a"] + c["victorias_b"] + c[AMBOS_BIEN] + c[AMBOS_MAL]


def wilson(victorias: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza del 95 % (Wilson) para una proporción.
    Indica cuánto podría variar el porcentaje con más votos."""
    if n == 0:
        return (math.nan, math.nan)
    p = victorias / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centro - margen, centro + margen)


def ranking(suma, min_votos: int, por_perfil: bool) -> list[dict]:
    """Calcula el ranking por (idioma, perfil) o por idioma (perfil = TODOS)."""
    # estadisticas[(idioma, perfil)][modelo] = contadores
    estad: dict[tuple[str, str], dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"victorias": 0, "derrotas": 0, "abstenciones": 0, "parejas_validas": 0}))

    for (idioma, perfil, a, b), c in suma.items():
        grupo = (idioma, perfil if por_perfil else TODOS)
        # Los modelos aparecen en el ranking aunque ninguna de sus parejas sea válida
        estad[grupo][a]; estad[grupo][b]  # noqa: B018  (crea la entrada)
        if participaciones(c) < min_votos:
            continue
        abst = c[AMBOS_BIEN] + c[AMBOS_MAL]
        for modelo, gana, pierde in ((a, c["victorias_a"], c["victorias_b"]),
                                     (b, c["victorias_b"], c["victorias_a"])):
            e = estad[grupo][modelo]
            e["victorias"] += gana
            e["derrotas"] += pierde
            e["abstenciones"] += abst
            e["parejas_validas"] += 1

    filas = []
    for (idioma, perfil) in sorted(estad):
        modelos = estad[(idioma, perfil)]
        con_datos, sin_datos = [], []
        for modelo, e in modelos.items():
            decididos = e["victorias"] + e["derrotas"]
            fila = {"idioma": idioma, "perfil": perfil, "modelo": modelo, **e,
                    "votos_con_ganador": decididos}
            if decididos > 0:
                fila["porcentaje"] = 100 * e["victorias"] / decididos
                inf, sup = wilson(e["victorias"], decididos)
                fila["ic95_inf"], fila["ic95_sup"] = 100 * inf, 100 * sup
                con_datos.append(fila)
            else:
                fila["porcentaje"] = fila["ic95_inf"] = fila["ic95_sup"] = None
                sin_datos.append(fila)
        # Orden: mayor %, luego más votos con ganador, luego nombre
        con_datos.sort(key=lambda f: (-f["porcentaje"], -f["votos_con_ganador"], f["modelo"]))
        mejor = con_datos[0]["porcentaje"] if con_datos else None
        empatados = [f for f in con_datos if f["porcentaje"] == mejor]
        for i, f in enumerate(con_datos, start=1):
            f["posicion"] = i
            f["ganador"] = ("empate" if len(empatados) > 1 else "sí") if f["porcentaje"] == mejor else ""
        for f in sorted(sin_datos, key=lambda f: f["modelo"]):
            f["posicion"] = ""
            f["ganador"] = "sin datos suficientes"
        filas.extend(con_datos + sin_datos)
    return filas


def fmt(x) -> str:
    return "" if x is None else f"{x:.1f}"


def escribir_ranking(ruta: Path, filas: list[dict]) -> None:
    columnas = ["idioma", "perfil", "posicion", "modelo", "porcentaje", "ic95_inf", "ic95_sup",
                "victorias", "derrotas", "votos_con_ganador", "abstenciones", "parejas_validas", "ganador"]
    with open(ruta, "w", newline="", encoding=CODIFICACION) as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({**fila, "porcentaje": fmt(fila["porcentaje"]),
                        "ic95_inf": fmt(fila["ic95_inf"]), "ic95_sup": fmt(fila["ic95_sup"])})


def escribir_suma(ruta: Path, suma, min_votos: int) -> None:
    columnas = ["idioma", "perfil", "modelo_a", "modelo_b", "participaciones", "victorias_a",
                "victorias_b", "ambos_bien", "ambos_mal", "valida"]
    with open(ruta, "w", newline="", encoding=CODIFICACION) as f:
        w = csv.writer(f)
        w.writerow(columnas)
        for (idioma, perfil, a, b), c in sorted(suma.items()):
            n = participaciones(c)
            w.writerow([idioma, perfil, a, b, n, c["victorias_a"], c["victorias_b"],
                        c[AMBOS_BIEN], c[AMBOS_MAL], "sí" if n >= min_votos else "no"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Suma votos de la Arena TTS y calcula la clasificación")
    ap.add_argument("entradas", nargs="+", help="Ficheros votos_*.csv o carpetas que los contienen")
    ap.add_argument("--min-votos", type=int, default=35,
                    help="Participaciones mínimas de una pareja de modelos para entrar en el ranking (35)")
    ap.add_argument("--salida", default="clasificacion", help="Carpeta de salida (clasificacion)")
    args = ap.parse_args()

    ficheros = recoger_ficheros(args.entradas)
    if not ficheros:
        raise SystemExit("No se ha encontrado ningún fichero de votos.")

    suma = sumar_votos(ficheros)
    por_perfil = ranking(suma, args.min_votos, por_perfil=True)
    general = ranking(suma, args.min_votos, por_perfil=False)

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    escribir_suma(salida / "suma_votos_parejas.csv", suma, args.min_votos)
    escribir_ranking(salida / "ranking_por_perfil.csv", por_perfil)
    escribir_ranking(salida / "ranking_general.csv", general)

    validas = sum(participaciones(c) >= args.min_votos for c in suma.values())
    ganadores = [{"idioma": f["idioma"], "perfil": f["perfil"], "modelo": f["modelo"],
                  "porcentaje": round(f["porcentaje"], 1), "ganador": f["ganador"]}
                 for f in general + por_perfil if f["ganador"] in ("sí", "empate")]
    resumen = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "min_votos": args.min_votos,
        "ficheros": [str(f) for f in ficheros],
        "parejas_con_votos": len(suma),
        "parejas_validas": validas,
        "ganadores": ganadores,
    }
    with open(salida / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    # Resumen por pantalla
    print(f"Ficheros leídos: {len(ficheros)}")
    print(f"Parejas de modelos con votos: {len(suma)} · válidas (>= {args.min_votos}): {validas}")
    if validas < len(suma):
        print(f"  {len(suma) - validas} parejas no llegan a {args.min_votos} participaciones "
              "y no cuentan para el ranking (detalle en suma_votos_parejas.csv).")
    for titulo, filas in (("GENERAL", general), ("POR PERFIL", por_perfil)):
        print(f"\nGanadores {titulo}:")
        grupos = sorted({(f["idioma"], f["perfil"]) for f in filas})
        for idioma, perfil in grupos:
            win = [f for f in filas if (f["idioma"], f["perfil"]) == (idioma, perfil)
                   and f["ganador"] in ("sí", "empate")]
            etiqueta = idioma if perfil == TODOS else f"{idioma} / {perfil}"
            if win:
                nombres = ", ".join(f"{f['modelo']} ({f['porcentaje']:.1f} %)" for f in win)
                extra = " [empate]" if len(win) > 1 else ""
                print(f"  {etiqueta}: {nombres}{extra}")
            else:
                print(f"  {etiqueta}: sin datos suficientes")
    print(f"\nResultados en {salida.resolve()}")


if __name__ == "__main__":
    main()
