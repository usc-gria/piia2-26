# ADR-003 · Un trabajo del CESGA por modelo TTS

- **Estado:** aceptada
- **Fecha:** 2026-11
- **Afecta a:** C4 · Síntesis, C5a · Revisión con ASR y C5 · Montaje del dataset; specs 04 y 05

## Decisión

La síntesis del dataset se ejecuta en el **FinisTerrae III del CESGA**, con el gestor de colas **Slurm**. Cada modelo TTS (OmniVoice, NOS, supertonic 3 y Chatterbox Multilingual V3) tiene **su propio script, su propio entorno de Python y su propio trabajo**. **Google Colab se usa solo como entorno de pruebas**: allí se prueba cada modelo con unas pocas frases y se hace la clonación de voces (C3), pero no se genera el dataset.

Todos los scripts siguen las mismas reglas:

1. **Misma entrada:** leen el corpus (`corpus_es.tsv` o `corpus_gl.tsv`) y sintetizan solo las voces que la columna `modelo` asigna a su modelo (ADR-005).
2. **Misma salida:** un WAV por voz, con el nombre `audios/<idioma>/<modelo>/<id>__p<n>.wav` (`n` es la posición de la voz en `prompts_voz`), y un CSV con las mismas columnas en todos los scripts (`file_name`, `id`, `n_voz`, `idioma`, `modelo`, `version_modelo`, `voz`, `estilo`, `semilla`, `duracion_s`).
3. **Versiones registradas:** cada entorno tiene sus librerías en versiones fijadas, y el script registra la versión del modelo, las de las librerías y la GPU usada, que pasan a la configuración del dataset (ADR-004).
4. **Semilla fija** por audio, calculada a partir del `id` y del número de voz, para que un audio se pueda volver a generar.

El CSV no lleva la transcripción: la pone el montaje del dataset (C5), copiándola del corpus por `id`, para que no pueda haber dos versiones del texto.

## Motivación

1. **Necesidad de una gran capacidad de cómputo.** Sintetizar el volumen de audio que necesitamos (al menos 5 h por idioma, más reintentos y réplicas) y transcribirlo después requiere muchas horas de GPU, más de las que se pueden conseguir de forma fiable con sesiones interactivas. El FinisTerrae III tiene nodos con GPU que se piden por trabajo.
2. **Colab es demasiado volátil para producción.** Las sesiones de Colab se cortan por tiempo o por inactividad y lo que hay en la sesión se pierde. Sirve para probar un modelo y escuchar el resultado, pero no para dejar horas de síntesis sin vigilancia.
3. **Dependencias incompatibles.** Cada modelo pide sus propias versiones de PyTorch y de librerías de audio. NOS, por ejemplo, viene del ecosistema de Coqui TTS, y OmniVoice y Chatterbox tienen sus propios paquetes. Con un entorno y un script por modelo, cada uno instala solo lo suyo y no rompe a los demás.
4. **Trabajo en paralelo.** Cada integrante puede lanzar el trabajo de un modelo distinto a la vez, y la cola los ejecuta sin que nadie tenga que vigilarlos.
5. **Un dataset único.** Si cada script guardara los audios y los metadatos a su manera, no se podrían juntar. Por eso fijamos un nombre de fichero y unas columnas comunes.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Notebooks de Google Colab para todo** | Sintetizar este volumen de audio en Colab es lento y depende de sesiones que se cortan: hay que vigilar que la sesión siga viva y se arriesga el progreso. Se mantiene solo para pruebas y para la clonación, que son trabajos cortos y con escucha del equipo. |
| **Un solo script con todos los modelos** | Conflictos de dependencias entre modelos, y una sola persona tendría que ejecutarlo todo. |
| **Ejecutar en nuestros ordenadores** | No todos tenemos GPU, y sin ella la síntesis es demasiado lenta. Los scripts de CPU (corpus y montaje del dataset) sí se ejecutan en local. |

## Consecuencias

- **Los trabajos tienen un tiempo máximo.** La cola corta un trabajo cuando agota el tiempo pedido, así que cada audio se guarda en cuanto se genera y, al relanzar el trabajo, se salta lo ya hecho.
- **Espera en cola.** Un trabajo no empieza al instante: hay que contar con el tiempo de cola al planificar, y probar primero en Colab antes de lanzar el corpus completo.
- **Versiones fijas.** Los pesos de cada modelo se usan en una revisión fija para que todos los trabajos generen con lo mismo. Hoy esas revisiones están marcadas como `por_fijar` en `codigo/corpus/config.yaml`, y hay que fijarlas antes de empezar la síntesis.
- **Reproducibilidad en la configuración.** La GPU puede cambiar de un trabajo a otro y algunos modelos no dan exactamente el mismo audio en GPUs distintas, así que la reproducibilidad se garantiza en la configuración (mismas frases, voces, modelos y semillas), no bit a bit.
- **Audios repartidos entre ordenadores.** Cada integrante descarga los audios de los trabajos que ha lanzado, así que el montaje (C5) comprueba que cada voz del corpus tiene exactamente un audio antes de seguir (ARCHITECTURE.md, riesgo 7).

## Referencias

- FinisTerrae III, guía de usuario del CESGA: <https://cesga-docs.gitlab.io/ft3-user-guide/index.html>
    - Ejemplos de trabajos con `sbatch`: <https://cesga-docs.gitlab.io/ft3-user-guide/batch_examples.html>
    - Nodos de IA (GPU): <https://cesga-docs.gitlab.io/ft3-user-guide/gpu_nodes.html>
- OmniVoice, instalación y ejemplo de uso: <https://huggingface.co/k2-fsa/OmniVoice>
- Chatterbox Multilingual (clonación a partir de un audio de referencia): <https://github.com/resemble-ai/chatterbox> · <https://huggingface.co/ResembleAI/chatterbox>
- Voces de Proxecto Nós con Coqui TTS (Celtia): <https://huggingface.co/proxectonos/Nos_TTS-celtia-vits-graphemes>

