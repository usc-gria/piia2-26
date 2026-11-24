# Entrenamiento y evaluación de un ASR con el dataset sintético

> **Nota:** esta funcionalidad es opcional y solo se desarrollará si el tiempo lo permite.

## Qué construir

Un proceso que entrena un modelo abierto de reconocimiento del habla (ASR) con el dataset sintético (spec 05 y, si se ha desarrollado, spec 06) y mide si reconoce mejor el habla médica que el mismo modelo sin entrenar. Es la última etapa del sistema: comprueba si los datos generados sirven para lo que se crearon.

**Métricas**

- **WER (tasa de error por palabra):** métrica principal. Porcentaje de palabras mal reconocidas respecto a la transcripción de referencia.
- **CER (tasa de error por carácter):** métrica complementaria, útil para términos médicos largos en los que un error de una letra cuenta como una palabra entera en el WER.

**Entradas**

- Un modelo ASR abierto con soporte para español y gallego.
- El dataset sintético, y su versión con ruido si existe.
- Un conjunto de test de habla médica real, en español y en gallego, con su transcripción.

**Salidas**

- Los modelos ASR entrenados.
- El WER y el CER de cada modelo sobre el conjunto de test, por idioma.
- Una comparación de los resultados frente al modelo sin entrenar.
- Un registro de cada entrenamiento con todo lo necesario para repetirlo.

**Funcionamiento**

1. Se comprueba que ninguna frase del conjunto de test aparece en los corpus de las specs 02 y 03, ni de forma exacta ni casi exacta (por encima del mismo umbral de similitud que usa la spec 02), tras normalizar ambas con las mismas reglas.
2. Se evalúa el modelo ASR sin entrenar sobre el conjunto de test. Este resultado es la línea base.
3. Se entrena el modelo con el dataset sintético. Si se separa una parte para validación, la separación se hace por identificador de frase. Como una frase tiene varios audios (dos voces, y su traducción al gallego con el mismo identificador), todos ellos quedan en el mismo lado.
4. Se evalúa el modelo entrenado sobre el mismo conjunto de test.
5. Se repiten los pasos 3 y 4 cambiando un solo factor cada vez. Por ejemplo:
    - con o sin las voces de un perfil, como las personas mayores;
    - con uno o dos prompts por frase;
    - con o sin un estilo de habla;
    - con o sin ruido, si existe la spec 06.
6. Se comparan los resultados de cada modelo con la línea base.

## Por qué

Que el audio sintético suene bien no garantiza que sirva para entrenar un reconocedor. La única forma de saberlo es entrenar un modelo con él y medir si reconoce mejor el habla real. Comparar con la línea base dice si los datos ayudan, y cambiar un factor cada vez dice qué parte del dataset es la que ayuda.

## Restricciones

- Depende de la spec 05 y, si se ha desarrollado, de la spec 06.
- El conjunto de test es siempre habla real, nunca sintética.
- Ninguna frase del conjunto de test aparece en los corpus usados para sintetizar, ni de forma exacta ni casi exacta.
- Todos los modelos se evalúan sobre el mismo conjunto de test.
- Para cada entrenamiento se registran el modelo base y su versión, la versión del dataset, los parámetros de entrenamiento, la semilla y las versiones de las librerías.

## Criterios de aceptación

- La comprobación del paso 1 da 0 frases del conjunto de test repetidas o casi repetidas en los corpus de las specs 02 y 03.
- Existe una línea base: el WER y el CER del modelo sin entrenar en cada idioma.
- Cada modelo entrenado tiene su WER y su CER en cada idioma, medidos sobre el mismo conjunto de test.
- Los resultados indican, para cada modelo, la diferencia de WER respecto a la línea base.
- Al relanzar un entrenamiento con lo registrado, el WER obtenido difiere en menos de 0,5 puntos del original.
