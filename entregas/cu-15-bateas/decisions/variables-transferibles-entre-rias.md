# Variables que sirvan en cualquier ría

Estado: aceptada. Relacionada con la [spec de predicción](../specs/prediccion-supervivencia.md) (la
restricción de que el modelo sea transferible) y con C4 de la [arquitectura](../ARCHITECTURE.md).

## Decisión

Construimos las variables para que signifiquen lo mismo en cualquier ría, también en una que el
modelo no ha visto nunca:

- No usamos nada que identifique al polígono: ni su código, ni la zona, ni la especie, ni las
  coordenadas.
- Las toxinas van divididas por su límite legal. `AO_frac = AO / 160`, y 1 quiere decir "justo en el
  límite".
- Solo usamos las toxinas que se acercan al límite con cierta frecuencia en los datos de
  entrenamiento: al menos 20 muestras por encima de la mitad del límite. Ahora mismo son PSP, ASP y
  AO.
- Los vecinos de un polígono son los de su misma zona de INTECMAR y los de las zonas de numeración
  contigua (I con II, II con III...). La zona no entra en el modelo, solo la usamos para saber de qué
  polígonos sacar las variables de vecinos.
- Lo que pasa en las otras rías lo resumimos en proporciones: qué parte de sus polígonos está cerrada
  y qué parte está por encima de la mitad del límite.

## Por qué

Si le das al modelo el nombre del polígono, aprende cosas como "CAMBA-A1 cierra mucho", y eso en una
ría nueva no vale para nada. En el prototipo de Arousa lo vimos claro. Meter la localización (zona,
especie y coordenadas) subía el AUC a 7 días +0,027, pero solo dentro de Arousa. En cambio, sin
localización, entrenar sin una zona de Arousa y predecirla daba casi lo mismo (0,799) que haberla
visto (0,801). Es decir, lo que aprende sin el nombre sí se lleva bien a sitios nuevos.

Lo de dividir por el límite surge porque cada ría tiene sus toxinas. En Arousa solo el AO llega al
límite. En Vigo y Pontevedra también lo hacen la PSP y la ASP (el 1,1 % y el 1,5 % de sus muestras
pasan el límite de PSP). Cada una se mide en unas unidades y tiene un límite distinto, y así "estar al
90 %" quiere decir lo mismo para todas. Además nos permite tener una sola variable, `frac_limite`, con
la toxina que esté más cerca de su límite.

Quitar las toxinas que nunca llegan al límite fue un poco por accidente. En Arousa, cuando las
dejábamos, el AUC a 7 días de 2023 bajaba de 0,78 a 0,55. Sus valores dependen más de cuándo decide
INTECMAR analizarlas que del riesgo real. Como la lista se calcula con los datos de entrenamiento de
cada prueba, si mañana llega una ría con episodios de otra toxina, entra sola.

Los vecinos los definimos por zonas porque no tenemos coordenadas oficiales de Vigo ni de Pontevedra.
En Arousa, que sí tiene coordenadas, comprobamos que la numeración de zonas sigue la costa bastante
bien:

| Dos polígonos de Arousa | Distancia media | Correlación del estado diario |
|---|---|---|
| Misma zona | 2,2 km | 0,67 |
| Zonas contiguas | 4,5 km | 0,55 |
| Otras zonas | 9,1 km | 0,48 |

Y que los vecinos importan se ve a simple vista en las tres rías. Un polígono abierto cierra en la
semana siguiente el 3,9 % de las veces si ningún vecino ha cerrado, el 21,2 % si ha cerrado uno de una
zona de al lado y el 29,2 % si ha cerrado uno de su misma zona.

Para las otras rías elegimos proporciones porque así la variable vale igual tanto si se entrena con
una ría vecina como con dos, y tanto para Pontevedra (8 polígonos) como para Arousa (25).

## Alternativas que descartamos

- **El código del polígono o la zona como variable**, como en PIIA 1: mejora dentro de Arousa pero no
  existe en una ría nueva.
- **Las coordenadas**: es casi lo mismo que el nombre, y las de Vigo y Pontevedra son aproximadas.
- **Las toxinas en sus unidades**: el modelo tendría que aprender cada límite por separado, y hay muy
  pocos ejemplos de PSP y ASP.
- **Meter siempre las cinco toxinas**: AZA y YTX solo meten ruido (lo de 2023).
- **Una lista fija con solo el AO**, como en Arousa: perderíamos los cierres por PSP y ASP de Vigo y
  Pontevedra.
- **Vecinos por distancia**: sería lo ideal, pero no hay coordenadas oficiales.
- **Usar toda la ría como vecindario**: eso ya lo hace el contexto de la ría, y los vecinos cercanos
  aportan más (en reapertura, quitarlos cuesta −0,023 de AUC).
- **Una variable por cada ría**, tipo "estado de Pontevedra": deja de funcionar si falta otra ría o si
  añadimos una cuarta.

## Consecuencias

El modelo tiene 59 variables de datos (más 3 que añade el método), y son las mismas sea cual sea la
ría que dejamos fuera. Para meter una ría nueva no hay que tocar código, pero su Excel tiene que traer
la columna `Zona` con la numeración de INTECMAR; si no, se queda sin variables de vecinos (el
validador avisa). El punto débil es que, si alguna ría numera las zonas sin seguir la costa, la idea
de "zona contigua" deja de funcionar.

## Referencias

El código está en `bateas/features.py` (`toxinas_relevantes`, `anadir_features`),
`bateas/multiria.py` (`vecinos_de`, `anadir_vecinos`, `tabla_otras_rias`, `features_pliegue`) y
`bateas/config.py` (`LIMITES`).

Toxinas en fracción del límite y cuáles entran:

```python
LIMITES = {'PSP': 800, 'ASP': 20, 'AO': 160, 'AZA': 160, 'YTX': 3.75}   # config.py

def toxinas_relevantes(panel, umbral_frac=0.5, min_muestras=20):
    return [t for t, lim in LIMITES.items() if (panel[t] / lim >= umbral_frac).sum() >= min_muestras]

relevantes = toxinas_relevantes(panel_train)       # solo con las rías de entrenamiento
```

Vecinos por zona (resumido de `vecinos_de`):

```python
ROMANOS = ['I', 'II', 'III', 'IV', 'V', 'VI', ...]
for punto, z in zonas.items():
    misma = [q for q, zq in zonas.items() if q != punto and zq == z]
    i = ROMANOS.index(z)
    contiguas = [q for q, zq in zonas.items() if zq in {ROMANOS[i - 1], ROMANOS[i + 1]}]
```

Fuentes:

- Límites legales de biotoxinas en moluscos: Reglamento (CE) 853/2004, anexo III, sección VII,
  capítulo V: <https://eur-lex.europa.eu/eli/reg/2004/853/oj>
- INTECMAR (zonas de producción y análisis): <https://www.intecmar.gal>
- Variables categóricas en el gradient boosting de scikit-learn, que es como habríamos metido la zona
  si no lo hubiéramos descartado: <https://scikit-learn.org/stable/modules/ensemble.html#categorical-features-support>

Los datos de esto están en `resultados/zonas_nuevas.csv` y `cv_ablacion.csv` (prototipo de Arousa,
secciones 7 y 8 de su notebook) y en la sección 3 del notebook final. Los tests `test_vecinos_de` y
`test_otras_rias` de `tests/test_multiria.py` comprueban estas variables.
