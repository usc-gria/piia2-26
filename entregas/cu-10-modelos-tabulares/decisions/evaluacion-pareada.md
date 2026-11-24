# ADR: evaluación con particiones compartidas y test reservado

**Estado:** adoptada en el pipeline y las baterías actuales.

## Decisión

Comparar LightGBM y TabPFN sobre particiones materializadas una sola vez por dataset y semilla, compartidas entre modelos y variantes. El test se reserva para la evaluación final; la imputación, codificación y selección de hiperparámetros o umbral utilizan exclusivamente el entrenamiento. Los agregados comparativos incluyen solo pares completados bajo la misma condición experimental.

Esta decisión implementa el protocolo de la [spec de experimentos](../specs/comparar-modelos.md) y sustenta la interpretación exigida por la [spec de resultados](../specs/consultar-resultados.md).

## Motivación

El proyecto compara algoritmos, tamaños de muestra y condiciones de los datos. Si cada modelo utilizara un test diferente, una diferencia en F1 o ROC-AUC podría deberse a la partición y no al modelo. Además, los problemas de impago, bajas de clientes y riesgo cardiovascular requieren controlar la representación de ambas clases.

La estratificación conserva aproximadamente las proporciones de clases. Guardar los índices y comprobar sus huellas permite verificar la comparación, en lugar de confiar únicamente en que se haya reutilizado una semilla. Reservar el test evita que la elección de imputación, hiperparámetros o umbral aproveche información de la evaluación final.

## Aplicación

1. El orquestador crea el reparto estratificado con la fracción de test y semilla configuradas. Valida que entrenamiento y test contienen ambas clases. Cada tamaño de entrenamiento es un subconjunto anidado del mismo conjunto disponible; cambiar ese tamaño no cambia el test.
2. El plan conserva índices, semillas, identidad del dataset y de sus reglas de preparación. Antes del ajuste se comprueba que la partición corresponde a los datos y no contiene solapamientos.
3. Dentro de una variante, ambos modelos utilizan las mismas reglas de preprocesamiento. Cada ejecución ajusta su propio transformador sobre entrenamiento; el test solo se transforma. Las perturbaciones de robustez se aplican al entrenamiento.
4. Si se activa la búsqueda de hiperparámetros, se evalúan candidatos mediante validación cruzada estratificada interna. Después, si se activa el ajuste de umbral, se generan probabilidades *out-of-fold* con los parámetros elegidos. Cada fold reajusta el preprocesamiento y las condiciones usando solo su entrenamiento.
5. El modelo final se ajusta con el entrenamiento disponible. Si no se optimiza el umbral, se conserva la decisión de `predict`; si se optimiza, se aplica el umbral registrado a las probabilidades del test.
6. La comparación admite exactamente un resultado completado por modelo para cada dataset, variante y `partition_id`, con igual `test_sha256`. Calcula medias y desviaciones entre semillas por tamaño y variante, además de diferencias TabPFN − LightGBM. Conserva fuera de esos agregados las ejecuciones fallidas o sin pareja.

Las métricas se calculan con la misma definición y clase positiva. `average_precision` usa `average_precision_score`; `pr_auc` integra la curva precisión–recall mediante trapecios. No se intercambian sus nombres ni sus valores.

## Alternativas y motivos para no adoptarlas

| Alternativa | Motivo |
|---|---|
| Dividir los datos de forma independiente por modelo | Impide atribuir las diferencias al algoritmo y dificulta verificar que se comparan las mismas observaciones. |
| Ajustar el preprocesamiento antes de dividir o elegir el umbral sobre test | Introduce información de evaluación en las decisiones de ajuste y puede producir resultados optimistas. |
| Usar una sola partición como evaluación principal | Es útil para una prueba rápida, pero no permite observar la variación entre semillas. Las baterías admiten repeticiones; con una sola semilla no se estima dispersión. |
| Validación cruzada anidada completa como protocolo por defecto | Aumentaría considerablemente los ajustes y llamadas al servicio TabPFN. Para este prototipo se usan particiones externas repetidas con selección interna acotada; no se presenta como equivalente a un estudio anidado exhaustivo. |

## Consecuencias y límites

Se obtiene una comparación auditable, con mayor coste cuando se activan búsquedas. Las puntuaciones internas sirven para seleccionar configuraciones; no son estimaciones independientes del rendimiento después de esa selección. La desviación entre semillas describe dispersión, no un intervalo de confianza.

Excluir pares incompletos reduce la evidencia disponible y puede sesgarla hacia las condiciones en las que ambos modelos terminan. Por eso se conserva la tabla completa con errores y se muestra cuántos pares entran en la comparación. Las referencias industriales con protocolo desconocido deberán presentarse separadas, conforme a las specs.

## Referencias y evidencia

- Implementación: [particiones e integridad](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/partitions.py), [selección interna de hiperparámetros y umbral](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/optimization.py) y [emparejado y agregación](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/comparison.py).
- scikit-learn: [prevención de fuga de datos](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) y [StratifiedKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html).
- Definición de [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), que documenta su diferencia respecto al área trapezoidal.
