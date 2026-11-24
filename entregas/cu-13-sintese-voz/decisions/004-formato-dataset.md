# ADR-004 · Formato del dataset: WAV mono a 16 kHz y `metadata.csv` compatible con AudioFolder

- **Estado:** aceptada
- **Fecha:** 2026-11
- **Afecta a:** specs 05 y 06 (C5 · Montaje del dataset, C6 · Aumento con ruido) y spec 07 (C7 · ASR)

## Decisión

Cada versión del dataset es una carpeta que no se modifica una vez creada (`dataset/v001/`, `dataset/v002/`…), con esta estructura:

```
v001/
  audio/es/*.wav
  audio/gl/*.wav
  metadata.csv          # una fila por audio; columna file_name + transcription + metadatos de la spec 05
  resumen.csv           # audios y horas por idioma × perfil × estilo × modelo
  configuracion.json    # modelos y sus versiones, semillas, versiones de librerías, y nodo y GPU de cada trabajo del CESGA
  descartados.csv       # audios descartados por la revisión con ASR y motivo
  README.md             # ficha del dataset
```

- **Audio:** WAV, **mono, 16 kHz, PCM 16 bits**, con normalización de sonoridad y silencios de los extremos recortados a ≤ 0,2 s.
- **Metadatos:** `metadata.csv` en UTF-8. Lleva la columna `file_name` (ruta relativa al audio) y `transcription`, más las columnas de la spec 05 y `cer_qc`, el CER de la revisión con ASR (C5a):

```
file_name,id_audio,id_frase,transcription,idioma,id_voz,prompt_voz,perfil_voz,estilo,modelo,semilla,replica,duracion_s,cer_qc
audio/es/es_00001__p2__dictado__r0.wav,a_000002,es_00001,"Se solicita una ecografía…",es,es_00001_p2,"A 52-year-old man from Spain…",adulta_hombre,dictado,<modelo>@<versión>,1234,0,6.42,0.00
audio/gl/es_00001__p2__dictado__r0.wav,a_004001,es_00001,"Solicítase unha ecografía…",gl,es_00001_p2,"A 52-year-old man from Galicia…",adulta_hombre,dictado,<modelo>@<versión>,1234,0,6.10,0.02
```

| Columna | Contenido |
| --- | --- |
| `id_audio` | Único en todo el dataset. |
| `id_frase` | El `id` del corpus (`es_NNNNN`). Es el mismo en español y en gallego para una frase y su traducción. |
| `id_voz` | `{id_frase}_p{n}`, donde `n` (1–2) es la posición de la voz en `prompts_voz`. Con clonación es el identificador de la voz clonada, y con voz fija, el de la voz del modelo (por ejemplo, `supertonic-3:F3`). |
| `prompt_voz` | La descripción de la voz del corpus. Con voces fijas o clonadas se copia igualmente, aunque el modelo solo aprovecha de ella el sexo y el estilo. |
| `perfil_voz` | Franja y sexo deducidos de la descripción: `infantil_nino`, `infantil_nina`, `joven_hombre`, `joven_mujer`, `adulta_hombre`, `adulta_mujer`, `mayor_hombre` o `mayor_mujer`. |
| `replica` | `0` para la síntesis normal; `1`, `2`… para los audios extra que se añadan para completar las horas (spec 05). |

- **Nombres de fichero:** `audio/{idioma}/{id_frase}__p{n}__{estilo}__r{replica}.wav`. Son únicos porque la carpeta separa los idiomas. El montaje (C5) renombra los audios de los scripts de síntesis (`<id>__p<n>.wav`, ADR-003) a este formato.
- La versión con ruido (spec 06) usa exactamente el mismo formato y añade columnas.

## Motivación

1. **Carga directa para entrenar.** Esta estructura es la de **AudioFolder** de Hugging Face `datasets`. Con un `metadata.csv` que tenga `file_name`, el resto de columnas se cargan automáticamente como metadatos con una sola línea (`load_dataset("audiofolder", data_dir=...)`), y la carpeta se puede subir tal cual al Hub. La spec 05 pide un dataset «listo para entrenar un reconocedor».
2. **16 kHz es lo que usan los ASR objetivo.** Whisper y los modelos wav2vec2 / w2v-BERT trabajan a 16 kHz. Por ejemplo, el ASR gallego w2v-BERT 2.0 de Proxecto Nós se entrenó normalizando todo el audio a 16 kHz. Guardar a 16 kHz evita remuestrear en cada entrenamiento y reduce el tamaño un 33 % respecto a 24 kHz.
3. **Un único formato** (criterio de aceptación de la spec 05), aunque cada modelo TTS genere a una frecuencia distinta (por ejemplo, OmniVoice genera a 24 kHz).
4. **WAV PCM** es universal, sin pérdidas y sin dependencia de códecs. Unas 10 h (los dos idiomas) a 16 kHz/16 bits ocupan unos 1,15 GB, un tamaño manejable.
5. **Trazabilidad.** `id_frase` + `idioma` enlazan con el corpus, `id_voz` con la posición de la voz en esa fila (o con la voz clonada), y `configuracion.json` dice con qué modelos y versiones se generó.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Guardar a la frecuencia nativa del TTS** (22,05 o 24 kHz) | Rompe el «mismo formato» si los modelos difieren y obliga a remuestrear al entrenar. |
| **Organizar por carpetas `idioma/modelo/tipo-de-voz/p<número>.wav`** (como en el Arena) | Sirve para escuchar y comparar modelos, pero el número de la frase no basta para recuperar el texto con seguridad, y no hay sitio para la voz, el estilo ni la versión del modelo. El `metadata.csv` lo resuelve. |
| **FLAC** | Ahorra alrededor de un 40–50 % de espacio sin pérdidas, pero el volumen (~1 GB) no lo justifica y algunas herramientas de evaluación esperan WAV. Es fácil de convertir más adelante. |
| **Parquet / Arrow con el audio embebido** | Eficiente para datasets muy grandes, pero opaco para escuchar y revisar audios uno a uno, algo que necesitamos durante el proyecto. El Hub puede convertirlo a Parquet automáticamente. |
| **MP3 / Opus** | Formatos con pérdidas: introducen artefactos de compresión en datos de entrenamiento. |

## Consecuencias

- El montaje (C5) remuestrea con un remuestreador de calidad (por ejemplo, `soxr` vía `librosa` o `torchaudio`) y registra la biblioteca y su versión en `configuracion.json`.
- La transcripción y la descripción de la voz van entre comillas en el CSV, porque contienen comas. Al terminar, el montaje recarga el CSV y comprueba que cada `transcription` es idéntica, carácter a carácter, a la frase del corpus con el mismo `id_frase` en el mismo `idioma` (criterio de la spec 05).
- Como `id_frase` no es único por sí solo (2 voces × 2 idiomas, más réplicas), la clave de una fila es `id_audio`.
- La división entre entrenamiento y validación no se guarda en el dataset: se hace en C7 **por `id_frase`**. Así, una frase, sus dos voces y su traducción al gallego quedan siempre en el mismo lado.

## Referencias

- Crear un dataset de audio con AudioFolder: <https://huggingface.co/docs/datasets/audio_dataset>
- Datasets de audio en el Hub (`metadata.csv` / `.jsonl` / `.parquet`): <https://huggingface.co/docs/hub/en/datasets-audio>
- w2v-BERT 2.0 gallego (audio normalizado a 16 kHz): <https://huggingface.co/proxectonos/w2v-bert-2.0-gl>

