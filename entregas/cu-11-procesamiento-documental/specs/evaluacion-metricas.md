---
description: Reduce la prueba del modelo de Groq y la evaluación de métricas a 24 documentos por la cuota, repite la prueba con los esquemas revisados para comprobar si el modelo cumple los objetivos de calidad, lleva el resumen de métricas a src/ y muestra el último reporte en la pestaña «Reporte de métricas».
state: Pendiente
---

# Spec — Prueba del modelo de Groq y evaluación de métricas acotadas

Esta spec junta las antiguas `prueba-modelo-groq.md` y `evaluacion-metricas.md`, que medían lo mismo con la misma muestra. Donde chocaban, manda lo decidido para la evaluación de métricas (tarea #22).

## Lo que ya existe
Se reutiliza sin cambios salvo lo que se dice en «Qué construir»:

- `ModelClient` envía `temperature=0` en todas sus llamadas y reintenta los 429, los fallos de conexión y los 5xx. Desde `PROMPT_VERSION` 1.2 pide a Groq `json_object`, valida la respuesta con el esquema y, si no lo cumple, pide al modelo que la corrija, hasta 3 llamadas (ver «Restricciones»).
- `process_document(client, image_data_url) -> DocumentResult` en `src/procesamiento_documental/pipeline.py` hace dos llamadas en serie:
  1. **Clasificación** con `client.classify()`: tipo `bill` o `discharge_summary`.
  2. **Extracción** con `client.extract()` y el tipo obtenido, que elige el esquema (`src/Hospital_Bill.json` o `src/Discharge_Summary.json`). La respuesta se valida con `validate_extraction()` de `specs/validacion-extraccion.md`.

  `DocumentResult` guarda el tipo predicho, las dos `ModelResponse` (o `None` si la llamada no se hizo o falló), el `ValidationResult` (o `None` si la extracción no se hizo o falló) y, si algo falló, el error y la etapa (`classification` o `extraction`). Ningún fallo del modelo sale como excepción. La app de `specs/prototipo-streamlit.md` la reutiliza.
- `tests/conftest.py` tiene `_client()` y `_completion()`, y `tests/test_pipeline.py` cubre la tubería sin red.
- `script/evaluar_metricas.py` es el único script de medición. Procesa cada documento **una sola vez** con `process_document()` y, con ese mismo resultado, escribe dos CSV en `output/`:
  - `prueba_modelo_<AAAAMMDD-HHMM>.csv`, para comprobar si el modelo cumple los objetivos de calidad;
  - `metricas_<AAAAMMDD-HHMMSS-ffffff>.csv`, con la comparación frente a la verdad de referencia.

  `evaluate_document(client, document) -> DocumentRows` devuelve las dos filas de un documento (`metrics` y `model_test`), construidas con `metrics_row()` y `model_test_row()`. Ya usa 12 imágenes por tipo (punto 1 de «Qué construir»). Antes había un `script/prueba_modelo.py` aparte que volvía a llamar a Groq por la misma muestra; se ha quitado para no gastar la cuota dos veces.
- `load_dataset()`, `sample_documents()` e `image_to_data_url()` de `ingesta.py`, los prompts de `prompts.py` y `compare_extraction()` de `metricas.py`.

## Qué construir

> **Estado (23-11-2026):** los puntos 1 a 3 ya están en el código: `--per-type` con 12 por defecto, `METRICS_FIELDS`, `summarize_metrics()` y `load_latest_metrics()` en `metricas.py`, y la sección «Última evaluación» en la app. Donde los puntos dicen «hoy», describen el código anterior a ese cambio. Faltan dos cosas:
> - El objetivo de coste de los criterios de «Prueba del modelo». El script solo mira la clasificación, los JSON válidos y la latencia p95, y siempre da «cumplidos» o «no cumplidos». Falta `MAX_DATASET_COST_USD` (10 USD), el resultado «sin comprobar: falta el coste» cuando no se pasan precios, y sus pruebas en `tests/test_evaluar_metricas.py`.
> - El punto 4.
>
> El intento del 19-11-2026 a las 18:25, con `PROMPT_VERSION` 1.2, se cortó por la cuota de Groq tras 8 facturas, así que no cuenta como medición (ver `README.md`, «Tecnologías»).

Cuatro cambios, en este orden:

1. **Muestra de 24 documentos.** `script/evaluar_metricas.py` procesa por defecto 12 facturas y 12 informes de alta, elegidos con `sample_documents(load_dataset(), per_type=12, seed=42)`. Un argumento opcional `--per-type N` (entero mayor que 0) cambia el número de cada tipo sin tocar el código. Nada más cambia en el script: sigue llamando a Groq una vez por documento, escribiendo los dos CSV con las mismas columnas e imprimiendo los dos resúmenes y si se cumplen los objetivos al terminar.

2. **Resumen y lectura del reporte de métricas en `src/`.** En `src/procesamiento_documental/metricas.py` se añaden:
   - `METRICS_FIELDS`, la lista de columnas del CSV de métricas, que hoy es `FIELDS` en `script/evaluar_metricas.py`. El script pasa a importarla.
   - `summarize_metrics(rows: list[dict]) -> MetricsSummary`, con el cálculo que hoy hace `main()` del script. `MetricsSummary` es una dataclass congelada con: `documents`, `classified`, `correct_classifications`, `extracted`, `total_fields`, `correct_fields`, `missing_fields`, `incorrect_fields`, `complete_documents`, `invalid_json`, `api_failures`, `failures_by_kind` (`dict[str, int]`) y `mean_seconds` (`float | None`, `None` si no hay filas). Usa las mismas reglas que hoy: una fila sin clasificación queda fuera del acierto de clasificación, y una fila sin campos evaluables queda fuera del acierto de extracción.
   - `load_latest_metrics(output_dir: Path) -> MetricsReport | None`. Busca los ficheros `metricas_*.csv` de `output_dir`, elige el más reciente por la fecha de su nombre y lo lee. Devuelve `None` si no hay ninguno. `MetricsReport` es una dataclass congelada con `path`, `created_at` (`datetime`, sacada del nombre) y `rows` (`list[dict]`). Las filas vuelven con los tipos con que se escribieron: `True`/`False` como booleanos, conteos como `int`, `tiempo_s` como `float` y las celdas vacías como `""`, igual que las filas que produce `evaluate_document()`. Así `summarize_metrics()` da el mismo resultado sobre las filas leídas que sobre las filas en memoria. Si la cabecera del CSV no coincide con `METRICS_FIELDS`, lanza `ValueError` con el nombre del fichero.

   `script/evaluar_metricas.py` imprime el resumen a partir de `summarize_metrics()`, con los mismos textos que hoy.

3. **Último reporte en la app.** La pestaña «Reporte de métricas» conserva todo lo que muestra ahora (el resumen de los documentos procesados en la sesión) y añade al final una sección «Última evaluación»:
   - llama a `load_latest_metrics()` con el directorio `output/` de la raíz del proyecto;
   - muestra la fecha del reporte y el nombre del fichero;
   - muestra con `st.metric` las cifras de `summarize_metrics()`: acierto de clasificación (`correct_classifications`/`classified`), campos correctos (`correct_fields`/`total_fields`), documentos completos (`complete_documents`/`extracted`), JSON inválidos, fallos de API y tiempo medio; y los fallos por tipo debajo;
   - muestra la tabla por documento con `st.dataframe`;
   - si `load_latest_metrics()` devuelve `None`, muestra un aviso con el comando `python script/evaluar_metricas.py`; si lanza `ValueError`, muestra el error. En ninguno de los dos casos se rompe la pestaña.

4. **Repetir la medición con los esquemas revisados**, con una sola ejecución de `script/evaluar_metricas.py`, y anotar si se cumplen los objetivos (ver criterios).

El resumen imprime `PROMPT_VERSION`, que identifica los prompts con los que se ha medido. Es la constante `PROMPT_VERSION` de `src/procesamiento_documental/prompts.py` (hoy `"1.2"`). Nadie la calcula: se sube a mano, en el mismo cambio, cada vez que se modifica un prompt de clasificación o de extracción o la forma de pedir la respuesta a Groq. Esta spec no cambia los prompts, así que no la sube.

## Por qué
El modelo (`qwen/qwen3.8-27b`) es el único de Groq que acepta imágenes y salida en modo JSON, así que la medición no decide si se usa: dice cuánto se puede confiar en él. Hay que medir, con una muestra, si lee nuestros documentos y devuelve un JSON utilizable en un tiempo y con un coste razonables, para saber cuánto trabajo recae en la revisión humana de la app. La primera prueba (11-11-2026) quedó incompleta y se hizo con esquemas que pedían campos de la verdad de referencia que no aparecen en las imágenes; esos campos ya se han quitado, así que hay que repetirla.

La cuota del modelo de Groq no da para procesar los 40 documentos de la muestra anterior: en la prueba del modelo del 11-11-2026, las 14 últimas imágenes no llegaron al modelo por el límite diario, y en la evaluación de métricas de ese mismo día 18 de los 40 documentos fallaron por cuota y 9 por errores de la API, y solo 13 llegaron a compararse con la referencia. Las dos mediciones procesaban la misma muestra con la misma tubería, y cada una llamaba a Groq por su cuenta. Con una sola ejecución y 24 documentos (48 llamadas en lugar de 160), la medición cabe en la cuota y sus cifras significan algo.

El resultado de la evaluación solo se ve hoy en la consola de quien ejecuta el script o abriendo el CSV. Mostrarlo en la app permite enseñarlo y comentarlo sin herramientas aparte, junto al resumen de la sesión.

## Restricciones
- Aplica `decisions/interfaz-streamlit.md`: el cálculo del resumen y la lectura del CSV viven en `src/`. `src/app.py` solo coloca los componentes, y los scripts solo orquestan y escriben resultados. Las llamadas, la tubería y la validación viven en `src/`.
- La clave y el modelo se leen de `GROQ_API_KEY` y `GROQ_MODEL`. Los scripts cargan `.env` con `python-dotenv`. El nombre del modelo no aparece en el código.
- Los 429, los fallos de conexión y los 5xx los reintenta el cliente, como ya hace.
- Las respuestas que no cumplen el esquema se corrigen en el cliente. Esta restricción decía antes que un 400 `json_validate_failed` no se reintentaba, para no ocultar la tasa de fallos del modelo. Las cifras lo justificaron: en la ejecución del 19-11-2026, Groq rechazó 11 de 22 extracciones y 2 clasificaciones, porque no aplicaba el modo `json_schema` estricto. Desde `PROMPT_VERSION` 1.2, el cliente pide `json_object`, valida con el esquema y, si la respuesta no lo cumple o Groq la rechaza, le devuelve al modelo los errores y le pide que la corrija, hasta 3 llamadas. `json_valid` mide el resultado final, y la columna `attempts` cuenta todas las llamadas, de modo que el coste de las correcciones sigue visible. Una extracción solo queda como error de la API si Groq rechaza también la última llamada.
- Si la clasificación falla (error de la API o tipo inválido), no se hace la extracción y la fila queda marcada con el error.
- Un error en una imagen no detiene el script: se anota en su fila y se sigue con la siguiente. Solo se detiene si faltan las variables de entorno.
- Cada documento se procesa una sola vez por ejecución: las dos filas salen del mismo `DocumentResult`. No se vuelve a tener un script aparte para la prueba del modelo.
- El precio por millón de tokens de entrada y de salida, en USD, se pasa como argumento (`--precio-entrada`, `--precio-salida`), porque depende del modelo y Groq lo cambia. Los dos son opcionales, pero van juntos: sin ellos el script no calcula el coste y lo dice en el resumen; con solo uno, termina con un error de argumentos. Sin precios el coste no se puede comprobar, así que los objetivos no pueden darse por cumplidos (ver criterios).
- Los scripts solo leen de `data/raw/` (imágenes) y de `data/processed/` (verdad de referencia).
- Mostrar el reporte no llama a Groq ni procesa documentos.
- El CSV de métricas sigue sin guardar valores extraídos ni de referencia, como hasta ahora.
- `output/` está en `.gitignore`: cada máquina ve sus propias ejecuciones. No se sube ningún CSV al repo.
- No cambian `compare_extraction()` ni las columnas de ninguno de los dos CSV.
- Queda fuera: elegir entre reportes antiguos, comparar ejecuciones, lanzar la evaluación o la prueba del modelo desde la app, exportar el reporte y mostrar en la app el CSV de `prueba_modelo`.

## Criterios de aceptación

### Prueba del modelo
- La medición se ejecuta con un solo comando, documentado al principio del fichero y en `README.md`:
  `python script/evaluar_metricas.py [--per-type N] [--precio-entrada <USD/M> --precio-salida <USD/M>]`.
- Esa única ejecución deja los dos CSV, con una fila por documento cada uno, y llama a Groq una sola vez por documento (clasificación y extracción).
- Deja en `output/prueba_modelo_<AAAAMMDD-HHMM>.csv` una fila por imagen (24 por defecto) con estas columnas: `filename`, `real_type`, `predicted_type`, `json_valid`, `error_stage`, `error`, `classification_latency_s`, `extraction_latency_s`, `input_tokens` y `output_tokens` (suma de las dos llamadas), `attempts` (suma de las dos etapas, incluidas las llamadas que piden corregir el formato), `missing_fields` (rutas separadas por `;`) y `extraction_raw` (el texto de la extracción o, si Groq rechazó la última llamada con un 400 que trae `failed_generation`, ese texto). `json_valid` es el `is_valid` de la validación contra el esquema del tipo predicho, aunque la clasificación se haya equivocado; si no hubo validación, `False`.
- Imprime un resumen con: el modelo de `GROQ_MODEL` y `PROMPT_VERSION`; el acierto en clasificación (aciertos/total y %); el porcentaje de JSON válidos sobre el total; la latencia media y p95 por imagen (suma de las dos llamadas, solo imágenes con las dos llamadas correctas); el número de errores por etapa; y, si se pasaron los precios, el coste estimado en USD de la muestra y extrapolado a las 1000 imágenes.
- Los objetivos de calidad se dan por **cumplidos** si el acierto en clasificación es ≥ 95 % (23/24 con la muestra por defecto), los JSON válidos son ≥ 90 % (22/24), la latencia p95 por imagen es ≤ 10 s y el coste extrapolado a las 1000 imágenes es ≤ 10 USD (`MAX_DATASET_COST_USD` en el script, junto a los otros umbrales). Si falla alguno de los cuatro, quedan **no cumplidos**: el modelo se sigue usando, porque no hay otro, y el incumplimiento se anota en `README.md` como limitación conocida que cubre la revisión humana de la app. Si los tres primeros se cumplen pero no se pasaron los precios, el resultado es **sin comprobar: falta el coste**, y hay que repetir con precios.
- La prueba se ejecuta con los esquemas revisados y con la cuota diaria sin gastar. El resultado, con las cifras del resumen, la fecha y el nombre del modelo, queda anotado en la sección «Tecnologías» de `README.md`, sustituyendo el de la primera prueba.

### Pruebas automáticas
- `tests/test_pipeline.py` sigue comprobando, sin red, que las peticiones llevan `temperature` 0; que una clasificación inválida devuelve el error en la etapa `classification` sin llamada de extracción; que un 400 `json_validate_failed` en la extracción devuelve el error en la etapa `extraction` sin lanzar excepción; y que una extracción correcta devuelve el tipo, las dos respuestas y una validación con `is_valid` verdadero.
- `tests/test_evaluar_metricas.py` sigue comprobando, sin red, que una ejecución escribe los dos CSV con una sola clasificación y una sola extracción por documento, y que un fallo inesperado queda anotado en las dos filas. Además comprueba que:
  - sin argumentos de muestra, hay 12 documentos de cada tipo y es la misma muestra que `sample_documents(..., per_type=12, seed=42)`;
  - con `--per-type 3`, hay 3 de cada tipo;
  - `--per-type 0` termina con un error de argumentos;
  - sin precios, el resumen dice que el coste no se ha calculado y los objetivos nunca salen «cumplidos», y con un solo precio termina con un error de argumentos;
  - con precios y los tres primeros umbrales cumplidos, un coste extrapolado de más de 10 USD da «no cumplidos», y uno de 10 USD o menos, «cumplidos».
- `tests/test_metricas.py` comprueba, sin red, que:
  - `summarize_metrics()` da los conteos esperados para unas filas de ejemplo que incluyen un documento correcto, uno con campos incorrectos y ausentes, uno con JSON inválido sin objeto, uno con fallo de clasificación por cuota y uno con fallo de extracción por API;
  - `summarize_metrics([])` devuelve ceros y `mean_seconds` igual a `None`;
  - con tres `metricas_*.csv` en un directorio temporal, `load_latest_metrics()` devuelve el de fecha más reciente en el nombre, aunque no sea el último modificado;
  - las filas escritas con `csv.DictWriter` a partir de las filas `metrics` de `evaluate_document()` vuelven iguales tras `load_latest_metrics()`, y `summarize_metrics()` da el mismo resultado sobre ambas;
  - sin ningún `metricas_*.csv`, `load_latest_metrics()` devuelve `None`;
  - con una cabecera distinta de `METRICS_FIELDS`, lanza `ValueError` con el nombre del fichero.
- `tests/test_app.py` comprueba con `AppTest`, sin red y sustituyendo `load_latest_metrics()` por una función de prueba, que:
  - con un reporte, la pestaña muestra la sección «Última evaluación» con el acierto de clasificación y la tabla por documento, y el resumen de la sesión sigue apareciendo;
  - sin reporte, muestra el aviso con `python script/evaluar_metricas.py`.

### Revisión y prueba manual
- `script/evaluar_metricas.py` y `src/app.py` no contienen el cálculo del resumen ni la lectura del CSV (revisión del diff en el PR).
- Prueba manual con la API real, anotada en el PR: ejecutar `python script/evaluar_metricas.py --precio-entrada <USD/M> --precio-salida <USD/M>` (con precios, para anotar el coste en `README.md`), comprobar que procesa 24 documentos, que deja los dos CSV y cuántos fallan por cuota, abrir la app y comprobar que «Última evaluación» muestra ese fichero con las mismas cifras que imprimió el script.
- `README.md` actualizado: muestra de 12 por tipo, el argumento `--per-type`, la sección «Última evaluación» de la pestaña y si el modelo cumple los objetivos.
- `python -m pytest`, `ruff check .` y `ruff format --check .` en verde.
