---
description: Groq solo devuelve un objeto JSON; el esquema se valida en cliente.py y, si no se cumple, se le pide al modelo que corrija su respuesta, como máximo en 3 llamadas.
state: Aceptado
---

# ADR — Validar el esquema en el cliente y pedir al modelo que corrija

## Decisión
Todas las llamadas a Groq piden `response_format={"type": "json_object"}`. Groq solo garantiza que la salida sea un objeto JSON, no que cumpla el esquema. El esquema se comprueba en `ModelClient.complete()` (`src/procesamiento_documental/cliente.py`) con `jsonschema`:

1. El prompt de sistema incluye un esqueleto de la respuesta, generado desde el esquema con `prompts.schema_skeleton()`.
2. Si la respuesta no cumple el esquema, o Groq la rechaza con un 400 `json_validate_failed` por no ser JSON, el cliente le devuelve al modelo su respuesta y la lista de errores, y le pide que la corrija.
3. Hace como máximo 3 llamadas (`MAX_FORMAT_ATTEMPTS`). Si la última sigue sin cumplir el esquema, la devuelve igualmente y `validacion.py` la marca como inválida. Si la última la rechazó Groq, lanza `ModelError`.

El código nunca repara el JSON: no rellena claves ni borra las que sobran. Cada respuesta cuenta las llamadas que ha necesitado (`attempts`), y la evaluación las guarda, de modo que el coste de las correcciones se ve.

## Motivación
El esquema es el contrato entre el modelo y el resto del sistema: las tablas editables, la exportación y la evaluación dependen de que la extracción tenga exactamente sus claves (ver el [ADR de esquemas](esquemas-extraccion-documental.md)). Hay que garantizarlo en algún sitio.

La primera opción fue pedírselo a Groq con `json_schema` en modo estricto, pero en nuestras peticiones con imagen no lo aplicó. En la ejecución del 19-11-2026 a las 12:24 (24 documentos), Groq rechazó con un 400 `json_validate_failed` 11 de 22 extracciones y 2 de 24 clasificaciones. Una de esas clasificaciones traía un `document_type` fuera del `enum`, algo imposible si el modo estricto restringiera la generación. Groq generaba libremente y solo validaba al final: la mitad de las extracciones se perdían sin ninguna posibilidad de corregirlas.

Validar en el cliente convierte ese rechazo en una segunda oportunidad. Como las llamadas usan `temperature=0`, repetir la misma petición daría la misma respuesta: por eso el reintento lleva los errores concretos, que cambian el prompt.

En la única ejecución hecha desde este cambio (19-11-2026, 18:25, `PROMPT_VERSION` 1.2), las 7 extracciones que llegaron al modelo dieron un JSON válido y no hubo ningún rechazo `json_validate_failed`. Son solo 7 facturas, porque la cuota diaria cortó la prueba: no basta para saber si el modelo cumple los objetivos (ver `README.md`, «Tecnologías»), pero el fallo que motivó la decisión no se repitió.

## Alternativas consideradas
- **`json_schema` estricto en Groq.** Rechazada por las cifras de arriba: con imágenes, Groq no restringía la generación y rechazaba la respuesta entera.
- **`json_object` sin validar el esquema.** Rechazada: una respuesta con claves de menos o de más llegaría a las tablas y a la exportación, y fallaría lejos de su causa.
- **Reparar el JSON en el código**, rellenando las claves que faltan con `null` y quitando las que sobran. Rechazada: ocultaría los errores del modelo, y la evaluación contaría como «leído y ausente» un campo que el modelo ni siquiera devolvió. El modelo debe corregirse a sí mismo o fallar a la vista.
- **Reintentar sin dar los errores.** Rechazada: con `temperature=0` la respuesta se repetiría.
- **Más de 3 llamadas.** Rechazada: cada corrección vuelve a enviar la conversación y gasta cuota, que es el recurso escaso del proyecto (200 000 tokens al día en el nivel `on_demand`). Si 3 llamadas no bastan, la respuesta se marca como inválida y cuenta como fallo en la evaluación.

## Referencias
- Salidas estructuradas de Groq, `json_object` frente a `json_schema`: https://console.groq.com/docs/structured-outputs
- Códigos de error de Groq: https://console.groq.com/docs/errors
- `jsonschema`, validación con `Draft202012Validator` e `iter_errors()`: https://python-jsonschema.readthedocs.io/en/stable/validate/
- [ADR de Groq](modelo-via-api-groq.md) y [ADR de esquemas](esquemas-extraccion-documental.md).
- Pruebas sin red en `tests/test_cliente.py` (repositorio del código).

Bucle de `ModelClient.complete()`, simplificado:

```python
validator = Draft202012Validator(schema, format_checker=FormatChecker())
conversation = list(messages)
for attempt in range(1, MAX_FORMAT_ATTEMPTS + 1):
    call = self._call(conversation)  # json_object, temperature=0
    errors = (
        ["The answer is not valid JSON."]
        if call.rejection is not None  # 400 json_validate_failed
        else schema_errors(validator, call.content)
    )
    if not errors or attempt == MAX_FORMAT_ATTEMPTS:
        return call  # quien llama valida y decide
    conversation.append({"role": "assistant", "content": call.content})
    conversation.append({"role": "user", "content": build_format_retry_prompt(errors)})
```
