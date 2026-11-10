"""
Núcleo de la Arena TTS (solo biblioteca estándar de Python, >= 3.9).

Aquí está todo lo que no depende de la interfaz:
  - descubrir los audios en la estructura AUDIOS/IDIOMA/MODELO/PERFIL/*.wav
  - generar todas las parejas posibles y muestrear una proporción de ellas
  - gestionar una sesión de votación a ciegas
  - leer y escribir los CSV de votos

La interfaz (votar.py) y la clasificación (clasificacion.py) usan este módulo.
Al no depender de Gradio, se puede probar por separado.
"""
from __future__ import annotations

import csv
import itertools
import json
import os
import platform
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Columnas del CSV de votos de una sesión: una fila por cada pareja posible.
COLUMNAS_VOTOS = ["idioma", "perfil", "frase", "modelo_a", "modelo_b", "resultado"]

# Valores posibles de la columna "resultado" (además del nombre del modelo ganador)
SIN_VOTO = "0"              # pareja no votada en esta sesión
AMBOS_BIEN = "AMBOS_BIEN"   # abstención: los dos suenan bien
AMBOS_MAL = "AMBOS_MAL"     # abstención: los dos suenan mal
ABSTENCIONES = (AMBOS_BIEN, AMBOS_MAL)

# utf-8 con BOM: Python lo lee sin problema y Excel en Windows muestra bien las tildes.
CODIFICACION = "utf-8-sig"


@dataclass(frozen=True, order=True)
class Pareja:
    """Dos audios de la misma frase, idioma y perfil, generados por dos modelos.

    Siempre se guarda con modelo_a < modelo_b (orden alfabético), para que la
    misma pareja tenga la misma clave en los ficheros de todos los evaluadores.
    El orden en pantalla (izquierda/derecha) se decide aparte, al azar.
    """
    idioma: str
    perfil: str
    frase: str      # nombre del fichero sin extensión, p. ej. "p03_es"
    modelo_a: str
    modelo_b: str


def crear_pareja(idioma: str, perfil: str, frase: str, m1: str, m2: str) -> Pareja:
    """Crea una pareja con los modelos en orden canónico."""
    a, b = sorted((m1, m2))
    return Pareja(idioma, perfil, frase, a, b)


# --------------------------------------------------------------------------
# Descubrimiento de audios y parejas
# --------------------------------------------------------------------------

def _subcarpetas(ruta: Path) -> list[Path]:
    return sorted(
        (p for p in ruta.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name,
    )


def leer_correspondencias(ruta) -> dict[tuple[str, str, str], str]:
    """Lee perfiles.csv: qué perfil representa cada carpeta de voz.

    Columnas: idioma, modelo, carpeta, perfil.
      - Si `perfil` tiene valor, los audios de esa carpeta compiten en ese perfil.
      - Si `perfil` está vacío, esa carpeta no participa en la votación.
      - Las carpetas que no aparecen en el fichero usan su propio nombre como perfil
        (por ejemplo, "VOZ ADULTA").
    Devuelve {(idioma, modelo, carpeta): perfil}.
    """
    corr: dict[tuple[str, str, str], str] = {}
    with open(ruta, newline="", encoding=CODIFICACION) as f:
        lector = csv.DictReader(f)
        faltan = {"idioma", "modelo", "carpeta", "perfil"} - set(lector.fieldnames or [])
        if faltan:
            raise ValueError(f"{Path(ruta).name}: faltan las columnas {sorted(faltan)}")
        for fila in lector:
            clave = (fila["idioma"].strip(), fila["modelo"].strip(), fila["carpeta"].strip())
            corr[clave] = (fila["perfil"] or "").strip()
    return corr


def descubrir_audios(raiz, correspondencias: dict | None = None) -> dict[tuple[str, str, str], dict[str, Path]]:
    """Recorre RAIZ/IDIOMA/MODELO/CARPETA_DE_VOZ/*.wav.

    Normalmente la carpeta de voz es el perfil ("VOZ ADULTA"...). Con
    `correspondencias` (ver leer_correspondencias) se puede asignar un perfil a
    carpetas con otro nombre ("mujer", "F3"...) o dejarlas fuera.

    Devuelve {(idioma, perfil, frase): {modelo: ruta_wav}}.
    La "frase" es el nombre del fichero sin extensión, así que la misma frase
    debe tener el mismo nombre en todos los modelos de un idioma.
    """
    raiz = Path(raiz)
    if not raiz.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de audios: {raiz}")
    correspondencias = correspondencias or {}

    indice: dict[tuple[str, str, str], dict[str, Path]] = defaultdict(dict)
    origen: dict[tuple[str, str, str], str] = {}  # (idioma, modelo, perfil) -> carpeta usada
    for d_idioma in _subcarpetas(raiz):
        for d_modelo in _subcarpetas(d_idioma):
            for d_voz in _subcarpetas(d_modelo):
                perfil = correspondencias.get((d_idioma.name, d_modelo.name, d_voz.name), d_voz.name)
                if not perfil:
                    continue  # carpeta excluida en perfiles.csv
                clave_origen = (d_idioma.name, d_modelo.name, perfil)
                if clave_origen in origen:
                    raise ValueError(
                        f"{d_idioma.name}/{d_modelo.name}: las carpetas '{origen[clave_origen]}' y "
                        f"'{d_voz.name}' tienen el mismo perfil '{perfil}'. "
                        "Cada modelo solo puede tener una voz por perfil (revisa perfiles.csv).")
                origen[clave_origen] = d_voz.name
                for wav in sorted(d_voz.iterdir()):
                    if wav.is_file() and wav.suffix.lower() == ".wav":
                        clave = (d_idioma.name, perfil, wav.stem)
                        indice[clave][d_modelo.name] = wav

    if not indice:
        raise ValueError(
            f"No se han encontrado audios .wav en {raiz}. "
            "Estructura esperada: IDIOMA/MODELO/PERFIL/*.wav"
        )
    return dict(indice)


def generar_parejas(indice) -> list[Pareja]:
    """Todas las parejas posibles: mismo idioma, perfil y frase, modelos distintos.

    Si a un modelo le falta un perfil o una frase, simplemente no aparece en
    esas parejas (no compite en ese perfil).
    """
    parejas = []
    for (idioma, perfil, frase), modelos in sorted(indice.items()):
        for a, b in itertools.combinations(sorted(modelos), 2):
            parejas.append(Pareja(idioma, perfil, frase, a, b))
    return parejas


def muestrear_parejas(parejas: list[Pareja], proporcion: float, rng: random.Random) -> list[Pareja]:
    """Selecciona al azar `proporcion` de las parejas de cada (idioma, perfil).

    Se muestrea por grupo para que todos los idiomas y perfiles tengan
    representación. Cada grupo aporta al menos una pareja.
    El orden final se baraja para no votar todo un perfil seguido.
    """
    if not 0 < proporcion <= 1:
        raise ValueError(f"La proporción debe estar en (0, 1] y es {proporcion}")

    grupos: dict[tuple[str, str], list[Pareja]] = defaultdict(list)
    for p in parejas:
        grupos[(p.idioma, p.perfil)].append(p)

    seleccion: list[Pareja] = []
    for clave in sorted(grupos):
        grupo = grupos[clave]
        n = max(1, round(len(grupo) * proporcion))
        seleccion.extend(rng.sample(grupo, n))
    rng.shuffle(seleccion)
    return seleccion


# --------------------------------------------------------------------------
# Lectura y escritura de CSV
# --------------------------------------------------------------------------

def escribir_votos(ruta, parejas: list[Pareja], votos: dict[Pareja, str]) -> None:
    """Escribe una fila por cada pareja posible: "0" si no se votó,
    el modelo ganador, AMBOS_BIEN o AMBOS_MAL.

    Se escribe en un fichero temporal y luego se renombra, para que un corte
    a mitad de escritura no deje el CSV corrupto.
    """
    ruta = Path(ruta)
    tmp = ruta.with_name(ruta.name + ".tmp")
    with open(tmp, "w", newline="", encoding=CODIFICACION) as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS_VOTOS)
        for p in parejas:
            w.writerow([p.idioma, p.perfil, p.frase, p.modelo_a, p.modelo_b, votos.get(p, SIN_VOTO)])
    try:
        os.replace(tmp, ruta)
    except PermissionError as e:
        raise PermissionError(
            f"No se puede escribir {ruta}. ¿Lo tienes abierto en Excel? Ciérralo y vuelve a votar."
        ) from e


def leer_votos(ruta) -> list[tuple[Pareja, str]]:
    """Lee un CSV de votos. Devuelve [(pareja, resultado)] incluidas las filas con "0"."""
    ruta = Path(ruta)
    filas = []
    with open(ruta, newline="", encoding=CODIFICACION) as f:
        lector = csv.DictReader(f)
        faltan = set(COLUMNAS_VOTOS) - set(lector.fieldnames or [])
        if faltan:
            raise ValueError(f"{ruta.name}: faltan las columnas {sorted(faltan)}")
        for fila in lector:
            p = crear_pareja(fila["idioma"], fila["perfil"], fila["frase"],
                             fila["modelo_a"], fila["modelo_b"])
            filas.append((p, fila["resultado"].strip()))
    return filas


def leer_frases(ruta) -> dict[str, str]:
    """Lee un CSV con columnas `id` y `frase` (como frases_prueba.csv).
    Sirve para mostrar el texto de la frase durante la votación."""
    with open(ruta, newline="", encoding=CODIFICACION) as f:
        return {fila["id"]: fila["frase"] for fila in csv.DictReader(f)}


def limpiar_nombre(nombre: str) -> str:
    """Convierte el nombre del evaluador en algo válido para un nombre de fichero."""
    limpio = re.sub(r"[^\w\-]+", "_", (nombre or "").strip()).strip("_")
    if not limpio:
        raise ValueError("Escribe el nombre del evaluador.")
    return limpio


# --------------------------------------------------------------------------
# Sesión de votación
# --------------------------------------------------------------------------

class SesionVotacion:
    """Una persona votando una muestra de parejas.

    Guarda el CSV después de cada voto, así que si se cierra el programa no se
    pierde nada de lo votado hasta ese momento.
    """

    def __init__(self, raiz_audios, proporcion: float, evaluador: str,
                 carpeta_salida, semilla: int | None = None, info_extra: dict | None = None,
                 correspondencias: dict | None = None):
        self.evaluador = limpiar_nombre(evaluador)
        # Si no se fija semilla, se genera una y se guarda en el JSON para poder repetir la muestra.
        self.semilla = semilla if semilla is not None else random.SystemRandom().randrange(2**31)
        rng = random.Random(self.semilla)

        self.raiz_audios = Path(raiz_audios).resolve()
        self.correspondencias = correspondencias or {}
        self.indice = descubrir_audios(self.raiz_audios, self.correspondencias)
        self.todas = generar_parejas(self.indice)
        if not self.todas:
            raise ValueError("No hay parejas: cada frase necesita al menos dos modelos con el mismo perfil.")
        self.seleccion = muestrear_parejas(self.todas, proporcion, rng)
        # Para cada pareja se decide al azar si modelo_a sale a la izquierda o a la derecha.
        self.a_la_derecha = [rng.random() < 0.5 for _ in self.seleccion]

        self.votos: dict[Pareja, str] = {}
        self.posicion = 0  # número de parejas ya votadas

        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"votos_{self.evaluador}_{marca}"
        self.ruta_csv = carpeta / f"{base}.csv"
        self.ruta_json = carpeta / f"{base}.json"

        self._guardar_config(proporcion, info_extra or {})
        self.guardar()

    # --- estado -----------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self.seleccion)

    @property
    def terminada(self) -> bool:
        return self.posicion >= self.total

    def actual(self) -> dict:
        """Datos de la pareja que toca votar, ya en el orden en que se muestra."""
        p = self.seleccion[self.posicion]
        modelos = self.indice[(p.idioma, p.perfil, p.frase)]
        izq, der = (p.modelo_b, p.modelo_a) if self.a_la_derecha[self.posicion] else (p.modelo_a, p.modelo_b)
        return {
            "pareja": p,
            "ruta_izquierda": modelos[izq],
            "ruta_derecha": modelos[der],
            "numero": self.posicion + 1,
            "total": self.total,
        }

    # --- acciones ---------------------------------------------------------
    def votar(self, opcion: str) -> None:
        """opcion: "izquierda", "derecha", AMBOS_BIEN o AMBOS_MAL."""
        if self.terminada:
            return
        p = self.seleccion[self.posicion]
        derecha_es_a = self.a_la_derecha[self.posicion]
        if opcion == "izquierda":
            resultado = p.modelo_b if derecha_es_a else p.modelo_a
        elif opcion == "derecha":
            resultado = p.modelo_a if derecha_es_a else p.modelo_b
        elif opcion in ABSTENCIONES:
            resultado = opcion
        else:
            raise ValueError(f"Opción de voto no válida: {opcion}")
        self.votos[p] = resultado
        self.posicion += 1
        self.guardar()

    def deshacer(self) -> None:
        """Anula el último voto y vuelve a esa pareja."""
        if self.posicion == 0:
            return
        self.posicion -= 1
        self.votos.pop(self.seleccion[self.posicion], None)
        self.guardar()

    # --- persistencia -----------------------------------------------------
    def guardar(self) -> None:
        escribir_votos(self.ruta_csv, self.todas, self.votos)

    def _guardar_config(self, proporcion: float, info_extra: dict) -> None:
        """Registra todo lo necesario para reproducir la sesión."""
        por_grupo: dict[str, dict[str, int]] = defaultdict(lambda: {"posibles": 0, "seleccionadas": 0})
        for p in self.todas:
            por_grupo[f"{p.idioma}/{p.perfil}"]["posibles"] += 1
        for p in self.seleccion:
            por_grupo[f"{p.idioma}/{p.perfil}"]["seleccionadas"] += 1
        config = {
            "evaluador": self.evaluador,
            "fecha_inicio": datetime.now().isoformat(timespec="seconds"),
            "carpeta_audios": str(self.raiz_audios),
            "proporcion": proporcion,
            "semilla": self.semilla,
            "parejas_posibles": len(self.todas),
            "parejas_seleccionadas": len(self.seleccion),
            "por_idioma_y_perfil": dict(por_grupo),
            # Qué carpeta de voz se ha usado en cada perfil (solo las que no se llaman como el perfil)
            "correspondencias": [
                {"idioma": i, "modelo": m, "carpeta": c, "perfil": p or "(excluida)"}
                for (i, m, c), p in sorted(self.correspondencias.items())],
            "python": platform.python_version(),
            "sistema": platform.platform(),
            **info_extra,
        }
        with open(self.ruta_json, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
