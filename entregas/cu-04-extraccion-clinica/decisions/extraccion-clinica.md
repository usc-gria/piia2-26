# ADR · Alternativas de extracción clínica con IA y evaluación

**Estado** · Propuesta para revisión del equipo

## Contexto

CLI-001 debe localizar menciones relevantes para las variables solicitadas, interpretar su contexto (afirmación, negación, sospecha, antecedente, sujeto, temporalidad) y producir candidatos respaldados por evidencia documental. La spec define 25 criterios de aceptación (`CLI-001-CA01`…`CA25`) y cinco estados de evaluación. El contrato clínico ya está modelado en Pydantic v2 y dataclasses, con constructores de casos sintéticos (`D1`–`D7` en la PoC anterior, `S1`–`S12` en el nuevo catálogo).

El equipo necesita decidir qué familia de motor usar para el prototipo y cómo evaluarla. La issue #4 pide comparar enfoques, proponer casos sintéticos, métricas y una recomendación condicionada.

## Decisión propuesta

**Usar un puerto `MotorExtraccion` (Protocol) con un motor de reglas explícitas (`MotorReglas`) como suelo de referencia ejecutable en esta entrega.** Los enfoques con modelo (LLM local, LLM alojado, híbrido) quedan diseñados en la interfaz pero no se ejecutan por falta de hardware (GPU) y autorización de la entidad. La recomendación es condicional: se propone el motor de reglas para el prototipo, condicionado a que la comparativa con modelo real (issue #7 y hardware) no lo supere de forma clara.

El arnés de evaluación recorre motores × casos sintéticos y produce métricas por dimensión, nunca una cifra agregada. Los casos no evaluables (5 de 25) se incluyen con su entrada y resultado esperado, marcados como no evaluables y con motivo.

## Alternativas consideradas y justificación

| Enfoque | Exactitud verificable | Coste | Trazabilidad | Privacidad | Complejidad |
|---|---|---|---|---|---|
| **Reglas / NLP clásico (propuesto)** | Alta en vocabulario controlado; baja en lenguaje libre | Muy bajo (CPU, sin dependencias pesadas) | Total: cada decisión es una regla inspeccionable | Total: ejecución local, sin red | Baja: once familias de regex sobre texto normalizado |
| **LLM local** | Potencialmente alta en lenguaje natural | Alto: requiere GPU con VRAM suficiente (el equipo no dispone) | Media: requiere logging de prompts/respuestas y atención | Total si modelo local; pero hardware no disponible | Alta: cuantización, serving, prompts, validación de salida |
| **LLM alojado** | Potencialmente más alta (modelos mayores) | Coste por token / suscripción | Media: depende de logging del proveedor | **No** sin autorización explícita de la entidad; material clínico no sale del entorno autorizado | Media: adaptador, reintentos, gestión de claves |
| **Híbrido (reglas + LLM contextual)** | Combina lo anterior | Suma de ambos | Media: frontera reglas/LLM debe ser explícita | Depende de la rama LLM | Alta: dos pipelines, fusión de resultados, criterios de paso |

**Justificación de la elección:**

- El motor de reglas cubre 20 de 25 criterios evaluables con el vocabulario sintético actual (afección Alfa, Delta, fármaco Beta, marcador Gamma, prueba Épsilon, abreviatura AX).
- No requiere hardware especial ni autorizaciones; se ejecuta en la suite principal.
- Es totalmente trazable: cada clasificación proviene de una familia de regex documentada y ordenada (la sospecha se evalúa antes que la negación para no convertir «no se descarta» en negación).
- Sirve como suelo de referencia honesto: los enfoques con modelo deben demostrar mejora clara sobre este suelo para justificar su complejidad y coste.
- Los 5 criterios no evaluables (`CA06`, `CA07`, `CA18`, `CA23`, `CA24`) dependen de campos que el contrato actual no tiene (`desenlace_busqueda`, `estado_casilla`, `temporalidad` estructurada). Se documentan como límites conocidos (H2, H3, H4).

## Evidencia experimental

### Catálogo de casos sintéticos (`S1`–`S12`)

Doce documentos ficticios con el vocabulario de la spec, construidos con `documento()`, `pagina()`, `bloque()`, `entrada()` e `incidencia()` para evitar duplicación literal (evita H5). Cubren:

- **S1**: Afirmación diagnóstica, administración de Beta, valor de Gamma
- **S2**: Negación explícita y repetición de administración
- **S3**: Sospecha («pendiente de estudio»)
- **S4**: Hipótesis («no se descarta»)
- **S5**: Antecedente histórico + negación actual
- **S6**: Mención en familiar (madre)
- **S7**: Valor de Gamma 2024 + abreviatura AX sin resolver
- **S8**: Formulario con casilla sin marcar + abreviatura resuelta en otra página
- **S9**: Tres bloques de tratamiento con Beta (prescripción, administración, antecedente)
- **S10**: Negación con misma fecha que afirmación de S9
- **S11**: Fecha del hecho distinta de fecha del informe + prueba Épsilon
- **S12**: Fecha remitida a otro documento + página con error

### 25 casos de evaluación (20 evaluables, 5 no evaluables)

| Dimensión | Criterios | Evaluable | Motivo si no |
|---|---|---|---|
| Afirmación | CA01 | Sí | — |
| Negación | CA02, CA13 | Sí | — |
| Familiar / sujeto | CA05 | Sí | — |
| Sospecha | CA03 | Sí | — |
| Temporalidad | CA04, CA10, CA11, CA12, CA20 | Sí | — |
| Contradicción | CA09 | Sí | — |
| Ausencia | CA13 | Sí | — |
| Ausencia documental | CA06, CA23, CA24 | **No** | H3 (falta `estado_casilla` en contrato DOC→CLI), H2 (falta `desenlace_busqueda`) |
| Ambigüedad y cobertura | CA14, CA15 | Sí | — |
| Ambigüedad y cobertura | CA07, CA23, CA24 | **No** | H3, H2 |
| Evidencia entre documentos | CA16 | Sí | — |
| Repetición | CA08, CA20 | Sí | — |
| Abreviaturas | CA19 | Sí | — |
| Tratamiento | CA18 | **No** | H4 (`temporalidad` es texto libre, no distinguen prescripción/administración/antecedente) |
| Alcance de la selección | CA17, CA21, CA25 | Sí | — |
| Bloqueo de etapa | CA22 | Sí | — |

### Métricas (todas por dimensión, sin agregado global)

| Métrica | Qué mide |
|---|---|
| `acierto_estado` | Proporción de casos por dimensión cuyo estado coincide con el esperado (5 estados de §4 spec) |
| `acierto_polaridad` | Acierto de polaridad por mención, separado del estado |
| `acierto_sujeto` | Acierto de sujeto (paciente/familiar/otra_persona/no_determinado) por mención |
| `acierto_temporal` | Fecha del hecho correcta, precisión conservada, `seleccion_temporal_pendiente` cuando corresponde |
| `citas_verificables` | **Medida por el arnés**: proporción de menciones cuyo `fragmento` es subcadena literal del bloque citado. Sustituye a «resolución de evidencias» (valía 100 % por construcción) |
| `abstencion_correcta` | Casos donde el esperado es insuficiencia o no encontrado y el motor no inventa candidato |
| `cobertura_declarada` | Documentos y páginas declarados frente a esperados. Parcial: sin `desenlace_busqueda` no se comprueba fin de búsqueda (H2) |

**Referencia correcta:** para el conjunto sintético, el resultado esperado declarado al construir cada caso, revisado por otro integrante. Para documentación real haría falta conjunto etiquetado autorizado, definiciones clínicas y temporales validadas, criterios de anotación acordados: **no existe** y depende de la issue #7.

**Distinción obligatoria:** estas métricas miden comportamiento contra un conjunto controlado. **No son umbrales clínicos de aceptación.** La spec §7 y §8 los reserva a la tutora. No se inventa ningún «90 % de precisión».

### Resultados del motor de reglas (suelo de referencia)

El `MotorReglas` implementa once familias de reglas explícitas (indeterminada, sospecha, negación, sujeto familiar, otra persona, fechas, contradicción, ausencia, repetición, abreviaturas, evidencia entre documentos) sobre texto normalizado (minúsculas sin diacríticos). Clasifica por cláusula (segmentos separados por `.;`) no por bloque entero, para no arrastrar contexto de frases vecinas.

- Pasa `comprobar_integridad` para todas las entradas de `casos_sinteticos` (PoC anterior y nuevo catálogo).
- No usa NLP, no abre red, no descarga pesos, no usa Pydantic.
- 21 pruebas suite principal + 61 pruebas PoC contratos = 82 pruebas en verde.

### Tabla de madurez

| Enfoque | Diseñado | Probado con dobles | Evaluado con modelo real | Qué falta |
|---|---|---|---|---|
| Reglas / NLP clásico | Sí | — | Sí, sobre sintéticos | Nada para el alcance actual |
| LLM local | Sí (interfaz `MotorExtraccion`) | No | No | Hardware; el equipo no dispone de GPU |
| LLM alojado | Sí (interfaz `MotorExtraccion`) | No | No | Autorización de la entidad |
| Híbrido | Sí (interfaz `MotorExtraccion`) | No | Solo la parte de reglas | Motor real en la rama contextual |

Con la decisión «puerto + reglas», los tres enfoques con modelo quedan en **diseñado**, no en «probado con dobles». El ADR lo dice explícitamente y **no** los presenta como recomendados.

## Alcance de la publicación

- Solo material sintético en el repositorio, en las pruebas y en los ejemplos del ADR.
- Nada de historias clínicas reales, capturas, transcripciones, anotaciones con texto real, extracciones brutas, registros ni resultados con datos personales.
- Ningún envío de material clínico a servicios externos. El adaptador del LLM alojado no se implementa en esta entrega; si se implementa, solo se ejecutará sobre material sintético mientras no haya autorización de la entidad.
- Nada de credenciales en el repositorio.
- Diagnósticos seguros: códigos y motivos predefinidos, rutas de esquema conocidas y referencias opacas. Nunca trazas, mensajes de excepción ni contenido de entrada.
- `data/` está en `.gitignore` y `local_path()` rechaza rutas fuera de él. No se sortea.
- Los materiales presentados como anonimizados y sus derivados pueden contener información identificativa.

## Consecuencias

### Positivas

- Puerto estable (`MotorExtraccion`) que permite comparar familias sin cambiar el arnés ni los casos.
- Suelo de referencia honesto y ejecutable hoy (CPU, sin dependencias nuevas).
- 20 criterios evaluables cubiertos con casos sintéticos revisados.
- Límites conocidos documentados explícitamente (H1–H6, 5 criterios no evaluables).
- Métricas por dimensión que discriminan fallos clínicamente relevantes (negación convertida en afirmación no se compensa con aciertos en ausencia).

### Negativas y costes

- El motor de reglas no entiende lenguaje natural fuera del vocabulario controlado; su exactitud cae fuera de los términos declarados.
- 5 criterios no evaluables en esta entrega por limitaciones del contrato (H2, H3, H4).
- Los enfoques con modelo (que podrían generalizar mejor) quedan sin evaluar por falta de hardware y autorización.
- La métrica `cobertura_declarada` es parcial sin `desenlace_busqueda`.

### Trabajo pendiente

#### Implementación y pruebas

- Completar fases 6–12 del plan: casos evaluables (20), casos no evaluables (5), `metricas.py`, `evaluacion.py`, `test_evaluacion.py`, `tests/test_extraccion_clinica.py`.
- Ejecutar arnés completo y verificar que `MotorReglas` acierta los 20 casos evaluables.

#### ADR y arquitectura

- Incorporar resultados del arnés al ADR (fase 18).
- Actualizar `ARCHITECTURE.md` §CLI-001 con enlace al ADR y corrección de líneas 114 y 147 (fase 19).
- Actualizar `README.md` a «ocho documentos» y «Los tres ADR» (fase 20).
- Corregir documentos de trabajo (fase 21).

#### Acuerdos con la entidad

- Autorización para evaluar LLM alojado sobre material sintético (issue #7).
- Hardware GPU para LLM local (issue #7).
- Conjunto etiquetado autorizado, definiciones clínicas y temporales validadas, criterios de anotación para evaluación real (issue #7).
- Umbrales clínicos de aceptación (spec §8, issue #7).

#### Contrato clínico

- Añadir `desenlace_busqueda` a `ResultadoClinico` (H2).
- Añadir `estado_casilla` al contrato DOC→CLI (H3).
- Estructurar `temporalidad` como enumeración (prescripción/administración/antecedente) (H4).
- Verificar cita textual en el contrato (H1).
- Distinguir `CitaNoVerificada` en el arnés, no en el contrato (H5/H6).

## Referencias

- [Spec CLI-001](../specs/extraccion-datos-clinicos.md) — Estados, comportamiento, 25 criterios de aceptación
- [Contrato clínico (Pydantic)](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/formato_intermedio_poc/cli_rcp/modelo_pydantic.py) — `ResultadoClinico`, `Mencion`, `Evidencia`, `Cobertura`
- [Contrato clínico (dataclasses)](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/formato_intermedio_poc/cli_rcp/modelo_dataclasses.py) — Mismo modelo sin Pydantic
- [Casos sintéticos PoC anterior](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/formato_intermedio_poc/cli_rcp/casos_sinteticos.py) — `D1`–`D7`
- [Nuevo catálogo S1–S12](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/extraccion_clinica_poc/casos.py) — Constructores parametrizables
- [Motor de reglas](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/extraccion_clinica_poc/motores.py) — `MotorReglas`, once familias, `MOTORES`
- [Puerto del motor](https://github.com/lucasmtnz23/cu04-extraccion-clinica/blob/main/experiments/extraccion_clinica_poc/contrato.py) — `MotorExtraccion`, `EstadoEjecucion`, `NoComprobado`
- [ADR estrategia de lectura PDF](../decisions/estrategia-lectura-pdf.md) — Patrón de ADR aceptado
- [ADR formato intermedio](../decisions/formato-intermedio.md) — Pydantic v2, JSON, validadores propios
- [Arquitectura CU-04](../ARCHITECTURE.md) — Componentes, flujo, contratos, trazabilidad
- [PaddleOCR pipeline](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html) — Referencia PP-OCRv6
- [Tesseract CLI](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html) — Referencia contingencia CPU
- [PyMuPDF text extraction](https://pymupdf.readthedocs.io/en/latest/app1.html) — Referencia texto digital