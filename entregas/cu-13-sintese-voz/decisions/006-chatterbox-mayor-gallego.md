# ADR-006 · Chatterbox para la persona mayor en gallego, si la clonación sale bien

- **Estado:** aceptada (condicional)
- **Fecha:** 2026-11-19
- **Afecta a:** ADR-005 (asignación de la persona mayor en gallego), spec 04, spec 05; componentes C2 · Corpus, C3 · Clonación de voces y C4 · Síntesis; tabla de modelos (sección `modelos` de `codigo/corpus/config.yaml`)

## Decisión

Si la clonación de la voz de persona mayor en castellano con Chatterbox Multilingual V3 sale bien (spec 04), **la persona mayor en gallego también se sintetiza con Chatterbox**, con voces clonadas, en lugar de con OmniVoice.

- **Condición:** que el equipo dé por buenas al menos una voz clonada de hombre y otra de mujer de persona mayor en castellano (spec 04).
- **Si se cumple:** en la tabla de modelos se cambia la persona mayor del gallego de OmniVoice a Chatterbox, y se genera una versión nueva del corpus gallego. Las frases y las descripciones de voz no cambian.
- **Si no se cumple:** la persona mayor en gallego sigue con OmniVoice (ADR-005).
- **Voces:** se crean voces clonadas propias del gallego, porque cada voz pertenece a un solo idioma (spec 04). Parten de las grabaciones de personas mayores que hablan gallego, que el equipo ya tiene con su consentimiento.

## Motivación

El equipo prefiere cubrir bien el perfil de voz de persona mayor, aunque el gallego se pronuncie algo peor. Según la escucha del equipo, OmniVoice no genera una voz que suene claramente a persona mayor a partir de una descripción (ADR-005, punto 4), y es un perfil importante en el ámbito sanitario.

## Lo que no está demostrado

- **Chatterbox no admite el gallego.** El gallego no está entre los idiomas de su ficha (ADR-005). No hay evidencia de que pronuncie bien el gallego: se espera que suene a castellano o a portugués. Que el audio sirva para entrenar un ASR gallego es una **hipótesis** del equipo.
- **Código de idioma.** El modelo pide el idioma del texto (`language_id`) y el gallego no tiene código propio. Se probarán el del castellano (`es`) y el del portugués (`pt`), y se elegirá escuchando y con el CER de la revisión con ASR.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Seguir con OmniVoice en la persona mayor gallega** (ADR-005) | Pronuncia bien el gallego, pero según la escucha del equipo la voz no suena a persona mayor. El equipo prefiere cubrir el perfil. |
| **Clonación interlingüe con OmniVoice** (clonar la voz de persona mayor y que OmniVoice hable gallego) | Es una opción posible, porque OmniVoice clona y habla gallego, pero el equipo ha elegido Chatterbox para el perfil de persona mayor. Si Chatterbox suena demasiado mal en gallego, se puede probar esta alternativa. |
| **Repartir el perfil entre OmniVoice y Chatterbox** | Posible si Chatterbox da muchos rechazos en gallego. De momento se usa solo Chatterbox. |

## Consecuencias

- **Más rechazos en la revisión con ASR.** Un gallego peor pronunciado sube el CER, así que habrá más audios rechazados en este perfil. Si se rechazan muchos más que en los demás perfiles, se investiga antes de seguir.
- **Error de pronunciación aprendido.** Si Chatterbox pronuncia el gallego con fonética castellana o portuguesa, el ASR puede aprender esa pronunciación. Se puede medir en la spec 07 con un experimento con y sin estos audios, sobre un test real.
- **Spec 05.** Las voces clonadas del gallego se sintetizan siempre con Chatterbox, como las del castellano.

## Referencias

- Ficha de Chatterbox (licencia MIT, Multilingual V3 y lista de idiomas, sin el gallego): <https://huggingface.co/ResembleAI/chatterbox>
- Repositorio y ejemplos de uso multilingüe (`ChatterboxMultilingualTTS`, `language_id`): <https://github.com/resemble-ai/chatterbox>
- OmniVoice, para la alternativa de clonación interlingüe: <https://huggingface.co/k2-fsa/OmniVoice>
- Uso básico de la clonación con un código de idioma (según los ejemplos del repositorio):

