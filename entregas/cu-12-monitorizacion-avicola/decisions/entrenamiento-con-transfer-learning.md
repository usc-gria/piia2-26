# ADR - Entrenamiento con aprendizaje por transferencia (Transfer Learning)

## 1. Estado

Aceptada como estrategia inicial, pendiente de validación experimental.

## 2. Contexto y motivación

El proyecto busca estimar el peso individual de pollos, expresado en gramos, a partir de imágenes obtenidas en la explotación avícola de Aviporto. La primera campaña de captura tiene como objetivo registrar imágenes y pesos reales de aproximadamente 30–40 animales diferentes, según el tiempo disponible, con varios fotogramas por individuo. Son cifras de planificación: todavía no se dispone del dataset propio.

El principal desafío es la escasez de **animales independientes con peso conocido**. Disponer de muchos fotogramas no equivale a disponer de muchos ejemplos independientes: las imágenes de un mismo pollo son muy similares. Esto aumenta el riesgo de sobreajuste y dificulta comprobar si el modelo generaliza a otros animales.

Por ello, se propone comenzar con **aprendizaje por transferencia**, reutilizando características visuales aprendidas por modelos preentrenados (por ejemplo, en conjuntos generales de imágenes) y adaptándolas a los datos de Aviporto. Esta estrategia puede reducir la cantidad de datos necesaria frente a entrenar toda una red desde cero. Sin embargo, existe una diferencia entre el dominio del preentrenamiento y las imágenes de granja: reconocer formas y texturas generales no garantiza distinguir pequeñas diferencias de peso entre pollos de aspecto parecido. La utilidad de esas características deberá verificarse experimentalmente.

## 3. Decisión adoptada

Se decide utilizar **Transfer Learning como estrategia inicial** para desarrollar el estimador de peso individual.

Se partirá de un modelo de visión artificial preentrenado y se sustituirá o adaptará su salida para obtener **un único valor numérico: el peso estimado en gramos**. El problema se plantea como **regresión**, no como clasificación, porque el peso es una magnitud continua; dividirlo en categorías supondría perder precisión respecto al valor en gramos solicitado por la [spec de estimación de peso individual](../specs/estimacion-peso-individual.md).

Como punto de partida, se contempla entrenar la nueva capa de regresión manteniendo congeladas las capas preentrenadas. Si los resultados de validación lo justifican, se estudiará ajustar también parte de estas capas (*fine-tuning*). Las funciones de pérdida apropiadas para regresión, como MSE, MAE/L1 o Huber, se seleccionarán durante los experimentos.

**No se fija todavía una arquitectura, configuración de entrenamiento ni biblioteca definitiva.** Se compararán alternativas mediante entrenamiento y validación con los datos disponibles. PyTorch y Torchvision son opciones de implementación, no requisitos cerrados.

## 4. Alternativas consideradas

### 4.1. Entrenamiento desde cero

Consiste en entrenar una red neuronal cuyos parámetros se inicializan sin utilizar pesos preentrenados. Ofrece libertad para adaptar el modelo al problema y evita depender de representaciones aprendidas en otro dominio.

No obstante, con el número reducido de animales previsto, aprender desde cero características visuales útiles podría requerir más datos, tiempo de entrenamiento y capacidad de regularización, con mayor riesgo de sobreajuste. Por ello, no se elige como primera opción, aunque podrá reconsiderarse si la evidencia experimental lo aconseja.

### 4.2. Características manuales y regresión tradicional

Otra opción es extraer medidas geométricas (área aparente, longitud, anchura o proporciones del animal) y utilizarlas en una regresión, por ejemplo lineal o basada en árboles. Su principal ventaja es la interpretabilidad y la posibilidad de funcionar con pocos datos si las medidas son fiables.

Su dificultad es que estas medidas dependen de la postura, la perspectiva, la distancia a la cámara, el encuadre y la posible necesidad de segmentación o calibración. **Estas limitaciones también afectan al Transfer Learning:** una red preentrenada no corrige automáticamente los cambios de escala ni garantiza que la imagen contenga información suficiente para inferir el peso.

Se mantiene como alternativa para comparar en el futuro, pero no como estrategia principal inicial.

## 5. Consecuencias prácticas

- **Datos y trazabilidad:** cada imagen estará vinculada con su identificador de animal, sesión, vídeo de origen, instante y peso real medido en gramos, de acuerdo con los metadatos definidos en el [apartado 4.1 de la arquitectura](../ARCHITECTURE.md#41-datos-de-entrada-y-datasets-preparados) y en el [ADR del dataset trazable con metadatos CSV](dataset-trazable-con-metadatos-csv.md).
- **Particiones sin fuga de información:** todos los fotogramas de un mismo animal se asignarán exclusivamente a entrenamiento, validación o test, mediante una partición agrupada por `animal_id`. El test se reservará para la evaluación final; si el número de grupos no permite particiones suficientemente representativas, se documentará esa limitación.
- **Entrenamiento:** se comparará el entrenamiento de una capa de regresión con el ajuste parcial del modelo preentrenado, utilizando validación para seleccionar las configuraciones. Las transformaciones de aumento de datos, si se usan, se aplicarán solo durante entrenamiento y deberán respetar la información relevante para el peso.
- **Preprocesado y escala:** se respetarán las transformaciones y normalización compatibles con los pesos preentrenados elegidos, de forma coherente en entrenamiento, validación y predicción. Al adaptar las imágenes a la entrada del modelo se evitarán deformaciones innecesarias de sus proporciones. Además, recortar o redimensionar todos los pollos para que ocupen un tamaño similar puede eliminar pistas de tamaño aparente; se deberá estudiar cómo conservar una referencia de escala o condiciones de captura comparables (altura, zoom y encuadre), sin imponer por ahora un método de calibración concreto.
- **Compatibilidad con la fase B:** el estimador se entrenará inicialmente con imágenes individuales de la fase A, pero también deberá recibir los recortes producidos por el detector en la fase B. Se comprobará que el encuadre, la escala y el tratamiento del fondo sean compatibles entre ambos tipos de imágenes. El detector y su entrenamiento quedan fuera del alcance de este ADR.
- **Evaluación:** el modelo seleccionado se evaluará en test con MAE en gramos, MAPE y los números de imágenes y animales diferentes evaluados. Como comprobación adicional, se comparará con un estimador de referencia sencillo que prediga siempre el peso medio de los animales de entrenamiento; esto permitirá valorar si utilizar imágenes mejora una predicción constante. Cuando resulte útil, también se examinarán los errores agrupados por animal para que muchos fotogramas de un mismo pollo no oculten la variabilidad entre individuos.
- **Predicciones y reproducibilidad:** las salidas deberán ser numéricas, finitas y positivas; de no ser así se registrará una incidencia. Cada predicción quedará asociada a su imagen de origen. Se conservarán el modelo, el preprocesado, las particiones, las configuraciones y los resultados para repetir los experimentos.

### Ejemplo de implementación orientativo

Si se emplease PyTorch con una arquitectura de tipo ResNet, la adaptación inicial a regresión podría realizarse así:

```python
from torch import nn
from torchvision.models import resnet18, ResNet18_Weights

modelo = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
for parametro in modelo.parameters():
    parametro.requires_grad = False
modelo.fc = nn.Linear(modelo.fc.in_features, 1)
```

El ejemplo muestra únicamente la congelación inicial de los parámetros y el reemplazo de la salida de clasificación por una salida escalar. **No implica haber elegido ResNet18**, ni constituye un entrenamiento o validación ya realizados.

### Limitaciones y aspectos pendientes

El número previsto de animales puede generar una evaluación poco estable, incluso si se dispone de muchos fotogramas. Asimismo, si los animales capturados presentan un rango de pesos estrecho, una predicción cercana a la media podría obtener un error reducido sin demostrar una relación visual sólida con el peso. Los resultados obtenidos en ese intervalo **no demostrarán generalización a animales de otros pesos, edades o condiciones de captura**.

El uso de modelos preentrenados tampoco garantiza un mejor rendimiento que las alternativas. La ampliación del dataset, la selección de la arquitectura y el tratamiento definitivo de la escala, el encuadre y el fondo dependerán de la captura real y de la evaluación experimental.

## 6. Referencias

1. [PyTorch — Transfer Learning for Computer Vision Tutorial](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html). Ejemplo oficial de entrenamiento de una nueva capa y ajuste de pesos preentrenados; el ejemplo original resuelve clasificación y debe adaptarse a regresión.
2. [Torchvision — Models and Pre-trained Weights](https://docs.pytorch.org/vision/stable/models.html). Modelos disponibles, carga de pesos y transformaciones de entrada asociadas a cada versión de preentrenamiento.
3. [Scikit-learn — GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html). Procedimiento para separar los datos mediante grupos como `animal_id` y evitar la presencia de un mismo animal en distintas particiones.
4. [Scikit-learn — Regression Metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#regression-metrics). Documentación para calcular MAE y MAPE y comparar predicciones con pesos de referencia.
5. [Li et al. (2023) — *An Improved Method for Broiler Weight Estimation Integrating Multi-Feature with Gradient Boosting Decision Tree*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10705486/). Trabajo sobre estimación del peso de pollos que combina características aprendidas y geométricas. Utiliza imágenes de profundidad, por lo que sirve como antecedente técnico, **no como evidencia de rendimiento directamente transferible a las imágenes RGB de Aviporto**.