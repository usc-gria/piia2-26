---
description: La inferencia se hace con la API de Groq; el modelo concreto se lee de GROQ_MODEL y no se fija en el código.
state: Aceptado
---

# ADR — Inferencia con la API de Groq

## Decisión
La clasificación, la extracción de entidades y las preguntas sobre el documento se resuelven llamando a la API de Groq. El nombre del modelo se lee de la variable de entorno `GROQ_MODEL` y la clave de `GROQ_API_KEY`. El modelo es `qwen/qwen3.8-27b` (`README.md`, «Tecnologías»): es el único de Groq que acepta imágenes y salida en modo JSON, así que no hay otro entre el que elegir. `specs/evaluacion-metricas.md` mide si cumple los objetivos de calidad, pero no decide si se usa.

## Motivación
SDG indicó Groq como servicio de inferencia. No requiere GPU propia, y Groq ofrece modelos multimodales con salida en modo JSON. Sus modelos con visión están en *preview* y pueden retirarse, por eso el modelo se cambia sin tocar el código.

Groq también ofrece salida ajustada a un esquema (`json_schema` en modo estricto), pero no la aplicó en nuestras peticiones con imagen: el 19-11-2026 rechazó con un 400 `json_validate_failed` 11 de 22 extracciones y 2 clasificaciones. Por eso no se confía en Groq para cumplir el esquema: se le pide un objeto JSON (`json_object`) y el esquema se valida en el cliente, que pide al modelo corregir la respuesta si no lo cumple (ver el [ADR de validación en el cliente](validacion-esquema-en-cliente.md)).

## Alternativas consideradas
- Inferencia local con vLLM y un modelo abierto. Rechazada: requiere una GPU que no tenemos. `README.md` la deja fuera del proyecto, sin condiciones.
- Otros proveedores de API con modelos de visión. No se evaluaron: `cliente.py` está escrito contra el SDK de Groq, su modo `json_object` y sus códigos de error (`json_validate_failed`, 429 con `retry-after`), que traduce `mensajes.py`. Cambiar de proveedor obligaría a rehacer el cliente y los mensajes, sin un beneficio medido que lo justifique. Además, SDG pidió Groq.
- Fijar el nombre del modelo en el código. Rechazada: si Groq retira el modelo o publica otro con visión habría que cambiar código.
- Elegir otro modelo de Groq. No hay alternativa: `qwen/qwen3.8-27b` es el único que acepta imágenes y salida en modo JSON.

## Referencias
- Visión en Groq (formato de la imagen como *data URL* y límites de tamaño): https://console.groq.com/docs/vision
- Salidas estructuradas, `json_object` frente a `json_schema`: https://console.groq.com/docs/structured-outputs
- Límites de uso por nivel (el diario de tokens cortó la primera prueba): https://console.groq.com/docs/rate-limits
- Códigos de error de la API: https://console.groq.com/docs/errors
- SDK de Python: https://github.com/groq/groq-python
- Planificación acordada con SDG (`docs/Planificación.pdf`, no publicado). En la semana 1 fija «configurar el entorno de desarrollo en Python y el acceso a la API online». La inferencia local queda como ampliación: «reemplazar las llamadas a la API online por un servidor local propio utilizando vLLM con un modelo abierto (ej. Qwen2-VL) […] sin modificar el código de la interfaz».
- Acta de la reunión con SDG del 22-10-2026: «Probar groq, aunque sea algo tipo "hola mundo"».
- Mediciones que justifican validar el esquema en el cliente. Salen de los CSV de `script/evaluar_metricas.py`, que no se versionan; el detalle está en `README.md`, sección «Tecnologías».

  | Ejecución | Forma de pedir la respuesta | Documentos que llegaron al modelo | Rechazos 400 `json_validate_failed` | JSON válidos |
  |---|---|---|---|---|
  | 19-11-2026, 12:24 | `json_schema` estricto | 24 | 11 de 22 extracciones y 2 de 24 clasificaciones | 11 / 24 |
  | 19-11-2026, 18:25 (`PROMPT_VERSION` 1.2) | `json_object` y validación en el cliente | 8 facturas (cortada por la cuota, 429) | 0 | 7 / 8 |

  Uno de los rechazos de clasificación traía un `document_type` fuera del `enum`. Con el modo estricto aplicado de verdad, eso sería imposible: por eso se concluye que Groq no lo aplicaba. La segunda ejecución es demasiado pequeña para saber si el modelo cumple los objetivos, pero no tuvo ningún rechazo.

Cómo se llama a Groq en `src/procesamiento_documental/cliente.py`. Es la única llamada del proyecto. El SDK no reintenta (`max_retries=0`): los reintentos los hace el cliente, para medir bien la latencia y respetar `retry-after`.

```python
import os
import groq

client = groq.Groq(api_key=os.environ["GROQ_API_KEY"], max_retries=0)
response = client.chat.completions.create(
    model=os.environ["GROQ_MODEL"],
    messages=[
        {"role": "system", "content": prompt_con_esqueleto_del_esquema},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the entities."},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },
            ],
        },
    ],
    response_format={"type": "json_object"},  # no "json_schema": ver Motivación
    temperature=0,
)
```

Configuración local, en `.env` (no se versiona):

```
GROQ_API_KEY=gsk_...
GROQ_MODEL=<modelo con visión y modo JSON>
```
