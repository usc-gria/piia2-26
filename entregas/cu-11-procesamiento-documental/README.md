# Sistema de procesamiento documental mediante IA

> Proyecto Integrador de IA II · Grado en Inteligencia Artificial · USC · Curso 2026/27
> Caso de uso CU-11, propuesto por SDG Group

> **Estado (23-11-2026):** están hechos la ingesta del dataset, los prompts, el cliente de Groq, la validación y la tubería de un documento, con sus pruebas. La app muestra el tipo, la validación y las entidades en tablas editables, deja marcar el resultado como validado por una persona y responde preguntas sobre el documento con el último JSON validado, avisando de los datos que una persona ha corregido, y exporta el resultado corregido a JSON, CSV y Excel. El modelo es `qwen/qwen3.8-27b`, el único de Groq que acepta imágenes y salida en modo JSON. La versión actual de los prompts (`PROMPT_VERSION` 1.2) solo se ha medido con 8 facturas y ningún informe de alta, porque la cuota diaria de Groq cortó la prueba. Falta repetir la medición completa para saber si cumple los objetivos de calidad (punto 4 de [`specs/evaluacion-metricas.md`](specs/evaluacion-metricas.md)). Las mediciones hechas hasta ahora están en «Tecnologías».

## Qué es

Una herramienta web en Streamlit que procesa imágenes de documentos médicos con un modelo de IA multimodal, sin entrenarlo para esta tarea. Resuelve dos casos de uso sobre los mismos documentos:

- **Clasificación documental:** identificar si el documento es una factura médica o un informe de alta hospitalaria.
- **Detección de entidades:** extraer sus datos (hospital, paciente, diagnóstico, procedimientos, medicación, importes…) a un JSON estructurado.

La persona usuaria carga un documento, ve el resultado, puede corregirlo y lo exporta.

## Motivación

Las organizaciones dedican mucho trabajo manual a leer, clasificar y transcribir los datos de sus documentos. La herramienta está pensada para el personal administrativo que lo hace a diario con documentos médicos: el de admisión y facturación de un hospital o el de tramitación de siniestros de una aseguradora de salud, que recibe facturas e informes de alta y tiene que registrar sus datos. Es una tarea lenta, cara y propensa a errores. Los modelos multimodales actuales prometen automatizarla sin entrenar un modelo para cada tipo de documento. Este proyecto quiere comprobar hasta dónde llega esa promesa: medir la precisión de un modelo de propósito general al clasificar y extraer datos de documentos con ruido realista, y demostrar en una herramienta interactiva, con una persona que valida los resultados, cuánto trabajo puede ahorrar.

## Alcance

### Dentro del proyecto

- Ingesta de las imágenes JPEG del dataset.
- Clasificación documental y extracción de entidades a JSON estructurado mediante un modelo multimodal servido por la API de Groq.
- Interfaz en Streamlit: carga e inspección de la imagen, ejecución del procesamiento y visualización de los resultados.
- Preguntas en lenguaje natural sobre el documento cargado (Visual QA).
- Edición y validación humana de las entidades extraídas.
- Exportación de los resultados a Excel, CSV y JSON.
- Control de errores: respuestas JSON malformadas, campos ausentes y fallos de conexión.
- Evaluación de la precisión en clasificación y extracción, y de los tiempos de respuesta de la API.

### Fuera del proyecto

- Entrenar o ajustar (*fine-tuning*) modelos propios.
- Las cuatro ampliaciones de la planificación. Quedan fuera de este proyecto sin condiciones; ninguna se abordará aunque sobre tiempo:
  - Detección de anomalías y reglas de negocio sobre los datos extraídos.
  - Indicador de evidencia: el fragmento de texto literal en el que se basa cada dato.
  - Inferencia local con vLLM y un modelo abierto, en lugar de la API online.
  - Resaltado en la imagen (*bounding boxes*) de dónde está cada dato.

## Equipo

| Nombre | Rol | Contacto |
|---|---|---|
| Héctor Barro | Estudiante | hector.barro@rai.usc.es |
| Alejandro Barros | Estudiante | alejandro.barros0@rai.usc.es |
| Rodrigo Boquete | Estudiante | rodrigo.boquete@rai.usc.es |

**Tutores profesionales (SDG Group):** Adriano Pezzi Fernández · adrianoluis.pezzi@sdggroup.com 
Esteban Fabello Gonzalez · esteban.fabello@sdggroup.com
Pablo Hervada Presedo · pablo.hervada@sdggroup.com
**Tutor académico (USC):** Ismael Rodríguez Fernández · ismael.rodriguez@usc.es

## Datos

1000 imágenes JPEG de documentos médicos en inglés, con ruido añadido (marcas de agua, brillos, sombras), cada una con su JSON de referencia:

| Tipo | Imágenes | Carpeta | Verdad de referencia original | Verdad de referencia limpia |
|---|---|---|---|---|
| Factura médica (`bill`) | 500 | `data/raw/bills/` | `data/raw/medical_bills_ground_truth.csv` | `data/processed/medical_bills_cleaned.csv` |
| Informe de alta (`discharge_summary`) | 500 | `data/raw/discharge_summaries/` | `data/raw/discharge_summaries_ground_truth.csv` | `data/processed/discharge_summaries_cleaned.csv` |

Origen: [Noisy Medical Document Images (Kaggle)](https://www.kaggle.com/datasets/devp1866/noisy-medical-document-images-ocr).

La verdad de referencia original incluye campos que no aparecen en las imágenes de su tipo. `Notebooks/limpieza_datos.ipynb` los quita y guarda el resultado en `data/processed/`, que es lo que lee `load_dataset()`. Los esquemas de extracción tienen los mismos campos que la verdad limpia:

| Tipo | Campos que se quitan |
|---|---|
| Factura médica | `medications` |
| Informe de alta | `hospital.address`, `hospital.npi`, `cpt` y `price` de cada procedimiento, `insurance`, `financials` |

## Tecnologías

- Python 3.11 o superior.
- Streamlit para la interfaz ([ADR](decisions/interfaz-streamlit.md)).
- API de Groq para el modelo multimodal ([ADR](decisions/modelo-via-api-groq.md)). Modelo: `qwen/qwen3.8-27b`, el único de Groq que acepta imágenes y salida en modo JSON, así que no hay otro entre el que elegir. Es un modelo en *preview* y puede retirarse sin aviso; por eso se lee de `GROQ_MODEL`.

  **Qué se ha medido.** Tres ejecuciones de `script/evaluar_metricas.py`, todas con `temperature=0`. Objetivos de calidad de [`specs/evaluacion-metricas.md`](specs/evaluacion-metricas.md): clasificación ≥ 95 %, JSON válidos ≥ 90 %, latencia p95 ≤ 10 s.

  | Fecha | `PROMPT_VERSION` | Muestra | Llegaron al modelo | Clasificación | JSON válidos | Latencia por imagen | Qué la cortó o la invalida |
  |---|---|---|---|---|---|---|---|
  | 11-11-2026 | 1.0 | 40 (20 + 20) | 26 | 25 / 26 (96 %) | 14 / 26 (54 %) | media 3,48 s, p95 6,89 s | Se agotó el límite diario de tokens de Groq (200 000 en el nivel `on_demand`). Además, Groq rechazó 12 extracciones con un 400 `json_validate_failed`. Esquemas anteriores a su revisión. |
  | 19-11-2026, 12:24 | anterior a 1.2: pedía `json_schema` estricto (el CSV no registra la versión exacta) | 24 (12 + 12) | 24 | 22 / 24 (92 %) | 11 / 24 (46 %): 5 facturas y 6 informes de alta | media 2,38 s, p95 3,25 s (11 imágenes) | Groq rechazó con un 400 `json_validate_failed` 11 extracciones y 2 clasificaciones. Esto llevó a la versión 1.2. |
  | 19-11-2026, 18:25 | **1.2 (la actual)** | 24 (12 + 12) | **8, todas facturas** | 8 / 8 | 7 / 8 | media 2,92 s (7 imágenes) | La cuota (429) cortó la prueba: 16 documentos, entre ellos los 12 informes de alta, no llegaron al modelo, y la extracción de la octava factura tampoco. |

  **Conclusión.** Ninguna ejecución sirve para saber si el modelo cumple los objetivos. Las dos primeras usaban una forma de pedir la respuesta que ya no existe. La única con la versión actual (1.2) midió 8 facturas, así que no dice nada de los informes de alta y es demasiado pequeña para comparar con los objetivos. Lo único que muestra es que en esas 8 facturas no hubo ningún rechazo `json_validate_failed`, que era el fallo principal de las ejecuciones anteriores. Falta repetir la medición completa con la versión 1.2 y la cuota diaria sin gastar.

  Coste medido el 11-11 (0,80 y 4,00 USD por millón de tokens de entrada y de salida): 0,085 USD la muestra, unos 2,12 USD las 1000 imágenes. Es una cota inferior, porque las llamadas rechazadas no informan de sus tokens.

  Los CSV de cada ejecución se guardan en `output/`, que no se versiona. Las cifras de esta tabla están copiadas de ellos.
- Ruff como linter y formateador, y pytest para las pruebas.

## Arquitectura y decisiones

La arquitectura de la solución está en **[`ARCHITECTURE.md`](ARCHITECTURE.md)**: dos diagramas (vista general y componentes de `src/`), la responsabilidad de cada componente y el flujo de extremo a extremo de cada funcionalidad.

Las decisiones de implementación están documentadas como ADRs en [`decisions/`](decisions/):

| ADR | Decisión |
|---|---|
| [`modelo-via-api-groq.md`](decisions/modelo-via-api-groq.md) | Inferencia con la API de Groq, con el modelo leído de `GROQ_MODEL` y el esquema validado en el cliente |
| [`esquemas-extraccion-documental.md`](decisions/esquemas-extraccion-documental.md) | Un JSON Schema por tipo documental, solo con los campos visibles, y una verdad de referencia limpia para evaluar |
| [`interfaz-streamlit.md`](decisions/interfaz-streamlit.md) | Interfaz en Streamlit como capa fina sobre `src/` |
| [`validacion-esquema-en-cliente.md`](decisions/validacion-esquema-en-cliente.md) | Groq solo devuelve JSON; el esquema se valida en el cliente, que pide al modelo corregir la respuesta |
| [`consulta-por-rutas-json.md`](decisions/consulta-por-rutas-json.md) | En la consulta, Groq solo elige rutas del JSON; el código lee los valores y redacta la respuesta |

El repositorio del código tiene además dos ADRs sobre herramientas de desarrollo, no sobre la solución: Ruff como linter y formateador (`decisions/linter-ruff.md`) y dónde vive la configuración de los asistentes de IA (`decisions/configuracion-asistentes.md`).

## Estructura del repositorio

````
PIIA-2-cu-11/
├── .claude/       # Configuración de asistentes de IA para el proyecto
│   ├── agents/    # Definiciones de agentes especializados
│   └── skills/    # Instrucciones y habilidades reutilizables para los agentes
├── .github/       # Instrucciones de GitHub Copilot, que remiten a AGENTS.md
├── .vscode/       # Configuración recomendada para trabajar en VS Code
├── data/          # Datos del proyecto
│   ├── processed/ # Datos derivados o transformados durante el procesamiento
│   └── raw/       # Dataset original y datos de referencia
├── decisions/     # Decisiones de arquitectura y diseño (ADR)
├── docs/          # Documentación general, materiales y actas del proyecto
├── Notebooks/     # Cuadernos para exploración y experimentación con los datos
├── output/        # Resultados generados, métricas y exportaciones
├── script/        # Scripts auxiliares, incluida la evaluación del modelo
├── specs/         # Especificaciones funcionales, hechas y pendientes
├── src/           # Código fuente de la aplicación y del procesamiento documental
├── tests/         # Pruebas automatizadas del proyecto
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE.md  # Arquitectura de la solución
└── README.md
````

### Especificaciones

En orden de ejecución; cada una depende de las anteriores.

| Spec | Encargo | Semana | Estado |
|---|---|---|---|
| [`validacion-extraccion.md`](specs/validacion-extraccion.md) | Validar el JSON de extracción contra su esquema y listar los campos ausentes | 2 | Hecha |
| [`prototipo-streamlit.md`](specs/prototipo-streamlit.md) | Primera versión de la app: cargar, procesar y ver resultados | 3 | Hecha |
| [`edicion-exportacion.md`](specs/edicion-exportacion.md) | Editar y validar los resultados, y exportarlos a JSON, CSV y Excel | 4 | Hecha |
| [`evaluacion-metricas.md`](specs/evaluacion-metricas.md) | Repetir la prueba del modelo con los esquemas revisados y comprobar si cumple los objetivos de calidad, reducir la prueba y la evaluación a 24 documentos por la cuota y mostrar el último reporte en la app | 2 → 5 | Pendiente: falta el objetivo de coste en el script y el punto 4 (repetir la medición) |
| [`consulta-documento.md`](specs/consulta-documento.md) | Responder las preguntas con el último JSON validado y avisar de los datos corregidos por una persona | 4 | Hecha |

La consulta al documento y los campos adicionales se hicieron en la semana 4 sin spec; `consulta-documento.md` solo cubre lo que se añade sobre ellos.

## Instalación y uso

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate · Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

`-e` instala en modo editable el paquete `procesamiento_documental` de `src/`, así que la app, los scripts y las pruebas lo importan sin más. Es obligatorio: los esquemas JSON están en `src/`, fuera del paquete, y solo se encuentran con la instalación editable. El extra `dev` añade Ruff y pytest.

Crea en la raíz un fichero `.env` (no se sube a git) con tu clave de Groq y el modelo:

```
GROQ_API_KEY=tu_clave
GROQ_MODEL=qwen/qwen3.8-27b
```

> **Privacidad:** las imágenes se envían completas, codificadas en Base64, a la API online de Groq. Las consultas también envían a Groq el JSON extraído, o el validado, y las preguntas. No proceses ni consultes documentos que no estés autorizado a compartir con ese servicio.

### Cómo funciona el procesamiento

Cada documento se procesa con **dos llamadas** consecutivas a Groq, con la misma imagen:

1. **Clasificación:** el modelo devuelve `{"document_type": ...}` con `bill` o `discharge_summary`. Si la respuesta no es válida, no se hace la extracción.
2. **Extracción:** con el esquema del tipo devuelto, el modelo devuelve las entidades en JSON. Cada tipo tiene su propio esquema, con campos distintos. Se mantienen todas las claves del esquema; los datos no visibles o ilegibles van como `null`.

Las dos llamadas, y las de consulta, piden a Groq `response_format={"type": "json_object"}`: Groq solo garantiza que la salida sea un objeto JSON, no que cumpla el esquema. Antes se pedía `json_schema` en modo estricto, pero Groq no lo aplicaba en estas peticiones: el modelo generaba libremente y Groq rechazaba con un 400 `json_validate_failed` lo que no cumplía el esquema (en la ejecución del 19-11-2026, 11 de 22 extracciones y 2 de 24 clasificaciones, una de ellas con un `document_type` fuera del `enum`, algo imposible con el modo estricto aplicado).

Ahora el esquema se comprueba en `cliente.py`:

1. El prompt de sistema muestra la estructura que debe tener la respuesta, generada desde el esquema con `schema_skeleton()`.
2. `ModelClient.complete()` valida la respuesta con `jsonschema` contra el esquema de la llamada.
3. Si no lo cumple, o Groq la rechaza con un 400 `json_validate_failed` por no ser JSON, le devuelve al modelo su respuesta y la lista de errores, y le pide que la corrija. Hace como máximo 3 llamadas en total (`MAX_FORMAT_ATTEMPTS`).
4. Si la última respuesta sigue sin cumplir el esquema, se devuelve igualmente y la validación (`validate_extraction()`) la marca como inválida; si la última la rechazó Groq, la llamada falla con `ModelError`.

El JSON nunca se repara en el código: no se rellenan claves ni se borran las que sobran.

### Código

| Módulo | Qué hace |
|---|---|
| `src/procesamiento_documental/ingesta.py` | `load_dataset()` lee los CSV de verdad de referencia limpia de `data/processed/` y enlaza cada fila con su imagen de `data/raw/`; falla ante la primera incoherencia. `sample_documents()` elige una muestra equilibrada por tipo con semilla fija. `image_to_data_url()` codifica imágenes JPEG o PNG para enviarlas a Groq, e `is_jpeg()` comprueba por el contenido que un fichero es un JPEG. |
| `src/procesamiento_documental/prompts.py` | Prompts, tipos documentales y esquemas de respuesta de clasificación y consulta. Cada `build_*_request()` devuelve los mensajes multimodales y el esquema con el que se valida la respuesta. `with_structure()` añade al prompt de sistema un esqueleto JSON con todas las claves del esquema y el tipo o los valores permitidos de cada una, generado con `schema_skeleton()`; `build_format_retry_prompt()` redacta el mensaje que pide al modelo corregir su respuesta. `PROMPT_VERSION` es una constante de este módulo que identifica la versión de los prompts de clasificación y extracción; se sube a mano cada vez que cambia uno de ellos, y `script/evaluar_metricas.py` la imprime en su resumen. La 1.1 añadió el esqueleto a la extracción; 1.2 lo extiende a las consultas y al campo adicional y deja de pedir `json_schema` a Groq. |
| `src/procesamiento_documental/cliente.py` | La única pieza que habla con Groq. `ModelClient.from_env()` lee `GROQ_API_KEY` y `GROQ_MODEL`; `classify()` devuelve el tipo validado y `extract()` el JSON en bruto. Pide `json_object`, valida cada respuesta con `jsonschema` y, si no cumple el esquema, pide al modelo que la corrija, hasta 3 llamadas (ver «Cómo funciona el procesamiento»). Cada respuesta incluye latencia y tokens, sumados entre esas llamadas, e intentos, que cuentan todas las llamadas hechas. Reintenta con espera los 429, los fallos de conexión y los 5xx, hasta 5 veces por llamada; cualquier otro fallo lanza `ModelError`, que guarda el último texto rechazado si Groq lo envía (`failed_generation`), el código HTTP (`status_code`) y el código de error de Groq (`error_code`, p. ej. `json_validate_failed`). |
| `src/procesamiento_documental/validacion.py` | `validate_extraction()` comprueba el JSON de extracción contra el esquema de su tipo, formatos incluidos, y lista las rutas de los campos ausentes (`null` o lista vacía). Solo informa: no corrige el JSON, y una respuesta mala del modelo no lanza excepciones. |
| `src/procesamiento_documental/pipeline.py` | `process_document()` encadena la clasificación, la extracción y la validación de una imagen y devuelve un `DocumentResult`. Ningún fallo del modelo sale como excepción: queda anotado con su etapa (`classification` o `extraction`). |
| `src/procesamiento_documental/metricas.py` | `compare_extraction()` compara una extracción con su verdad de referencia y cuenta los campos evaluables, los correctos y los ausentes. |
| `src/procesamiento_documental/tablas.py` | `entities_to_tables()` reparte el JSON de extracción en las tablas del tipo de documento: `campos`, `procedimientos` y, en los informes de alta, `medicamentos`. `tables_to_entities()` es su inversa: reconstruye el JSON desde las tablas, ya editadas, con el tipo que el esquema da a cada campo. `validate_tables()` valida ese JSON con `validate_extraction()`. |
| `src/procesamiento_documental/revision.py` | `entity_changes()` lista los campos en los que el JSON validado por una persona no vale lo mismo que el que extrajo el modelo, con los dos valores. Las listas se comparan enteras, y `null`, una lista vacía, un texto en blanco y una clave ausente cuentan como el mismo valor. |
| `src/procesamiento_documental/exportacion.py` | `to_json_bytes()`, `to_csv_bytes()` y `to_excel_bytes()` generan en memoria, sin escribir en disco, los ficheros de exportación del resultado de un documento. `export_file_name()` da su nombre: `<imagen>_entidades.<extensión>`. |
| `src/procesamiento_documental/mensajes.py` | `model_error_message()` traduce un fallo del modelo (etapa, tipo, código HTTP y código de error de Groq) a un `UserMessage` en castellano: qué ha pasado (`problem`) y qué hacer (`action`). Cubre el 400 `json_validate_failed`, otros 400, 401, 403, 404, 413, 429, 5xx, los fallos de conexión y las respuestas inutilizables; lo demás recibe un mensaje genérico. |
| `src/procesamiento_documental/integraciones.py` | Las funciones que usa la app: `procesar_documento()` traduce el resultado de la tubería, `responder_pregunta()` responde sobre el JSON del modelo o, si lo hay, sobre el validado, `responder_preguntas()` resuelve un lote de preguntas independientes en una sola llamada, y `extraer_campo_adicional()` busca en la imagen un campo pedido bajo demanda. |

### Pruebas

```bash
python -m pytest     # pruebas unitarias, sin red ni cuota de Groq
ruff check .         # obligatorio antes de subir cambios
ruff format --check .
```

Prueba de extremo a extremo con la API real: clasifica y extrae el primer JPEG de `data/raw/` e imprime las dos respuestas, sin guardar nada.

```bash
python tests/envio_imagenes_groq.py
```

### Prueba del modelo y evaluación de métricas

Una sola ejecución mide el modelo de `GROQ_MODEL` y compara su extracción con la verdad de referencia:

```bash
python script/evaluar_metricas.py
python script/evaluar_metricas.py --per-type 3
python script/evaluar_metricas.py --precio-entrada <USD/M> --precio-salida <USD/M>
```

Procesa 12 facturas y 12 informes de alta (muestra fija, semilla 42); `--per-type N` cambia el número de cada tipo. Llama a Groq una sola vez por documento. Con ese mismo resultado guarda dos ficheros en `output/`, con una fila por documento cada uno:

- `prueba_modelo_<AAAAMMDD-HHMM>.csv`: tipo predicho, validez del JSON, latencia de cada llamada, tokens, intentos (incluidas las llamadas que piden corregir el formato), campos ausentes y el texto en bruto de la extracción.
- `metricas_<AAAAMMDD-HHMMSS-ffffff>.csv`: clasificación, validez del JSON, conteos de campos frente a la referencia, errores y tiempo total. No guarda los valores de referencia ni los extraídos.

Al terminar imprime el resumen de las métricas y el de la prueba: acierto en clasificación, JSON válidos, latencia, errores por etapa, coste estimado y si se cumplen los objetivos de calidad. Los precios, en USD por millón de tokens, son opcionales y van juntos: dependen del modelo y Groq los cambia. Sin ellos no se calcula el coste.

Gasta cuota de Groq y envía imágenes: son 48 llamadas con la muestra por defecto. En el nivel `on_demand` el límite es de 200 000 tokens al día; si se agota a mitad de la ejecución, los documentos restantes quedan como errores con un 429, y hay que descontarlos al leer el resumen.

La comparación es `compare_extraction()` de `metricas.py`: compara los campos no nulos de la verdad de referencia limpia, ignorando mayúsculas y espacios. Las listas se comparan completas y en orden, como un solo campo. Un documento es correcto si coinciden todos sus campos evaluables. Una extracción sin objeto JSON queda fuera del acierto de extracción, y un fallo sin clasificación, fuera del acierto de clasificación. El tiempo incluye los reintentos y las esperas.

### Interfaz Streamlit

`src/app.py` solo contiene presentación: la conversión entre el JSON y las tablas, la validación y las llamadas a Groq viven en `procesamiento_documental`.

- **Documentos:** se elige una imagen del dataset local, por tipo, o se suben ficheros JPEG propios, que no se guardan en disco. Si el contenido de un fichero no es un JPEG, la app lo dice y no deja procesarlo.
- **Pestaña «Documento»:** muestra la imagen y, tras pulsar «Procesar documento», el tipo predicho, si el JSON cumple el esquema (con los errores si no), los campos ausentes, las tablas editables del tipo de documento, el JSON editado, la latencia y los tokens de cada llamada y el JSON en bruto que devolvió el modelo, que no cambia al editar. Las tablas son `campos`, `procedimientos` y, en los informes de alta, `medicamentos`. Si el procesado falla, la app no muestra el texto técnico de Groq: un aviso en castellano explica qué ha pasado, nombrando la etapa (identificar el tipo o extraer los datos), y qué hacer, por ejemplo reintentar, esperar a que se libere la cuota o revisar `GROQ_API_KEY` o `GROQ_MODEL`. El texto original queda plegado en «Detalle técnico del error». Una imagen no válida o un fallo inesperado se muestran igual, sin trazas de Python.
- **Edición y validación humana:** en `campos` se corrige la columna `valor`; la columna `campo` no se edita. En `procedimientos` y `medicamentos` se pueden además añadir y borrar filas. Tras cada cambio la app reconstruye el JSON con `tables_to_entities()` y lo valida contra el esquema de su tipo: los errores, con la ruta del campo, y los campos ausentes aparecen sobre las tablas. Una celda vacía es `null`, una tabla de lista sin filas es `null` y un número escrito como texto se guarda como número; los códigos (`cpt`, `npi`) son texto y conservan los ceros a la izquierda. El botón «Marcar como validado» solo está activo si el JSON editado es válido, y cualquier edición posterior lo deja otra vez como no validado. Editar no llama a Groq.
- **Exportación:** bajo las tablas, tres botones descargan el resultado como `<imagen>_entidades.json`, `.csv` y `.xlsx`, donde `<imagen>` es el nombre del documento sin la extensión. Solo están activos si el JSON editado es válido. Se exporta lo que la persona ha editado, esté o no validado, no la respuesta original del modelo. El JSON lleva `source_file`, `document_type`, `validated_by_human` y `entities`. El CSV tiene las columnas `campo` y `valor`, con una fila por valor y rutas como `patient.name` o `procedures[0].cpt`; va en UTF-8 con BOM y un `null` es una celda vacía. El Excel tiene una hoja por tabla. Los códigos conservan los ceros a la izquierda en los tres; al abrir el CSV en una hoja de cálculo hay que importar la columna `valor` como texto para no perderlos.
- **Pestaña «Consulta al documento»:** permite conversar sobre el JSON del documento y pedir campos adicionales visibles en la imagen. «Marcar como validado» funciona como un guardado para el chat: responde con el último JSON validado y, mientras no se haya validado ninguno, con el que extrajo el modelo. Editar después de validar no cambia lo que usa el chat hasta que se valida otra vez. Una línea sobre el chat dice qué versión está usando y si hay cambios sin validar. El chat localiza el dato en el JSON y responde con su valor; si la pregunta es ambigua o el dato falta, pide una aclaración. Cuando una respuesta se apoya en un dato corregido, lo dice, y debajo aparece el campo y el valor que había extraído el modelo.
- **Pestaña «Reporte de métricas»:** resume los 1000 documentos del dataset, cuántos se han procesado en la sesión, el acierto de clasificación frente al tipo del dataset y los tiempos. Un documento cuya clasificación falló aparece como «Error» y no cuenta en el acierto. Al final, la sección «Última evaluación» muestra el `metricas_*.csv` más reciente de `output/` (por la fecha de su nombre): su fecha y nombre, el acierto de clasificación, los campos correctos, los documentos completos, los JSON inválidos, los fallos de API y por tipo, el tiempo medio y la tabla por documento. No llama a Groq; si no hay ningún reporte, indica el comando para generarlo.

Si faltan `GROQ_API_KEY` o `GROQ_MODEL`, la app indica qué variable configurar y desactiva el procesamiento; se puede seguir navegando por los documentos. Los resultados, las correcciones y las conversaciones se conservan solo en la sesión activa de Streamlit: volver a un documento ya procesado muestra su resultado, con lo que se haya corregido y su marca de validación, sin llamar a Groq. Volver a procesar un documento descarta sus correcciones. La app guarda la revisión de cada documento en `st.session_state["document_reviews"]`, con el JSON corregido (`entities`), la marca (`validated`) y la copia del JSON de la última validación (`validated_entities`), que es la que usa la consulta.

Las respuestas del chat anteriores a una validación se quedan en el historial como estaban. La comparación de los campos extraídos con la verdad de referencia no está en la app: la hace `script/evaluar_metricas.py`.

#### Integración frontend-backend

La interfaz usa tres funciones de `src/procesamiento_documental/integraciones.py`:

| Función | Entrada | Respuesta | Uso |
|---|---|---|---|
| `procesar_documento(client, imagen)` | Cliente de Groq y bytes de la imagen | `ResultadoProcesamiento` | Clasifica, extrae y valida con `process_document()`. Un fallo del modelo no lanza excepción: queda en `error` y `error_stage`, y su explicación en castellano en `error_message`. |
| `responder_pregunta(pregunta, resultado, historial, entidades_validadas)` | Pregunta, resultado procesado, historial de la conversación y, si lo hay, el JSON validado por una persona | `ResultadoPregunta` | Traduce la pregunta a rutas JSON, las resuelve en Python y responde con los valores encontrados y sus evidencias. Con `entidades_validadas` responde con ese JSON en lugar del que extrajo el modelo. |
| `extraer_campo_adicional(imagen, nombre_campo, resultado)` | Bytes de la imagen, nombre del campo y resultado procesado | Objeto con el campo y su valor | Busca un dato visible en la imagen y lo conserva separado del esquema original. |

`ResultadoProcesamiento` tiene estos campos:

| Campo | Contenido |
|---|---|
| `document_type` | El tipo predicho; `None` si falló la clasificación |
| `processing_seconds` | Suma de las latencias de las dos llamadas; `None` si alguna falló |
| `entities` | El JSON de la extracción, aunque no cumpla el esquema; `None` si no hubo validación |
| `validation` | El `ValidationResult` de `validate_extraction()`, o `None` |
| `classification`, `extraction` | Las dos `ModelResponse`, con su latencia, sus tokens y sus intentos, o `None` |
| `error`, `error_stage` | El error técnico, tal como lo da Groq, y su etapa (`classification` o `extraction`), o `None` |
| `error_message` | El `UserMessage` de `model_error_message()` que la app muestra en lugar del error técnico, o `None` |
| `additional_fields` | Campos pedidos bajo demanda en la consulta, separados de `entities` |

La app crea el cliente una sola vez con `ModelClient.from_env()` y se lo pasa a `procesar_documento()`. `responder_pregunta()` envía el prompt base, el JSON del documento, el historial reciente y la pregunta (no la imagen). Groq devuelve una intención y las rutas JSON candidatas, no una respuesta factual. Python comprueba que las rutas existan, obtiene sus valores y redacta la respuesta con esos valores; así, el modelo no puede cambiar el dato al parafrasearlo. Si falta un valor o la pregunta es ambigua, el chat pide una aclaración y puede sugerir rutas como `hospital.name`. Las preguntas ajenas al documento se rechazan. Este flujo solo recupera valores explícitos del JSON: no calcula ni deduce datos. Si recibe el JSON validado, envía ese JSON en lugar del que extrajo el modelo y calcula con `entity_changes()` los cambios entre los dos, que no viajan a Groq. Cada evidencia sobre `entities` vuelve con una clave `changes` si la afecta algún cambio: uno en su mismo campo, en uno que lo contiene (`procedures` para `procedures.0.desc`) o en uno contenido en él. La respuesta dice entonces que una persona corrigió el campo y qué valor había extraído el modelo, sin depender de que Groq lo mencione. `extraer_campo_adicional()` sí envía la imagen para localizar el campo solicitado; si no está visible, muestra un error. Estas dos funciones crean su propio cliente desde el entorno.

Lanza la aplicación desde la raíz del repositorio:

```bash
.\.venv\Scripts\python.exe -m streamlit run src/app.py
```
