---
description: Conecta la interfaz existente de src/app.py con la tubería de src/ para procesar una imagen JPEG y mostrar el tipo, la validación y las entidades en tablas.
state: Hecha
---

# Spec — Prototipo base en Streamlit

## Qué construir
`src/app.py` ya tiene la interfaz, pero sin backend: `procesar_documento()` lanza `IntegracionPendienteError`. Esta spec la conecta con la tubería de `specs/evaluacion-metricas.md` y ajusta lo que ya existe. No se crea otra app.

### Conexión con el backend
`procesar_documento()` de `src/procesamiento_documental/integraciones.py` sigue siendo el único punto de entrada de la app, con esta firma:

```python
procesar_documento(client: ModelClient, imagen: bytes) -> ResultadoProcesamiento
```

Convierte los bytes con `image_to_data_url()`, llama a `process_document()` y traduce su `DocumentResult`. El `TypedDict` `ResultadoProcesamiento` pasa a tener estos campos:

| Campo | Tipo | Contenido |
|---|---|---|
| `document_type` | `str \| None` | El tipo predicho; `None` si falló la clasificación |
| `processing_seconds` | `float \| None` | Suma de las latencias de las dos llamadas; `None` si alguna falló |
| `entities` | `dict \| None` | `validation.data`; `None` si no hubo validación |
| `validation` | `ValidationResult \| None` | El resultado de `validate_extraction()` |
| `classification`, `extraction` | `ModelResponse \| None` | Las dos respuestas, con su latencia y sus tokens |
| `error`, `error_stage` | `str \| None` | El error y su etapa (`classification` o `extraction`) |
| `additional_fields` | `dict` | Campos pedidos bajo demanda en la consulta al documento; vacío al procesar |

Desaparecen `classification_confidence`, porque el modelo no devuelve ninguna confianza, y `annotated_image`, porque el resaltado es una ampliación que el `README.md` deja fuera del alcance. `responder_pregunta()` y `extraer_campo_adicional()` no cambian.

### Cambios en la app
1. **Barra lateral:** se añade el modelo en uso (valor de `GROQ_MODEL`) y se quita la métrica «Confianza».
2. **Documentos:** se conservan los dos orígenes, el dataset local y la subida de ficheros. Solo se aceptan `.jpg` y `.jpeg`. La lista del dataset sale de `load_dataset()`, una sola vez (`st.cache_data`), y sustituye a `_document_files()` y a `DATA_DIR`. Si el dataset no está, la app lo indica y la subida sigue funcionando.
3. **Inspección:** la imagen se sigue mostrando como ahora. Se quita la leyenda sobre las *bounding boxes* y la rama de la imagen anotada.
4. **Procesamiento:** el botón «Procesar documento» llama a `procesar_documento()` con un spinner mientras espera. Procesa solo el documento activo.
5. **Resultados** de la pestaña «Documento»:
   - el tipo de documento predicho;
   - si el JSON es válido (`st.success`) o no (`st.warning`, con los errores de la validación);
   - la lista de campos ausentes;
   - las tablas de solo lectura (`st.dataframe`) del tipo de documento: campos (`campo`, `valor`), procedimientos (`desc`, `cpt` y `price` en las facturas; solo `desc` en los informes de alta) y, solo en los informes de alta, medicamentos (`medicamento`);
   - la latencia y los tokens de cada llamada;
   - el JSON en bruto, dentro de un `st.expander`.
6. **Editor y descargas:** se retiran de la pestaña «Documento» el `st.data_editor` actual, sus dos botones de descarga y las funciones `_value_from_editor()` y `_edited_entities()`. Los sustituye `specs/edicion-exportacion.md`.
7. **Pestaña «Reporte de métricas»:**
   - se conservan el resumen, el acierto de clasificación, los tiempos y el detalle por documento;
   - un documento con `error_stage` igual a `classification` aparece con estado «Error» y no cuenta en el acierto;
   - se quitan la columna y la media de «Confianza»;
   - se retira el bloque «Coincidencia de campos extraídos», con `_ground_truth()`, `_flatten_metric_fields()` y `_normalize_metric_value()`. Penaliza los `null` de campos no visibles, algo que `decisions/esquemas-extraccion-documental.md` no permite. La comparación con la verdad de referencia vuelve con la spec de evaluación.
8. **Pestaña «Consulta al documento»:** no cambia. La consulta y los campos adicionales ya están implementados (`responder_pregunta()` y `extraer_campo_adicional()`), fuera de esta spec.

### Conversión a tablas
La conversión del JSON a tablas vive en `src/procesamiento_documental/tablas.py`, en una función `entities_to_tables(document_type: str, data: dict) -> dict[str, pandas.DataFrame]` que devuelve las tablas `campos`, `procedimientos` y, si el esquema del tipo tiene `medications`, `medicamentos`, y sustituye a `_flatten_entities()`. Las columnas de `procedimientos` son las claves que el esquema del tipo da a cada procedimiento. La de campos tiene una fila por cada valor que no está en `procedures` ni en `medications`, con la misma notación de ruta que `missing_fields` (`patient.name`, `financials.total_charges`). Los campos `null` también tienen fila, con el valor vacío, para que la edición de `specs/edicion-exportacion.md` pueda rellenarlos. Las otras tienen una fila por elemento de su lista.

Si `entities` es `None`, no se muestran tablas: solo los errores y, si lo hay, el JSON en bruto. Si `entities` es un objeto pero no cumple el esquema, las tablas se muestran igual, junto con los errores. La edición y la exportación de `specs/edicion-exportacion.md` reutilizarán esta función.

## Por qué
Es uno de los objetivos impuestos: crear la interfaz principal, el componente de carga e inspección de imágenes y conectarla con la API para mostrar los resultados. SDG pidió ver los resultados en tabla. La interfaz ya está construida, así que falta conectarla y sacar de ella lo que no es presentación. Sobre esta app se construyen después la edición, la exportación y las preguntas sobre el documento.

## Restricciones
- Aplica `decisions/interfaz-streamlit.md`: `src/app.py` solo contiene presentación. No importa `groq` ni `jsonschema`, y no construye prompts ni valida JSON: todo eso lo hace a través de `procesamiento_documental`.
- La app carga `.env` con `python-dotenv` y crea el cliente con `ModelClient.from_env()` una sola vez (`st.cache_resource`).
- Las imágenes subidas no se guardan en disco. Las del dataset solo se leen.
- Los resultados se guardan en `st.session_state["document_results"]`, uno por documento, como ahora. Volver a un documento ya procesado muestra su resultado sin llamar a Groq.
- Ningún error muestra una traza de Python en pantalla:
  - si faltan `GROQ_API_KEY` o `GROQ_MODEL`, un `st.error` dice qué variable configurar y el botón «Procesar documento» queda desactivado. Navegar por los documentos e inspeccionarlos sigue funcionando;
  - si el fichero no es un JPEG, un `st.error` lo dice y el botón queda desactivado. Se comprueba por el contenido, no por la extensión: los tres primeros bytes deben ser `FF D8 FF`. La comprobación es una función `is_jpeg(image: bytes) -> bool` de `ingesta.py`, que usa `JPEG_SIGNATURE`;
  - si la tubería devuelve un error, se muestra con su etapa (clasificación o extracción).
- Queda fuera de esta spec: editar los resultados, exportarlos, las preguntas sobre el documento, procesar varias imágenes de una vez y aceptar formatos distintos de JPEG.

## Criterios de aceptación
- `python -m streamlit run src/app.py` arranca la app sin errores en la consola.
- `tests/test_tablas.py` comprueba, sin red, que `entities_to_tables()` con una factura de ejemplo de 3 procedimientos devuelve 3 filas en `procedimientos`, ninguna tabla `medicamentos`, y una tabla `campos` que incluye `patient.name` y `financials.total_charges` pero ninguna fila de `procedures`. Con un informe de alta de ejemplo de 2 procedimientos y 2 medicamentos devuelve 2 filas en cada tabla, y `procedimientos` solo tiene la columna `desc`. Con `procedures: null` en la factura, la tabla de procedimientos está vacía y conserva sus tres columnas.
- `tests/test_ingesta.py` comprueba que `is_jpeg()` acepta los bytes de un JPEG y rechaza los de un PNG y un fichero vacío.
- `tests/test_integraciones.py` comprueba, sin red y con el transporte simulado de `tests/conftest.py`, que `procesar_documento()`:
  - con una extracción correcta devuelve el tipo, las entidades, la validación y `processing_seconds` igual a la suma de las dos latencias;
  - con una clasificación inválida devuelve `document_type` y `entities` a `None` y `error_stage` igual a `classification`;
  - con un 400 `json_validate_failed` en la extracción devuelve el tipo, `entities` a `None` y `error_stage` igual a `extraction`.
- `tests/test_app.py` usa `AppTest.from_file("src/app.py", default_timeout=30)`, de `streamlit.testing.v1`, sin red y comprueba que la app arranca sin excepciones y que, sin `GROQ_API_KEY`, muestra un `st.error` que nombra la variable. Para que no lea el `.env` de la máquina, el test parchea `dotenv.load_dotenv` y borra `GROQ_API_KEY` y `GROQ_MODEL` con `monkeypatch`.
- `src/app.py` no contiene `import groq` ni `import jsonschema`, ni las funciones que esta spec retira (comprobable con una búsqueda en el fichero).
- En `src/app.py`, `ModelClient.from_env()` se llama en un solo sitio, la función `_model_client()`, que lleva el decorador `@st.cache_resource` (comprobable con una búsqueda en el fichero).
- Prueba manual con la API real, anotada en el PR:
  - con `med_doc_bill_100001_noisy.jpg`, elegida en el dataset local, la app muestra el tipo `bill`, el hospital «Lilavati Hospital», el nombre de paciente «Amit Singh» y 5 procedimientos;
  - con cualquier informe de `data/raw/discharge_summaries/`, muestra el tipo `discharge_summary` y una fila `hospital_course` en la tabla de campos;
  - con `GROQ_MODEL` apuntando a un modelo que no existe, la app muestra el error con la etapa «clasificación» y sin traza de Python;
  - un fichero PNG renombrado a `.jpg` y subido a la app muestra el `st.error` de «no es un JPEG».
- `README.md` actualiza el estado del proyecto, que dice que la app no existe, y la sección «Interfaz Streamlit», con el nuevo `ResultadoProcesamiento` y sin las funciones retiradas. `ARCHITECTURE.md` nombra la app como `src/app.py`.
- `python -m pytest`, `ruff check .` y `ruff format --check .` en verde.
