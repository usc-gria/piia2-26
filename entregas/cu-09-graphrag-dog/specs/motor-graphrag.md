# Spec de funcionalidad: Motor de recuperación GraphRAG (Fase 3C)

## Qué hay que construir

Un motor de recuperación basado en grafos. Es el motor 3C de la Fase 3, junto al RAG tradicional (3A) y Elasticsearch (3B), y recibe las consultas que el enrutador (Fase 2) clasifica como "relacionar información de varios documentos".

Ejemplos:

- "¿Qué normas modifican a la que regula esta ayuda?"
- "¿Qué requisitos comparten estas dos convocatorias?"

Funcionamiento:

1. Un LLM detecta las normas, convocatorias y documentos citados en la consulta (no los organismos), y una regex recoge los números tipo `2/2016` que se le escapen. Después se buscan en el grafo.
2. Recorre el grafo desde ellas siguiendo todas sus relaciones, sean del tipo que sean (modifica, deroga, cita...), a un solo salto. Las consultas no dependen de las etiquetas ni de los tipos de relación del grafo.
3. Recupera de Neo4j el texto y los metadatos (título y URL) de los documentos encontrados, junto con las relaciones en forma de hechos ("A -[MODIFICA]-> B").
4. Los devuelve con el mismo formato que el motor 3A, para que pasen por el filtrado de la Fase 4 (en esta ruta no se usa el JEV, solo se comprueba que tengan título y contenido; ver [ADR](../decisions/filtro-validador-adr.md)) y la generación (Fase 5). Los documentos también se guardan en la memoria de sesión (Fase 1).

**Fuera de alcance:** construir y mantener el grafo; el motor solo lo consulta.

## Por qué

El RAG tradicional busca por similitud y no puede seguir relaciones entre normas. Para responder "¿qué cambió en esta ayuda tras la última modificación?" hay que encontrar la norma original y la que la modifica, y leer las dos; ningún fragmento suelto tiene esa respuesta. Además, Lynx solo usa fragmentos de un documento cada vez. El grafo permite recuperar información conectada de varios documentos y comparar normativas.

## Restricciones

- Solo lectura sobre el grafo existente.
- Todo documento devuelto lleva título y URL para poder citarlo.
- Profundidad de 1 salto. Como máximo 5 normas por pregunta, 5 nodos de partida por norma, 50 relaciones y 20 documentos por respuesta. Los valores se fijan en el código.
- Las referencias como "esa ayuda" o "la norma anterior" las resuelve antes la memoria de sesión (Fase 1): el motor recibe la pregunta ya reformulada.
- Si no encuentra ninguna norma en el grafo, devuelve un resultado vacío (no inventa).

## Criterios de aceptación

Usaremos 15 preguntas multi-documento con respuesta conocida y 5 conversaciones de seguimiento.

1. El nodo de partida coincide con el anotado en al menos 13 de las 15 preguntas.
2. Los documentos devueltos (por URL) incluyen todos los de la respuesta esperada en al menos 11 de las 15 preguntas, y en más preguntas que el RAG tradicional con las mismas preguntas.
3. Todos los documentos tienen título, URL y contenido no vacío, así que ninguno se descarta en la Fase 4.
4. Ningún resultado incluye nodos a más de 1 salto de los de partida, ni más de 50 relaciones ni de 20 documentos.
5. En al menos 4 de las 5 conversaciones de seguimiento, tras la reformulación de la Fase 1, el nodo de partida es el anotado.
6. Responde en menos de 5 segundos (sin contar la generación).
7. Si las entidades no existen en el grafo, devuelve una lista vacía avisando de ello, sin errores.
8. Las consultas Cypher son fijas, no tienen cláusulas de escritura (`CREATE`, `MERGE`, `SET`, `DELETE`) y se lanzan en modo lectura (`RoutingControl.READ`); el número de nodos y relaciones del grafo no cambia tras las pruebas.
