# Voz sintética para mejorar el reconocimiento del habla médica en español y gallego

## Qué es

Este proyecto estudia cómo usar voz sintética de alta calidad para entrenar y mejorar modelos de reconocimiento automático del habla (ASR) en español y gallego. Los sistemas ASR necesitan muchas horas de audio transcrito, y grabarlo es caro y lento; en gallego, además, los recursos disponibles son escasos. Proponemos aprovechar modelos abiertos de síntesis de voz (TTS), adaptados a ambos idiomas, para generar audio de dominio médico con su transcripción exacta, variando voces y estilos de habla. El resultado será un dataset sintético de unas 10 horas en ambos idiomas y una metodología reproducible para seguir generando estos datos.

**Documentación técnica (Entrega 2):**

- [Arquitectura de la solución](ARCHITECTURE.md): diagrama, componentes, flujo de datos, correspondencia con las specs, privacidad y riesgos.
- Decisiones de arquitectura (ADR):
  - [ADR-001 · Generar el corpus de textos médicos con un LLM](decisions/001-corpus-generado-con-llm.md)
  - [ADR-002 · Traducir al gallego con NOS-MT-OpenNMT-es-gl](decisions/002-traduccion-nos-mt.md)
  - [ADR-003 · Un trabajo del CESGA por modelo TTS (Colab solo para pruebas)](decisions/003-sintesis-cesga-un-trabajo-por-modelo.md)
  - [ADR-004 · Formato del dataset: WAV 16 kHz y metadata.csv compatible con AudioFolder](decisions/004-formato-dataset.md)
  - [ADR-005 · Modelos TTS por idioma y perfil de voz](decisions/005-modelos-por-perfil.md)
  - [ADR-006 · Chatterbox para la persona mayor en gallego, si la clonación sale bien](decisions/006-chatterbox-mayor-gallego.md)
- Código:
  - [Corpus en castellano y en gallego](codigo/corpus/README.md) (specs 02 y 03): el script de preprocesado que valida el corpus generado por el LLM y lo traduce al gallego.

## Motivación

Este proyecto retoma la línea de trabajo de la asignatura PIIA I, en la que desarrollamos un agente conversacional por voz: un sistema que reconocía lo que decía el usuario (ASR), generaba una respuesta con un modelo de lenguaje (LLM) y la leía en voz alta mediante síntesis de voz (TTS), con un detector de turnos para gestionar la conversación. No continuamos aquel proyecto, sino su temática. Trabajar con tecnologías del habla nos gustó mucho, y ahora queremos profundizar en la síntesis de voz y en cómo puede ayudar a mejorar el reconocimiento.

Lo que más nos atrae es la generación de datos sintéticos: poder crear de forma controlada los datos que necesita un modelo, en lugar de depender solo de los que ya existen.

Aplicaremos el proyecto al ámbito médico, un área que también nos resulta muy interesante. En sanidad, el reconocimiento de voz tiene usos claros, como el dictado de informes clínicos. Sin embargo, el vocabulario es muy específico y las grabaciones reales son difíciles de conseguir, porque contienen información sensible de los pacientes. La voz sintética permite generar audio con terminología médica sin recurrir a datos de pacientes.

El gallego tiene un papel central en el proyecto: los datos se generarán tanto en español como en gallego, y el gallego es imprescindible para que el resultado sea útil en el contexto en el que se aplicará.

Al terminar el proyecto queremos:

- Comparar distintos modelos abiertos de síntesis de voz mediante un método tipo Arena: varias personas escuchan los modelos por parejas, votan cuál suena mejor y seleccionamos el más votado.
- Generar un dataset sintético de unas 10 horas de audio, al menos 5 en español y 5 en gallego, sintetizado con los modelos mejor valorados en el método Arena y con voces variadas diseñadas mediante prompts.
- Definir una metodología que permita repetir la generación tantas veces como haga falta para aumentar el volumen de datos.
- Si el tiempo lo permite, aportar evidencia experimental de en qué casos la voz sintética mejora un ASR.

## Alcance

### Qué entra en el proyecto

- Selección y comparación de modelos abiertos de síntesis de voz en español y gallego mediante el método Arena.
- Preparación de un corpus de frases médicas en español, generadas con un LLM y, de forma complementaria, tomadas de fuentes abiertas. Cada frase lleva dos descripciones de las voces que la leerán y el modelo de síntesis de cada una.
- Traducción automática del corpus de textos del español al gallego.
- Diseño de voces mediante prompts, y clonación cuando haga falta, para cubrir perfiles de hablantes poco representados en los modelos disponibles, como las personas mayores y los niños.
- Generación de un dataset sintético de unas 10 horas en español y gallego, con variación de voces y estilos de habla.
- Documentación del dataset y de una metodología que permita repetir la generación.
- De forma opcional, si un estudio previo confirma que es viable: aumento del dataset con ruido y otros efectos acústicos.
- De forma opcional, si el tiempo lo permite: entrenamiento y evaluación de un modelo de reconocimiento del habla con los datos generados.

### Qué queda fuera

- El diseño de nuevas arquitecturas de síntesis o reconocimiento: trabajaremos con modelos abiertos existentes.
- El uso de servicios comerciales cerrados de síntesis.
- El despliegue en producción, las aplicaciones para usuario final y el reconocimiento en tiempo real.
- Dominios distintos del médico.
- Una prueba de percepción formal por perfil de voz: los perfiles se validaron con la escucha del equipo ([spec 04](specs/04-adaptacion-clonacion-voz.md)).

## Caso de uso

**Generar datos de voz médica en español y gallego para entrenar sistemas de reconocimiento del habla.**

Balidea quiere entrenar un sistema de reconocimiento de voz para el ámbito sanitario en Galicia, como el dictado de informes clínicos. Para ello necesita audio médico transcrito en español y en gallego. Las grabaciones reales de este tipo son escasas, y en gallego prácticamente no existen. Balidea usa nuestro sistema para generar ese audio de forma sintética.

**Flujo**

1. Se eligen los modelos de síntesis de voz mediante el método Arena, por idioma y perfil de voz.
2. Se genera un corpus de frases médicas en español, cada una con dos descripciones de voz, se preprocesa y se traduce al gallego.
3. Se clonan las voces de persona mayor, que no se pueden diseñar bien con una descripción: primero en castellano y, si salen bien, también en gallego, aunque el modelo de clonación no admita oficialmente el gallego ([ADR-006](decisions/006-chatterbox-mayor-gallego.md)). El equipo las escucha antes de usarlas.
4. Se sintetiza cada frase con sus dos voces y estilos de habla.
5. Opcionalmente, si el estudio de viabilidad lo confirma, se añade ruido y otros efectos acústicos para acercar el audio a condiciones reales.
6. Se obtiene un dataset de audio con su transcripción, listo para entrenar un ASR.
7. El proceso se repite tantas veces como haga falta para aumentar el volumen de datos.
8. Opcionalmente, si el tiempo lo permite, se entrena y evalúa un ASR con los datos generados.

El detalle técnico de este flujo (qué componente hace cada paso, dónde se ejecuta y qué ficheros intercambian) está en [ARCHITECTURE.md](ARCHITECTURE.md#4-flujo-de-principio-a-fin).

**Criterios de éxito**

- El dataset contiene al menos 5 horas de audio en español y 5 en gallego, cada audio con su transcripción exacta.
- Los modelos usados son los elegidos tras el método Arena ([ADR-005](decisions/005-modelos-por-perfil.md), [ADR-006](decisions/006-chatterbox-mayor-gallego.md)), y las voces clonadas figuran en su catálogo con su referencia y parámetros.
- Otra persona puede repetir la generación siguiendo la documentación.

## Equipo

| Nombre | Rol | Contacto |
| --- | --- | --- |
| Javier Arrojo | Tech Lead | javier.arrojo@rai.usc.es |
| Mara Barreiro | Voice AI Engineer | mara.barreiro@rai.usc.es |
| Yara Costas | Voice AI Engineer | yara.costas@rai.usc.es |
| Elena Couto | Project Manager | elena.couto@rai.usc.es |

## Estructura de la entrega

```
entregas/
  cu-13-voz-sintetica-asr-medico/
    README.md
    ARCHITECTURE.md
    specs/
      01-seleccion-modelos-tts.md
      02-corpus-textos-medicos.md
      03-traduccion-gallego.md
      04-adaptacion-clonacion-voz.md
      05-generacion-dataset.md
      06-aumento-ruido.md
      07-entrenamiento-evaluacion-asr.md
    decisions/
      001-corpus-generado-con-llm.md
      002-traduccion-nos-mt.md
      003-sintesis-cesga-un-trabajo-por-modelo.md
      004-formato-dataset.md
      005-modelos-por-perfil.md
      006-chatterbox-mayor-gallego.md
    prompts/
      generacion-textos-medicos-es.md
    codigo/
      corpus/          # script de preprocesado del corpus, con su configuración y sus pruebas
```

| Fichero | Contenido |
| --- | --- |
| `README.md` | Qué es el proyecto, motivación, alcance, caso de uso, equipo y estructura de la entrega. |
| `ARCHITECTURE.md` | Arquitectura de la solución: diagrama, componentes, flujo, correspondencia con las specs, privacidad y riesgos. |
| `specs/01-seleccion-modelos-tts.md` | Búsqueda de modelos abiertos de síntesis y comparación mediante el método Arena. |
| `specs/02-corpus-textos-medicos.md` | Generación y preparación de las frases médicas en español, con sus prompts de voz, modelo y fuente. |
| `specs/03-traduccion-gallego.md` | Traducción automática del corpus al gallego. |
| `specs/04-adaptacion-clonacion-voz.md` | Método de voz por perfil (diseño, voz fija o clonación) y clonación de la voz de persona mayor en castellano y, si sale bien, en gallego. |
| `specs/05-generacion-dataset.md` | Síntesis del audio con variación de voces y estilos de habla, y formato final del dataset. |
| `specs/06-aumento-ruido.md` | Funcionalidad opcional: aplicación de ruido y otros efectos acústicos al audio generado. |
| `specs/07-entrenamiento-evaluacion-asr.md` | Funcionalidad opcional: entrenar y evaluar un ASR con los datos generados. |
| `decisions/*.md` | Una decisión de arquitectura por fichero: decisión, motivación, alternativas descartadas y referencias. |
| `prompts/generacion-textos-medicos-es.md` | Prompt versionado con el que se genera el corpus en español (ADR-001). |
| `codigo/corpus/` | Script de preprocesado del corpus en castellano y en gallego (specs 02 y 03, componente C2). |
