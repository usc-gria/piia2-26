"""
Igualación de los audios antes de reproducirlos en la Arena.

En una prueba a ciegas, el audio que suena más fuerte suele parecer mejor, y
una frecuencia de muestreo distinta (44,1 kHz frente a 24 kHz) suena más
brillante y puede delatar al modelo. Por eso, al servir cada audio:

  1. Se pasa a mono.
  2. Se remuestrea a una frecuencia común (por defecto 24 000 Hz).
  3. Se ajusta el volumen para que todos tengan el mismo nivel en la parte
     con voz (los silencios no cuentan), sin que el pico pase de -1 dBFS.

Los ficheros originales no se modifican: se procesa una copia en memoria.

Necesita numpy (viene con Anaconda). Sin numpy, solo se ajusta el volumen
(sin remuestrear), y el programa avisa al arrancar.
"""
from __future__ import annotations

import array
import io
import math
import sys
import wave
from functools import lru_cache
from pathlib import Path

try:
    import numpy as np
except ImportError:  # sin numpy: solo ajuste de volumen
    np = None

NIVEL_OBJETIVO_DBFS = -23.0   # nivel medio de la parte con voz
PICO_MAXIMO_DBFS = -1.0       # el pico nunca supera este valor
UMBRAL_VOZ_DBFS = -45.0       # tramos de 20 ms por debajo de esto se tratan como silencio


def _db(x: float) -> float:
    return 20 * math.log10(x) if x > 0 else -120.0


def _leer_wav(ruta: Path):
    with wave.open(str(ruta)) as w:
        return w.getframerate(), w.getnchannels(), w.getsampwidth(), w.readframes(w.getnframes())


def _escribir_wav(muestras_int16: bytes, frecuencia: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frecuencia)
        w.writeframes(muestras_int16)
    return buf.getvalue()


def _procesar_numpy(frecuencia, canales, datos, frecuencia_objetivo):
    x = np.frombuffer(datos, dtype="<i2").astype(np.float64) / 32768.0
    if canales > 1:
        x = x.reshape(-1, canales).mean(axis=1)
    # Remuestreo limitado en banda por FFT: elimina lo que queda por encima de la nueva
    # frecuencia de Nyquist, así un audio de 44,1 kHz suena con el mismo ancho de banda que uno de 24 kHz.
    if frecuencia_objetivo and frecuencia != frecuencia_objetivo and len(x) > 1:
        n_nuevo = max(1, round(len(x) * frecuencia_objetivo / frecuencia))
        espectro = np.fft.rfft(x)[: n_nuevo // 2 + 1]
        x = np.fft.irfft(espectro, n_nuevo) * (n_nuevo / len(x))
        frecuencia = frecuencia_objetivo
    # Nivel medido solo en los tramos con voz
    tramo = max(1, int(0.02 * frecuencia))
    n_tramos = len(x) // tramo
    if n_tramos:
        energia = (x[: n_tramos * tramo].reshape(n_tramos, tramo) ** 2).mean(axis=1)
        umbral = 10 ** (UMBRAL_VOZ_DBFS / 10)
        activa = energia[energia > umbral]
        rms = math.sqrt(activa.mean()) if activa.size else math.sqrt(energia.mean())
    else:
        rms = math.sqrt(float((x ** 2).mean())) if len(x) else 0.0
    pico = float(np.abs(x).max()) if len(x) else 0.0
    ganancia = _ganancia(rms, pico)
    y = np.clip(x * ganancia, -1.0, 32767 / 32768)
    return (y * 32768).round().astype("<i2").tobytes(), frecuencia


def _procesar_simple(frecuencia, canales, datos):
    """Sin numpy: mono y volumen, sin remuestrear."""
    m = array.array("h")
    m.frombytes(datos)
    if sys.byteorder == "big":
        m.byteswap()
    if canales > 1:
        m = array.array("h", (int(sum(m[i:i + canales]) / canales) for i in range(0, len(m), canales)))
    if not m:
        return datos, frecuencia
    rms = math.sqrt(sum(v * v for v in m) / len(m)) / 32768
    pico = max(abs(v) for v in m) / 32768
    g = _ganancia(rms, pico)
    salida = array.array("h", (max(-32768, min(32767, round(v * g))) for v in m))
    if sys.byteorder == "big":
        salida.byteswap()
    return salida.tobytes(), frecuencia


def _ganancia(rms: float, pico: float) -> float:
    if rms <= 0 or pico <= 0:
        return 1.0
    g = 10 ** ((NIVEL_OBJETIVO_DBFS - _db(rms)) / 20)
    g_max = 10 ** ((PICO_MAXIMO_DBFS - _db(pico)) / 20)   # que el pico no sature
    return min(g, g_max)


@lru_cache(maxsize=64)
def audio_igualado(ruta: Path, frecuencia_objetivo: int) -> bytes:
    """Devuelve el wav igualado (mono, 16 bits). Si el formato no es de 16 bits,
    devuelve el original sin tocar."""
    frecuencia, canales, ancho, datos = _leer_wav(ruta)
    if ancho != 2:
        return ruta.read_bytes()
    if np is not None:
        muestras, frecuencia = _procesar_numpy(frecuencia, canales, datos, frecuencia_objetivo)
    else:
        muestras, frecuencia = _procesar_simple(frecuencia, canales, datos)
    return _escribir_wav(muestras, frecuencia)


def descripcion(frecuencia_objetivo: int) -> dict:
    """Parámetros usados, para guardarlos en el .json de cada sesión."""
    return {
        "igualado": True,
        "nivel_objetivo_dbfs": NIVEL_OBJETIVO_DBFS,
        "pico_maximo_dbfs": PICO_MAXIMO_DBFS,
        "umbral_voz_dbfs": UMBRAL_VOZ_DBFS,
        "frecuencia_objetivo_hz": frecuencia_objetivo if np is not None else None,
        "numpy": np.__version__ if np is not None else None,
    }
