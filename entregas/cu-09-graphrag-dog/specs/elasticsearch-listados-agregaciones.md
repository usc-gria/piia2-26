# Spec de funcionalidad: Motor de recuperación Elasticsearch (Fase 3B)

## Qué hay que construir

Un motor que responde a preguntas de listados y conteos sobre el DOG consultando directamente los metadatos de Elasticsearch (entidad, sección, subsección y fecha). Es el motor 3B de la Fase 3, junto al RAG tradicional (3A) y GraphRAG (3C), y recibe las consultas que el enrutador (Fase 2) clasifica como listados o agregaciones.

Ejemplos:

- "¿Qué documentos publicó el IGAPE en marzo de 2025?" → lista de documentos.
- "¿Cuántas publicaciones hubo por sección en junio de 2025?" → número de publicaciones por sección.

Funcionamiento:

1. Un LLM saca de la pregunta los parámetros en un JSON con formato fijo: listar o contar, filtros, agrupación y orden.
2. Los nombres que da el usuario se traducen al valor que hay en el índice ("IGAPE" → "Instituto Galego de Promoción Económica (IGAPE)").
3. El código monta la consulta a Elasticsearch y la ejecuta.
4. Se devuelven los documentos con sus metadatos (`doc_id`, título, fecha y URL) y el total. Como el resultado ya es exacto, no pasa por el JEV: va directo a la generación (Fase 5), y los documentos se guardan en la memoria de sesión (Fase 1).

**Fuera de alcance:** listados por tema ("lista las ayudas para pymes"), preguntas sobre el contenido de un documento (van a 3A) y relaciones entre normas (van a 3C).

## Por qué

El RAG actual responde con los fragmentos más parecidos a la pregunta, así que no sirve para preguntas de tipo "cuántos" o "cuáles": si hay 37 documentos que cumplen la condición, solo ve unos pocos y la respuesta sale incompleta. Esos datos ya están en los metadatos de Elasticsearch, así que con una consulta con filtros se obtiene la respuesta exacta y completa, más rápido y sin gastar contexto del LLM.

## Restricciones

- Se cuenta por documento, no por chunk (en el índice cada documento está partido en varios chunks).
- Solo documentos en gallego (`lang = gl`).
- El LLM solo rellena el JSON; la consulta la construye el código. Acceso de solo lectura.
- Como máximo 100 documentos por respuesta (20 por defecto). Si hay más, se indica el total.
- Supuesto: los campos de entidad, sección y fecha permiten filtrar y agrupar. Lo comprobaremos cuando tengamos acceso al índice.
- El motor no inventa: si no reconoce la entidad, si la pregunta no se puede responder con metadatos o si no hay resultados, lo indica y la Fase 5 se lo explica al usuario.

## Criterios de aceptación

Usaremos 15 consultas de prueba (listados, conteos, entidades que no existen y consultas sin resultados), con la respuesta correcta sacada a mano de Elasticsearch.

1. El LLM extrae bien los parámetros en al menos 13 de las 15 consultas.
2. Cuando los parámetros son correctos, los listados y los conteos coinciden exactamente con la respuesta esperada.
3. Ningún listado repite documentos.
4. Todos los documentos devueltos tienen `doc_id`, título y URL.
5. Si la entidad no existe, el motor lo indica y no hace la búsqueda sin ese filtro.
6. Si no hay resultados, devuelve una lista vacía avisando de ello.
7. Responde en menos de 3 segundos en al menos 14 de las 15 consultas.
