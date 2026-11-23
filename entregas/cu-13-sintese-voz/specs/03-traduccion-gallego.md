# Traducción del corpus al gallego

## Qué construir

Un proceso que traduce automáticamente al gallego el corpus de textos médicos en español (spec 02). El resultado es un corpus paralelo: cada frase en gallego lleva el mismo identificador que su frase original en español. El corpus en gallego es el que leerán los modelos de síntesis para generar la parte gallega del dataset (spec 05).

**Entradas**

- El corpus de frases médicas en español, ya limpio, normalizado y validado, con sus prompts de voz.
- Un sistema de traducción automática del español al gallego (ver [ADR-002](../decisions/002-traduccion-nos-mt.md)).
- La lista de frases reservadas para la evaluación en gallego: las frases de prueba del Arena (spec 01) y, cuando exista, el texto del test real del ASR (spec 07).
- La asignación de modelos de síntesis para el gallego (sección `modelos` de `codigo/corpus/config.yaml`, ver [ADR-005](../decisions/005-modelos-por-perfil.md)).

**Salidas**

- Un corpus de frases en gallego con las mismas columnas que el corpus en español (`id`, `frase`, `prompts_voz`, `modelo`, `fuente`):
    - `id`: el mismo identificador que la frase en español (`es_NNNNN`). El idioma lo indica el corpus al que pertenece la frase y, en el dataset, la columna `idioma`.
    - `frase`: la traducción, normalizada.
    - `prompts_voz`: los dos prompts de la frase en español, adaptados al gallego. Se sustituye «from Spain speaking European Spanish» por «from Galicia speaking Galician», y el resto de la descripción se mantiene.
    - `modelo`: un modelo por prompt, asignado con la tabla del gallego de la configuración. Puede ser distinto del de la frase en español.
    - `fuente`: la misma que la frase en español.
- Un registro de descartes con las frases eliminadas y el motivo.
- Un registro del sistema de traducción usado y su versión.

**Funcionamiento**

1. Se traduce cada frase del corpus en español al gallego.
2. Se aplican a las frases traducidas las mismas reglas de limpieza y normalización que al corpus en español, con las reglas propias del gallego.
3. Se descartan:
    - las traducciones vacías;
    - las repetidas;
    - las que quedan fuera del rango de longitud;
    - las que conservan dígitos, abreviaturas o siglas sin expansión segura;
    - las que coinciden con una frase reservada en gallego o se le parecen demasiado.
4. Se copian y adaptan los prompts de voz, y se asigna el modelo de cada prompt con la tabla del gallego.
5. Se guarda el corpus en gallego, enlazado con el corpus en español mediante el identificador de cada frase.

## Por qué

El sistema se aplicará en Galicia, así que el dataset tiene que incluir audio en gallego. Sin embargo, apenas existen textos médicos en gallego. Traducir el corpus en español permite disponer de un volumen similar de frases en ambos idiomas, con el mismo contenido y vocabulario médico. Mantener el mismo identificador permite comparar ambos idiomas, localizar el origen de cualquier error de traducción y mantener juntas en el mismo lado del reparto entre entrenamiento y validación una frase y su traducción.

Conservar los prompts de voz hace que cada frase gallega la lean voces del mismo perfil que su original en español, de modo que el reparto de edades, sexos y estilos es igual en los dos idiomas.

## Restricciones

- Depende del corpus en español de la spec 02.
- Se usa el mismo sistema de traducción para todo el corpus.
- Se registra qué sistema de traducción se ha usado y su versión.
- Las frases traducidas siguen las mismas reglas de normalización que el corpus en español: números, abreviaturas y siglas escritos con palabras.
- Las frases traducidas tienen entre 3 y 30 palabras.
- Los prompts de voz solo cambian en la indicación del idioma. La edad, el sexo, el timbre y el estilo son los mismos que en español.

## Criterios de aceptación

- Cada frase en gallego tiene el mismo identificador que una frase del corpus en español, y no hay identificadores en gallego que no existan en español.
- Ninguna frase en gallego contiene dígitos.
- No hay frases duplicadas.
- Todas las frases tienen entre 3 y 30 palabras.
- Cada frase tiene sus 2 prompts de voz, idénticos a los de su frase en español salvo la indicación del idioma.
- Cada prompt de voz tiene un modelo en la columna `modelo`, asignado con la tabla del gallego.
- Ninguna frase coincide con una frase reservada en gallego ni la supera en similitud.
- Está registrado el sistema de traducción usado y su versión.
- Cada frase descartada figura en el registro de descartes con su motivo.

## Implementación

En [`codigo/corpus`](../codigo/corpus/README.md), el mismo script del castellano hace los cinco pasos con `python corpus.py gl`: traduce con NOS-MT, limpia y valida con las reglas del gallego, adapta los prompts, asigna los modelos y comprueba los criterios de aceptación. El sistema de traducción y su commit quedan en el `manifest.json` de cada versión.

Como en el castellano (spec 02), el script todavía no compara el corpus con las frases reservadas: esa comprobación se hace en C7, antes de entrenar (spec 07, paso 1).

Resultado de la primera ejecución: de 2.000 frases quedan 1.736 en gallego. Los descartes y la revisión pendiente están en el [ADR-002](../decisions/002-traduccion-nos-mt.md).
