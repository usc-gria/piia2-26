# ADR - Dataset trazable con archivos y metadatos CSV

## 1. Estado

Aceptada como estrategia inicial, pendiente de validación experimental.

## 2. Contexto y motivación

El estimador de peso necesita un dataset en el que cada imagen esté vinculada, sin ambigüedad, al animal que aparece en ella y a su peso real medido en gramos. La primera campaña de captura en Aviporto prevé registrar imágenes y pesos de aproximadamente 30–40 animales diferentes, según el tiempo disponible, con varios fotogramas por individuo. Son cifras de planificación: todavía no se dispone del dataset propio.

Hay tres necesidades que condicionan cómo se organizan los datos:

- **Trazabilidad.** Debe ser posible recorrer el camino inverso desde cualquier imagen hasta el vídeo del que procede, el instante exacto del fotograma y el pesaje que la etiqueta. Si una imagen resulta sospechosa, o un pesaje se corrige, hay que poder localizar todas las imágenes afectadas.
- **Separación por animal.** Los fotogramas de un mismo pollo son casi idénticos. Si unos acaban en entrenamiento y otros en test, la evaluación resulta demasiado optimista sin que nada lo delate. La pertenencia a un conjunto debe decidirse por animal y quedar registrada.
- **Reproducibilidad con un equipo pequeño.** El dataset lo preparan y consumen tres personas con scripts y notebooks, sin infraestructura de servidor. Además, los datos de la explotación están sujetos a confidencialidad (NDA), por lo que las imágenes, los vídeos y los metadatos reales no se publican en el repositorio.

Esta decisión se refiere al **dataset individual de la fase A** descrito en el [apartado 4.1 de la arquitectura](../ARCHITECTURE.md#41-datos-de-entrada-y-datasets-preparados). Las escenas con varios animales y sus anotaciones de rectángulos (fase B) tendrán un formato adaptado a las herramientas de detección que se elijan, y quedan fuera del alcance de este ADR.

## 3. Decisión adoptada

Se decide **conservar los vídeos y las imágenes como archivos y relacionarlos con sus datos mediante ficheros CSV de metadatos**.

- Los **vídeos originales** se conservan sin modificaciones.
- Las **imágenes** extraídas se guardan como archivos de imagen en una carpeta, sin que el nombre ni la carpeta lleven la información de etiquetado.
- Un **CSV de etiquetas** contiene una fila por imagen, con los campos definidos en el [apartado 4.1 de la arquitectura](../ARCHITECTURE.md#41-datos-de-entrada-y-datasets-preparados):

| Campo | Significado |
| --- | --- |
| `image_id` | Identificador único de la imagen. |
| `image_path` | Ruta del archivo de imagen. |
| `animal_id` | Identificador del animal utilizado para agrupar sus imágenes. |
| `weight_g` | Peso de referencia medido en la sesión, expresado en gramos. |
| `session_id` | Sesión de captura. |
| `video_id` | Vídeo de procedencia. |
| `timestamp_s` | Instante del fotograma respecto al inicio del vídeo, en segundos. |
| `split` | Asignación a entrenamiento, validación o test. |

El CSV constituye la referencia de metadatos para consumir el dataset, en lugar del nombre o la ubicación de los archivos. Los pesos y las asociaciones entre animales e intervalos proceden de los registros originales de captura y pesaje, que se conservan para su comprobación. La asignación de cada animal a un conjunto se calcula una vez, por `animal_id`, y se guarda para reutilizarla entre experimentos.

Dos decisiones de diseño merecen una explicación:

- **El instante se guarda en segundos, no como número de fotograma.** La tasa de fotogramas de una cámara puede no ser constante, y el instante en segundos permite localizar el fotograma en el vídeo original con independencia de la frecuencia de extracción que se haya configurado.
- **El peso se guarda por imagen, pero corresponde a la sesión.** Si un animal vuelve a grabarse en otra sesión y puede reconocerse de forma fiable, mantiene su `animal_id` y su peso se registra por sesión, que es el valor que corresponde a cada imagen.

### Ejemplo ficticio

Los siguientes datos son **inventados** y solo ilustran el formato. No proceden de ninguna captura ni de ningún animal real. El animal `P002` aparece en dos sesiones con pesos distintos y todas sus imágenes están en el mismo conjunto.

```csv
image_id,image_path,animal_id,weight_g,session_id,video_id,timestamp_s,split
IMG_000001,images/IMG_000001.jpg,P001,1720,S01,V001,12.0,train
IMG_000002,images/IMG_000002.jpg,P001,1720,S01,V001,13.0,train
IMG_000003,images/IMG_000003.jpg,P002,1655,S01,V002,4.0,val
IMG_000004,images/IMG_000004.jpg,P002,1655,S01,V002,5.0,val
IMG_000005,images/IMG_000005.jpg,P002,1790,S02,V007,8.0,val
IMG_000006,images/IMG_000006.jpg,P003,1835,S01,V003,6.0,test
IMG_000007,images/IMG_000007.jpg,P003,1835,S01,V003,7.0,test
```

Con estos datos, la imagen `IMG_000004` se puede rastrear así: pertenece al animal `P002`, se extrajo del vídeo `V002` en el segundo 5,0, su etiqueta es 1655 g y está en validación. Para auditar la etiqueta se localiza en el registro de pesajes la fila cuyo vídeo e intervalo contienen ese instante y se comprueba que coincide el animal y el peso.

## 4. Alternativas consideradas

### 4.1. Organizar solo mediante nombres de archivo

Consiste en codificar la información en el nombre de cada imagen, por ejemplo `P002_S01_V002_000005_1655g.jpg`. Su ventaja es que cada archivo lleva su etiqueta consigo y no hace falta ningún otro fichero.

Se descarta como mecanismo principal por varios motivos:

- Obliga a interpretar los nombres con código propio, y un guion o un separador mal colocado puede producir una etiqueta errónea.
- Añadir un campo nuevo implica renombrar todos los archivos, lo que rompe cualquier referencia anterior a ellos.
- Los nombres largos con datos de la explotación se propagan a cualquier lugar donde se copie o se muestre el archivo.
- Un nombre no impide que el mismo archivo exista con dos nombres distintos, y no permite comprobar fácilmente que los campos son coherentes.

Sí se mantiene un nombre de archivo sencillo y único, derivado de `image_id`, como ayuda para el manejo manual.

### 4.2. Organizar mediante carpetas

Consiste en una estructura de carpetas, por ejemplo `train/P001/…`, `val/P002/…`, o bien una carpeta por clase al estilo de `imagefolder`. Es la opción más sencilla de entender y es la que el equipo ya conoce del dataset de pesos del curso anterior.

Se descarta como mecanismo principal porque:

- Una carpeta solo expresa una dimensión. Para el peso, la sesión, el vídeo y el instante habría que combinar nombres y carpetas, con los mismos problemas del caso anterior.
- Las carpetas por conjunto hacen que el reparto entre entrenamiento, validación y test dependa de dónde esté físicamente cada archivo. Reasignar un animal implica mover archivos, y una copia o un movimiento incompleto puede dejar al mismo animal en dos conjuntos sin que se note.
- El peso es un valor continuo, y una carpeta por valor, o por categoría de peso, perdería precisión o generaría cientos de carpetas.
- Un animal grabado en dos sesiones con pesos distintos no encaja de forma natural en una estructura de una sola jerarquía.

Se admite que, para ciertas herramientas, pueda generarse una estructura de carpetas derivada del CSV, pero esa estructura sería una vista generada y no la fuente de verdad.

### 4.3. Utilizar una base de datos SQLite

Consiste en guardar los metadatos y las referencias a los archivos en una base de datos SQLite. Es una alternativa seria: no necesita servidor, se almacena en un único fichero y permite consultas, tipos de datos y restricciones de integridad entre tablas.

Se descarta como opción inicial, aunque no por ser inadecuada, sino porque su ventaja principal no compensa el coste en este momento:

- El volumen previsto (decenas de animales y miles de imágenes) cabe cómodamente en un CSV y se carga entero en memoria con `pandas`. Las consultas necesarias (agrupar por animal, comprobar duplicados, filtrar por conjunto) se resuelven con esa biblioteca.
- Un CSV es texto: se puede abrir con cualquier editor o con una hoja de cálculo, y facilita la revisión manual de las imágenes y las incidencias, que es una parte explícita del flujo de preparación. Un fichero de base de datos es binario y requiere herramientas específicas para inspeccionarlo o para comparar versiones.
- El CSV puede cargarse directamente desde nuestros scripts y notebooks y transformarse al formato que requiera cada herramienta.
- El equipo es de tres personas, sin accesos concurrentes de escritura que justifiquen un motor de base de datos.

La pérdida que se acepta es la **integridad referencial automática**: un CSV no impide por sí mismo una fila con una ruta inexistente, un peso negativo o un animal asignado a dos conjuntos. Esa garantía se sustituye por comprobaciones explícitas, descritas en el apartado siguiente. Esta decisión se podrá reconsiderar si el dataset crece de forma notable, si aparecen varias tablas relacionadas (por ejemplo, detecciones, anotaciones y resultados integrados) o si varias personas necesitan modificar los datos a la vez.

## 5. Consecuencias prácticas

- **Trazabilidad hacia atrás.** Cada imagen se enlaza con su vídeo (`video_id`), su instante (`timestamp_s`) y su sesión (`session_id`), y a través de ellos con la fila del registro de pesajes que la etiqueta. Los vídeos originales se conservan sin modificaciones, de modo que los fotogramas pueden regenerarse con el mismo instante. Conviene guardar los hashes de los vídeos para detectar cambios.
- **Separación por animal.** La partición se realiza agrupando por `animal_id`: todas las imágenes de un animal reciben el mismo valor de `split`, incluso si el animal aparece en varias sesiones. La asignación de cada animal se registra, de modo que el test se mantiene idéntico entre experimentos. Esto es coherente con la partición agrupada que describe el [ADR de entrenamiento con aprendizaje por transferencia](entrenamiento-con-transfer-learning.md).
- **Comprobaciones automáticas.** Como el CSV no valida sus propios datos, el proceso de preparación debe verificar, como mínimo, que:
  - `image_id` es único y todas las rutas de `image_path` corresponden a archivos existentes;
  - `animal_id` y `session_id` no están vacíos y `weight_g` es un número positivo;
  - cada animal aparece en un único valor de `split`;
  - un mismo animal tiene un único peso por sesión.
- **Comprobación de ausencia de fuga.** Con `pandas`, la separación por animal puede verificarse de forma sencilla. El siguiente fragmento es orientativo y no representa ningún resultado:

```python
import pandas as pd

df = pd.read_csv("labels.csv")

# Cada animal debe estar en un único conjunto.
assert df.groupby("animal_id")["split"].nunique().eq(1).all()

# Los conjuntos no comparten animales.
animales = df.groupby("split")["animal_id"].apply(set)
assert animales["train"].isdisjoint(animales["val"])
assert animales["train"].isdisjoint(animales["test"])
assert animales["val"].isdisjoint(animales["test"])
```

- **Formato y codificación.** Los CSV se guardan en UTF-8, con cabecera, separador coma y punto decimal. Los tipos se fijan al leer el fichero, de modo que `animal_id` y `session_id` se interpretan como texto y no como números.
- **Cambios en el esquema.** Añadir campos al CSV no obliga a tocar las imágenes ni sus nombres. Si se añade un campo, se documenta y se mantiene la compatibilidad con los experimentos anteriores, que registran la versión del dataset y de las particiones que utilizaron.
- **Compatibilidad.** El CSV puede adaptarse a otras herramientas sin cambiar la referencia de metadatos del dataset. Por ejemplo, la biblioteca `datasets` de Hugging Face admite cargar imágenes con un fichero de metadatos, y las carpetas por conjunto, si alguna herramienta las exige, pueden generarse a partir del CSV.
- **Confidencialidad.** Los metadatos de la explotación (identificadores de animales, pesos, fechas) están sujetos al mismo acuerdo de confidencialidad que las imágenes. Los datos reales se guardan en una ubicación privada acordada con la entidad y no se suben al repositorio ni a servicios públicos. Los ejemplos de la documentación son ficticios.

### Limitaciones y aspectos pendientes

- El CSV no impone sus propias reglas. Las garantías descritas dependen de que las comprobaciones automáticas se ejecuten siempre que se genere o se modifique el dataset.
- Si hay pocos animales, la partición por animal da conjuntos de validación y test muy pequeños. Esta decisión permite hacerla de forma correcta y registrada, pero no resuelve esa limitación, que se documenta en el resumen del dataset.
- Los nombres definitivos de los campos y el formato de los identificadores deben mantenerse coherentes entre el protocolo de captura, las herramientas de preparación y la arquitectura. Cualquier cambio se refleja en [ARCHITECTURE.md](../ARCHITECTURE.md) y en este ADR.
- Los datos de la fase B (escenas, rectángulos anotados y resultados de predicción) tienen otra estructura y requerirán su propia decisión si el formato elegido no encaja con este esquema.

## 6. Referencias

1. [Python — módulo `csv`](https://docs.python.org/3/library/csv.html). Lectura y escritura de ficheros CSV con la biblioteca estándar.
2. [pandas — `read_csv`](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html). Carga de un CSV, con control de los tipos de cada columna.
3. [RFC 4180 — Common Format and MIME Type for CSV Files](https://www.rfc-editor.org/rfc/rfc4180). Descripción de referencia del formato CSV.
4. [SQLite — Appropriate Uses For SQLite](https://www.sqlite.org/whentouse.html). Documentación oficial sobre los casos en que SQLite resulta adecuado y aquellos en que no.
5. [Hugging Face Datasets — Create an image dataset](https://huggingface.co/docs/datasets/image_dataset). Carga de imágenes mediante carpetas y ficheros de metadatos.
6. [Scikit-learn — GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html). Separación de los datos por grupos, como `animal_id`, para evitar que un mismo animal aparezca en varios conjuntos.