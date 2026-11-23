# ADR-001 · Generar el corpus de textos médicos con un LLM

- **Estado:** aceptada
- **Fecha:** 2026-11
- **Afecta a:** spec 02 y spec 03 (C2 · Corpus), spec 04 (C3 · Clonación de voces) y spec 05 (C4 · Síntesis)

## Decisión

El corpus de textos médicos en español se genera **con un modelo de lenguaje (LLM)**, en 20 tandas de 100 frases (2.000 frases), cada una centrada en una especialidad médica, con el prompt versionado en [`prompts/generacion-textos-medicos-es.md`](../prompts/generacion-textos-medicos-es.md) (versión v3). Cada tanda se pide al LLM en 4 partes de 25 filas, y todas las respuestas se juntan después en **un único fichero** con el corpus entero. Los corpus médicos de la red quedan como fuente complementaria opcional, solo si su licencia lo permite.

El corpus tiene esta estructura:

```
id | frase | prompts_voz | modelo | fuente
```

- El LLM devuelve `id`, `frase` (ya normalizada, sin dígitos, abreviaturas ni siglas) y `prompts_voz`: una lista JSON con **2 descripciones de voz en inglés**, cada una con edad, sexo, timbre, ritmo y una de las tres etiquetas de estilo de la spec 05.
    - En las frases de dictado, las 2 voces son de dos franjas adultas distintas (joven, adulta o mayor), con estilos distintos, un hombre y una mujer. Las combinaciones se rotan de una fila a otra para que el corpus quede equilibrado.
    - En las frases infantiles, las 2 voces son un niño y una niña, una en lectura neutra y otra en habla rápida.
- El script de preprocesado añade `modelo` (un TTS por voz, según su franja de edad y la sección `modelos` de [`codigo/corpus/config.yaml`](../codigo/corpus/config.yaml); ADR-005) y `fuente` (desde la sección `fuente` de la misma configuración). El LLM no las rellena: no sabe qué modelo elegirá el Arena, y no queremos que se equivoque con la fuente.
- El perfil de cada voz (franja de edad y sexo) no se pide como columna aparte: se deduce del principio de cada descripción, así que no puede contradecirla.

El fichero completo pasa por el validador automático del script antes de convertirse en corpus. El LLM no es fiable al cien por cien, así que el validador decide y no el LLM.

## Motivación

1. **Dominio y registro adecuados.** Queremos frases de *dictado clínico* (anamnesis, exploración, posología, juicio clínico) y frases de pacientes. Los corpus biomédicos abiertos suelen ser artículos científicos o prospectos, con un registro escrito que no se parece al dictado.
2. **Normalización en origen.** La spec 02 exige frases sin dígitos ni siglas. En textos reales («5 mg/12 h», «EPOC», «TA 140/90») la normalización automática es la mayor fuente de errores entre audio y transcripción. Pedirla al LLM y verificarla con un validador reduce mucho ese trabajo.
3. **Control de la diversidad.** Podemos fijar el reparto por especialidad y la longitud. Con dos voces por frase y las combinaciones rotadas entre filas, el reparto de franjas de edad, sexos y estilos queda equilibrado en el conjunto del corpus, incluidas las personas mayores y los niños que pide la spec 04.
4. **Licencias y privacidad.** El texto generado no contiene datos de pacientes. Evitamos tener que comprobar licencia por licencia el uso para entrenamiento, que exige la spec 02.
5. **Menos riesgo de fuga hacia el test (spec 07).** Un texto generado a propósito no sale de las mismas fuentes que un test de habla médica real, y el prompt prohíbe usar o parafrasear frases reservadas para la evaluación. Aun así, la comprobación no la hace el validador del corpus: como el test real todavía no existe, se hace en C7 (spec 07, paso 1), con coincidencia exacta y por similitud, y las frases que coincidan se quitan del entrenamiento por `id`.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Solo corpus médicos de la red** (artículos, prospectos, guías clínicas) | Registro escrito y no de dictado, muchas cifras y siglas difíciles de normalizar, licencias heterogéneas (muchos textos clínicos no permiten redistribución) y ninguna información sobre qué voz debería leer cada frase. |
| **Frases escritas a mano por el equipo** | Imposible llegar a miles de frases variadas en el tiempo del proyecto; además, el equipo no es médico. |
| **LLM sin normalización en el prompt, normalizando después con reglas** | Duplica el trabajo: habría que construir un normalizador médico completo (dosis, fracciones, tensiones, decimales). El script mantiene una tabla de abreviaturas seguras como red de seguridad, no como paso principal. |
| **Un solo prompt de voz por frase** (versión v1 del prompt) | La mitad de audios y de voces distintas por frase. |
| **Tres prompts de voz por frase** (versión v2 del prompt) | El equipo decidió pasar a dos voces por frase. Sin embargo, las frases reales son más cortas de lo previsto (mediana de 8 palabras), y con dos voces no se llega a las 5 h por idioma (ARCHITECTURE.md, riesgo 1). Una tercera voz por frase es una de las formas de completar las horas. |
| **Catálogo cerrado de pocas voces** en lugar de una descripción por audio | Menos hablantes distintos. Se descarta a favor del diseño de voz por descripción, que el equipo dio por bueno escuchando los audios del Arena (ADR-005). |
| **Preprocesar tanda a tanda**, un fichero por parte | Más ficheros y más pasos manuales. El equipo trabaja con el corpus entero en un fichero, así que el script recibe ese fichero. |
| **Mezcla al 50 % LLM y corpus de la red** | Se mantiene como opción si el validador revela poca variedad léxica en el texto generado; no es el punto de partida. |

## Consecuencias

- **Volumen.** 2.000 frases con una mediana de 8 palabras dan, con 2 voces por frase, unas 3,5–4 h en castellano. Para llegar a 5 h hay que añadir voces por frase o generar más frases. Las horas reales se confirmarán con los primeros audios.
- **Riesgo de homogeneidad.** Los LLM tienden a repetir estructuras. Mitigación: tandas por especialidad, instrucción explícita de variedad y deduplicación. El validador informa de la diversidad léxica (proporción de bigramas distintos) para detectarlo.
- **Riesgo de errores médicos.** Una frase puede ser inverosímil clínicamente. Para entrenar un ASR importa sobre todo el vocabulario y la pronunciación; aun así, revisaremos una muestra.
- **Cada frase aparece dos veces en el dataset** (y dos más en gallego, con el mismo `id`). La división entre entrenamiento y validación se hace siempre por `id` (ADR-004, spec 07).
- **La columna `modelo` acopla el corpus con el TTS.** Si cambia la asignación de modelos (ADR-005), se genera una versión nueva del corpus con la columna actualizada; las frases y las voces no cambian.
- **Una sola fuente por corpus.** Todo el fichero se registra con un único LLM y versión. Si se usaran varios, habría que separarlos en ficheros distintos o ampliar el registro.
- **Reproducibilidad.** La salida de un LLM no es determinista. Por eso no se regenera: el corpus validado se guarda versionado (`data/corpus/es/v001`…), con una copia exacta del fichero de entrada. En la configuración se registran el modelo, la versión exacta, la fecha y la versión del prompt.

## Referencias

- Prompt de generación, plan de tandas y comprobaciones: [`prompts/generacion-textos-medicos-es.md`](../prompts/generacion-textos-medicos-es.md).
- Reglas de validación: spec [02](../specs/02-corpus-textos-medicos.md).
- Implementación del validador y del preprocesado: [`codigo/corpus/corpus.py`](../codigo/corpus/README.md), con sus pruebas (`test_corpus.py`) y su README.


