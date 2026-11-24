## ¿Qué es el proyecto?
Este proyecto se enmarca en el caso de uso 9 (CU-9), en colaboración con la empresa gallega de inteligencia artificial Imaxin. Este caso de uso consiste en crear un sistema RAG (Retrieval Augmented Generation) enmarcado en el ámbito legal para responder a consultas relacionadas con el DOG (Diario Oficial de Galicia). El objetivo es desarrollar un clasificador de consultas que permita mediante agentes, consultar la nueva arquitectura para responder a las preguntas propuestas.

---

## ¿Qué problema resuelve?
El problema principal consistía en que el sistema RAG anterior, llamado Lynx, era muy simple. En casos complejos, como la consulta de múltiples documentos, cruces de información o en conversaciones con contextos muy largos, el modelo se perdía y no era capaz de formular una respuesta correcta.

Como solución hemos decidido crear un sistema más completo de cinco fases: memoria de la sesión, enrutamiento, recuperación, filtrado y generación (detalladas en «Nuestra solución»). El enrutador clasifica la consulta mediante reglas y el análisis de una respuesta hipotética como borrador, y la redirige al motor de recuperación adecuado según el tipo de información que necesita. Dentro de la fase de recuperación existen tres mecanismos: RAG tradicional, Elasticsearch y GraphRAG.

A) El primero es el **RAG tradicional**, que utiliza Qdrant y Elasticsearch para localizar  ragmentos de texto relevantes cuando se buscan datos específicos, como el plazo de solicitud de una ayuda.

B) El segundo mecanismo utiliza **Elasticsearch** directamente, aprovechando los metadatos de los documentos, como la entidad, la sección, la subsección o la fecha, para realizar filtros y obtener listados y conteos concretos.

C) El tercer mecanismo incorpora **GraphRAG**, basado en una estructura de grafos que relaciona entidades, normativas y requisitos, permitiendo recuperar información conectada de diferentes documentos.

Con esto buscamos mejorar la recuperación de información y resolver consultas más complejas que las abordadas mediante la estrategia de búsqueda original de Imaxin.

---

## ¿Por qué hemos escogido este proyecto?
Hemos escogido este proyecto principalmente porque todos los integrantes del grupo tenemos claro que una vez finalizado el grado, nos gustaría dedicarnos al trabajo en una empresa. Este caso de uso es una oportunidad de demostrar que podemos colaborar con una entidad y crear un proyecto complejo, autónomamente, solucionando un problema real, que finalmente se integrará en el código base de la empresa y los clientes le darán un uso.

Por otro lado, nos gustaba la idea de trabajar con Imaxin. Las empresas en Galicia suelen pertenecer a sectores más tradicionales o menos tecnológicos, por lo que cuando descubrimos a Imaxin no dudamos. Poder participar con una empresa de IA puntera a nivel regional y nacional, con un equipo tan experimentado y completo era uno de nuestros objetivos para poder desarrollarnos como estudiantes.

Finalmente, el tema era un reto relacionado con contenidos que habíamos estudiado en clase, pero bastante más avanzado. De tal manera que podríamos aplicar nuestros conocimientos, aprender nuevas metodologías y usar herramientas como LiteLLM, Qdrant o ElasticSearch, que no habíamos usado nunca.

---

## Nuestra solución:
La solución se estructura en cinco fases:
1. Gestión de la memoria conversacional
2. Enrutamiento de consultas
3. Recuperación de información
4. Filtrado de relevancia de las evidencias
5. Generación de respuestas fundamentadas

El diagrama de arquitectura, la descripción de cada componente y el flujo entre ellos están en [ARCHITECTURE.md](ARCHITECTURE.md), y las decisiones de implementación en [decisions/](decisions/).

La principal innovación consiste en combinar diferentes mecanismos de recuperación (RAG tradicional, Elasticsearch y GraphRAG) según el tipo de consulta del usuario. Además, incorpora un sistema de memoria contextual (lista de documentos recientes más relevantes durante la conversación) y un filtro de relevancia (JEV, un modelo binario que indica si una pieza de información es o no relevante; ver [ADR](decisions/filtro-validador-adr.md)) para gestionar conversaciones extensas, consultar múltiples documentos y reducir la incorporación de información irrelevante.

---

## ¿Qué entra en el proyecto y qué queda fuera?
El proyecto se centra en ampliar las consultas que puede resolver Lynx sobre los documentos del DOG disponibles en la infraestructura de Imaxin. Partimos del RAG tradicional que ya tiene la empresa y desarrollamos los componentes necesarios para elegir cómo recuperar la información, mantener el contexto de la conversación y generar respuestas con las fuentes utilizadas.

Dentro del proyecto incluimos:

- La gestión de memoria conversacional, mediante resúmenes acumulativos, turnos recientes y metadatos de documentos relacionados, para poder hacer preguntas de seguimiento sin perder el contexto.
- Un enrutador agéntico que combina reglas y un modelo de lenguaje para elegir entre los tres motores de recuperación: el RAG tradicional para datos concretos o búsquedas por contenido, Elasticsearch para listados basados en metadatos, y GraphRAG para consultar las relaciones de las normas citadas.
- La integración del RAG tradicional de Imaxin, aprovechando la implementación existente en lugar de desarrollarlo desde cero.
- El motor de Elasticsearch descrito en su guía (`src/retrieval_engine/elastic_search/README.md` en el repositorio del código), que permite filtrar por entidad, sección, subsección, fecha, idioma e identificadores en el índice `doga-publications`. El buscador recupera todos los fragmentos coincidentes; el pipeline los agrupa por `file_id` y conserva hasta 20 publicaciones y dos fragmentos por publicación para la generación. El idioma es un filtro opcional. Quedan pendientes los recuentos exhaustivos de publicaciones únicas y la indicación del total cuando el listado esté limitado.
- El motor GraphRAG descrito en su guía (`README_GRAPHRAG.md` en el repositorio del código), que ejecuta consultas Cypher de solo lectura sobre Neo4j para recuperar las relaciones directas de una norma, por ejemplo, con las disposiciones que la modifican o derogan. Está integrado en el pipeline y probado con un driver simulado; sigue pendiente contrastarlo con el esquema y los datos del grafo real.
- El filtro de relevancia para la respuesta de Lynx y la generación que solicita citas a los documentos utilizados. En las rutas de Elasticsearch y GraphRAG, el pipeline comprueba que haya título y contenido y conserva las coincidencias de metadatos o las relaciones del grafo, sin aplicar el filtro temático del modelo. Para los listados de Elasticsearch, si la respuesta generada omite títulos de las publicaciones seleccionadas, se devuelve el listado construido a partir de los resultados recuperados.
- La evaluación de los módulos y del pipeline con pruebas automatizadas y mocks, junto con ejemplos por consola para ejecutar las cinco fases. La evaluación completa de la calidad de las respuestas, la exactitud de los recuentos, los tiempos de respuesta y el funcionamiento de GraphRAG con datos reales sigue pendiente.

Fuera del proyecto quedan:

- La creación de un asistente legal general que consulte otras fuentes distintas del DOG, así como el asesoramiento jurídico o la garantía de que una norma está vigente. El sistema ayuda a localizar y relacionar información documental.
- La descarga, preparación e indexación de nuevos documentos, y la construcción y el mantenimiento del grafo de entidades y relaciones. Los motores implementados consultan los datos disponibles y no los modifican.
- El desarrollo desde cero del RAG tradicional, el entrenamiento de un modelo de lenguaje propio y la administración de la infraestructura de Imaxin.
- Los listados o conteos exhaustivos por temas que no estén representados en los metadatos. Por ejemplo, buscar «ayudas para pymes» corresponde al RAG tradicional porque requiere consultar el contenido, pero no permite garantizar que se hayan encontrado todas las ayudas.

El trabajo depende del acceso autorizado a los servicios y datos de Imaxin, de la API de Lynx, de Elasticsearch, de Neo4j y del servidor Ollama utilizado mediante LiteLLM, bajo el acuerdo de confidencialidad del caso de uso. La necesidad de VPN depende de las condiciones de acceso de cada servicio. Además, GraphRAG necesita un grafo ya construido y accesible, con sus datos y metadatos asociados. El mapping conocido de Elasticsearch ya está incorporado en la implementación; en Neo4j sigue pendiente validar el acceso, el esquema y la recuperación con datos reales. Estas condiciones delimitan lo que podemos integrar y evaluar actualmente.

---

## Equipo:
  - Asier Acuña Casal (asier.acuna@rai.usc.es)
  - Iago Calvo Cuervo (iago.calvo.cuervo@rai.usc.es)
  - Martín Casais Blanco (martin.casais@rai.usc.es)

---

## Estructura del repositorio:
Este repositorio contiene la documentación de la entrega, organizada así:

```text
cu-09-graphrag-dog/
├── README.md
├── ARCHITECTURE.md
├── specs/
│   ├── memoria-sesion.md
│   ├── enrutador-agentico.md
│   ├── elasticsearch-listados-agregaciones.md
│   └── motor-graphrag.md
├── decisions/
│   ├── llm-extrae-parametros-codigo-construye-consultas.md
│   └── filtro-validador-adr.md
└── presentacion/
    └── presentacion.md
```

- [README.md](README.md): explica el caso de uso, el problema que queremos resolver, la motivación del equipo y los límites del proyecto.
- [ARCHITECTURE.md](ARCHITECTURE.md): describe las cinco fases de la solución, sus componentes y cómo se comunican entre sí.
- [specs/](specs/): contiene las especificaciones, con sus responsabilidades, restricciones y criterios de aceptación, de la [memoria de sesión](specs/memoria-sesion.md) (Fase 1), el [enrutador agéntico](specs/enrutador-agentico.md) (Fase 2) y los motores de [Elasticsearch](specs/elasticsearch-listados-agregaciones.md) y [GraphRAG](specs/motor-graphrag.md) (Fase 3).
- [decisions/](decisions/): recoge las decisiones de implementación (ADRs), con su motivación, las alternativas consideradas y referencias:
  - [El LLM extrae parámetros y el código construye las consultas](decisions/llm-extrae-parametros-codigo-construye-consultas.md): por qué los motores de Elasticsearch y GraphRAG no dejan que el LLM escriba consultas DSL o Cypher.
  - [Filtro validador con un LLM como juez](decisions/filtro-validador-adr.md): cómo funciona el JEV de la Fase 4 y por qué solo se aplica a la ruta A.
- [presentacion/](presentacion/): carpeta destinada a la presentación y los recursos de la demo. 


### Código del proyecto
El código está en un repositorio aparte, que no forma parte de esta entrega, así que las rutas siguientes no se pueden abrir desde aquí. Su estructura principal, resumida, es:

```text
cu-09/
├── README.md
├── __main__.py
├── .env.example
├── requirements.txt
├── src/
│   ├── config.py
│   ├── llm_aux.py
│   ├── deep_memory/
│   ├── router/
│   ├── retrieval_engine/
│   │   ├── trad_rag/
│   │   ├── elastic_search/
│   │   └── graph_rag/
│   ├── noise_filter/
│   ├── final_response/
│   └── pipeline/
└── tests/
```

- `README.md`: describe la instalación, la configuración compartida, las cinco fases y la ejecución del pipeline.
- `src/pipeline/`: conecta la memoria, el enrutador, los motores, el filtrado y la generación de respuestas.
- `src/deep_memory/` (Fase 1), `src/router/` (Fase 2), `src/retrieval_engine/` (Fase 3), `src/noise_filter/` (Fase 4) y `src/final_response/` (Fase 5): contienen los componentes de las cinco fases y sus guías disponibles.
- `__main__.py`: ejecuta ejemplos de las rutas A, B y C y una pregunta de seguimiento, sin entrada interactiva. El indicador `OK` comprueba el enrutamiento, no la calidad factual de la respuesta.
- `tests/`: contiene las pruebas automatizadas de los componentes y de su integración con mocks.
