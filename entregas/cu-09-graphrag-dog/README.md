## ¿Qué es el proyecto?
Este proyecto se entabla en el caso de uso 9 (CU-9), en colaboración la empresa gallega de inteligencia artificial Imaxin. Este caso de uso consisten en crear un sistema RAG (Retrieval Augmented Generation) enmarcado en el ámbito legal para responder a consultas relacionadas con el DOG (Diario Oficial de Galicia). El objetivo es desarrollar un clasificador de consultas que permita mediante agentes, consultar la nueva arquitectura para responder a las preguntas propuestas.

---

## ¿Qué problema resuelve?
El problema principal consistía en que el sistema RAG anterior, llamado Lynx, era muy simple. En casos complejos, como la consulta de múltiples documentos, cruces de información o en conversaciones con contextos muy largos, el modelo se perdía y no era capaz de formular una respuesta correcta.

Como solución hemos decidido crear un sistema más complejo y completo de cinco fases que clasifique una consulta según su respuesta y la redirija al motor de búsqueda correcto basado en la complejidad de esta respuesta:

A) El primero es el **RAG tradicional**, que utiliza Qdrant y Elasticsearch para localizar  ragmentos de texto relevantes cuando se buscan datos específicos, como el plazo de solicitud de una ayuda.

B) El segundo mecanismo utiliza **Elasticsearch** directamente, aprovechando los metadatos de los documentos, como la entidad, la sección, la subsección o la fecha, para realizar filtros y obtener listados y conteos concretos.

C) El tercer mecanismo incorpora **GraphRAG**, basado en una estructura de grafos que relaciona entidades, normativas y requisitos, permitiendo recuperar información conectada de diferentes documentos.

Esto nos permite mejorar la recuperación de información y resolver consultas más complejas que las abordadas mediante la estrategia de búsqueda original de Imaxin.

---

## ¿Por qué hemos escogido este proyecto?
Hemos escogido este proyecto principalmente porque todos los integrantes del grupo tenemos claro que una vez finalizado el grado, nos gustaría dedicarnos al trabajo en empresa. Este caso de uso es una oportunidad de demostrar que podemos colaborar con una entidad y crear un proyecto complejo, autónomamente, solucionando un problema real, que finalmente se integrará en el código base de la empresa y los clientes le darán un uso.

Por otro lado, nos gustaba la idea de trabajar con Imaxin. Las empresas en Galicia suelen pertenecer a sectores más tradicionales o menos tecnológicos, por lo que cuando descubrimos a Imaxin no dudamos. Poder participar con una empresa de IA puntera a nivel regional y nacional, con un equipo tan experimentado y completo era uno de nuestros objetivos para poder desarrollarnos como estudiantes.

Finalmente, el tema era un reto relacionado con temas que habíamos estudiado en clase, pero bastante más avanzado. De tal manera que podríamos aplicar nuestros conocimientos, aprender nuevas metodologías y usar herramientas como LiteLLM, Qdrant o ElasticSearch, que no habíamos usado nunca.

---

## Nuestra solución:
La solución se estructura en cinco fases:
1. Gestión de memoria conversacional
2. Enrutamiento de consultas
3. Recuperación de información
4. Validación de evidencias
5. Generación de respuestas fundamentadas.

La principal innovación consiste en combinar diferentes mecanismos de recuperación (RAG
tradicional, Elasticsearch y GraphRAG) según el tipo de consulta del usuario. Además, incorpora un sistema de memoria contextual y un filtro de relevancia que permiten gestionar conversaciones extensas, consultar múltiples documentos y reducir la incorporación de información irrelevante.

---

## ¿Qué entra en el proyecto y qué queda fuera?

El proyecto se centra en ampliar las consultas que puede resolver Lynx sobre los documentos del DOG disponibles en la infraestructura de Imaxin. Partimos del RAG tradicional que ya tiene la empresa y desarrollamos los componentes necesarios para elegir cómo recuperar la información, mantener el contexto de la conversación y generar respuestas con las fuentes utilizadas.

Dentro del proyecto incluimos:

- La gestión de memoria conversacional, mediante resúmenes acumulativos y un conjunto de documentos relacionados, para poder hacer preguntas de seguimiento sin perder el contexto.
- Un enrutador agéntico que clasifique la consulta y elija entre los tres motores de recuperación: el RAG tradicional para datos concretos o búsquedas por contenido, Elasticsearch para listados y conteos basados en metadatos, y GraphRAG para relacionar información de varios documentos.
- La integración del RAG tradicional de Imaxin, aprovechando la implementación existente en lugar de desarrollarlo desde cero.
- El motor de Elasticsearch definido en [su spec](specs/elasticsearch-listados-agregaciones.md), que permite filtrar por entidad, sección, subsección y fecha, y obtener listados y conteos sin duplicar documentos. En este motor solo se consideran las publicaciones en gallego para no contar dos veces una misma publicación. Los listados se limitan a un máximo de 100 documentos por consulta, indicando el total real cuando haya más resultados.
- El motor GraphRAG definido en [su spec](specs/motor-graphrag.md), que consulta un grafo para recuperar fragmentos de documentos conectados, por ejemplo, una norma y las disposiciones que la modifican o derogan.
- El filtro de relevancia JEV para los fragmentos recuperados por el RAG tradicional y GraphRAG, y la generación de respuestas con citas a los documentos utilizados. Los listados y conteos de Elasticsearch pasan directamente a la generación para conservar los resultados de los filtros exactos.
- La evaluación de los motores con consultas de prueba, comprobando la recuperación de documentos, la exactitud de los listados y conteos, la trazabilidad de las fuentes y los tiempos de respuesta establecidos en las specs.

Fuera del proyecto quedan:

- La creación de un asistente legal general que consulte otras fuentes distintas del DOG, así como el asesoramiento jurídico o la garantía de que una norma está vigente. El sistema ayuda a localizar y relacionar información documental.
- La descarga, preparación e indexación de nuevos documentos, y la construcción y el mantenimiento del grafo de entidades y relaciones. Según las specs actuales, los motores consultan los datos disponibles y no los modifican.
- El desarrollo desde cero del RAG tradicional, el entrenamiento de un modelo de lenguaje propio y la administración de la infraestructura de Imaxin.
- Los listados o conteos exhaustivos por temas que no estén representados en los metadatos. Por ejemplo, buscar «ayudas para pymes» corresponde al RAG tradicional porque requiere consultar el contenido, pero no permite garantizar que se hayan encontrado todas las ayudas.

El trabajo depende del acceso por VPN a los datos de Imaxin, de la API de Lynx y de los modelos disponibles mediante LiteLLM, bajo el acuerdo de confidencialidad del caso de uso. Además, GraphRAG necesita un grafo ya construido con sus fragmentos y metadatos asociados. La disponibilidad de ese grafo debe confirmarse con la empresa, al igual que los campos que permiten filtrar y agrupar en Elasticsearch. Estas condiciones delimitan lo que podemos integrar y evaluar con las specs actuales.

---

## Equipo:
  - Asier Acuña Casal (asier.acuna@rai.usc.es)
  - Iago Calvo Cuervo (iago.calvo.cuervo@rai.usc.es)
  - Martín Casais Blanco (martin.casais@rai.usc.es)

---

## Estructura del repositorio:

```text
cu-09-graphrag-dog/
├── README.md
├── ARCHITECTURE.md
├── specs/
│   ├── elasticsearch-listados-agregaciones.md
│   └── motor-graphrag.md
├── decisions/
│   └── mock-decision.md
└── presentacion/
    └── presentacion.md
```

- [README.md](README.md): explica el caso de uso, el problema que queremos resolver, la motivación del equipo y los límites del proyecto.
- [ARCHITECTURE.md](ARCHITECTURE.md): describe las cinco fases de la solución, sus componentes y cómo se comunican entre sí.
- [specs/](specs/): contiene las especificaciones de los motores de Elasticsearch y GraphRAG, con sus responsabilidades, restricciones y criterios de aceptación. Ambos forman parte de la fase de recuperación de información de la arquitectura.
- [decisions/](decisions/): carpeta destinada a recoger las decisiones de implementación, su motivación y las alternativas consideradas. Actualmente contiene una plantilla de ejemplo, pendiente de sustituir por las decisiones reales.
- [presentacion/](presentacion/): carpeta destinada a la presentación y los recursos de la demo. Actualmente contiene una nota de ejemplo con las indicaciones para prepararla.
