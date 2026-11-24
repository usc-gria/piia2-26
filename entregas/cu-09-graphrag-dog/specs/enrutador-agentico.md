# Spec de funcionalidad: Enrutador agéntico (Fase 2)

## Qué hay que construir

Un módulo que decide qué motor de recuperación de la Fase 3 responde a cada consulta. Recibe la consulta reformulada por la memoria de sesión (Fase 1) y la envía a uno de los tres motores según el tipo de información que necesita:

- **A · RAG tradicional (Lynx):** datos concretos o búsquedas por contenido. "¿Cuál es el plazo de solicitud de las ayudas del IGAPE para la digitalización?"
- **B · Elasticsearch:** listados y conteos por metadatos (entidad, sección, subsección, fecha). "¿Cuántas publicaciones hubo por sección en junio de 2025?" (ver [spec](elasticsearch-listados-agregaciones.md)).
- **C · GraphRAG:** relaciones entre normas o entre varios documentos. "¿Qué normas modifican la Ley 2/2016?" (ver [spec](motor-graphrag.md)).

Funcionamiento:

1. Un LLM genera un borrador hipotético de la respuesta.
2. Se aplican reglas para los casos claros, sobre la pregunta en minúsculas y sin tildes:
   - Una palabra de relación ("modifica", "deroga", "compara", "relaciona", "sustituye", "en común") junto a un tipo de norma ("ley", "decreto", "orden", "resolución", "disposición", "convocatoria") → C.
   - Una palabra de listado ("lista", "enumera", "cuántos", "qué documentos") junto a un metadato (un año, un mes, "publicó", "sección", "subsección") → B.
   - Las reglas aceptan también los términos en gallego e inglés.
3. Si ninguna regla se cumple, el LLM recibe la consulta y el borrador y responde con una sola letra (`A`, `B` o `C`). El código toma la primera letra válida de la respuesta.
4. La consulta y el borrador se envían al motor elegido. El borrador es una respuesta provisional: se sustituye por la respuesta de Lynx si el filtro la acepta, por el listado en la ruta B o por las relaciones encontradas en la ruta C.

**Fuera de alcance:** enviar una misma consulta a varios motores y combinar sus resultados, y elegir el motor por la complejidad de la pregunta (se elige solo por el tipo de información que necesita).

## Por qué

Cada motor solo resuelve bien un tipo de pregunta: Lynx no puede contar ni listar todos los documentos que cumplen una condición, Elasticsearch no lee el contenido de los documentos y el grafo solo sirve si hay relaciones que seguir. Si una pregunta va al motor equivocado, la respuesta sale incompleta o vacía aunque los datos existan. Las reglas resuelven sin clasificador los casos claros; el borrador hipotético ayuda al modelo pequeño a ver qué tipo de respuesta hace falta (un dato, una lista o una relación) cuando la pregunta no lo dice de forma explícita.

## Restricciones

- Cada consulta va a una sola ruta.
- Si una regla se cumple, la ruta la decide la regla y no se pide la clasificación al LLM.
- Ninguna regla manda a la ruta A: A es la ruta del LLM y la de reserva.
- Si la respuesta del LLM no contiene `A`, `B` ni `C`, la consulta va a la ruta A, que es el sistema que ya existe. Si Ollama no responde, el error se propaga y no se elige ninguna ruta.
- El LLM se ejecuta en local con Ollama mediante LiteLLM.

## Criterios de aceptación

Usaremos 30 consultas de prueba (10 por ruta, incluidas preguntas de seguimiento ya reformuladas), con la ruta correcta anotada a mano.

1. La ruta elegida coincide con la anotada en al menos 26 de las 30 consultas, y en al menos 8 de las 10 de cada ruta.
2. Todas las consultas que cumplen una regla van a la ruta de esa regla sin que se pida la clasificación al LLM.
3. Todas las respuestas del LLM sin una letra válida se envían a la ruta A, sin errores.
4. Si Ollama no responde, el turno termina con un error y no con una ruta inventada.
5. Cuando el motor encuentra fuentes, la respuesta final se construye con ellas y no con el borrador.
6. La decisión, incluido el borrador, tarda menos de 2 segundos en al menos 27 de las 30 consultas.
