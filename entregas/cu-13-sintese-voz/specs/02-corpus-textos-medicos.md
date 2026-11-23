# Corpus de textos médicos en español

## Qué construir

Un proceso que reúne frases médicas en español, las valida y las prepara para que puedan sintetizarse. Cada frase lleva dos descripciones de la voz que debe leerla y, para cada una, el modelo de síntesis con el que se leerá. El resultado es el corpus que se traducirá al gallego (spec 03) y que leerán los modelos de síntesis para generar el dataset (spec 05).

**Entradas**

- Un único fichero con todas las frases médicas en español, de una de estas dos fuentes o de ambas:
    - Fuente principal: textos generados con un modelo de lenguaje (LLM) mediante el prompt versionado [`prompts/generacion-textos-medicos-es.md`](../prompts/generacion-textos-medicos-es.md) (ver [ADR-001](../decisions/001-corpus-generado-con-llm.md)). Aunque el LLM las genere por partes, todas sus respuestas se reúnen en ese fichero.
    - Fuente complementaria opcional: corpus de texto médico disponibles en la red, solo si su licencia lo permite.
- La lista de frases reservadas para la evaluación: las frases de prueba del Arena (spec 01) y, cuando exista, el texto del conjunto de test real del ASR (spec 07).
- La asignación de modelos de síntesis por idioma y franja de edad (sección `modelos` de `codigo/corpus/config.yaml`, ver [ADR-005](../decisions/005-modelos-por-perfil.md)).

**Salidas**

- Un corpus con una fila por frase y estas columnas:

| Columna | Contenido |
| --- | --- |
| `id` | Identificador único con el formato `es_NNNNN`. |
| `frase` | La frase escrita tal como se pronuncia. |
| `prompts_voz` | Lista de exactamente 2 descripciones de voz en inglés. Cada una indica edad, sexo, timbre, ritmo y estilo de habla, y se sintetiza por separado. |
| `modelo` | Lista con el nombre del modelo de síntesis de cada prompt, en el mismo orden que `prompts_voz` (por ejemplo, `["omnivoice", "nos"]`). El repositorio y la revisión de cada modelo están en la copia de la tabla de modelos que se guarda con cada versión del corpus. Se asigna según la franja de edad de cada prompt y las proporciones de la configuración. |
| `fuente` | De dónde procede la frase: el LLM, su versión y la versión del prompt, o el corpus de la red. |

- Un registro de fuentes:
    - para cada corpus de la red, su nombre, su dirección de descarga y su licencia;
    - para el texto generado con un LLM, el nombre y la versión exacta del modelo, la fecha y la versión del prompt.
- Un registro de descartes con cada frase rechazada y el motivo.
- Una copia exacta del fichero de entrada, para poder rehacer la versión.

**Funcionamiento**

1. Se reúnen las frases en un único fichero: las generadas con el LLM y, opcionalmente, las de corpus de la red.
2. Se leen las filas del fichero (`id`, `frase`, `prompts_voz`). Los textos de la red se dividen antes en frases y reciben sus propios prompts.
3. Se limpian: se eliminan referencias bibliográficas, tablas, direcciones web y caracteres extraños.
4. Se normalizan: los números, las abreviaturas y las siglas se escriben con palabras, tal como se leen. Por ejemplo, «5 mg» pasa a «cinco miligramos». Las abreviaturas que tienen una expansión segura en la tabla del normalizador se expanden solas. Las frases con abreviaturas o siglas que no figuran en la tabla se descartan.
5. Se descartan:
    - las frases demasiado cortas o demasiado largas;
    - las repetidas;
    - las que coinciden con una frase reservada para la evaluación o se le parecen demasiado;
    - las filas cuyos prompts de voz no cumplen las reglas.
6. Se añaden las columnas `modelo` y `fuente`:
    - `modelo`: un modelo por prompt, según su franja de edad y las proporciones de la configuración. El reparto es exacto y sale igual con la misma semilla.
    - `fuente`: desde el registro de fuentes.
7. Se guarda el corpus junto al registro de fuentes, al de descartes y a la copia de la entrada.

**Reglas de los prompts de voz**

- Cada prompt empieza indicando la edad en años y el sexo («A 52-year-old man from Spain speaking European Spanish.»). También se aceptan «An» y «elderly» delante del sexo («An 80-year-old elderly woman …»), como en el corpus inicial. De ahí se deducen el perfil de la voz y su franja de edad: infantil (6–11), joven (20–35), adulta (40–60) y persona mayor (65–85).
- Cada prompt termina con uno de los tres estilos de habla de la spec 05: `neutral reading` (lectura neutra), `dictation` (dictado) o `fast speech` (habla rápida).
- Frases de dictado clínico:
    - las dos voces son de franjas adultas distintas (dos de entre joven, adulta y persona mayor);
    - cada voz tiene un estilo distinto;
    - una voz es de hombre y la otra de mujer.
- Frases infantiles:
    - las dos voces son infantiles: un niño y una niña;
    - una usa lectura neutra y la otra habla rápida.
- En el conjunto del corpus, las franjas y los estilos de las frases de dictado quedan repartidos de forma parecida (lo ideal es un tercio cada uno). Con dos voces por frase no caben las tres franjas en la misma fila, así que el equilibrio se consigue rotando las combinaciones de una fila a otra. Se avisa si alguna franja o algún estilo queda por debajo del 25 % de los prompts de dictado.

## Por qué

Los modelos de síntesis leen exactamente el texto que reciben. Si el texto contiene abreviaturas, cifras o restos de formato, el modelo puede pronunciarlos mal, y la transcripción del audio dejaría de coincidir con lo que realmente se oye. Un corpus limpio y normalizado garantiza que cada audio del dataset tenga una transcripción exacta. Usar textos médicos hace que el vocabulario del dataset sea el que encontrará después el reconocedor de voz.

Las dos descripciones de voz por frase hacen que cada frase la lean dos personas distintas, de edades, sexos y estilos variados. Así se multiplica el volumen de audio sin escribir más frases y se cubren perfiles poco representados, como las personas mayores y los niños.

Las frases reservadas se excluyen también cuando solo se parecen, no únicamente cuando son idénticas. Si una casi igual entrara en el entrenamiento, el ASR la habría «visto» antes del test y el resultado saldría mejor de lo que es.

## Restricciones

- Los corpus de la red solo se usan si su licencia permite este uso.
- Para cada frase se registra si procede de un corpus de la red, indicando cuál, o de un LLM, indicando qué modelo la generó y con qué versión del prompt.
- Las frases tienen entre 3 y 30 palabras.
- No hay frases duplicadas.
- Todas las frases siguen las mismas reglas de normalización: números, abreviaturas y siglas escritos con palabras. La única cifra permitida en toda la fila es la edad dentro de los prompts de voz.
- Ninguna frase coincide con una frase reservada para la evaluación ni se le parece por encima del umbral de similitud. El umbral es configurable y se registra; el valor inicial propuesto es 0,8 de similitud de caracteres.
- Las filas que no pasan la validación no se corrigen a mano: se descartan y se registran con su motivo. Para recuperar un identificador descartado se añade al final del fichero una fila nueva generada con el LLM.

## Criterios de aceptación

- Ninguna frase contiene dígitos.
- No hay frases duplicadas.
- Todas las frases tienen entre 3 y 30 palabras.
- Cada frase tiene un identificador único con el formato `es_NNNNN` y su fuente.
- Cada frase tiene exactamente 2 prompts de voz distintos que cumplen las reglas de los prompts de voz.
- Cada prompt de voz tiene un modelo en la columna `modelo`, y en cada franja el reparto entre modelos es el de la configuración.
- Ninguna frase coincide con una frase reservada para la evaluación ni la supera en similitud.
- Cada fuente que aparece en el corpus figura en el registro de fuentes.
- Cada corpus de la red del registro tiene anotada su licencia, y esa licencia permite el uso con fines de entrenamiento.
- Cada frase descartada figura en el registro de descartes con su motivo.

## Estado de la implementación

El script [`codigo/corpus/corpus.py`](../codigo/corpus/README.md) cumple todos los criterios salvo el de las frases reservadas: todavía no compara el corpus con ellas, porque el test real del ASR no existe. Mientras tanto, esa comprobación se hace en C7, antes de entrenar (spec 07, paso 1), con el mismo umbral, y las frases que coincidan se quitan del entrenamiento por `id` ([ARCHITECTURE.md](../ARCHITECTURE.md), C2 y C7).
