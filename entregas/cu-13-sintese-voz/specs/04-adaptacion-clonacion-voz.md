# Adaptación y clonación de voz

*Revisada el 2026-11-19: se elimina la prueba de percepción formal (5 voces por perfil y modelo, 3 evaluadores a ciegas). Los perfiles quedan validados por la escucha del equipo durante el Arena y las pruebas de los modelos, y se vigilan durante la generación con el CER por perfil y modelo de la revisión con ASR (spec 05). Que cada perfil suene a su edad es, por tanto, una valoración del equipo y no un resultado medido. Si la clonación de la persona mayor sale bien, también se usa en gallego ([ADR-006](../decisions/006-chatterbox-mayor-gallego.md)).*

## Qué construir

Un proceso para obtener voces sintéticas que cubran perfiles de hablantes variados, incluidos los que suelen faltar en los modelos (personas mayores y niños). Se puede hacer de tres formas, según lo que admita el modelo asignado a cada idioma y perfil:

- **Adaptación mediante prompt (diseño de voz), método principal.** El modelo recibe una descripción de la voz y habla de esa forma. Por ejemplo: «A 78-year-old woman from Spain speaking European Spanish. She has a soft, slightly trembling voice…». Las descripciones son los `prompts_voz` del corpus (specs 02 y 03): cada frase lleva dos, y cada prompt se sintetiza directamente, de modo que cada audio del dataset tiene su propio hablante.
- **Clonación.** El modelo imita una voz a partir de una grabación corta de referencia. Se usa para la persona mayor en castellano, porque en la escucha del equipo ningún modelo genera bien esa voz a partir de una descripción. Si sale bien, también se usa para la persona mayor en gallego (ADR-006).
- **Voz fija, complemento.** Modelos con un catálogo cerrado de voces que no aceptan descripciones (NOS, supertonic). Se usan para dar variabilidad, como el acento gallego de NOS en castellano. Del prompt solo se aprovechan el sexo, para elegir la voz, y el estilo.

**Perfiles**

Un perfil combina franja de edad y sexo, y se deduce del principio de cada prompt de voz. Hay 8 perfiles por idioma: infantil (6–11 años), joven (20–35), adulta (40–60) y persona mayor (65–85), cada uno en hombre y en mujer (niño y niña en la franja infantil).

**Método por idioma y franja ([ADR-005](../decisions/005-modelos-por-perfil.md) y [ADR-006](../decisions/006-chatterbox-mayor-gallego.md))**

| Idioma | Infantil | Joven | Adulta | Persona mayor |
| --- | --- | --- | --- | --- |
| Castellano | Diseño (OmniVoice) | Diseño (OmniVoice) | Diseño (OmniVoice, 45 %) y voz fija (NOS, 45 %; supertonic 3, 10 %) | Clonación (Chatterbox Multilingual V3) |
| Gallego | Diseño (OmniVoice) | Diseño (OmniVoice) | Diseño (OmniVoice, 25 %) y voz fija (NOS, 75 %) | Clonación (Chatterbox Multilingual V3) si la clonación en castellano sale bien; si no, diseño (OmniVoice) |

Esta asignación se hizo con la escucha del equipo durante el Arena y las pruebas de los modelos, y es la que da por validados los perfiles ([ADR-005](../decisions/005-modelos-por-perfil.md)). Está en `codigo/corpus/config.yaml` (sección `modelos`).

**Persona mayor en gallego con Chatterbox ([ADR-006](../decisions/006-chatterbox-mayor-gallego.md))**

- Chatterbox **no admite oficialmente el gallego**. El equipo acepta que se pronuncie algo peor a cambio de cubrir bien el perfil de voz. No hay evidencia de que su gallego sirva para entrenar un ASR: es una hipótesis.
- Las voces del gallego son voces clonadas propias (`gl_mayor_*`). Si se consiguen, las referencias deberían ser de personas mayores que hablen gallego; si no, se usan las mismas referencias que en castellano.
- Si el modelo pide el idioma del texto, se prueba el gallego con el código del castellano y con el del portugués, y se elige el que suene mejor y dé menos CER en el control de calidad.

**Referencias para clonar la voz de persona mayor**

- En principio, grabaciones reales de personas mayores con su consentimiento (en castellano y, si se puede, en gallego).
- En paralelo se prueba si sirven como referencia voces de persona mayor diseñadas con un modelo de diseño de voz. Es lo que se hizo en el Arena, donde Chatterbox clonó una voz diseñada con Qwen3-TTS VoiceDesign.
- El equipo escucha las voces clonadas de las dos opciones y elige cuáles se usan.

**Entradas**

- `codigo/corpus/config.yaml` (sección `modelos`), con el modelo y el método de cada idioma y franja.
- Para la clonación: grabaciones de referencia de personas mayores (hombre y mujer), con su transcripción y el consentimiento de la persona, o voces diseñadas que hagan de referencia.

**Salidas**

- Un catálogo de voces clonadas que indica, para cada una, su idioma, su perfil, el modelo con el que se creó y con el que se sintetiza, la grabación de referencia, los parámetros usados y, en gallego, el código de idioma con el que se pide.
- Las grabaciones de referencia y, si son reales, su consentimiento.

**Funcionamiento**

1. Se reúnen las referencias de persona mayor, de hombre y de mujer: grabaciones reales con consentimiento y, en paralelo, voces diseñadas.
2. Se crea una voz clonada por cada referencia con Chatterbox Multilingual V3, con semilla y parámetros fijos.
3. El equipo escucha cada voz clonada en castellano con unas frases de prueba del Arena y descarta las que no suenen a persona mayor o tengan artefactos.
4. Si queda al menos una voz de hombre y otra de mujer en castellano, se crean las voces del gallego y se escuchan con las frases de prueba del Arena en gallego, probando los códigos de idioma. Si se dan por buenas, se cambia `asignacion.gl.mayor` a `chatterbox-mv3` en `config.yaml` y se genera una versión nueva del corpus gallego. Si no, el gallego sigue con OmniVoice.
5. Las voces que se quedan se registran en el catálogo de voces clonadas.

## Por qué

Los modelos de síntesis suelen ofrecer pocas voces, normalmente de adultos de mediana edad grabados en estudio. Un reconocedor de voz entrenado solo con esas voces puede funcionar peor con personas cuya voz es distinta, como las personas mayores, que son una parte importante de los usuarios del ámbito sanitario. Diseñar una voz distinta para cada prompt da miles de hablantes diferentes y hace que el dataset sea mucho más diverso que con un catálogo de unas pocas voces. Para la persona mayor, donde el diseño no da buen resultado, la clonación permite cubrir el perfil, también en gallego aunque se pronuncie algo peor.

## Restricciones

- Depende de la asignación de modelos por idioma y franja de edad ([ADR-005](../decisions/005-modelos-por-perfil.md), [ADR-006](../decisions/006-chatterbox-mayor-gallego.md)), que se refleja en la columna `modelo` de los corpus (specs 02 y 03).
- Si el equipo decide cambiar el modelo de un perfil, se cambia la asignación en `config.yaml` y se genera una versión nueva del corpus.
- Una voz clonada se sintetiza siempre con el modelo con el que se creó.
- Cada voz pertenece a un solo idioma.
- Las grabaciones reales solo se usan con el consentimiento de la persona.

## Criterios de aceptación

- Cada perfil de cada idioma tiene asignados su método y su modelo o modelos en `config.yaml`.
- Hay al menos una voz clonada de persona mayor en castellano de hombre y otra de mujer.
- Si la persona mayor en gallego usa Chatterbox, hay al menos una voz clonada de persona mayor en gallego de hombre y otra de mujer.
- Cada voz clonada figura en el catálogo con su idioma, perfil, modelo, grabación de referencia y parámetros (y, en gallego, el código de idioma usado).
