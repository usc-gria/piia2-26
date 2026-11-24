# ADR: el LLM extrae los parámetros y el código construye las consultas

## Decisión

En los motores de Elasticsearch (3B) y GraphRAG (3C) el LLM no escribe las consultas. Solo devuelve un JSON pequeño con los datos que saca de la pregunta, y es nuestro código el que construye la consulta a partir de ese JSON.

- **Elasticsearch:** el LLM devuelve los filtros (entidad, sección, subsección, idioma y fechas). Antes de llamarlo, sacamos del índice la lista de valores que existen para cada campo y se la pasamos, para que elija un valor real. Después comprobamos que cada valor está en esa lista y montamos una consulta `bool` con filtros `terms` y `range`.

  Por ejemplo, para "¿Qué documentos publicó Sanidade en marzo de 2025?", el LLM devuelve:

  ```json
  {"entity": ["Consellería de Sanidade"], "date_from": "2025-03-01", "date_to": "2025-03-31"}
  ```

- **GraphRAG:** el LLM solo devuelve las normas que se citan en la pregunta, por ejemplo `{"references": ["Ley 2/2016"]}`. Con eso lanzamos dos consultas Cypher que ya están escritas en el código: una busca el nodo de la norma y la otra sus relaciones (modifica, deroga...), de cualquier tipo y a un salto, sin depender de las etiquetas del grafo. La norma se pasa como parámetro y las consultas se ejecutan en modo lectura.

## Motivación

- **Necesitamos resultados exactos.** La spec de Elasticsearch pide que los listados y conteos coincidan exactamente. Si el LLM escribe la consulta entera, se puede equivocar en un detalle, como dejar fuera el último día del mes, y nadie se daría cuenta. Un JSON con pocos campos sí se puede comprobar: si el LLM se inventa un organismo, el código da error en vez de devolver un listado incorrecto.
- **Usamos un modelo pequeño.** Todas las fases usan un mismo modelo local en Ollama (`OLLAMA_MODEL`: `qwen2.5:0.5b` por defecto y Salamandra 2B en nuestras pruebas), porque los datos de Imaxin no pueden salir a la nube. Un modelo así no escribe bien una consulta de Elasticsearch o Cypher completa, pero sí puede elegir valores de una lista o copiar el nombre de una norma.
- **No podemos modificar los datos de Imaxin.** Si el LLM generase Cypher, podría acabar ejecutándose un `DELETE` o un `SET`, por ejemplo por una inyección de prompt. Con consultas fijas y parámetros eso no puede pasar.

## Alternativas

- **Que el LLM genere la consulta completa** (text-to-Cypher o text-to-DSL, por  ejemplo con `GraphCypherQAChain` de LangChain). La descartamos por lo dicho arriba: con un modelo pequeño fallaría a menudo, los fallos no se ven y supone ejecutar código generado en el servidor de la empresa. LangChain incluso obliga a activar `allow_dangerous_requests` para usarlo.
- **Sacar los filtros solo con reglas o expresiones regulares, sin LLM.** No sirve para abreviaturas ("IGAPE") ni para nombres escritos en castellano cuando en el índice están en gallego. En GraphRAG la usamos solo como apoyo: si el LLM se olvida de un número de norma tipo `2/2016`, lo cogemos con una regex.
- **Usar búsqueda semántica (el RAG de siempre) también para los listados.** Solo devuelve los fragmentos más parecidos, no todos los que cumplen la condición. Es justo el problema que tenía Lynx con este tipo de preguntas.

## Referencias

- Código del proyecto: `src/retrieval_engine/elastic_search/catalogue.py` (lista de valores del índice), `src/retrieval_engine/elastic_search/query.py` (construcción y validación de filtros), `src/retrieval_engine/graph_rag/entities.py` (extracción de normas y regex) y `src/retrieval_engine/graph_rag/queries.py` (consultas Cypher fijas).
- [Bool query de Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- [Parámetros en Cypher (Neo4j)](https://neo4j.com/docs/cypher-manual/current/syntax/parameters/)
- [Salida en JSON con LiteLLM](https://docs.litellm.ai/docs/completion/json_mode)
- [GraphCypherQAChain de LangChain](https://reference.langchain.com/python/langchain-neo4j/chains/graph_qa/cypher/GraphCypherQAChain) (el aviso de `allow_dangerous_requests`)
