# ADR · Estrategia de lectura de PDF para DOC-001

**Estado** · Propuesta para revisión del equipo

## Contexto

DOC-001 prevé recuperar texto de PDF digitales, escaneados y mixtos, conservando la procedencia, las limitaciones de lectura y el orden cuando puede determinarlo. La interpretación clínica corresponde a CLI-001. [Especificación DOC-001](../specs/ingesta-documentos.md)

## Decisión propuesta

**Usar PyMuPDF para extraer texto digital visible y PP-OCRv6 small para procesar imágenes escaneadas, con ejecución local y procedencia por documento, página y región.**

- **Texto digital visible.** Extraer con PyMuPDF, conservar los caracteres y el idioma original y recuperar el orden de los bloques cuando sea determinable.
- **Página escaneada.** Si carece de texto digital recuperable y contiene material que requiere lectura de imagen, renderizarla y aplicar OCR. Registrar las páginas realmente vacías como «sin texto recuperado».
- **Texto e imágenes en la misma página.** Examinar las regiones de imagen, aplicar OCR donde corresponda y combinar los bloques por posición y orden. Eliminar duplicados por superposición de capas y conservar las repeticiones del original. La fusión con PyMuPDF y PP-OCRv6 requiere validación experimental.
- **GPU ausente o entorno incompatible.** Considerar Tesseract como alternativa de contingencia en CPU. Ante fallos parciales, conservar los bloques recuperados y registrar la incidencia con su procedencia.
- **Lectura incierta.** Señalar manuscritos dudosos, casillas indeterminadas y relaciones inciertas entre campos o celdas para revisión humana. Distinguir esas advertencias del texto transcrito. Conservar el texto tachado legible con una advertencia y omitir el texto bajo ocultaciones opacas observables.

## Alternativas consideradas y justificación

### Texto digital

- **PyMuPDF, propuesto.** `Page.get_text("words")` devuelve palabras con cajas e índices de bloque y línea. Reutiliza la API que emplea el benchmark para renderizar recortes y llevar las posiciones del OCR a las coordenadas de página, teniendo en cuenta la rotación. [API de páginas de PyMuPDF](https://pymupdf.readthedocs.io/en/latest/page.html) · [Formatos de extracción de texto](https://pymupdf.readthedocs.io/en/latest/app1.html)
- **pdfplumber, alternativa viable.** Extrae texto y palabras con cajas y permite recortar y renderizar páginas para inspección visual. Su integración con el renderizado actual requeriría un adaptador y comprobar la correspondencia de coordenadas, recortes, rotación y orden. La comparación es documental. [Documentación de pdfplumber](https://github.com/jsvine/pdfplumber#extracting-text)

### OCR

- **Tesseract, contingencia en CPU.** Funciona localmente con paquetes de idioma y modos de segmentación configurables. La salida TSV proporciona cajas de palabras para localizar el texto. Su instalación en CPU simplifica el despliegue. En la muestra obtuvo más errores de texto y dejó más dificultades de asignación a celdas que PP-OCRv6. [Documentación de Tesseract](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)
- **PP-OCRv6 small, propuesto.** Combina detección y reconocimiento de texto y devuelve resultados localizables para el procesamiento por regiones. Obtuvo menor error en las regiones escaneadas comunes y más coincidencias en las celdas anotadas. Requiere modelos y un entorno Paddle compatible. Los tiempos publicados se midieron con GPU. [Pipeline OCR de PaddleOCR](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)
- **PaddleOCR-VL-1.6, evaluación inconclusa.** Combina análisis de diseño y reconocimiento multimodal, de interés para la estructura documental y las tablas. Inicializó en CPU y superó el límite de 180 segundos durante el procesamiento. Queda para una evaluación posterior con métricas comparables. [Documentación de PaddleOCR-VL](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)

## Evidencia experimental

### Pruebas sintéticas

La fixture mixta combina la cabecera digital «CABECERA DIGITAL», «SELLO COMÚN» presente en dos capas superpuestas y «ANEXO ESCANEADO 007» presente solo en una imagen. La referencia fija esas tres líneas en ese orden y cuenta el sello una vez. En la auditoría, el híbrido PyMuPDF/Tesseract obtuvo CER y WER del 0 % en esa región y registró la supresión de coincidencias solapadas. PyMuPDF por sí solo dejó sin recuperar el anexo. El caso comprueba la fusión de esas dos vías en un PDF controlado. La combinación con PP-OCRv6 sigue pendiente.

En otro PDF sintético de la auditoría, una imagen opaca cubría un marcador recuperable de la capa textual. El benchmark devolvió el marcador sin advertencia en ausencia de una exclusión anotada. El filtro actual examina capas invisibles y determinados rectángulos dibujados. Una prueba con exclusión anotada verifica el enmascaramiento suministrado y deja por demostrar la detección de esa ocultación. DOC-001 exige omitir el texto bajo ocultaciones opacas observables y mantenerlo fuera de las evidencias de CLI-001.

### Evaluación clínica local

La evaluación complementaria se realizó en el equipo de prueba local sobre cuatro páginas clínicas. Se presentan resultados agregados.

La ejecución histórica registró **160 regiones de referencia validadas** y revisadas visualmente por un integrante, además de 47 excluidas y una pendiente por una selección en blanco sin texto evaluable. Las excluidas y la pendiente quedaron fuera de las métricas de precisión. Las regiones de OCR textual se contrastaron con transcripciones humanas. El recuento de referencias validadas incluye distintos tipos de tarea. El número de regiones puntuadas puede variar según el motor.

El equipo usó WSL2, un Intel i9-12900K y una RTX 3060 de 12 GB. La tabla recoge la comparación pareada de **99 regiones de texto escaneado puntuadas por ambos motores**. CER y WER dividen la suma de ediciones por la suma de caracteres o palabras de referencia, respectivamente. Una región que un motor no puntúa queda fuera del par. Este resumen no dispone del total de caracteres o palabras ni de los recuentos de fallos y cobertura por motor para ese subconjunto.

| Métrica | Tesseract en CPU | PP-OCRv6 small en GPU |
| --- | ---: | ---: |
| CER | 5,64 % | 3,08 % |
| WER | 17,79 % | 14,06 % |
| Mediana por región | 187 ms | 20 ms |

- **Texto digital.** PyMuPDF obtuvo CER y WER del 0 % en 14 regiones con referencia procedente de la propia capa textual. El resultado mide fidelidad respecto a esa capa. Queda pendiente una referencia visual independiente.
- **Tabla.** PP-OCRv6 obtuvo 29 coincidencias de 31 celdas anotadas y Tesseract 0 de 31, con 12 bloques de Tesseract sin asignar. La proyección geométrica combina reconocimiento y asignación a cajas anotadas. Una celda de referencia vacía puede coincidir sin un bloque asignado. El recuento deja por medir el reconocimiento de la estructura de tabla y la calidad del texto por separado.
- **Manuscritos.** PP-OCRv6 obtuvo un CER del 37,01 %. El número de regiones puntuadas y el total de caracteres de referencia no constan en este resumen.
- **Casillas.** El clasificador acertó las 16 decisiones que emitió y se abstuvo en 30 de 46 referencias. El acierto entre decisiones emitidas fue 16/16, la cobertura de decisiones 16/46 y el acierto sobre todas las referencias 16/46.

La ventaja de PP-OCRv6 en error justifica priorizarlo para escaneados en el prototipo. Los tiempos describen las configuraciones de ejecución en CPU y GPU. La velocidad relativa en el mismo hardware queda por medir. La muestra permite orientar la implementación y es insuficiente para estimar la precisión sobre historias clínicas completas. El híbrido ejecutado combinaba PyMuPDF y Tesseract. Las cuatro páginas carecían de un caso verdaderamente mixto para comprobar la fusión.

### Alcance de la publicación

La evidencia de esta entrega consiste en los casos sintéticos descritos y las métricas agregadas de la comparación clínica. Los originales, transcripciones, anotaciones, resultados brutos y el informe clínico se conservan en el entorno autorizado. El uso de documentación clínica real requiere autorización de la entidad y está sujeto a sus condiciones de tratamiento y acceso. [Privacidad en DOC-001](../specs/ingesta-documentos.md#privacidad-y-decisiones-tecnicas-pendientes)

## Consecuencias

### Positivas

- Menor error observado con PP-OCRv6 en la muestra escaneada y posibilidad de ejecutar ambas etapas en local.
- Reutilización de PyMuPDF para texto, renderizado y coordenadas, como base para conservar la procedencia por documento, página y región.
- Separación entre lectura documental y razonamiento clínico.

### Negativas y costes

- Mayor complejidad de instalación y mantenimiento del entorno Paddle. El rendimiento medido depende de la configuración con GPU.
- Calidad insuficiente para confiar automáticamente en valores manuscritos. Las abstenciones y las asociaciones inciertas en formularios y tablas requieren mecanismos explícitos de incertidumbre y revisión humana.

### Trabajo pendiente

- Implementar y evaluar el híbrido PyMuPDF + PP-OCRv6 en páginas mixtas representativas. Incluir casos sintéticos de orden de lectura, duplicados por superposición, tachaduras y fallos parciales. Añadir ocultaciones por imagen sin exclusiones anotadas y comprobar que se preservan los segmentos visibles, se localiza la limitación y el texto tapado queda fuera de las evidencias clínicas. [Criterios de aceptación de DOC-001](../specs/ingesta-documentos.md#7-criterios-de-aceptacion)
- Ampliar la variedad de documentos e idiomas, incluido el francés, y comparar resoluciones. Completar la evaluación de PaddleOCR-VL si su coste permite una comparación útil.
- Acordar criterios de aceptación con la entidad y verificar en la implementación que se conservan las limitaciones de lectura y su procedencia según el contrato documental. [Contrato documental](../ARCHITECTURE.md#contratos-y-validación)
