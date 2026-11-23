# ADR-002 · Traducir al gallego con NOS-MT-OpenNMT-es-gl (Proxecto Nós)

- **Estado:** aceptada; aplicada al corpus. Falta la revisión manual de la muestra de 100 frases (`muestra_revision.tsv`).
- **Fecha:** 2026-11
- **Afecta a:** spec 03 (C2 · Corpus)

## Decisión

El corpus en español se traduce al gallego con el modelo **NOS-MT-OpenNMT-es-gl** de Proxecto Nós (Universidade de Santiago de Compostela), en una revisión fija de Hugging Face que queda registrada junto al corpus gallego. Todo el corpus se traduce con esa misma revisión, como exige la spec 03.

## Motivación

1. **Específico del par español-gallego.** Es un transformer entrenado con OpenNMT para este par, con corpus auténticos (traducciones humanas) y sintéticos de Proxecto Nós.
2. **Licencia MIT.** Permite el uso comercial que necesita Balidea, además de la modificación y la redistribución.
3. **Determinista y versionable.** Un modelo NMT local con decodificación por haz da la misma salida para la misma entrada y la misma revisión, algo que la spec 03 necesita («mismo sistema para todo el corpus, versión registrada») y que un LLM a través de una API no garantiza.
4. **Coste y privacidad.** Se ejecuta en local, incluso en CPU para 2.000 frases, sin enviar textos fuera.
5. **Ecosistema gallego.** Es el mismo proyecto que publica las voces TTS (NOS) y los ASR gallegos que podemos usar, con convenciones de normalización coherentes.

## Alternativas consideradas

| Alternativa | Por qué se descarta |
| --- | --- |
| **Traducción con LLM** (el mismo que genera el corpus) | Salida no determinista y versión difícil de fijar si es un servicio; puede «mejorar» o reescribir la frase en lugar de traducirla y romper la correspondencia con la frase en español. Además, la calidad en gallego de los LLM generalistas no está evaluada de forma sistemática para el dominio médico. Se reserva como **segunda opinión** para revisar discrepancias. |
| **Apertium / Opentrad (reglas)** | Muy buena cobertura morfológica entre lenguas cercanas, pero menos natural en frases largas. El propio NOS-MT la usó para generar parte de sus datos sintéticos. Queda como respaldo si NOS-MT falla en terminología. |
| **NLLB-200 (Meta)** | Multilingüe y con gallego, pero su licencia es no comercial (CC-BY-NC 4.0 en las fichas oficiales de Hugging Face), lo que impide el uso por parte de Balidea. Además, la propia ficha lo presenta como un modelo de investigación, no pensado para producción ni para textos de dominio específico como el médico. |
| **Traducción humana** | Inviable para 2.000 frases en el plazo; se usa solo para revisar una muestra. |

## Consecuencias

- **Resultado de la primera traducción.** De 2.000 frases quedan 1.736 en gallego:
    - 264 se descartan, 260 de ellas porque el traductor dejó palabras sin traducir, marcadas como `<unk>` (por ejemplo, «intravenosa» o «gasometría»);
    - 75 frases aceptadas salieron iguales que en castellano, es decir, sin traducir;
    - hay traducciones erróneas, como «Me mareo cuando me levanto de la cama» → «Érgome cando me mareo da tixola».

  Tantos `<unk>` en términos médicos apuntan a un problema en la preparación del texto antes de traducir (tokenización o BPE), no solo al modelo. Hay que revisarlo antes de dar el corpus gallego por bueno.
- **El dominio médico no está evaluado.** Los BLEU publicados no cubren textos médicos. Mitigación: revisión manual de la muestra aleatoria de 100 frases, clasificando los errores (terminología, concordancia, castellanismos, omisiones). Si los errores graves superan el 10 %, se reconsidera la decisión.
- **La validación se repite en gallego.** El traductor puede reintroducir dígitos o abreviaturas, así que el script vuelve a validar el corpus gallego con las reglas de la spec 03.
- **Menos horas en gallego.** Las frases descartadas reducen el volumen del gallego, que hay que compensar en la síntesis (spec 05).

## Referencias

- Ficha del modelo, uso y métricas: <https://huggingface.co/proxectonos/NOS-MT-OpenNMT-es-gl>
- Corpus de entrenamiento de Proxecto Nós: <https://github.com/proxectonos/corpora>
- Ficha de NLLB-200 (licencia CC-BY-NC 4.0 y uso previsto): <https://huggingface.co/facebook/nllb-200-distilled-600M> · <https://huggingface.co/facebook/nllb-200-3.3B>
- Implementación en el script del corpus: `corpus.py gl` ([`codigo/corpus/README.md`](../codigo/corpus/README.md)).
- Uso según la ficha:
    - tokenizar con el `tokenizer.perl` del repositorio (Linguakit);
    - aplicar BPE con `bpe/es.bpe` (subword-nmt);
    - traducir con el modelo CTranslate2 `ct2-es-gl_12L` mediante `translate.py`;
    - quitar las marcas `@@ `.
  El modelo se entrenó con OpenNMT-py 3.2, y la ficha recomienda Python 3.9.
- BLEU publicados en la ficha: GOLD 1 79,5; GOLD 2 43,5; FLORES 21,4; test-suite 73,4. Ninguno es de dominio médico.
