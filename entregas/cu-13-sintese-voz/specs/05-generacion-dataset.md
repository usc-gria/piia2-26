# Generación del dataset sintético

## Qué construir

Un proceso que sintetiza los corpus de textos médicos en español (spec 02) y en gallego (spec 03). Cada frase se sintetiza una vez por cada uno de sus dos prompts de voz, con el modelo que la columna `modelo` de su corpus asigna a ese prompt, y el resultado se guarda como un dataset de al menos 5 horas de audio por idioma con su transcripción, listo para entrenar un reconocedor de voz. Con el corpus actual (2.000 frases con una mediana de 8 palabras) salen unas 3,5–4 h en castellano, así que hará falta añadir voces por frase, réplicas o más frases (ARCHITECTURE.md, riesgo 1). Es el producto principal del proyecto: opcionalmente, la spec 06 le añade ruido y la spec 07 lo usa para entrenar un ASR.

**Estilos de habla**

Se contemplan tres estilos, pensados para el dictado clínico. Cada prompt de voz del corpus termina con la etiqueta de uno de ellos:

- **Lectura neutra** (`neutral reading`): ritmo y entonación normales, como al leer un texto en voz alta.
- **Dictado** (`dictation`): ritmo pausado y pronunciación cuidada, como al dictar un informe.
- **Habla rápida** (`fast speech`): ritmo más rápido de lo normal, como al dictar con prisa.

Si el modelo admite instrucciones, el estilo se pide dentro del propio prompt. Si no, se traduce a sus propios parámetros, por ejemplo la velocidad.

**Entradas**

- Los corpus de frases en español y en gallego, con sus prompts de voz y su modelo.
- El resultado de la spec 04: el método de cada idioma y perfil (diseño, voz fija o clonación) y, si las hay, las voces clonadas.
- Una configuración de la generación: semilla, parámetros de síntesis y reglas de equilibrado de horas.

**Salidas**

- Un fichero de audio por cada prompt sintetizado.
- Un fichero de metadatos con una fila por audio, con estos campos:
    - identificador del audio y de la frase, y transcripción;
    - idioma, voz (frase y número de prompt), prompt de voz, perfil de la voz y estilo de habla;
    - modelo, semilla, réplica y duración.
- Un resumen del dataset: número de audios y horas totales por idioma, perfil, estilo y modelo, y número de voces distintas por modelo.
- Un registro de los audios descartados por el control de calidad, con el motivo.

**Funcionamiento**

1. Se lee la configuración de la generación.
2. Para cada frase de cada corpus se crea un trabajo de síntesis por cada uno de sus dos prompts de voz. La voz depende del método de su modelo (spec 04 y [ADR-005](../decisions/005-modelos-por-perfil.md)):
    - con diseño de voz, se usa el prompt;
    - con voz fija, se elige una voz del mismo sexo del catálogo del modelo;
    - con clonación, se asigna una voz clonada de ese perfil.

    Las voces fijas y las clonadas se reparten de forma equilibrada.
3. Se sintetiza el audio con el modelo que la columna `modelo` asigna a ese prompt.
4. Se comprueba la calidad del audio. Se transcribe con un ASR de referencia y se compara con la frase, y se revisan su duración, silencios y saturación. Si no supera el control, se vuelve a sintetizar con otra semilla (dos veces como máximo). Si sigue fallando, se descarta y se registra el motivo.
5. Se guarda el audio y se añade su fila al fichero de metadatos.
6. Se comparan las horas de cada idioma. Si el gallego tiene menos horas, se sintetizan réplicas de frases gallegas con sus mismos prompts y una semilla nueva hasta igualarlas. Cada réplica produce un hablante distinto con la misma descripción.
7. Al terminar, se calcula el resumen del dataset.
8. Se guarda la configuración usada junto al dataset, con una versión que lo identifique.

## Por qué

Un reconocedor de voz necesita muchas horas de audio con su transcripción exacta, y en el ámbito médico, sobre todo en gallego, esas grabaciones apenas existen. La síntesis permite producirlas a partir de texto. Sintetizar cada frase con dos voces de edades, sexos y estilos distintos evita que el reconocedor aprenda solo una forma de hablar. El control de calidad evita que entren en el dataset audios que no dicen exactamente lo que pone su transcripción. Guardar la configuración y los metadatos hace posible repetir la generación, aumentar el volumen con nuevas ejecuciones y saber exactamente cómo se obtuvo cada audio.

## Restricciones

- Depende de las specs 01, 02, 03 y 04.
- La transcripción de cada audio es exactamente la frase del corpus que se sintetizó.
- Cada audio se sintetiza con el modelo que la columna `modelo` de su corpus asigna a su prompt. Una voz clonada se sintetiza siempre con el modelo con el que se creó, que es el asignado a su perfil.
- Todos los audios se guardan en el mismo formato (ver [ADR-004](../decisions/004-formato-dataset.md)).
- Cada frase se sintetiza en el idioma de su corpus.
- El volumen de audio es el mismo en español y en gallego. Como la traducción (spec 03) puede descartar frases, el corpus gallego puede quedar más corto. Las horas se igualan con réplicas de las frases gallegas, nunca recortando el español por debajo del mínimo.
- Un estilo solo se genera con modelos que permiten producirlo.
- Cada ejecución genera una versión nueva del dataset sin sobrescribir las anteriores.

## Criterios de aceptación

- El dataset contiene al menos 5 horas de audio en español y al menos 5 en gallego.
- La diferencia de horas entre los dos idiomas es como máximo del 5 %.
- Cada audio tiene una fila en el fichero de metadatos, y cada fila tiene su audio.
- La transcripción de cada audio es idéntica, carácter a carácter, a la frase del corpus con su mismo identificador de frase e idioma.
- Cada prompt de voz de cada frase de los corpus tiene al menos un audio en el dataset o figura en el registro de descartes.
- Ningún audio del dataset supera los umbrales del control de calidad, y cada audio descartado figura en el registro de descartes con su motivo.
- Cada audio tiene uno de los tres estilos de habla definidos, y cada estilo aparece en los dos idiomas.
- Todos los audios están en el mismo formato.
- El modelo que figura en los metadatos de cada audio es el que la columna `modelo` de su corpus asigna a su prompt.
- El resumen indica el número de audios y las horas por idioma, perfil, estilo y modelo.
- El dataset incluye la configuración con la que se generó.
