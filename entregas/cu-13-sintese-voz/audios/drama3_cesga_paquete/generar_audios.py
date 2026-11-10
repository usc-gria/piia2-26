#!/usr/bin/env python3
"""Genera 8 ZIP de Drama 3, por idioma y edad aparente, vía API local Fish Speech."""
import argparse
import csv
import os
from pathlib import Path
import time
import wave
import zipfile

import ormsgpack
import requests

VOCES = {
    'infantil': 'A 9-year-old girl, naturally high-pitched, light childlike voice, clear and conversational.',
    'joven': 'A 25-year-old woman, bright youthful timbre, medium-high pitch, relaxed conversational delivery.',
    'mediana': 'A 50-year-old woman, mature warm timbre, medium pitch, calm and confident delivery.',
    'mayor': 'A 75-year-old woman, warm aged voice, slightly raspy timbre, gentle and natural measured rhythm, not cartoonish.',
}
IDIOMAS = {
    'es': 'Speak in European Spanish with natural Spanish pronunciation.',
    'gl': 'Speak in Galician from Galicia with natural native Galician pronunciation, not Castilian Spanish.',
}

def leer_frases(path):
    grupos = {'es': [], 'gl': []}
    with path.open(encoding='utf-8-sig', newline='') as f:
        lector = csv.DictReader(f)
        if not {'id', 'idioma', 'frase'}.issubset(lector.fieldnames or []):
            raise ValueError('El CSV necesita las columnas id, idioma y frase')
        for fila in lector:
            idioma = fila['idioma'].strip().lower()
            if idioma in grupos and fila['frase'].strip():
                grupos[idioma].append((fila['id'].strip(), fila['frase'].strip()))
    if any(not filas for filas in grupos.values()):
        raise ValueError('Faltan frases en es o gl en el CSV')
    for idioma, filas in grupos.items():
        ids = [i for i, _ in filas]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Hay identificadores duplicados en {idioma}')
    return grupos

def wav_valido(path):
    try:
        with wave.open(str(path), 'rb') as w:
            return w.getnframes() > 0 and w.getframerate() > 0
    except Exception:
        return False

def generar(url, texto, destino, timeout, intentos):
    payload = {'text': texto, 'references': [], 'format': 'wav', 'streaming': False}
    data = ormsgpack.packb(payload)
    for intento in range(1, intentos + 1):
        try:
            respuesta = requests.post(url, params={'format': 'msgpack'},
                                     data=data, headers={'content-type': 'application/msgpack'},
                                     timeout=timeout)
            respuesta.raise_for_status()
            temporal = destino.with_suffix('.partial.wav')
            temporal.write_bytes(respuesta.content)
            if not wav_valido(temporal):
                temporal.unlink(missing_ok=True)
                raise RuntimeError('La respuesta no es un WAV válido')
            temporal.replace(destino)
            return
        except Exception:
            if intento == intentos:
                raise
            time.sleep(3 * intento)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='frases_prueba.csv')
    parser.add_argument('--salida', default='resultados_drama3')
    parser.add_argument('--url', default='http://127.0.0.1:8080/v1/tts')
    parser.add_argument('--prueba', action='store_true', help='Solo una frase por idioma y edad')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--intentos', type=int, default=2)
    a = parser.parse_args()
    grupos = leer_frases(Path(a.csv))
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    total_ok = total_error = 0
    for idioma in ('es', 'gl'):
        frases = grupos[idioma][:1] if a.prueba else grupos[idioma]
        for edad, voz in VOCES.items():
            nombre = f'drama3_{idioma}_{edad}'
            carpeta = salida / nombre
            carpeta.mkdir(parents=True, exist_ok=True)
            informe = []
            for identificador, frase in frases:
                if not identificador.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f'ID de archivo no válido: {identificador!r}')
                destino = carpeta / f'{identificador}.wav'
                # La descripción en corchetes es experimental: no equivale a una voz diseñada estable.
                prompt = f'<|speaker:0|>[{voz} {IDIOMAS[idioma]}] {frase}'
                inicio = time.monotonic()
                try:
                    if not wav_valido(destino):
                        generar(a.url, prompt, destino, a.timeout, a.intentos)
                    estado, error = 'OK', ''
                    total_ok += 1
                    print(f'OK   {nombre}/{identificador}', flush=True)
                except Exception as exc:
                    estado, error = 'ERROR', str(exc)
                    total_error += 1
                    print(f'ERROR {nombre}/{identificador}: {error}', flush=True)
                informe.append({'id': identificador, 'idioma': idioma, 'edad': edad,
                                'frase': frase, 'instruccion': voz,
                                'archivo': destino.name if estado == 'OK' else '',
                                'estado': estado, 'error': error,
                                'tiempo_segundos': round(time.monotonic() - inicio, 2)})
            with (carpeta / 'resultados.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=list(informe[0]))
                w.writeheader()
                w.writerows(informe)
            with zipfile.ZipFile(salida / f'{nombre}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
                for p in sorted(carpeta.glob('*')):
                    if p.is_file() and (p.name == 'resultados.csv' or (p.suffix == '.wav' and wav_valido(p))):
                        z.write(p, arcname=p.name)
    print(f'Finalizado: {total_ok} correctos; {total_error} errores. ZIP en {salida.resolve()}', flush=True)
    if total_error:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
