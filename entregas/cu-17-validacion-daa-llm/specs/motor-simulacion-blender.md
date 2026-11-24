# Planificación adaptativa de escenarios con LLM 

## 1. Qué hay que construir

Se debe desarrollar un sistema de exploración automática de generación de escenarios sintéticos mediante un modelo de lenguaje ya existente (LLM). 
Esta funcionalidad se integrará con el script de Python desarrollado en PIIA 1 (implementando las nuevas condiciones de escenario necesarias) y con el modelo de detección YOLO-X, creando un ciclo iterativo de generación, evaluación y ajuste de parámetros.

El sistema permitirá definir inicialmente los parámetros que se desean analizar y sus respectivos rangos de valores como, por ejemplo, la intensidad de la niebla.
A partir de esta configuración inicial, el LLM se encargará de proponer las configuraciones posteriores que se evaluarán en cada iteración, teniendo en cuenta los resultados obtenidos en las iteraciones anteriores. 
Las rejillas de rangos propuestas crearán escenarios JSON que generarán las imágenes y sus correspondientes anotaciones en formato COCO. A continuación, se ejecutará el modelo YOLO-X sobre estas para obtener las métricas necesarias para valorar el rendimiento de cada configuración. 
El LLM será responsable de analizar estos resultados, comparar las distintas configuraciones y decidir qué parámetros es mejor modificar o mantener. Para eso, este concentrará la búsqueda en las regiones donde el rendimiento del detector cae, con el objetivo de acotar el valor de cada parámetro a partir del cual YOLO-X deja de detectar la aeronave.
Al terminar quedarán guardados los resultados de todas las iteraciones en los archivos json que genera el proyecto (métricas.json). Estos archivos contienen un registro por cada escenario evaluado en formato común, con la etiqueta de cada foto, relacionados por *scenario_id* y son los datos de entrada del generador de informe (ver generador-informe-robustez.md).


## 2. Por qué

La funcionalidad pretende automatizar la búsqueda de las condiciones de generación de escenarios en las que el detector YOLO-X empieza a fallar, para conocer sus límites de robustez y sus puntos débiles.

La modificación manual de los parámetros y la ejecución individual de mucha cantidad de experimentos necesitan tiempo y dificultan la exploración de los distintos valores posibles. Además, no siempre resulta evidente a partir de qué intensidad de cada condición, como la niebla, el detector deja de detectar.

El LLM actúa como componente de decisión, utiliza los resultados para crear nuevas rejillas y así orientar las siguientes pruebas, reducir evaluaciones innecesarias y concentrar la creación de escenarios en las regiones donde el rendimiento cae, hasta acotar el límite con precisión.

De este modo no habrá necesidad de modificar manualmente el código en cada iteración.

## 3. Restricciones

- **Integración con PIIA 1:** el sistema deberá reutilizar el script de generación de escenarios de PIIA 1, lo que necesitará una mejora de este script para adaptarse a las necesidades del LLM o el aumento de requisitos de parámetros.

- **Responsabilidad del LLM:** el LLM analizará los resultados, propondrá los valores de los parámetros y considerará el criterio de parada (aun no definido).

- **Rangos:** todas las configuraciones propuestas deberán respetar los rangos, tipos de datos y restricciones definidos para cada parámetro. Las configuraciones no válidas deberán rechazarse antes de ejecutar el generador.

- **Comparación:** las configuraciones se evalúan bajo las mismas condiciones, donde la configuración de YOLO-X no cambia entre iteraciones y las fotos de iteraciones anteriores no se regeneran ni se modifican. La métrica principal es el mAP50, calculada por configuración sobre las fotos con visible = true. Se considera que el detector falla cuando el mAP50 es inferior a un umbral (todavía no definido). 

- **Tamaño de la configuración:** cada configuración se evalúa con un número de imágenes suficiente, todavía no definido (images_per_combination en la rejilla), para que el mAP50 sea estable y comparable.

- **Asociación etiquetas:** cada evaluación deberá quedar asociada a los valores de los parámetros utilizados y a las métricas obtenidas. 

- **Criterios de parada:** la búsqueda deberá finalizar cuando se cumpla el criterio de parada (aun sin definir).

## 4. Criterios de aceptación

- **Configuración de parámetros:** el sistema permite definir los rangos iniciales de los parámetros a analizar y utiliza esta información para generar configuraciones de prueba.

- **Integración con el script de Python:** los valores propuestos por el LLM se utilizan automáticamente en el script de PIIA 1, sin necesidad de modificar manualmente el código entre iteraciones.

- **Generación de datos:** para cada configuración válida, el sistema genera los escenarios correspondientes y sus anotaciones en formato COCO.

- **Evaluación con YOLO-X:** el sistema ejecuta la evaluación de cada configuración válida y registra las métricas seleccionadas para comparar su rendimiento.

- **Comparación de resultados:** el sistema identifica qué rangos fallan y cuáles son robustos según el mAP50, con el umbral de fallo definido.

- **Búsqueda de rangos de fallo:** a partir de la segunda iteración, la mayoría de los escenarios propuestos caen en grupos donde el detector falla o que todavía tienen pocas fotos.

- **SIN evaluaciones redundantes:** el sistema no repite automáticamente una configuración ya evaluada.

- **Parada del bucle:** el proceso se detiene y no continúa ejecutando iteraciones indefinidamente.

- **Resultados:** al finalizar, quedan guardados cada escenario y sus resultados, relacionados por scenario_id.

- **Gestión de errores:** si falla la generación de escenarios o la evaluación de YOLO-X el sistema registra el error.
