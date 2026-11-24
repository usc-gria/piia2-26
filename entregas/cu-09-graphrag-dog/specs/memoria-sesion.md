# Spec de funcionalidad: Memoria de sesión o memoria profunda (Fase 1)

## Qué hay que construir

Un módulo que guarda el contexto de cada conversación y lo usa para convertir las preguntas de seguimiento en consultas que se entienden por sí solas. Es la Fase 1 del pipeline: recibe la pregunta del usuario junto al identificador de su sesión y entrega al enrutador (Fase 2) la consulta reformulada.

Ejemplos:

- Turno 1: "¿Cuál es el plazo de solicitud de las ayudas del IGAPE para la digitalización de pymes?" → se pasa tal cual.
- Turno 2: "¿Y qué norma regula esa ayuda?" → "¿Qué norma regula las ayudas del IGAPE para la digitalización de pymes?"

Funcionamiento:

1. Por cada sesión se guardan tres cosas: los 2 últimos turnos completos (pregunta y respuesta), un resumen acumulativo de la conversación anterior a esos turnos y la lista de documentos usados en las respuestas (identificador, título y URL), que llamamos *subgrafo activo*.
2. La primera pregunta de la sesión se pasa sin cambios y sin llamar al LLM. A partir de ahí, un LLM decide con ese contexto si la pregunta es de seguimiento y, si lo es, la reformula para que no dependa de turnos anteriores ("esa ayuda", "la norma anterior", "¿y en 2024?"). Si ya se entiende sola, la deja igual.
3. La consulta reformulada va al enrutador (Fase 2). El subgrafo activo solo se usa dentro de la reformulación; no se pasa al enrutador ni a los motores.
4. Al terminar el turno (Fase 5), se guardan la pregunta, la respuesta y los documentos citados. Cuando un turno sale de los 2 últimos, un LLM lo añade al resumen.

**Fuera de alcance:** guardar la memoria entre sesiones distintas o entre usuarios, y usar el subgrafo activo como fuente de respuestas (solo sirve para entender referencias; los documentos se vuelven a recuperar en la Fase 3).

## Por qué

Lynx trata cada pregunta por separado, así que en una conversación larga pierde el hilo: si el usuario pregunta "¿y qué norma la regula?", no sabe a qué ayuda se refiere y busca algo que no tiene que ver. Pasar toda la conversación al LLM tampoco sirve, porque con un modelo pequeño el contexto se llena enseguida. Con un resumen, los últimos turnos y la lista de documentos se mantiene lo necesario para resolver las referencias sin que el contexto crezca con cada turno.

## Restricciones

- Las sesiones no se mezclan: cada consulta solo usa el contexto de su propia sesión, identificada por su `session_id`.
- Como máximo 2 turnos completos, un resumen de 1200 caracteres y 10 documentos en el subgrafo activo (los más recientes). Los valores se fijan en el código (`MemorySettings`).
- El LLM se ejecuta en local con Ollama mediante LiteLLM; la conversación no sale de la infraestructura de Imaxin.
- La reformulación no añade información que no esté en la pregunta o en el contexto: si la referencia no se puede resolver, se pasa la pregunta original sin inventar el documento.
- Si el LLM devuelve una salida no válida, se pasa la pregunta original. Si Ollama no responde, el error se propaga y el turno falla: no se inventa una reformulación.

## Criterios de aceptación

Usaremos 10 conversaciones de prueba con 20 preguntas de seguimiento en total, con la consulta reformulada esperada y el documento al que se refiere anotados a mano.

1. En al menos 16 de las 20 preguntas de seguimiento, la consulta reformulada nombra la misma norma, ayuda u organismo que la esperada.
2. La primera pregunta de cada conversación se pasa sin cambios y sin llamar al LLM en las 10 conversaciones.
3. Las preguntas que no hacen referencia a turnos anteriores se pasan sin cambios.
4. Nunca se guardan más de 2 turnos, 1200 caracteres de resumen ni 10 documentos por sesión.
5. Si se lanzan dos conversaciones a la vez, ninguna consulta reformulada contiene documentos o entidades de la otra sesión.
6. Si la referencia no se puede resolver o el LLM devuelve una salida no válida, se pasa la pregunta original.
7. Si Ollama no responde, el turno termina con un error y no con una consulta inventada.
8. La reformulación tarda menos de 2 segundos en al menos 18 de las 20 preguntas.
