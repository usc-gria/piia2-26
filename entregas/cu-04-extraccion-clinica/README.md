# CU-04 — Extracción y estructuración de información clínica para REDCap

Proyecto de la asignatura **Proyecto Integrador de IA II**, del Grado en Inteligencia Artificial de la Universidade de Santiago de Compostela (USC).

| Referencia | Detalle |
|---|---|
| Caso de uso | CU-04 |
| Título original | Extracción automática de datos de IANUS a RedCap para estudos de investigación |
| Entidad | IDIS-FPGMX (Instituto de Investigación Sanitaria de Santiago de Compostela / Fundación Pública Galega de Medicina Xenómica) |
| Tutora profesional | Ceres Fernández Rozadilla |
| Alcance | Propuesta del equipo pendiente de validación con la entidad |

## Presentación y motivación

El proyecto propone un sistema basado en IA para extraer y estructurar información clínica relevante para estudios de investigación a partir de documentación procedente de IANUS, y preparar los resultados para su incorporación a REDCap. Está dirigido al personal investigador que actualmente consulta las historias clínicas, copia información a documentos Word y después introduce los datos en REDCap.

La motivación es reducir el trabajo manual de búsqueda y transcripción en ese procedimiento. El interés académico y tecnológico reside en combinar el procesamiento de documentación heterogénea, la extracción de información clínica mediante IA, la interpretación contextual y la estructuración de datos para investigación, respetando las limitaciones de la información de origen. La utilidad y la reducción efectiva del esfuerzo deberán evaluarse; no se presupone que todos los documentos puedan interpretarse correctamente.

Los objetivos iniciales propuestos son:

- Preparar la documentación de un paciente para su análisis, contemplando las dificultades de lectura de los materiales disponibles.
- Extraer un subconjunto de variables clínicas que se acuerde con la tutora, diferenciando los valores respaldados por los documentos de la información ausente o incierta.
- Organizar los resultados conforme a los campos, tipos, opciones y reglas pertinentes del libro de códigos de REDCap.
- Facilitar la comprobación de los resultados mediante referencias a su procedencia documental, descritas en las tres specs y en la arquitectura.

## Punto de partida confirmado

Según la información de la primera reunión, el contexto facilitado al equipo y las aclaraciones de Ceres Fernández Rozadilla del 2 de noviembre de 2026:

- Se dispone de varios PDF de historias clínicas facilitadas como ejemplos anonimizados.
- IANUS únicamente permite exportar los informes en PDF. El resto de la información necesaria se obtiene mediante copia y pegado manual.
- Los documentos incluyen texto digital, páginas escaneadas, formularios, anotaciones manuscritas y contenido en distintos idiomas. Se han identificado tachaduras, casillas sin marcar, información repetida, datos históricos y fragmentos ilegibles.
- Cada entrada al sistema corresponde a **un único paciente**. Se han contemplado PDF, DOCX, texto copiado desde el portapapeles y carpetas con varios documentos como posibles entradas; esto no confirma que todos esos formatos deban admitirse inicialmente.
- Se dispone de un libro de códigos de REDCap que describe campos, tipos, opciones y reglas. La tutora ha indicado que **no es necesario extraer todas sus variables** y que el subconjunto prioritario se facilitará posteriormente.

Los originales y sus derivados se conservan en el entorno autorizado. La entrega recoge observaciones generales y métricas agregadas. Los escenarios de aceptación emplean documentos, valores y definiciones de campos ficticios.

DOC-001 y CLI-001 resumen las observaciones documentales que motivan sus requisitos. RCP-001 utiliza un diccionario sintético para comprobar los comportamientos de preparación. Las variables prioritarias y sus correspondencias siguen pendientes de acuerdo con la entidad.

## Alcance inicial propuesto

Esta delimitación es una propuesta del equipo para orientar las especificaciones; no constituye una aprobación de la tutora.

### Incluido en la propuesta

- Ingesta de documentación de un único paciente por entrada, limitada inicialmente a PDF. Este alcance propuesto todavía no cubre toda la información que actualmente requiere copia y pegado manual. El posible conjunto de documentos de una entrada debe pertenecer a ese mismo paciente.
- Preparación del contenido digital y escaneado para su análisis. DOC-001 describe cómo conservar el idioma original y señalar las limitaciones de lectura. La cobertura exigida de idiomas y manuscritos queda pendiente de evaluación y acuerdo con la entidad.
- Extracción del subconjunto de variables que se acuerde, considerando el contexto clínico y temporal para evitar confundir datos históricos con actuales o tratar las repeticiones como hechos nuevos.
- Identificación de información ausente, ambigua, contradictoria o ilegible, sin completar valores mediante suposiciones. La resolución de contradicciones queda pendiente de acordar.
- Estructuración de los resultados según el subconjunto aplicable del libro de códigos y preparación de una salida intermedia para su comprobación. El ADR de formato intermedio propone Pydantic v2 y JSON para los contratos internos. El formato y el mecanismo de incorporación a REDCap quedan pendientes de acuerdo con la entidad.

### Fuera de la propuesta inicial

- Procesamiento conjunto de varios pacientes en una misma entrada y asociación automática de documentos de pacientes distintos.
- Extracción exhaustiva de todas las variables del libro de códigos.
- Diagnóstico, recomendación terapéutica o toma de decisiones asistenciales.
- Reconstrucción de contenido ilegible o garantía de interpretación completa de cualquier documento.
- Despliegue operativo en el entorno sanitario dentro del alcance inicial.

El acceso directo a IANUS y la escritura automática en REDCap no se incluyen en la propuesta inicial. Su eventual incorporación depende de confirmar las posibilidades de integración y el flujo de trabajo con la tutora.

### Pendiente de validación

Las aclaraciones de la tutora concretan la exportación desde IANUS y mantienen abiertas las decisiones siguientes. El análisis de ejemplos y los debates pendientes no equivalen a reglas clínicas ni a un flujo de revisión ya acordados.

| Cuestión | Decisión que condiciona |
|---|---|
| Variables clínicas prioritarias | Qué información se extraerá y qué parte del libro de códigos se utilizará. |
| Contradicciones entre documentos | Su gestión requiere analizar ejemplos concretos antes de acordar los criterios aplicables. |
| Registro de REDCap de referencia | La entidad podría prepararlo, pero todavía no lo ha proporcionado. |
| Salida intermedia o introducción directa en REDCap | Qué resultado entregará el sistema y cómo se incorporará al estudio. |
| Posible revisión intermedia de resultados | Debe debatirse con el equipo; su obligatoriedad, responsables y momento no están acordados. |
| Métricas y umbrales de rendimiento | Cómo se evaluará la extracción y con qué condiciones se considerará aceptable. |
| Otros formatos, manuscritos e idiomas | Si se admitirán DOCX, portapapeles o carpetas y qué cobertura de lectura se exigirá. |
| Tratamiento de los materiales y resultados | Qué entorno y condiciones de acceso, almacenamiento y procesamiento se acordarán con la entidad. |

## Funcionalidades previstas

La división en tres áreas relaciona el alcance con las tres specs funcionales. La propuesta técnica se desarrolla en la arquitectura y los ADR.

| Identificador | Funcionalidad e intención | Especificación |
|---|---|---|
| `DOC-001` | **Ingesta y procesamiento de documentación clínica.** Recibir la documentación de un paciente y preparar su contenido para el análisis, señalando los problemas de lectura. Busca reducir la preparación manual de materiales heterogéneos. | [ingesta-documentos.md](specs/ingesta-documentos.md) |
| `CLI-001` | **Extracción e interpretación de información clínica.** Localizar las variables acordadas e interpretar su contexto, señalando ausencias, ambigüedades y contradicciones. Busca reducir la búsqueda manual sin presentar como ciertos datos que no estén respaldados. | [extraccion-datos-clinicos.md](specs/extraccion-datos-clinicos.md) |
| `RCP-001` | **Estructuración y preparación de resultados compatibles con REDCap.** Relacionar los datos extraídos con los campos y reglas aplicables del libro de códigos, y señalar incompatibilidades. Busca facilitar su incorporación posterior, mediante un mecanismo aún por acordar. | [exportacion-redcap.md](specs/exportacion-redcap.md) |

El flujo funcional propuesto es: documentación de un paciente → contenido preparado (`DOC-001`) → información clínica extraída (`CLI-001`) → resultados estructurados (`RCP-001`). Este flujo no presupone acceso directo a IANUS ni escritura mediante la API de REDCap.

## Equipo y contactos

Los cuatro estudiantes participan como integrantes del equipo de desarrollo. Sus contactos públicos son los correos institucionales de la USC.

| Persona | Rol o responsabilidad | Contacto |
|---|---|---|
| Lucas Andrea Martínez Calveiro | Integrante del equipo de desarrollo | [lucasandrea.martinez@rai.usc.es](mailto:lucasandrea.martinez@rai.usc.es) |
| Martín Rodríguez Penedo | Integrante del equipo de desarrollo | [martin.rodriguez.penedo@rai.usc.es](mailto:martin.rodriguez.penedo@rai.usc.es) |
| Santiago Pereira Olmeda | Integrante del equipo de desarrollo | [santiago.pereira.olmeda@rai.usc.es](mailto:santiago.pereira.olmeda@rai.usc.es) |
| Carlos Rodríguez Pérez | Integrante del equipo de desarrollo | [carlos.rodriguez.perez1@rai.usc.es](mailto:carlos.rodriguez.perez1@rai.usc.es) |
| Ceres Fernández Rozadilla | Tutora profesional de IDIS-FPGMX | [ceres.fernandez.rozadilla@gmail.com](mailto:ceres.fernandez.rozadilla@gmail.com) |

## Organización de la documentación y método de trabajo

El proyecto sigue un desarrollo guiado por especificaciones (*spec-driven development*): este README define la visión y el alcance, y las specs concretan cada funcionalidad como referencia para su implementación y verificación.

- [ARCHITECTURE.md](ARCHITECTURE.md) describe el diagrama, los componentes, los contratos y el recorrido de un caso sintético, incluidos los fallos parciales. La arquitectura está redactada y revisada técnicamente. El visto bueno formal del equipo sobre la versión consolidada sigue pendiente.
- La [estrategia de lectura de PDF](decisions/estrategia-lectura-pdf.md) resume la comparación de lectura digital y OCR. El ADR de [formato intermedio](decisions/formato-intermedio.md) justifica Pydantic v2, JSON y los validadores propios. El ADR de [extracción clínica](decisions/extraccion-clinica.md) compara familias de motor y propone un suelo de referencia basado en reglas. Los tres ADR incluyen ejemplos sintéticos, resultados y límites de la evidencia. La revisión cruzada entre la arquitectura y el ADR de formato intermedio está registrada. La aprobación formal de las propuestas técnicas sigue pendiente de constancia.
- `specs/`: definiciones funcionales de `DOC-001`, `CLI-001` y `RCP-001`, respectivamente. El nombre `exportacion-redcap.md` no presupone integración directa con REDCap.

La Entrega 2 se ha presentado mediante una pull request al repositorio docente, con ocho documentos en `entregas/cu-04-extraccion-clinica/`. La evidencia experimental se explica en los ADR. Los originales, transcripciones, capturas, registros y exportaciones de depuración de ejecuciones clínicas se mantienen dentro del entorno autorizado. La evidencia experimental se explica en los ADR. Los originales, transcripciones, capturas, registros y exportaciones de depuración de ejecuciones clínicas se mantienen dentro del entorno autorizado.

Cada spec describe intención, comportamiento, restricciones, supuestos y criterios de aceptación observables y comprobables. Las métricas y los umbrales de rendimiento quedan pendientes de acuerdo, según la tabla de validaciones. Los acuerdos con la tutora deben reflejarse de forma coherente en el alcance, la arquitectura y las specs afectadas.

Referencias de evaluación: [Entrega 1](https://github.com/usc-gria/piia2-26/blob/main/evaluacion/entrega-1.md) y [Entrega 2](https://github.com/usc-gria/piia2-26/blob/main/evaluacion/entrega-2.md).
