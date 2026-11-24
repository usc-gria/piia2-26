# ADR: LangChain y LangGraph para orquestar el LLM

## Decisión
Usamos **LangChain** y **LangGraph** para orquestar el LLM en la explicación, la detección de errores y su corrección.

## Motivación
- El proceso es un **ciclo**: generar → verificar → corregir → volver a verificar, con un máximo de 2 correcciones. LangGraph lo expresa de forma natural con un estado compartido y transiciones condicionales, y cada paso se puede probar por separado.
- Integraciones con los proveedores que usamos (Gemini y Groq), con la misma API para llamadas y para salida estructurada. Esto simplifica los jueces, que devuelven JSON con un esquema.
- Experiencia previa de la AI Engineer del equipo con el framework.
- Integración sencilla con **MLflow** para depurar las trazas del LLM (solo en desarrollo).

## Alternativas
- **SDKs oficiales (Google, Groq) + bucle propio:** es lo más ligero, y el bucle tiene como máximo 3 iteraciones. Lo descartamos porque habría que mantener dos APIs distintas para la salida estructurada y construir a mano el estado y la trazabilidad.
- **LangChain sin LangGraph:** el ciclo sería código Python propio, sin estado explícito ni trazas por nodo.
- **LlamaIndex:** orientado a RAG, que aquí no hace falta.
- **Otros frameworks de orquestración de LLMs:** cubren los requisitos pero ningún miembro del equipo tiene experiencia previa con ellos.

## Consecuencias
- Dependencias pesadas, que aumentan el tamaño del programa empaquetado.
- LangChain cambia su API con frecuencia, por lo que se fija una versión 1.5.0.
- No usamos memoria ni *checkpointers* (p. ej. en SQLite): cada explicación es independiente.

## Referencias
- Documentación de [LangChain](https://docs.langchain.com/oss/python/langchain/quickstart) y [LangGraph](https://docs.langchain.com/oss/python/langgraph/quickstart).
- Trazado automático de MLflow con [LangChain](https://mlflow.org/docs/latest/genai/tracing/integrations/listing/langchain/) y [LangGraph](https://mlflow.org/docs/latest/genai/tracing/integrations/listing/langgraph/).
