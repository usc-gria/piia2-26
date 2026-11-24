# Modelo de lenguaje: Qwen3 Next Instruct en Databricks

## Decisión

Todos los agentes usan el mismo modelo: **Qwen3 Next 80B Instruct**, a través de Databricks
(endpoint `databricks-qwen3-next-80b-a3b-instruct`), con temperatura 0. El modelo se define en un
único sitio, `src/piia/config_llm.py`, que lee el nombre del modelo de `.env`. Para cambiar de modelo
solo hay que cambiar la variable `DATABRICKS_MODELO`; el resto del código no se toca.

## Motivación

Nuestro sistema tiene que leer artículos científicos largos (unos 25 000 tokens por artículo) y
devolver datos en un formato fijo (JSON validado con Pydantic) para tres agentes de CrewAI. Por eso
necesitábamos un modelo que:

- sea **gratuito** y accesible para todo el grupo (usamos Databricks Free Edition);
- funcione con **CrewAI** sin piezas extra;
- devuelva bien el **formato estructurado** que piden los agentes;
- acierte lo máximo posible en nuestra tarea, que es lo que medimos.

En vez de elegir por intuición, lo **medimos**: repetimos el estudio del iMATUS con los mismos
prompts, con los 20 artículos de desarrollo, temperatura 0 y el mismo corrector, cambiando solo el
modelo. Qwen3 Next fue el que más acertó y el más rápido.

Además, tener el modelo en un solo sitio nos permite compararlo con otros sin tocar los agentes, y
asegura que todas las piezas usan siempre el mismo modelo.

## Alternativas

| | Qwen3 Next (elegido) | Llama 4 Maverick | Llama 3.3 70B |
|---|---|---|---|
| Exactitud global | **0,539** | 0,491 | 0,420 |
| Impresión | 0,355 | 0,233 | 0,357 |
| Tinta (reología) | 0,732 | 0,741 | 0,684 |
| Dosis | 0,548 | 0,534 | 0,277 |
| Tiempo (20 artículos) | **17,5 min** | 38,1 min | 34,5 min |

*Repetición del estudio, 20 artículos de desarrollo, 08/11/2026 (Issue #28).*

- **Llama 4 Maverick:** acierta menos en total, tarda más del doble y escribe peor el JSON
  (7 respuestas no se podían leer).
- **Llama 3.3 70B:** es el que menos acierta; en dosis encuentra muchos menos datos que las expertas.
- **Modelos de razonamiento (GPT OSS 120B, Qwen3.5 122B):** Databricks devuelve su respuesta como una
  lista de bloques (razonamiento + texto) y CrewAI falla. Los probamos con un adaptador que deja solo
  el texto (Issue #82) y tampoco mejoraron a Qwen3 Next con el agente de impresión (0,400 y 0,333
  frente a 0,404, con la nota estricta), así que los descartamos.
- **Modelos de pago (por ejemplo, GPT-4, el del estudio):** el proyecto no tiene presupuesto, y la idea
  es ver hasta dónde se llega con un modelo abierto y gratuito.

## Referencias

- Comparación completa y motivo: `docs/decisiones.md`, §4 (Issues #28 y #82).
- Código: `src/piia/config_llm.py`. Ejemplo de uso en un agente:

  ```python
  from piia.config_llm import crear_crew, crear_llm

  agente = crear_agente_tinta(crear_llm())   # el LLM sale siempre de config_llm
  crew = crear_crew(agents=[agente], tasks=[crear_tarea(agente)])   # Crew sin trazas
  ```

- Configuración (`.env`, sin valores en el repositorio):
  `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_MODELO=databricks-qwen3-next-80b-a3b-instruct`.
- Documentación de Databricks (modelos fundacionales con API compatible con OpenAI):
  https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/
- Documentación de CrewAI sobre LLM: https://docs.crewai.com/concepts/llms
