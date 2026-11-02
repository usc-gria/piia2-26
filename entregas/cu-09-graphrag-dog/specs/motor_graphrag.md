# Spec de funcionalidad: Motor de recuperación GraphRAG (Fase 3C)

## Qué hay que construir

Un motor de recuperación basado en grafos. Es el motor 3C de la Fase 3, junto al RAG tradicional (3A) y Elasticsearch (3B), y recibe las consultas que el enrutador (Fase 2) clasifica como "relacionar información de varios documentos".

Ejemplos:

- "¿Qué normas modifican a la que regula esta ayuda?"
- "¿Qué requisitos comparten estas dos convocatorias?"

Funcionamiento:

1. Detecta las entidades de la consulta (normas, organismos, ayudas...) y las busca en el grafo.
2. Recorre el grafo desde ellas siguiendo las relaciones (modifica, deroga, desarrolla, cita...) con una profundidad limitada.
3. Recupera el texto y los metadatos (`doc_id`, título y URL) de los documentos encontrados.
4. Los devuelve con el mismo formato que el motor 3A, para que pasen por el JEV (Fase 4) y la generación (Fase 5). Los documentos también se guardan en la memoria de sesión (Fase 1).

**Fuera de alcance:** construir y mantener el grafo; el motor solo lo consulta.

## Por qué

El RAG tradicional busca por similitud y no puede seguir relaciones entre normas. Para responder "¿qué cambió en esta ayuda tras la última modificación?" hay que encontrar la norma original y la que la modifica, y leer las dos; ningún fragmento suelto tiene esa respuesta. Además, Lynx solo usa fragmentos de un documento cada vez. El grafo permite recuperar información conectada de varios documentos y comparar normativas.

## Restricciones

- Solo lectura sobre el grafo existente.
- Todo fragmento devuelto lleva `doc_id`, título y URL para poder citarlo.
- Máximo 2-3 saltos en el recorrido y número de fragmentos limitado (configurable).
- Usa la memoria de sesión para entender referencias como "esa ayuda" o "la norma anterior".
- Si no encuentra ninguna entidad en el grafo, devuelve un resultado vacío (no inventa). Si el subgrafo es muy grande, prioriza los nodos más cercanos.

## Criterios de aceptación

Usaremos 15 preguntas multi-documento con respuesta conocida y 5 conversaciones de seguimiento.

1. Encuentra el nodo de partida correcto en al menos 13 de las 15 preguntas.
2. Recupera todos los documentos necesarios en al menos 11 de las 15 preguntas, y en más que el RAG tradicional con las mismas preguntas.
3. Todos los fragmentos tienen `doc_id`, título y URL, y el JEV los acepta sin cambios.
4. Nunca se pasa de la profundidad ni del número máximo de fragmentos.
5. Entiende bien la referencia en al menos 4 de las 5 conversaciones de seguimiento.
6. Responde en menos de 5 segundos (sin contar la generación).
7. Si las entidades no existen en el grafo, devuelve una lista vacía avisando de ello, sin errores.
