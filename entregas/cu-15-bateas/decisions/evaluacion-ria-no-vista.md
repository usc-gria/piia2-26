# Evaluación en una ría que el modelo no ha visto

Estado: aceptada. Relacionada con la [spec de predicción](../specs/prediccion-supervivencia.md), con
la [spec del informe](../specs/informe-dependencia-datos.md) y con C7 de la
[arquitectura](../ARCHITECTURE.md).

## Decisión

Siempre evaluamos entrenando sin la ría que se evalúa y solo con datos de antes del periodo
evaluado. Lo hacemos de dos formas:

- **Año a año**, para decidir cosas. Para cada año de 2018 a 2025 y cada ría, entrenamos con las otras
  dos rías hasta ese año (dejando 14 días de hueco) y evaluamos esa ría durante ese año. Son 8 × 3 = 24
  pruebas.
- **Prueba estricta**, que es el resultado que presentamos. Entrenamos una vez con las otras dos rías
  hasta 2021 y evaluamos 2022-2025.

La métrica principal es el AUC a 7 días comparado con la regla simple (más riesgo cuanto más cerca del
límite estuvo la última analítica). Para ver si las probabilidades valen algo usamos el Brier frente a
Kaplan-Meier. Cuando comparamos dos versiones del modelo calculamos un intervalo de confianza del 95 %
remuestreando años enteros. El F1 lo damos, pero no decidimos con él.

## Por qué

Uno de los objetivos del proyecto es saber si el modelo funciona en una ría nueva, y eso solo se
puede comprobar si esa ría no aparece en el entrenamiento. Por eso dejamos fuera la ría entera y no
unos días o unos polígonos al azar.

Lo del corte temporal lo aprendimos por las malas. Las algas afectan a toda la costa a la vez
(Pontevedra cierra casi siempre primero y luego Vigo y Arousa), así que si entrenas con las otras rías
en las mismas fechas que evalúas, el modelo ya "sabe" que ese mes hay episodio. Lo comprobamos con el
modelo de cierre:

| Cómo se entrena | AUC a 7 días |
|---|---|
| Otras rías, mismas fechas que el test | 0,909 |
| Otras rías, solo hasta 2021 (prueba estricta) | 0,879 |
| Prueba estricta pero viendo también el pasado de la ría evaluada | 0,896 |

Sin corte temporal salían tres centésimas de más. Esa cifra la seguimos enseñando en el notebook, pero
como referencia.

Las 24 pruebas vinieron después de un susto. Al principio elegíamos las mejoras con una sola
validación (2019-2021) y luego las comprobábamos en 2022-2025. La exposición del polígono mejoraba el
cierre +0,011 en la validación y lo empeoraba −0,003 en la comprobación (en reapertura, +0,018 y
−0,015). Con un solo periodo puedes acabar quedándote con algo que ha tenido suerte.

El intervalo lo hacemos remuestreando años y no pruebas sueltas porque las tres rías de un mismo año
comparten episodios. Si las tratas como independientes, el intervalo sale más estrecho de lo que
debería.

Y no decidimos con el F1 por dos razones. La primera, que ya nos engañó en PIIA 1 (ver el
[ADR del modelo](modelo-supervivencia-tiempo-discreto.md)). La segunda, que depende del umbral que
elijas para dar la alarma. En la prueba estricta de cierre, con nuestro umbral, la regla simple saca
0,386 y el modelo 0,369. Pero con el mejor umbral posible el modelo llega a 0,395 y la regla a 0,392, o
sea que el modelo ordena igual o mejor y lo que fallamos es en elegir el umbral. El AUC no depende de
eso.

Comparamos con dos referencias porque miden cosas distintas: la regla simple es lo que haría alguien
mirando la última analítica, y Kaplan-Meier es la media histórica. Si el modelo no le gana a la
primera en AUC no aporta nada, y si no le gana a la segunda en Brier sus probabilidades no sirven.

## Alternativas que descartamos

- **Validación cruzada aleatoria.** Mete días seguidos del mismo episodio en entrenamiento y test.
  Además la spec 2 pide particiones temporales.
- **Solo partición temporal, con todas las rías.** No responde a si funciona en una ría nueva.
- **Dejar fuera una ría sin corte temporal.** Da 0,909 en vez de 0,879: demasiado optimista.
- **Un solo periodo de validación.** Es lo que hicimos al principio y nos salió mal con la exposición.
- **Dejar fuera zonas de Arousa.** Era el plan B de la entrega 1 por si no llegaban más rías. Llegaron
  Vigo y Pontevedra.
- **F1 o exactitud como métrica principal.** Dependen del umbral y las domina la clase mayoritaria.
- **Índice C.** Lo calculamos y dice lo mismo que el AUC, pero el AUC a 7 días se le explica mejor a un
  productor.
- **Bootstrap por pruebas sueltas.** Intervalos demasiado estrechos.

## Consecuencias

Recalcular todo cuesta unas dos horas, así que guardamos los resultados en `resultados/` y el notebook
los vuelve a cargar. Las variables de "otras rías" hay que recalcularlas en cada prueba con las rías de
entrenamiento, si no la ría evaluada se cuela por ahí. Y un aviso: 2022-2025 está dentro de las 24
pruebas con las que decidimos, así que la prueba estricta no es del todo limpia. La prueba de verdad
serán los datos de 2026.

## Referencias

El código está en `bateas/multiria.py` (`evaluar_dejando_fuera_ria`, `evaluar_por_anios`,
`intervalo_mejora`) y en `bateas/supervivencia.py` (`evaluar`, `kaplan_meier`, `c_index`).

La partición de la prueba estricta, con el hueco de 14 días:

```python
hueco = pd.Timedelta(days=14)
for ria in rias:
    train = lm[(lm['ria'] != ria) & (lm['fecha'] < corte - hueco)]
    test  = lm[(lm['ria'] == ria) & (lm['fecha'] >= corte)]
```

El bootstrap por años, resumido de `intervalo_mejora`:

```python
dif = auc_config - auc_base                       # una fila por (año, ría)
por_anio = dif.groupby('anio').agg(['sum', 'count'])
muestras = rng.integers(0, n_anios, size=(5000, n_anios))   # se remuestrean años
boot = por_anio['sum'].values[muestras].sum(1) / por_anio['count'].values[muestras].sum(1)
ic95 = np.percentile(boot, [2.5, 97.5])           # "mejora" si ic95[0] > 0
```

El AUC y el Brier a 7 días, resumido de `supervivencia.evaluar`. Las fotos que se cortan antes del día
7 no sabemos si cerraron y no se cuentan:

```python
from sklearn.metrics import roc_auc_score
y = np.full(len(test), np.nan)
y[(test['E'] == 0) & (test['T'] >= 7)] = 0      # siguió abierto 7 días
y[(test['E'] == 1) & (test['T'] > 7)] = 0       # cerró, pero después del día 7
y[(test['E'] == 1) & (test['T'] <= 7)] = 1      # cerró en los 7 días
ok = ~np.isnan(y)
auc_modelo = roc_auc_score(y[ok], (1 - S[:, 6])[ok])
auc_regla  = roc_auc_score(y[ok], test['frac_limite'][ok])
brier      = np.mean(((1 - S[:, 6])[ok] - y[ok]) ** 2)
```

Documentación:

- `roc_auc_score`: <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html>
- `brier_score_loss`: <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html>
- Validación cruzada en scikit-learn (`TimeSeriesSplit`, `LeaveOneGroupOut`), de donde sacamos la idea
  de combinar las dos: <https://scikit-learn.org/stable/modules/cross_validation.html>
- Efron y Tibshirani (1993), *An Introduction to the Bootstrap*, Chapman & Hall, para el bootstrap por
  bloques.

Los números están en `resultados/validacion_anios.csv` (las 24 pruebas), en
`resultados/loro_cierre_temporal.csv` y `loro_reapertura_temporal.csv` (prueba estricta) y en
`mejoras_validacion.csv` y `mejoras_test.csv` (lo de la exposición). En el notebook final son las
secciones 4 a 8.
