# ADR: Filtro validador con un LLM como juez y salida JSON estricta

## Decisión

El filtro validador (Fase 4, JEV) usa como juez de relevancia el mismo modelo local que el resto del pipeline (`OLLAMA_MODEL`, con Ollama), que en nuestras pruebas es Salamandra 2B (`hdnh2006/salamandra-2b-instruct`):

- La salida se fuerza con un esquema JSON (`json_schema` en LiteLLM) y se vuelve a validar con Pydantic en modo estricto (`strict=True`, `extra="forbid"`).
- Si algo falla se descarta: la respuesta cuenta como no relevante.
- El juez solo se aplica a la ruta A (Lynx): evalúa la respuesta de Lynx usando sus tres fragmentos como contexto. En las rutas B (Elasticsearch) y C (GraphRAG) solo se comprueba que cada documento tenga título y contenido, porque son coincidencias exactas de metadatos o relaciones del grafo y se tratan más documentos.

## Motivación

- **Problemas con modelos pequeños**. Es necesario entender la pregunta, ya que en ocasiones el ruido es la respuesta a otra ayuda o norma similar, con muchas palabras en común con la respuesta buscada, y no debe aceptarse a pesar de esto. Los modelos probados con menos parámetros (entre 100M y menos de 2B) tienen problemas para generar veredictos bien formados. Por eso en nuestras pruebas usamos Salamandra 2B para todo el pipeline; `qwen2.5:0.5b` queda solo como valor por defecto de la configuración.

- **Idioma de los documentos**. Los documentos del DOG están en gallego y castellano. Salamandra está entrenado por el BSC con un peso importante de lenguas de la península, incluido el gallego, por lo que lo preferimos frente a otros modelos del mismo tamaño entrenados sobre todo en inglés.

- **Normalización de modelos**. En el proyecto ya se utiliza Ollama mediante `src/llm_aux.py` (`_call_llm`), con herramientas como Langfuse para el trazado. Esta reutilización evita la necesidad de nuevas dependencias o servicios y enviar documentos fuera.

- **Seguridad de respuesta**. Es mejor descartar que aceptar la respuesta en caso de dudas, ya que si el filtro deja pasar ruido, la fase 5 de generación lo citará como fuente, lo cual es sensible al estar tratando con documentación legal. Si no hay documentos citados, debe indicarse en la fase de generación que no se ha encontrado información y no inventar citas o referencias.

## Alternativas

| Alternativa | Por qué se descartó |
| --- | --- |
| Umbral de similitud (embeddings / score de Elasticsearch) | No distingue "misma ayuda" de "ayuda parecida", y habría que calibrar el umbral para cada motor. |
| Cross-encoder de reranking (p. ej. `bge-reranker`) | Otro modelo que instalar y servir; da una puntuación, no una decisión, así que seguiría haciendo falta un umbral. Se puede revisar si el juez no llega a los criterios necesarios. |
| LLM externo (Gemini, OpenAI) | Mandaría documentos y preguntas fuera, necesita claves y el resto del pipeline ya es local. |
| Pedir JSON libre y repararlo (regex, `"true"` → `true`) | Esconde los errores del modelo y puede convertir ruido en un `true`. |
| Aceptar si el juez falla | Un Ollama caído dejaría pasar todo el ruido sin filtrado. |
| Juez también en las rutas B y C (`complex_filter.py`, documento a documento) | Se usó en la ruta B hasta el commit `e16baaa`: el veredicto temático del modelo descartaba publicaciones válidas. El código sigue en el repositorio, pero ninguna ruta lo usa. |

## Referencias

- Código: `src/noise_filter/_llm.py` (`judge`, `Verdict`), `src/noise_filter/complex_filter.py`, `src/noise_filter/simple_filter.py`, `src/noise_filter/prompts.py`; integración en `src/pipeline/engines.py` (`lynx_route`, `elastic_route`, `graph_route`).
- Documentación del módulo: `src/noise_filter/README.md`.
- Validación estricta del veredicto:

```python
class Verdict(BaseModel):
	model_config = ConfigDict(strict=True, extra="forbid")

class AnswerVerdict(Verdict):
	relevant: bool

verdict = AnswerVerdict.model_validate_json(response, strict=True)
```

- Versión documento a documento de `complex_filter.py`, que conserva los metadatos con una máscara (ya no la usa ninguna ruta):

```python
texts = [str(source.get("text") or "") for source, url in results]
decisions = evaluate_documents(question, texts)
kept = [item for item, ok in zip(results, decisions) if ok]
```

- Salamandra 2B (BSC): https://huggingface.co/BSC-LT/salamandra-2b-instruct
- LiteLLM, salida estructurada: https://docs.litellm.ai/docs/completion/json_mode
- Ollama, salida estructurada: https://ollama.com/blog/structured-outputs
- Pydantic, modo estricto: https://docs.pydantic.dev/latest/concepts/strict_mode/
- LLM como juez: Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (2023), https://arxiv.org/abs/2306.05685
