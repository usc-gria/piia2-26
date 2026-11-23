# ADR 2: Cuándo cuenta un dato como acierto en el corrector

- **Estado:** aceptada (reglas de números desde el 24/10/2026; reglas de textos desde el 10/11/2026; dosis leídas de gráficas desde el 17/11/2026)
- **Afecta a:** el corrector, el emparejamiento de casos, el análisis de errores y la revisión con el artículo abierto

## Decisión

Si el sistema y las expertas dan los dos un valor, el dato es **acierto (TP)** cuando, después de normalizar los dos lados, se cumple la regla de su tipo. Si no se cumple, es **FP1**.

- **Números:** se pasan los dos a la unidad fija de la variable y se aceptan con una **tolerancia relativa del 1 %** respecto al valor de las expertas. Si el valor de las expertas es 0, el del sistema tiene que ser exactamente 0.
- **Dosis leídas de una gráfica** (las que marca la hoja `GRAPHS`): tolerancia del **20 %** y, aparte, su error relativo medio y su mediana, como la Table S3 del estudio.
- **Textos:** regla **`limpio+sistema_contiene`**. Se normalizan los dos lados, se quita lo que sabemos que sobra (la ciudad y el país de los proveedores, y todo menos el mecanismo en la tecnología) y el texto del sistema tiene que contener **entero** el de las expertas, en palabras completas.
- **Unidad que no se puede convertir** (por ejemplo, una dosis en µg/cm²): cuenta como **FP1**.

El corrector da siempre **dos notas**: la normal, con estas reglas, y la **estricta** (`exactitud_estricta`), en la que los textos tienen que ser iguales después de normalizar.

Las reglas se configuran en un único sitio (`Parametros`, en `src/piia/evaluacion/corrector.py`). Para volver a corregir con otras reglas solo se cambia ese objeto, sin tocar la clasificación.

## Motivación

Con el corrector medimos todo el proyecto: la elección de modelo, cada cambio de prompt y la prueba final. Pero una misma respuesta puede ser TP o FP1 según cómo se comparen los valores, y un mismo dato se escribe de muchas formas:

| Expertas | Sistema | ¿Mismo dato? |
|---|---|---|
| 2,6 mPa·s | 0,0026 Pa·s | Sí: otra unidad |
| HP_970 | HP 970 | Sí: las expertas escriben con guion bajo |
| Empresa X | Empresa X (Ciudad, País) | Sí: el proveedor es el mismo |
| piezoelectric | piezoelectric inkjet printing | Sí: el mecanismo es el mismo |
| piezoelectric inkjet | inkjet | No: la respuesta del sistema está incompleta |

Para elegir el criterio había cuatro condiciones:

1. **Medir errores de contenido, no de forma.** Un dato bien extraído pero escrito de otra manera no es un fallo del sistema. Si cuenta como error, el análisis de errores se llena de falsos errores y no muestra dónde falla de verdad el LLM.
2. **Poder compararnos con el estudio.** El objetivo es acercarse al 94 % de GPT-4. Tiene que haber una nota que cuente como el estudio, para separar la mejora del sistema de la que viene de contar de otra forma.
3. **Que cada regla se pueda explicar con ejemplos reales del Excel.** No queremos reglas genéricas que acepten cosas sin querer. En la revisión, un error cuya causa es `regla` (no hay un criterio claro de qué es lo correcto) es la señal de que hay que revisar el criterio.
4. **Que se pueda cambiar y medir.** Todo lo discutible tiene que ser un parámetro, para ver cuánto cambia la nota con cada opción.

**Dos notas** por la condición 2. La estricta reproduce la base de **0,9357** de GPT-4 del estudio. La normal es la que usamos para decidir, por la condición 1.

**La misma tolerancia y la misma normalización en el emparejamiento** (`emparejamiento.py`), para que un caso no se empareje con un criterio y luego se corrija con otro.

## Alternativas consideradas

### 1. Igualdad exacta para todo

Descartada como nota principal. Un cambio de unidad, un redondeo o un guion bajo darían error en datos correctos (condición 1). Se queda como **nota estricta** porque es la que permite compararnos con el estudio.

La diferencia no es pequeña. En la prueba de los modelos de razonamiento (ADR 1), el agente de impresión con Qwen3 Next sacó **0,404** con la comparación estricta y **0,603** con la flexible, con las mismas respuestas.

### 2. Otras reglas para los textos

Todas están implementadas en `comparacion.REGLAS_TEXTO`, con y sin limpieza, para poder medirlas (Issue #53):

| Regla | Qué acepta | Por qué se descartó |
|---|---|---|
| `igualdad` | Solo textos iguales tras normalizar | Penaliza diferencias de forma (proveedor con ciudad, «piezoelectric inkjet printing»). Es la nota estricta. |
| `contiene` | Uno dentro del otro, en cualquier dirección | Da por buena una respuesta incompleta: «inkjet» frente a «piezoelectric inkjet». |
| `sistema_contiene` sin limpiar | El texto del sistema contiene al de las expertas | Falla cuando son las expertas quienes añaden ciudad y país, o cuando el sistema da solo el mecanismo. |
| `parecido` (difflib ≥ 0,9) | Textos muy parecidos | Dos modelos distintos pueden tener nombres casi iguales («HP 970» y «HP 979»). Un umbral de parecido no distingue una errata de un dato distinto. |

La limpieza se aplica solo a las variables en las que sabemos qué sobra: los cuatro proveedores y `Inkjet_technology`. En el resto de variables, el texto se compara tal como queda tras normalizarlo (condición 3).

### 3. La misma tolerancia para las dosis leídas de gráficas

Descartada. Un valor leído a ojo de una figura nunca es exacto, así que con un 1 % casi todas esas dosis saldrían como error aunque estén bien leídas. Subir la tolerancia al 20 % sin más tampoco servía, porque escondería si el lector de gráficas mejora o empeora. Por eso se da también su error relativo aparte (punto 8, opción A + C; equipo y tutor, 17/11/2026).

### 4. Excluir los datos con una unidad que no se puede convertir

Descartada por defecto. Excluirlos puede esconder errores reales del sistema. Contarlos como FP1 a veces castiga un dato correcto en otra unidad, pero ese caso se ve en la revisión. Se puede cambiar con `unidad_incompatible="excluir"` (punto 16).

## Consecuencias

- Las notas, el análisis de errores y la revisión parten de la misma clasificación. Los errores que llegan a la revisión son, en su mayoría, de contenido.
- Todos los informes tienen que dar **las dos notas** e indicar con qué `Parametros` se han calculado. Una nota sin sus reglas no se puede comparar con otra.
- La tolerancia del 1 % y la regla de textos son criterios nuestros, no del estudio. Para comparar con el 94 % de GPT-4 se usa la nota estricta.
- `sistema_contiene` puede premiar respuestas demasiado largas: si el sistema da varias impresoras y una es la correcta, cuenta como acierto. Hay que vigilarlo en la revisión de errores.
- Cambiar una regla cambia las cifras de todas las pruebas anteriores. Si se cambia, se vuelven a corregir los resultados guardados antes de comparar.

## Referencias

### Cómo se aplica en el código

`src/piia/evaluacion/corrector.py` (resumido): las reglas discutibles son parámetros.

```python
@dataclass(frozen=True)
class Parametros:
    tolerancia: float = 0.01               # números: 1 % respecto a las expertas
    tolerancia_grafica: float = 0.20       # dosis leídas de gráficas (punto 8)
    unidad_incompatible: str = "fp1"       # o "excluir" (punto 16)
    regla_textos: str = REGLA_TEXTOS       # "limpio+sistema_contiene" (punto 17)
    umbral_parecido: float = UMBRAL_PARECIDO  # solo para las reglas "parecido"
```

`src/piia/evaluacion/comparacion.py` (resumido): normalización y reglas de comparación.

```python
def normalizar_texto(texto: str) -> str:
    # NFKC (µ = μ, ² = 2), guiones y comillas a ASCII, minúsculas,
    # guion bajo como espacio y sin puntuación en los extremos.
    t = unicodedata.normalize("NFKC", texto).translate(_GUIONES).translate(_COMILLAS).casefold()
    return re.sub(r"[\s_]+", " ", t).strip(" .,;:")

def _sistema_contiene(gt: str, sis: str, umbral: float) -> bool:
    # Una respuesta incompleta («inkjet» frente a «piezoelectric inkjet») no cuenta.
    return gt == sis or _contiene(sis, gt)

def numeros_iguales(sistema: float, gt: float, tolerancia: float) -> bool:
    if gt == 0:
        return sistema == 0
    return abs(sistema - gt) <= tolerancia * abs(gt) * (1 + 1e-9)
```

Corregir con otras reglas, sin tocar el código:

```python
from piia.evaluacion.corrector import Parametros, corregir

evaluacion = corregir(carpeta_gt, carpeta_resultados,
                      parametros=Parametros(regla_textos="limpio+parecido"))
evaluacion.metricas  # exactitud normal y exactitud_estricta, global, por bloque y por variable
```

### Detalles prácticos

- **Número frente a texto** («~20» frente a 20): se comparan como texto, con el número escrito a 15 cifras significativas para no redondearlo.
- **El margen de `1e-9`** evita que 101 frente a 100 quede fuera del 1 % por redondeo de coma flotante.
- **`clase_estricta`** se calcula con las mismas reglas que la clase normal salvo la de textos. Los datos que cuentan son los mismos y solo puede cambiar un TP por un FP1.
- **Las dosis de gráficas se enlazan por artículo, orden y formulación**, porque `graficas.csv` no tiene el identificador de caso de `casos.csv`. Lo que no se enlaza se corrige con la tolerancia normal.

### Documentación

- Estudio de referencia: Carou-Senra et al., *Int. J. Pharm.* 691 (2026), iMATUS. Clasificación TP, FP1, FP2, FN y TN (Table 2), exactitud (Eq. 3) y error de las dosis leídas de gráficas (Table S3).
- Python: [`unicodedata.normalize`](https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize) y [`difflib.SequenceMatcher`](https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher).
- Reglas de conteo del proyecto: `decisiones.md` §5 (puntos 8, 16 y 17) e Issue #53.

### Cómo se comprobó

- **Artículos:** solo los 20 de desarrollo. Los 50 reservados no se han usado.
- **Nota estricta:** con las respuestas de GPT-4 del estudio y emparejamiento por orden, da **0,9357**, la base del estudio.
- **Efecto de la regla de textos:** en el agente de impresión con Qwen3 Next (ADR 1, 10/11/2026), 0,404 con la nota estricta y 0,603 con la normal.
- **Fechas:** reglas de números, 24/10/2026; reglas de textos, acordadas por el equipo el 10/11/2026; dosis leídas de gráficas, acordadas por el equipo y el tutor el 17/11/2026.
