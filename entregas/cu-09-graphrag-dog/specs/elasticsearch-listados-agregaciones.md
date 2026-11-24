# Spec de funcionalidad: Motor de recuperación Elasticsearch (Fase 3B)

## Qué hay que construir

Un motor que responde a preguntas de listados y conteos sobre el DOG consultando directamente los metadatos de Elasticsearch (entidad, sección, subsección y fecha). Es el motor 3B de la Fase 3, junto al RAG tradicional (3A) y GraphRAG (3C), y recibe las consultas que el enrutador (Fase 2) clasifica como listados o agregaciones.

Ejemplos:

- "¿Qué documentos publicó el IGAPE en marzo de 2025?" → lista de documentos.
- "¿Cuántas publicaciones hubo por sección en junio de 2025?" → número de publicaciones por sección.

Funcionamiento:

1. Un LLM saca de la pregunta los parámetros en un JSON con formato fijo: listar o contar, filtros, agrupación y orden.
2. Los nombres que da el usuario se traducen al valor que hay en el índice ("IGAPE" → "Instituto Galego de Promoción Económica (IGAPE)"). Para ello, antes de llamar al LLM sacamos del propio índice la lista de valores que existen para cada campo y se la pasamos, para que elija uno real. Después el código comprueba que el valor elegido está en esa lista; si no está, la entidad se considera no reconocida (ver [ADR](../decisions/llm-extrae-parametros-codigo-construye-consultas.md)).
3. El código monta la consulta a Elasticsearch y la ejecuta.
4. Se devuelven los documentos con sus metadatos (`file_id`, título, fecha y URL) y el total. Como el resultado ya es exacto, no pasa por el JEV (el filtro validador de la Fase 4, ver [ADR](../decisions/filtro-validador-adr.md)): solo se comprueba que cada documento tenga título y contenido y va a la generación (Fase 5), y los documentos se guardan en la memoria de sesión (Fase 1).

**Fuera de alcance:** listados por tema ("lista las ayudas para pymes"), preguntas sobre el contenido de un documento (van a 3A) y relaciones entre normas (van a 3C).

## Por qué

El RAG actual responde con los fragmentos más parecidos a la pregunta, así que no sirve para preguntas de tipo "cuántos" o "cuáles": si hay 37 documentos que cumplen la condición, solo ve unos pocos y la respuesta sale incompleta. Esos datos ya están en los metadatos de Elasticsearch, así que con una consulta con filtros se obtiene la respuesta exacta y completa, más rápido y sin gastar contexto del LLM.

## Restricciones

- Se cuenta por documento, no por chunk (en el índice cada documento está partido en varios chunks).
- Solo documentos en gallego o castellano (`lang = gl` o `lang = es`). Si la pregunta no pide un idioma, se busca en los dos.
- El LLM solo rellena el JSON; la consulta la construye el código. Acceso de solo lectura.
- Como máximo 100 documentos por respuesta (20 por defecto). Si hay más, se indica el total.
- Los campos de entidad, sección y subsección son de tipo `keyword` (`entity.keyword`, `section.keyword`, `subsection.keyword`) y la fecha es `doga_date`, así que permiten filtrar y agrupar. Cada chunk lleva el `file_id` de su documento, que se usa para agrupar.
- El motor no inventa: si no reconoce la entidad, si la pregunta no se puede responder con metadatos o si no hay resultados, lo indica y la Fase 5 se lo explica al usuario.

## Criterios de aceptación

Usaremos 15 consultas de prueba (listados, conteos, entidades que no existen y consultas sin resultados), con la respuesta correcta sacada a mano de Elasticsearch.

1. El JSON que extrae el LLM coincide campo a campo con el esperado en al menos 13 de las 15 consultas.
2. Cuando los parámetros son correctos, los listados y los conteos coinciden exactamente con la respuesta esperada.
3. Ningún listado repite documentos.
4. Todos los documentos devueltos tienen `file_id`, título y URL.
5. Si la entidad no existe, el motor lo indica y no hace la búsqueda sin ese filtro.
6. Si no hay resultados, devuelve una lista vacía avisando de ello.
7. Responde en menos de 3 segundos en al menos 14 de las 15 consultas.
8. Ningún documento devuelto tiene un `lang` distinto de `gl` o `es`, y si la consulta pide un idioma, todos están en ese idioma.
9. En las consultas con más de 20 resultados se devuelven 20 documentos (o los que se pidan, hasta 100) y se indica el total.
10. El motor se conecta con un usuario de solo lectura y el número de documentos del índice es el mismo antes y después de las pruebas.
