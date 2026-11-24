---
description: La consulta al documento responde con el último JSON validado por una persona y avisa cuando un dato de la respuesta no es el que extrajo el modelo.
state: Hecha
---

# Spec — Consulta al documento con el JSON validado y sus cambios

## Qué construir
Tres cambios sobre la consulta al documento que ya existe (`responder_pregunta()` y la pestaña «Consulta al documento») y sobre la revisión humana de `specs/edicion-exportacion.md`:

1. **El chat usa el JSON validado.** «Marcar como validado» funciona como un guardado para el chat:
   - al pulsarlo, la app guarda una copia del JSON editado en `st.session_state["document_reviews"][<documento>]["validated_entities"]`;
   - el chat responde con esa copia. Mientras no se haya validado nada, responde con el JSON que devolvió el modelo (`entities` del resultado);
   - editar después de validar desmarca la validación, como hasta ahora, pero no cambia lo que recibe el chat: sigue con la última copia validada hasta que se vuelva a pulsar el botón;
   - volver a procesar el documento descarta la revisión entera, también la copia validada.

2. **Cambios entre el JSON del modelo y el validado.** Un módulo nuevo `src/procesamiento_documental/revision.py` con:

   ```python
   entity_changes(original: dict, validated: dict) -> list[EntityChange]
   ```

   `EntityChange` es un `TypedDict` con `field` (la ruta, con la notación de `missing_fields`: `patient.mrn`), `original` (el valor del modelo) y `validated` (el valor validado). Reglas:
   - solo se baja de nivel cuando el valor es un objeto en los dos JSON. Cualquier otro valor se compara entero, así que `procedures` y `medications` dan como mucho un cambio cada una, con la lista completa en `original` y en `validated`;
   - la comparación es exacta: corregir una mayúscula o un espacio es un cambio. `243` y `243.0` son el mismo número;
   - `null`, una lista vacía, un texto en blanco y una clave que falta son el mismo valor, «sin dato», también dentro de una lista: pasar de uno a otro no es un cambio. Así no aparecen como cambios las conversiones que hace `tables_to_entities()` sin que nadie edite nada;
   - los cambios salen en el orden de las claves del JSON validado.

3. **La consulta conoce los cambios.** `responder_pregunta()` gana un cuarto parámetro opcional:

   ```python
   responder_pregunta(pregunta, resultado, historial=None, entidades_validadas=None)
   ```

   La consulta funciona como un planificador: Groq traduce la pregunta a rutas del JSON y `src/` resuelve esas rutas y redacta la respuesta con sus valores. Sobre ese diseño:
   - Sin `entidades_validadas`, hace exactamente lo de ahora.
   - Con `entidades_validadas`, el contexto que envía a Groq lleva en `entities` el JSON validado. No envía el JSON del modelo ni la lista de cambios: Groq solo elige rutas y no los necesita.
   - Las rutas se resuelven contra el contexto enviado, es decir, contra el JSON validado: la respuesta se da siempre con el valor validado.
   - Los cambios son `entity_changes(resultado["entities"], entidades_validadas)`. Cada evidencia de origen `entities` lleva además una clave `changes` con los cambios que la afectan: los que tienen su misma ruta, una ruta que la contiene (`procedures` para `procedures.0.desc`) o una ruta contenida en ella (`patient.mrn` para `patient`). Si no la afecta ninguno, la evidencia no lleva esa clave. Las evidencias de `additional_fields` y `metadata` no la llevan nunca.
   - La respuesta añade una frase por cada cambio de sus evidencias, una sola vez aunque lo compartan varias: «Una persona corrigió `patient.mrn`; el modelo había extraído 1039485.». Si el modelo no había extraído ningún valor, la frase lo dice.
   - Si el campo por el que se pregunta está vacío en el JSON validado y lo afecta un cambio, la respuesta de dato ausente añade la misma frase: una persona vació lo que el modelo había extraído.

### Cambios en la app
- La llamada a `responder_pregunta()` pasa `validated_entities` de la revisión del documento (o `None` si no hay). Desaparece `_reviewed_result()`.
- Sobre el chat, una línea dice qué versión usa:
  - nunca validado: que responde con el JSON extraído por el modelo y que las correcciones contarán cuando se marque como validado;
  - validado y sin ediciones posteriores: que responde con el JSON validado;
  - validado y editado después: que responde con la última versión validada y que hay cambios sin validar.
- Bajo cada respuesta, junto a las evidencias, una línea por cada cambio de sus evidencias: la ruta del campo y el valor que extrajo el modelo.

## Por qué
Tras `specs/edicion-exportacion.md` la persona usuaria corrige las entidades, pero el chat recibe el JSON editado en cuanto cambia una celda, aunque esté a medias o no cumpla el esquema. Atarlo a la validación hace que el chat solo trabaje con datos que alguien ha dado por buenos, y da al botón un efecto visible.

Cuando el dato por el que se pregunta se ha corregido, quien pregunta tiene que saberlo: la respuesta ya no es lo que leyó el modelo en la imagen. El aviso se calcula y se redacta en `src/`, sobre las evidencias, así que no depende de que el modelo lo mencione y se prueba sin red.

No se envían a Groq ni el JSON del modelo ni la lista de cambios porque Groq solo traduce la pregunta a rutas: no redacta la respuesta ni compara valores, y ampliar el contexto gastaría una cuota diaria que ya se ha agotado en dos pruebas.

Las listas se comparan enteras porque borrar o añadir una fila desplaza las demás, y comparar por posición daría cambios falsos. Es el criterio de `compare_extraction()`.

## Restricciones
- Aplica `decisions/interfaz-streamlit.md`: la comparación entre los dos JSON vive en `src/`. `src/app.py` solo guarda la copia validada, pasa los datos y coloca los componentes.
- Aplica `decisions/esquemas-extraccion-documental.md`: `entity_changes()` no conoce los campos de ningún tipo documental; trabaja sobre cualquier par de objetos JSON.
- Las preguntas siguen sin enviar la imagen a Groq, y cada pregunta sigue siendo una sola llamada.
- Lo que se valida cumple siempre el esquema, porque el botón solo se activa con un JSON válido. No se añade otra validación.
- `PROMPT_VERSION` no cambia: identifica los prompts de clasificación y extracción que mide `script/evaluar_metricas.py`.
- No cambian `procesar_documento()`, `extraer_campo_adicional()`, `responder_preguntas()`, `QUESTION_SYSTEM_PROMPT` ni `QUESTION_RESPONSE_SCHEMA`. Las consultas por lotes de `responder_preguntas()` siguen usando el JSON del modelo: la app no las usa.
- Queda fuera: la exportación, editar o borrar campos adicionales, guardar más versiones que la del modelo y la última validada, reescribir las respuestas anteriores del historial y comparar con la verdad de referencia.

## Criterios de aceptación
- `tests/test_revision.py` comprueba, sin red, que `entity_changes()`:
  - devuelve una lista vacía para dos JSON iguales;
  - con `patient.mrn` cambiado de `"1039485"` a `"MRN-1039485"` devuelve un único cambio con esa ruta y los dos valores;
  - devuelve un cambio cuando un campo pasa de `null` a un dato y cuando pasa de un dato a `null`;
  - con un procedimiento añadido, borrado o modificado devuelve un único cambio con la ruta `procedures` y las dos listas completas;
  - no devuelve cambios entre `null`, `[]`, `""` y una clave ausente, ni entre `243` y `243.0`;
  - no devuelve cambios entre una factura y un informe de alta de ejemplo y el resultado de pasarlos por `entities_to_tables()` y `tables_to_entities()`.
- `tests/test_integraciones.py` comprueba, sin red y con el cliente simulado, que `responder_pregunta()`:
  - sin `entidades_validadas` envía las entidades del resultado y responde con ellas, sin aviso;
  - con `entidades_validadas` envía esas entidades, y el contexto no lleva ni la clave `changes` ni el valor original de un campo cambiado;
  - devuelve con `changes` una evidencia sobre un campo cambiado, una sobre un elemento de una lista cambiada (`procedures.0.desc`) y una sobre un objeto que contiene un campo cambiado (`patient`);
  - devuelve sin `changes` una evidencia sobre un campo que no ha cambiado y una de `metadata`;
  - responde sobre un campo cambiado con el valor validado y la frase del aviso, con el valor del modelo o diciendo que no había extraído ninguno;
  - menciona una sola vez un cambio que comparten dos evidencias;
  - añade el aviso a la respuesta de dato ausente cuando una persona vació el campo.
- `tests/test_app.py` comprueba con `AppTest`, sin red y sustituyendo `responder_pregunta()`, que:
  - con ediciones sin validar, el chat recibe `None` como `entidades_validadas` y la pestaña dice que responde con el JSON del modelo;
  - tras pulsar «Marcar como validado», recibe el JSON editado y la pestaña dice que responde con el JSON validado;
  - con una copia validada y ediciones posteriores, sigue recibiendo la copia validada y la pestaña avisa de que hay cambios sin validar;
  - una respuesta cuya evidencia lleva `changes` muestra la ruta del campo y el valor del modelo.
- `src/app.py` no contiene la comparación entre los dos JSON ni la función `_reviewed_result()` (comprobable con una búsqueda en el fichero).
- Prueba manual con la API real, anotada en el PR: con `med_doc_bill_100001_noisy.jpg`, corregir `patient.mrn` y preguntar por el MRN antes de validar (responde el valor del modelo); marcar como validado y volver a preguntar (responde el valor corregido, dice que una persona lo corrigió y cuál era el valor del modelo, y bajo la respuesta aparece el campo corregido).
- `README.md` y `ARCHITECTURE.md` actualizados: la versión del JSON que usa el chat, `revision.py` y la nueva firma de `responder_pregunta()`.
- `python -m pytest`, `ruff check .` y `ruff format --check .` en verde.
