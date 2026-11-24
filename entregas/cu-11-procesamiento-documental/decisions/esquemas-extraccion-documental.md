---
description: Define los esquemas JSON independientes para facturas médicas e informes de alta, solo con los campos visibles en las imágenes, y la verdad de referencia limpia con la que se evalúa.
state: Aceptado
---

# ADR — Esquemas de extracción documental

## Decisión

El sistema utilizará dos esquemas JSON independientes:

- `bill`, definido en `src/Hospital_Bill.json`.
- `discharge_summary`, definido en `src/Discharge_Summary.json`.

Los esquemas tienen estructuras y campos propios para cada tipo documental.
`bill` incluye, entre otros, `insurance`, `financials` y los campos `cpt` y
`price` de sus procedimientos. `discharge_summary` incluye `hospital_course`,
`medications` y procedimientos con su propia estructura. Cada esquema sigue
los datos de referencia y los ejemplos proporcionados por el dataset.

Los archivos seguirán JSON Schema Draft 2020-12 y se utilizarán para describir
y validar las respuestas estructuradas del modelo.

Cada respuesta deberá mantener todas las claves obligatorias del esquema
correspondiente. Cuando un campo no aparezca en la imagen o no pueda
identificarse, se representará con el valor `null`.

No se permitirán propiedades adicionales que no estén definidas en el esquema.

Cada esquema contiene solo los campos que aparecen en las imágenes de su tipo.
Los campos de la verdad de referencia original que no se ven en ellas se quitan
del esquema y de la verdad de referencia:

| Tipo | Campos que se quitan |
|---|---|
| `bill` | `medications` |
| `discharge_summary` | `hospital.address`, `hospital.npi`, `cpt` y `price` de cada procedimiento, `insurance`, `financials` |

La verdad de referencia sin esos campos se genera con
`Notebooks/limpieza_datos.ipynb` a partir de los CSV de `data/raw/`, que no se
modifican, y se guarda en `data/processed/`. La ingesta y la evaluación usan
esa verdad limpia, no la original. Cada esquema debe tener los mismos campos y
tipos que la verdad limpia de su tipo.

La evaluación compara todos los valores no nulos de la verdad limpia. Un valor
de referencia que falta en la extracción cuenta como error, aunque su
visibilidad en esa imagen concreta no se haya verificado. Las referencias nulas
no se puntúan.

## Motivación

Las facturas médicas y los informes de alta son clases documentales
diferentes. Mantener un esquema independiente para cada una evita imponer una
estructura común y permite que cada definición evolucione de forma separada.

El uso de JSON Schema permite validar automáticamente las respuestas del
modelo, comprobar los tipos de datos y detectar propiedades inesperadas.

Mantener las claves obligatorias con valor `null` cuando no haya datos facilita
la validación, la edición humana en Streamlit, la exportación y la evaluación
frente a la verdad de referencia.

El `json_data` de los CSV originales contiene, para cada tipo, campos que no
aparecen en ninguna de sus imágenes. Si se conservaran, el modelo solo podría
devolverlos como `null` y la evaluación los contaría como fallos, de modo que
las métricas no reflejarían cómo lee el modelo los documentos. Quitarlos del
esquema y de la verdad de referencia hace que todo lo que se evalúa sea
observable en la imagen.

Esta decisión sustituye a la anterior, que conservaba esos campos en el esquema
y dejaba para la evaluación distinguir los no observables.

La limpieza quita campos enteros por tipo documental, no valores imagen a
imagen. Si hay dudas sobre si un valor concreto se ve en su imagen, debe
comprobarse con revisión humana.

## Alternativas consideradas

- **Un único esquema común para los dos tipos**, con todos los campos
  opcionales. Rechazada: las facturas y los informes de alta casi no comparten
  campos fuera de `hospital`, `patient` y `diagnosis`. Con un esquema común, el
  modelo puede rellenar campos del otro tipo, como `medications` en una
  factura, y la validación no lo detecta. Las tablas y la exportación tendrían
  además secciones vacías según el tipo.
- **Conservar todos los campos de la verdad de referencia original** y dejar
  que la evaluación distinga los que no se ven. Era la decisión anterior.
  Sustituida: el modelo solo podía devolverlos como `null`, la evaluación los
  contaba como fallos y las métricas mezclaban errores de lectura con datos que
  no están en la imagen.
- **Omitir las claves que no aparecen** en lugar de devolverlas con `null`.
  Rechazada: sin una forma fija, las tablas editables, la exportación CSV y la
  comparación con la verdad tendrían que adivinar qué claves faltan. Además,
  no se podría distinguir «el modelo vio que no estaba» de «el modelo olvidó la
  clave».
- **Permitir propiedades adicionales** (`additionalProperties: true`).
  Rechazada: el modelo inventa claves (por ejemplo, `hospital.phone`) que no se
  evalúan ni se exportan con estructura. Los campos que pide la persona
  usuaria van en `additional_fields`, fuera de `entities`.
- **Definir los tipos con modelos Pydantic** y generar el JSON Schema desde
  ellos. Rechazada: los esquemas se insertan tal cual en el prompt (como
  esqueleto) y los leen la validación, las tablas y la evaluación. Un fichero
  JSON es la única fuente para todos ellos, sin depender de un lenguaje ni
  añadir una dependencia. `jsonschema` ya valida tipos, `required`, `format:
  date` y `additionalProperties`.
- **Delegar el cumplimiento del esquema en Groq** (`json_schema` estricto).
  Probada y descartada: Groq no lo aplicó en las peticiones con imagen. Ver el
  [ADR de Groq](modelo-via-api-groq.md). El esquema se valida en el cliente.

## Consecuencias

- El cliente de Groq deberá seleccionar el esquema según la clase documental.
- La validación deberá aplicar el esquema correspondiente a cada respuesta.
- Los cambios futuros en los campos deberán actualizar el archivo de esquema
  correspondiente.
- La aplicación y los scripts de evaluación deberán conservar los nombres de
  campo definidos en los esquemas.
- Una respuesta con propiedades no definidas será inválida.
- La evaluación compara con la verdad de referencia limpia de
  `data/processed/`. Un `null` en la extracción cuenta como campo ausente si
  esa verdad tiene un valor. Las referencias nulas no se puntúan.
- Si cambia un esquema, hay que regenerar la verdad limpia con el notebook para
  que sigan teniendo los mismos campos.
- Las tablas, la edición y la exportación de la aplicación dependen del tipo
  documental: una factura no tiene medicamentos y los procedimientos de un
  informe de alta solo tienen descripción.

## Referencias

- `src/Hospital_Bill.json` y `src/Discharge_Summary.json`: los dos esquemas,
  en el repositorio del código, que es privado. Más abajo hay un fragmento, y
  los campos que se quitan de cada uno están en la tabla de «Decisión».
- `Notebooks/limpieza_datos.ipynb`, en el mismo repositorio: genera la verdad
  limpia de `data/processed/` quitando esos campos.
- [`specs/evaluacion-metricas.md`](../specs/evaluacion-metricas.md): cómo se
  compara la extracción con la verdad limpia.
- Especificación de JSON Schema Draft 2020-12:
  https://json-schema.org/draft/2020-12
- Guía de `null`, `required` y `additionalProperties`:
  https://json-schema.org/understanding-json-schema/reference/object
- Librería `jsonschema` de Python, validación y `FormatChecker`:
  https://python-jsonschema.readthedocs.io/en/stable/validate/
- Salidas estructuradas de Groq (por qué no se usa `json_schema` estricto):
  https://console.groq.com/docs/structured-outputs
- Dataset original: https://www.kaggle.com/datasets/devp1866/noisy-medical-document-images-ocr

Fragmento de `src/Hospital_Bill.json`: cada objeto cierra sus propiedades y
declara todas sus claves como obligatorias, pero admite `null`.

```json
"patient": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": { "type": ["string", "null"] },
    "dob":  { "type": ["string", "null"], "format": "date" },
    "mrn":  { "type": ["string", "null"] }
  },
  "required": ["name", "dob", "mrn"]
}
```

Cómo se aplica en `src/procesamiento_documental/validacion.py`. `FormatChecker`
es necesario para que `format: date` se compruebe; sin él, solo se anota.

```python
from jsonschema import Draft202012Validator, FormatChecker

validator = Draft202012Validator(
    load_extraction_schema(document_type), format_checker=FormatChecker()
)
errors = [error.message for error in validator.iter_errors(data)]
```

El mismo esquema se convierte en un esqueleto para el prompt
(`prompts.schema_skeleton`), de modo que el modelo ve exactamente las claves
que luego se validan:

```json
{"patient": {"name": "string|null", "dob": "YYYY-MM-DD|null", "mrn": "string|null"}}
```
