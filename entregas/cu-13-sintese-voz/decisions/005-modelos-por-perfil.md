# ADR-005 · Modelos TTS por idioma y perfil de voz

- **Estado:** aceptada; modificada por [ADR-006](006-chatterbox-mayor-gallego.md)
- **Fecha:** 2026-11-18
- **Afecta a:** spec 01 (resultado del Arena), specs 02 y 03 (columna `modelo`), spec 04 (método por perfil) y spec 05 (generación); componentes C1, C2, C3 y C4

> Los perfiles de esta tabla se dan por validados con la escucha del equipo durante el Arena y las pruebas de los modelos; la spec 04 ya no incluye una prueba de percepción formal. Durante la generación se vigilan con el CER por perfil y modelo de la revisión con ASR (C5a). El [ADR-006](006-chatterbox-mayor-gallego.md) cambia la persona mayor en gallego: si la clonación con Chatterbox sale bien en castellano, el gallego también usa Chatterbox; si no, sigue con OmniVoice, como dice este ADR.

## Decisión

Cada prompt de voz se sintetiza con un modelo que depende de su **idioma** y de su **franja de edad**. Si una franja tiene varios modelos, sus prompts se reparten entre ellos con estas proporciones:

| Idioma | Infantil | Joven | Adulta | Persona mayor |
| --- | --- | --- | --- | --- |
| **Castellano** | OmniVoice | OmniVoice | 45 % OmniVoice · 45 % NOS · 10 % supertonic 3 | Chatterbox Multilingual V3 (clonación) |
| **Gallego** | OmniVoice | OmniVoice | 25 % OmniVoice · 75 % NOS | OmniVoice (Chatterbox si se cumple la condición del ADR-006) |

- La tabla está en [`codigo/corpus/config.yaml`](../codigo/corpus/config.yaml) (sección `modelos`), junto con el repositorio, la revisión, el método y la licencia de cada modelo. La usan el script del corpus (C2), la clonación (C3) y los scripts de síntesis (C4).
- La columna `modelo` del corpus pasa a ser una **lista con el modelo de cada prompt**, en el mismo orden que `prompts_voz`. La rellena el script del corpus y lleva solo el nombre de cada modelo (`omnivoice`, `nos`…); el repositorio y la revisión están en la copia de la tabla que se guarda con cada versión del corpus.
- **Reparto:**
    - Es exacto: con 20 prompts de voz adulta en castellano salen 9 de OmniVoice, 9 de NOS y 2 de supertonic.
    - Se hace por perfil (franja y sexo), así que cada modelo recibe la misma proporción de hombres y de mujeres.
    - El orden lo fija un hash de la semilla, el idioma, el `id` de la frase y la posición del prompt. Con las mismas entradas, la asignación es siempre la misma.
- Las proporciones se aplican al **número de prompts**, no a las horas.
- Los audios de NOS y supertonic **sustituyen** a una parte de los de OmniVoice. Cada frase sigue teniendo 2 audios por idioma.

**Método de cada modelo** (spec 04):

| Modelo | Método | Qué aprovecha del prompt de voz |
| --- | --- | --- |
| OmniVoice | Diseño de voz | Todo: edad, sexo, timbre, ritmo y estilo. |
| Chatterbox Multilingual V3 | Clonación | El sexo, para elegir la voz clonada, y el estilo. |
| NOS | Voz fija | El sexo (una voz de hombre o una de mujer) y el estilo, que se traduce a velocidad. |
| supertonic 3 | Voz fija | El sexo (voces F1–F5 de mujer y M1–M5 de hombre) y el estilo, que se traduce a velocidad. |

**Referencias para clonar la voz de persona mayor en castellano:**
- En principio, grabaciones reales de personas mayores, con su transcripción y su consentimiento (spec 04).
- En paralelo se probará si sirven como referencia voces de persona mayor diseñadas con un modelo de diseño de voz. Es lo que se hizo en el Arena: Chatterbox clonó una voz diseñada con Qwen3-TTS VoiceDesign (`audios/CASTELLANO/QWEEN-TTS-voice-design/VOZ PERSONA MAYOR/p02_es.wav`).
- El equipo escucha las voces clonadas de las dos opciones y elige cuáles se usan (spec 04).

## Motivación

1. **Castellano: OmniVoice gana el Arena.** En la clasificación del Arena (5 ficheros de votos) ganó en los cuatro perfiles: 89,2 % de victorias en total, 96,0 % en voz adulta, 89,5 % en joven, 88,9 % en infantil y 75,0 % en persona mayor.
2. **NOS en la voz adulta en castellano.** En la escucha, el equipo ve que tiene bastante acento gallego, y eso da variabilidad. Que esto ayude al ASR con hablantes reales de Galicia es una **hipótesis**: se puede medir en la spec 07 con un experimento con y sin NOS.
3. **supertonic 3.** Unos pocos audios de voz adulta en castellano, para añadir variedad de modelo.
4. **Chatterbox para la persona mayor en castellano.** En la escucha del equipo, ningún modelo genera bien una voz de persona mayor a partir de una descripción, así que la mejor opción es clonar una voz.
    - El Arena apunta en la misma dirección. La persona mayor es el perfil en el que OmniVoice, el ganador, saca peor resultado: un 75,0 % de victorias, frente al 89–96 % de los demás perfiles. También es el perfil con más abstenciones: 19 de los 31 votos de sus parejas.
    - Chatterbox Multilingual V3 es el modelo de clonación que se probó en el Arena. No aparece en la clasificación, que solo incluye OmniVoice y las dos variantes de Qwen3-TTS.
    - En gallego, Chatterbox no admite oficialmente el idioma, así que la persona mayor gallega se quedó con OmniVoice. El ADR-006 cambia esto si la clonación sale bien en castellano.
5. **Gallego sin votación.** En la escucha del equipo, OmniVoice y NOS son los únicos modelos que hablan gallego de verdad; los demás que dicen admitirlo suenan a portugués. Con solo dos modelos válidos, el Arena no habría cambiado la elección, así que se usan los dos directamente. Es una desviación de la spec 01, que se ha actualizado para recogerla.
6. **Proporciones: calidad frente a variabilidad.** El equipo fijó las proporciones ponderando dos cosas: la calidad de los audios de cada modelo en la escucha y la variabilidad que aporta tener varios modelos en un mismo perfil.
    - Un modelo de más calidad lleva más peso, porque un audio que suena mal enseña poco al ASR y tiene más probabilidades de rechazarse en la revisión con ASR.
    - Una parte del perfil se reserva a otros modelos, aunque suenen algo peor, porque cada modelo tiene su propia prosodia, timbre y acento, y un ASR entrenado con un solo modelo puede aprender sus particularidades en lugar del habla.
    - En castellano, por eso OmniVoice, el mejor del Arena, sigue con una parte grande; NOS lleva otra igual por la variabilidad de su acento gallego, y supertonic se queda con una parte pequeña.
    - En gallego, NOS lleva la mayor parte de la voz adulta: es un modelo entrenado específicamente para el gallego por Proxecto Nós y es, con OmniVoice, uno de los dos modelos que el equipo considera que hablan gallego de verdad.
    - Las cifras concretas son una valoración del equipo, no el resultado de una medida. Se revisarán con la primera ejecución, a la vista del CER y de los descartes de la revisión con ASR (C5a) por modelo.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Un solo modelo por idioma** (diseño anterior, con un único valor en la columna `modelo`) | Se pierden la clonación para la persona mayor y la variabilidad de NOS y supertonic. |
| **Reparto a partes iguales entre los modelos de un perfil** | Daría el mismo peso a modelos que suenan peor, con más audios de baja calidad y más rechazos en la revisión con ASR. |
| **Audios de NOS y supertonic añadidos a los de OmniVoice** | Las frases dejarían de tener 2 audios cada una y unas pesarían más que otras en el dataset. El equipo prefirió sustituir una parte. |
| **Arena también en gallego** | Solo dos modelos hablan gallego de verdad, así que la votación no habría cambiado nada. |
| **Asignar el modelo en los scripts de síntesis (C4) y no en el corpus** | Sería igual de reproducible, pero el corpus dejaría de decir con qué se sintetiza cada prompt. |
| **Validar los perfiles con una prueba de percepción formal a ciegas** (5 voces por perfil y modelo, 3 evaluadores) | Se planteó en la spec 04 y se eliminó: el equipo ya había escuchado todos los perfiles en el Arena y en las pruebas, y no se esperaba que cambiara la asignación. El coste es que la validación de los perfiles es subjetiva (ARCHITECTURE.md, riesgo 10). |

## Licencias

| Modelo | Licencia de los pesos | Uso comercial | Clonación | Castellano | Gallego |
| --- | --- | --- | --- | --- | --- |
| OmniVoice (k2-fsa) | CC-BY-NC según el texto de la ficha (por los datos de entrenamiento, como Emilia); el código es Apache 2.0. Los metadatos de la ficha indican `apache-2.0`, así que nos quedamos con la lectura más restrictiva | No según la licencia; el equipo confirma que tiene autorización para este uso | Sí | Sí | Sí, según la escucha del equipo; la ficha dice cubrir más de 600 idiomas |
| Chatterbox Multilingual V3 (Resemble AI) | MIT | Sí | Sí | Sí | No figura entre sus idiomas |
| NOS (Proxecto Nós) | Apache 2.0 en las voces publicadas; datos de entrenamiento CC-BY 4.0 | Sí | No (voces fijas) | Con acento gallego | Sí |
| supertonic 3 (Supertone) | BigScience Open RAIL-M; el código es MIT | Sí, con restricciones de uso (por ejemplo, declarar que el audio es sintético) | No (voces fijas) | Sí | No figura entre sus idiomas |

**NOS solo tiene dos voces utilizables**, una de hombre y otra de mujer (lo confirma el equipo). Falta anotar en la configuración el repositorio y la revisión exactos de cada una, porque en el Arena la carpeta solo dice `NOS/hombre` y `NOS/mujer`.

## Consecuencias

- **Licencia de OmniVoice.** Es el modelo principal en los dos idiomas y, según el texto de su ficha, sus pesos son de uso no comercial. El equipo confirma que tiene autorización para este uso. Conviene guardar esa autorización por escrito junto a la documentación del proyecto.
- **Pocos hablantes en las voces fijas.** Estimación con el corpus previsto: 2.000 frases, 80 % de dictado, con las franjas de edad repartidas por tercios.
    - En gallego, unos 800 audios de voz adulta tendrían solo 2 hablantes, los de NOS. En castellano serían unos 480.
    - supertonic aportaría unos 110 audios repartidos entre 10 voces.
    - El resumen del dataset dará las horas por modelo y por voz para vigilarlo.
- **Las voces fijas no respetan la edad del prompt.** `perfil_voz` sale del prompt, pero con una voz fija la edad que se oye es la de la voz del catálogo. Como solo se usan en la voz adulta, se da por bueno que sus voces suenan adultas.
- **supertonic ya no tiene mantenimiento.** Supertone ha cerrado el proyecto abierto. Hay que guardar una copia de los pesos de la revisión que se use.
- **Clonar una voz sintética es una hipótesis.** Usar como referencia una voz diseñada puede acumular artefactos de dos modelos. Lo dirán la escucha del equipo y el CER de la revisión con ASR (C5a) por modelo.
- **Cambios en el código.**
    - El script del corpus pasa a la versión 1.2.0: lee la sección `modelos` de la configuración, asigna los modelos, guarda una copia de la tabla en cada versión del corpus y avisa de las revisiones sin fijar (`por_fijar`).
    - `modelo_tts` desaparece de la configuración del corpus.
    - Si cambia la tabla, se genera una versión nueva del corpus; las frases y los prompts no cambian.

## Referencias

- Clasificación del Arena: `ranking_general.csv` y `ranking_por_perfil.csv`.
- OmniVoice, ficha y licencia: <https://huggingface.co/k2-fsa/OmniVoice> · artículo: <https://arxiv.org/abs/2604.00688>
- Chatterbox Multilingual V3, ficha (licencia MIT y lista de idiomas): <https://huggingface.co/ResembleAI/chatterbox>
- Proxecto Nós, Celtia: <https://huggingface.co/proxectonos/Nos_TTS-celtia-vits-graphemes> · Sabela: <https://huggingface.co/proxectonos/Nos_TTS-sabela-vits-phonemes>
- HiTZ, voces gallegas (Brais, Iago, Paulo…): <https://huggingface.co/HiTZ/TTS-gl_iago>
- supertonic 3, copia literal de los pesos con su licencia, la lista de idiomas (con `es` y sin `gl`) y el aviso de cierre del proyecto: <https://huggingface.co/jiangzhuo9357/supertonic-3>
