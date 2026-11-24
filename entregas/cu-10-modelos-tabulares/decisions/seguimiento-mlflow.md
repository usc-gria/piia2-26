# ADR: seguimiento local de experimentos con MLflow

**Estado:** adoptada en el pipeline, las baterías y la interfaz actuales.

## Decisión

Utilizar MLflow como registro común de experimentos, con una base SQLite local para metadatos y un directorio local para artefactos. Cada batería se representa mediante una ejecución padre y cada trabajo del plan mediante una hija, que agrupa sus búsquedas opcionales y ajuste final. La interfaz y el análisis consultan los resultados persistidos por sus identificadores de ejecución.

La decisión se limita al seguimiento experimental descrito en la [arquitectura](../ARCHITECTURE.md); no incorpora un servicio de predicción ni un registro de modelos para producción.

## Motivación

El proyecto genera combinaciones de datasets, modelos, semillas, tamaños y variantes. Una métrica aislada no permite saber con qué datos, partición o configuración se obtuvo. La [spec de experimentos](../specs/comparar-modelos.md) exige conservar ese contexto y la [spec de resultados](../specs/consultar-resultados.md) necesita consultarlo junto con errores y tiempos.

MLflow ya se utiliza en los ensayos del equipo y permite agrupar ejecuciones, registrar parámetros y métricas y conservar artefactos consultables desde Python. SQLite y el almacenamiento local son suficientes para el prototipo y evitan administrar un servidor de seguimiento, una base remota y un almacén de objetos.

## Aplicación

| Nivel | Registro |
|---|---|
| Experimento | Agrupa baterías bajo el nombre configurado. |
| Ejecución padre | Conserva `plan.json`, `results.csv` y `summary.json`, con todos los trabajos previstos y su estado. Cada invocación crea un padre nuevo. |
| Ejecución hija | Registra modelo, dataset, configuración, partición y, si termina, métricas, tiempos, contexto y predicciones. Las búsquedas opcionales conservan sus resultados. |
| Informe de comparación | Añade CSV agregados, diferencias pareadas, notas metodológicas y PNG al directorio de artefactos `comparison/` del padre. |

El código fija como destino local `mlflow.db` y guarda los artefactos en `mlruns/`. El registro no depende de tener abierta la interfaz web de MLflow. Los archivos de `results/streamlit/<id>/` sirven para enviar la solicitud y comunicar progreso; no sustituyen el historial persistente.

Streamlit lanza un proceso independiente que llama al mismo motor de baterías usado por la CLI. Esto aísla entre sesiones el estado de seguimiento de MLflow y permite consultar el historial tras cerrar la pestaña. Dentro de cada batería, los entrenamientos son secuenciales. Si falla uno, se registra su error y se continúa; la batería se identifica como fallida si contiene fallos, aunque haya resultados válidos de otros modelos.

Las gráficas se generan leyendo artefactos, sin volver a entrenar. Un fallo al producirlas deja disponibles los resultados ya registrados. Los tokens del servicio remoto se suministran mediante el entorno del proceso y no forman parte de los YAML ni de los parámetros registrados.

## Alternativas y motivos para no adoptarlas

| Alternativa | Motivo |
|---|---|
| Guardar únicamente CSV y salidas de notebooks | Los CSV son útiles para intercambiar resultados, pero como único registro obligarían a implementar la asociación entre configuraciones, particiones, errores y artefactos. Se conservan como salida de MLflow. |
| Crear tablas SQLite y una interfaz de seguimiento propias | Duplicaría la gestión de experimentos y las operaciones de consulta que MLflow ya ofrece y que el equipo utiliza. |
| Servidor MLflow compartido con base de datos y artefactos remotos | Facilitaría el acceso simultáneo entre equipos, pero añade despliegue, credenciales y mantenimiento fuera de las necesidades actuales del prototipo local. |

## Consecuencias y límites

El historial sobrevive a las sesiones de Streamlit y las ejecuciones tienen identificadores aunque se repitan sus nombres. Las tablas y gráficas se pueden reconstruir a partir de los resultados conservados.

El almacenamiento es local: otros integrantes no ven automáticamente el historial. Para conservarlo o trasladarlo hay que mantener tanto la base de metadatos como los artefactos y sus rutas accesibles. Repetir un experimento requiere además los datos originales; el plan no contiene una copia del dataset. Las huellas y versiones registradas ayudan a comprobar identidad y contexto, pero no garantizan resultados idénticos de un servicio remoto que pueda cambiar.

No se ofrece reanudación automática ni coordinación distribuida. SQLite y los archivos locales pueden sufrir bloqueos; existen reintentos acotados para errores temporales de acceso a archivos, pero los errores persistentes se notifican. Las versiones de MLflow deben ser compatibles con el esquema de la base.

## Referencias y evidencia

- Implementación: [destino y registro común](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/tracking.py), [padre, hijas y estados de batería](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/batteries.py) y [proceso de ejecución de la interfaz](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/app/dashboard_worker.py).
- MLflow: [seguimiento de experimentos](https://mlflow.org/docs/latest/ml/tracking/) y [API de Python](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html), especialmente `start_run(nested=True)`, `log_params`, `log_metrics` y `log_dict`.
- [Pruebas existentes de integración](https://github.com/RodrigoRego5/Modelos_Fundacionales/blob/e6e52c4ede57066659d9ee31b637c63640c7bd52/tests/test_dashboard.py): verifican el registro y la lectura de baterías con almacenamiento temporal de MLflow; sustituyen el cliente remoto de TabPFN por un estimador local controlado.
