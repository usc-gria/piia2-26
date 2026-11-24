# Modelo de supervivencia en tiempo discreto

Estado: aceptada. Relacionada con la [spec de predicción](../specs/prediccion-supervivencia.md) y con
C5 y C6 de la [arquitectura](../ARCHITECTURE.md).

## Decisión

Usamos supervivencia en tiempo discreto con landmarks diarios y, como clasificador,
`HistGradientBoostingClassifier` de scikit-learn con parámetros fijos. Entrenamos dos modelos iguales:
uno para el cierre y otro para la reapertura.

En la práctica: cada día que un polígono está abierto es una foto. Esa foto se repite una vez por
cada día siguiente (hasta 14) y se marca con un 1 solo el día en que cierra. El clasificador aprende el
riesgo de cerrar cada uno de esos días, y la probabilidad de seguir abierto *h* días es el producto de
(1 − riesgo) desde el día 1 hasta el *h*. Si dejamos de saber el estado del polígono, se corta ahí
(censura) y no nos inventamos el final.

## Por qué

Todo viene de lo que nos pasó en PIIA 1. Allí predecíamos con XGBoost si el polígono estaría cerrado
al día siguiente y sacábamos un F1 de 0,93. Al revisarlo vimos que copiar el estado de hoy daba 0,942:
de 19.136 filas de test solo 143 cambiaban de estado. El modelo no anticipaba nada, simplemente
acertaba que mañana suele ser igual que hoy.

Con supervivencia ese atajo desaparece, porque el modelo de cierre solo ve polígonos que están
abiertos, que son los que todavía pueden cerrar. Además contesta a lo que le interesa a un productor
("¿voy a poder seguir sacando mejillón la semana que viene?") a 1, 3, 7 y 14 días con un solo modelo.
Y como al final es una clasificación, seguimos trabajando con lo que ya sabíamos de PIIA 1.

Lo de usar gradient boosting en vez de algo lineal lo decidimos con el prototipo de Arousa, validando
año a año de 2018 a 2025 (`resultados/cv_modelos.csv`):

| | AUC a 7 días | Índice C | Brier a 7 días |
|---|---|---|---|
| Gradient boosting | 0,873 | 0,790 | 0,031 |
| Regresión logística (tiempo discreto) | 0,782 | 0,736 | 0,032 |
| Regla simple (% del límite en la última analítica) | 0,785 | 0,700 | |

El boosting ganó a la logística los 8 años. La logística ni siquiera mejoraba la regla simple. Creemos
que hay dos motivos: el riesgo no crece de forma lineal con la toxina (estar al 90 % del límite no es
el doble de peligroso que estar al 45 %) y la logística necesita rellenar los huecos. En 2025, que
faltaba el 74 % de la meteo, se quedó en 0,639. El boosting acepta valores vacíos sin hacer nada, y eso
nos viene muy bien porque las analíticas son semanales y casi todas las fuentes tienen huecos.

Con el modelo de las tres rías, en la prueba estricta (entrenar hasta 2021 sin la ría evaluada y
evaluar 2022-2025), sacamos 0,879 de AUC en cierre y 0,818 en reapertura. La regla simple saca 0,814 y
0,731.

## Alternativas que descartamos

- **Seguir con el clasificador de "mañana sí o no" de PIIA 1.** Es justo lo que queríamos cambiar.
- **Regresión logística en tiempo discreto.** La probamos y se quedó por debajo de la regla simple.
- **Modelo de Cox** (por ejemplo con `lifelines`). Supone que cada variable pesa igual durante los 14
  días y no admite huecos. Como nuestras variables cambian cada día, habría que montarlo con
  covariables dependientes del tiempo, que es bastante más lío para nosotros.
- **Random Survival Forest** (`scikit-survival`). Más pesado y tampoco admite huecos. En la entrega 1
  ya decidimos quedarnos con un único método que pudiéramos entender y defender bien.
- **XGBoost o LightGBM.** Son lo mismo que el `HistGradientBoostingClassifier` que ya trae scikit-learn,
  que también acepta huecos y variables categóricas. No nos compensaba añadir otra librería.
- **Predecir directamente los días hasta el cierre** con una regresión. No sabe qué hacer con las vidas
  que no sabemos cómo terminan, habría que tirarlas.
- **Equilibrar las clases** (`class_weight='balanced'`). Detecta más cierres, pero las probabilidades
  dejan de ser probabilidades, y las necesitamos para multiplicarlas.
- **Buscar hiperparámetros.** Con pocos episodios por año acabaríamos ajustando el modelo a la propia
  validación. Lo dejamos con parámetros fijos, como pusimos en la spec.

## Consecuencias

Las probabilidades nunca suben al alargar el horizonte, porque cada día se multiplica por algo menor
que 1 (es el CA1 de la spec 2). Por otro lado, repetir cada foto hasta 14 veces hace que haya muchas
filas, así que entrenamos con una foto de cada dos días (`paso=2`); dos días seguidos de la misma vida
son casi iguales y el resultado apenas cambia. Y hay que tener claro que el modelo ordena bien el
riesgo, pero sus probabilidades son orientativas: en Vigo, en la prueba estricta de cierre, el Brier es
peor que el de Kaplan-Meier (BSS −0,062).

## Referencias

El código está en `bateas/supervivencia.py` (`tabla_landmarks`, `expandir` y `ModeloSupervivencia`).
Así se pasa de una foto a una fila por día (versión resumida de `expandir`):

```python
n = np.minimum(lm['T'], horizonte)                  # días observados de cada foto
idx = np.repeat(np.arange(len(lm)), n)              # una fila por día k
k = np.arange(len(idx)) - np.repeat(np.cumsum(n) - n, n) + 1
X = lm[features].iloc[idx].assign(k=k)
y = (lm['E'].to_numpy()[idx] == 1) & (k == lm['T'].to_numpy()[idx])   # 1 solo el día del cambio
```

Y del riesgo de cada día a la probabilidad de seguir igual:

```python
riesgo = modelo.predict_proba(X_pred)[:, 1].reshape(n_fotos, 14)
S = np.cumprod(1 - riesgo, axis=1)                   # S[:, 6] = P(seguir abierto 7 días)
```

Los parámetros que usamos:

```python
HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_leaf_nodes=31,
                               min_samples_leaf=200, l2_regularization=1.0,
                               categorical_features='from_dtype', random_state=42)
```

Documentación y lecturas que nos sirvieron:

- `HistGradientBoostingClassifier`: <https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html>
- Cómo trata los valores vacíos: <https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting>
- Singer y Willett (1993), *It's about time: Using discrete-time survival analysis to study duration
  and the timing of events*, Journal of Educational Statistics 18(2). De aquí sacamos la idea de una
  fila por periodo.
- van Houwelingen (2007), *Dynamic prediction by landmarking in event history analysis*, Scandinavian
  Journal of Statistics 34(1). Lo de los landmarks.
- `lifelines`: <https://lifelines.readthedocs.io> y `scikit-survival`: <https://scikit-survival.readthedocs.io>,
  las dos alternativas que miramos.

Los números salen de `resultados/cv_modelos.csv` y de la sección 5 de
`notebooks/modelo_supervivencia_piia2_arousa.ipynb`. Lo del F1 de PIIA 1 se puede reproducir con
`scripts/auditoria_modelo_piia1.py`.
