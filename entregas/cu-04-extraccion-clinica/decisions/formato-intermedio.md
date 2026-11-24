# ADR · Representación intermedia y validación de contratos del CU-04

**Estado documental** · Las fronteras, los contratos y las propuestas de validación y compatibilidad están documentados y reconciliados con la arquitectura.

**Estado de revisión** · Revisión cruzada técnica con la arquitectura realizada y registrada en la issue interna #3.

**Estado de aprobación** · Propuesta pendiente de aprobación formal del equipo.

## Contexto

El CU-04 prepara documentación de un paciente para extraer variables clínicas y estructurar resultados para REDCap. Una página ilegible puede convivir con páginas útiles y un candidato validado puede quedar pendiente de incorporación. Cada etapa necesita conservar la procedencia y las limitaciones de los datos para poder comprobarlos en la siguiente. [Alcance del CU-04](../README.md)

## Decisión propuesta

**Usar Pydantic v2 para definir y validar los modelos de contrato en Python, con JSON cuando se necesite intercambiar o conservar representaciones y con comprobaciones propias de integridad y coherencia.** Pydantic automatiza la validación estructural y la reconstrucción de modelos anidados con menos código manual que la alternativa con `dataclasses` ensayada. Las invariantes del dominio siguen requiriendo validadores propios. JSON permite reconstruir los contratos sin compartir instancias de Python. El formato y el mecanismo de incorporación posterior a REDCap quedan por acordar. [Modelos de Pydantic](https://pydantic.dev/docs/validation/latest/concepts/models/) · [Serialización](https://pydantic.dev/docs/validation/latest/concepts/serialization/)

- **DOC-001 → CLI-001.** Entregar la identidad de la entrega y el estado global de la entrada, los documentos en orden de recepción con identificador, archivo y estado, y las páginas con número físico, naturaleza y estado de lectura. Distinguir texto transcrito y elementos descritos, con orden y localización cuando consten. Conservar las páginas fallidas y las incidencias con motivo, efecto y procedencia. [DOC-001](../specs/ingesta-documentos.md#4-entradas-y-resultados-esperados)
- **CLI-001 → RCP-001.** En una entrega válida, incluir la referencia a la entrega documental exacta y un resultado por variable solicitada con su definición, estados de evaluación e interpretación, candidatos, menciones contextuales y relaciones. Conservar polaridad, sujeto, fechas con su precisión, ámbito temporal, desenlace de búsqueda, cobertura efectiva e incidencias. Cada evidencia enlaza el fragmento o descripción con su origen e indica qué parte respalda. Mantener las alternativas ante contradicciones o una selección temporal pendiente. [CLI-001](../specs/extraccion-datos-clinicos.md#4-entradas-y-resultados-esperados)
- **Salida de RCP-001.** En una entrega válida, incluir la referencia a la entrega clínica y un resultado por campo solicitado con el diccionario, la definición, la correspondencia y las validaciones aplicadas o el motivo de su ausencia. Separar el valor preparado del candidato y sus evidencias, con vínculos por opción en selecciones múltiples. Conservar el estado de preparación, las dependencias con los valores o estados de evaluación y la incorporación propuesta con sus motivos. [RCP-001](../specs/exportacion-redcap.md#4-entradas-y-resultados-esperados)

### Entregas, incidencias y acceso a evidencias

El orquestador reúne las entregas válidas y un resumen que distingue las etapas ejecutadas con entrega válida, las bloqueadas por sus entradas o configuración y las fallidas al ejecutar o validar. Si una etapa carece de entrega, el resumen conserva el motivo y las referencias de las variables o campos afectados cuando se conocen. Con las entradas previas válidas, una selección vacía produce una entrega válida con cero resultados. También se conservan las entregas válidas con resultados pendientes. [Incidencias y ejecución parcial](../ARCHITECTURE.md#incidencias-y-ejecucion-parcial)

DOC-001 emite una entrega validada e inmutable identificada por ejecución y entrega. Si se reconstruye con cambios, recibe otra identidad. CLI-001 registra la entrega exacta que consumió y RCP-001 tiene acceso de solo lectura a esa misma entrega para resolver las evidencias. El paquete sintético propuesto reúne el resumen, las entregas válidas, la configuración efectiva y la versión de los validadores para repetir las comprobaciones. [Trazabilidad y acceso a evidencias](../ARCHITECTURE.md#trazabilidad-y-acceso-a-evidencias)

### Validación en los límites de los módulos

- **Estructural.** Declarar tipos, propiedades admitidas, objetos anidados y formatos. Usar validación estricta para evitar coerciones como leer un número de página enviado como texto. Al leer JSON, aplicar la validación del modelo y después las comprobaciones de integridad del contrato. La arquitectura también propone validar las entregas recibidas en memoria antes de publicarlas. [Modo estricto de Pydantic](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/)
- **De integridad.** Comprobar con código propio la unicidad de identificadores, la identidad de las entregas enlazadas, la resolución de referencias y su pertenencia a la cobertura declarada. CLI-001 coteja que cada cita sea un fragmento literal no vacío del bloque y que cada descripción coincida con su elemento documental. RCP-001 comprueba esa correspondencia para las evidencias de una asignación. Una negación documentada requiere una mención negada con evidencia, y un campo proponible requiere un valor validado y las condiciones de incorporación resueltas. [Contratos y validación](../ARCHITECTURE.md#contratos-y-validación)
- **Funcional.** CLI-001 interpreta si una evidencia respalda al sujeto y al hecho y aplica los criterios de selección temporal acordados. RCP-001 aplica las correspondencias, códigos, restricciones y reglas del estudio. La coherencia de un estado declarado se comprueba en el contrato. Su justificación clínica o conforme al estudio corresponde al módulo productor. [Comportamiento de CLI-001](../specs/extraccion-datos-clinicos.md#5-comportamiento-funcional) · [Comportamiento de RCP-001](../specs/exportacion-redcap.md#5-comportamiento-funcional)

### Versionado y compatibilidad

Cada entrega identifica el esquema de su frontera y su versión `mayor.menor`. Las referencias a la configuración clínica, al diccionario y a las reglas se registran aparte. Cada consumidor declara las versiones admitidas, selecciona el modelo correspondiente y rechaza las combinaciones desconocidas con un motivo explícito.

Se mantiene la validación estricta de propiedades y estados. Un campo opcional conocido puede omitirse si el modelo lo permite. Un lector anterior puede rechazar un campo nuevo presente aunque el productor lo declare opcional. Los cambios aditivos incrementan la versión menor y los cambios incompatibles de estructura o significado incrementan la mayor. Se actualizan los lectores y sus pruebas de compatibilidad antes de que los productores emitan la nueva versión. [Política de compatibilidad propuesta](../ARCHITECTURE.md#versionado-y-compatibilidad)

## Alternativas consideradas y justificación

- **Pydantic v2, propuesto.** En las dos fronteras comparadas, los modelos declarados reconstruyen objetos anidados con menos código de carga estructural que los lectores manuales. Ambas opciones comparten los validadores de integridad.
- **`dataclasses` con validación manual, alternativa viable.** Obtiene el mismo resultado en los casos comparados y prescinde de una dependencia externa. Requiere escribir comprobaciones de tipos y propiedades, componer rutas de error y reconstruir cada nivel de documentos y evidencias. [Documentación de `dataclasses`](https://docs.python.org/3.13/library/dataclasses.html)
- **Diccionarios Python y JSON con JSON Schema, comparación documental.** Los diccionarios y JSON transportan datos. JSON Schema valida su estructura con herramientas independientes de Python. Resolver evidencias contra otra entrada requiere lógica adicional y mantener esquemas separados duplicaría la descripción estructural. Si se necesita publicar esa descripción, Pydantic permite generarla a partir del modelo. [JSON Schema](https://json-schema.org/understanding-json-schema/about) · [Generación de esquemas con Pydantic](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)

## Evidencia experimental

- **DOC-001 → CLI-001.** Pydantic y `dataclasses` conservan en JSON documentos con el mismo nombre, páginas fallidas y contenido legible independiente. Las pruebas rechazan identificadores duplicados, tipos incorrectos, propiedades desconocidas, referencias inexistentes y contenido atribuido a archivos rechazados.
- **CLI-001 → RCP-001.** Ambas alternativas conservan menciones contextuales, fechas con su precisión, alternativas contradictorias declaradas, cobertura por documento y selección temporal pendiente. Comprueban que las referencias resuelvan a documentos, páginas y elementos existentes y que el documento figure en la cobertura declarada. La auditoría confirmó que ambos validadores aceptan una cita de negación vinculada a otro bloque existente cuyo texto afirma lo contrario. Resolver un identificador acredita su existencia. El cotejo de la cita con el contenido y la interpretación de lo que sustenta requieren comprobaciones adicionales.
- **Salida de RCP-001.** La PoC en Pydantic conserva campos válidos junto a incompatibles o pendientes. Detecta evidencias omitidas al comparar la instantánea con la entrega clínica de entrada. Comprueba algunos estados de incorporación declarados, entre ellos la exclusión por una dependencia de incorporación incumplida. Rechaza propiedades y estados desconocidos y versiones de salida distintas de `"1"`.

El registro original documenta **61 pruebas** de `unittest` por versión de Python (3.13.14 y 3.14.10), con Pydantic 2.13.4. Son 18 documentales, 30 clínicas y 13 de preparación. La auditoría repitió las 61 en Python 3.13.18. Verifican carga, conservación y determinadas invariantes sobre datos preconstruidos. El OCR, la extracción clínica, las correspondencias y las reglas del estudio requieren pruebas funcionales propias.

### Ejemplo sintético

- **Negación explícita documentada.** Para «afección Alfa» se conserva «El 3 de marzo de 2026 se descarta afección Alfa» (`D1`, página 1, elemento `B1`) como evidencia de la negación.
- **No encontrado en la documentación disponible.** En un conjunto limitado a `D6`, que contiene un valor de Gamma, una búsqueda terminada sin mención de Alfa conserva la cobertura y el motivo, sin fragmento probatorio de ausencia. La PoC conserva un estado de ausencia preconstruido con cobertura declarada en `D6`. El fin de búsqueda queda por verificar.

En el diccionario ficticio DS-01, una correspondencia expresa para el sujeto y el ámbito permite preparar `0` para la negación en `alfa_presente`. El resultado «no encontrado» deja ese campo sin valor preparado. La PoC conserva ambas salidas al serializarlas y reconstruirlas. En el contrato documental, ambas alternativas rechazan el número de página `"2"` como cadena y aceptan `2` como entero si el resto de la entrega es válido. [Diccionario sintético DS-01](../specs/exportacion-redcap.md#diccionario-sintetico-de-referencia-ds-01)

## Consecuencias

### Positivas

- Las etapas pueden comprobar la procedencia y conservar los resultados útiles junto a las incidencias, sin perder alternativas ni decisiones pendientes.
- La preparación local y la incorporación propuesta quedan separadas. Una asignación validada puede conservarse para revisión cuando su incorporación está excluida o pendiente.

### Negativas y costes

- Pydantic añade una dependencia y el equipo debe mantener los validadores y sus pruebas. `hide_input_in_errors=True` e `include_input=False` ayudan a ocultar valores de entrada. La auditoría comprobó que una clave desconocida puede aparecer en la ruta de error aunque se oculte el valor. Los diagnósticos al usuario y los logs usarán códigos y motivos predefinidos, rutas de esquema conocidas y referencias opacas. Se deben filtrar claves desconocidas y advertencias de serialización y excluir trazas, mensajes de excepción y fragmentos derivados. Las exportaciones de depuración de ejecuciones reales quedan desactivadas mientras su uso no se acuerde. La propuesta se verificará con datos sintéticos. [Diagnósticos en la arquitectura](../ARCHITECTURE.md#diagnosticos) · [Configuración de Pydantic](https://pydantic.dev/docs/validation/latest/api/pydantic/config/) · [Detalles de `ValidationError`](https://pydantic.dev/docs/validation/latest/api/pydantic-core/pydantic_core/)
- La validación estricta mediante `extra="forbid"` exige coordinar el despliegue cuando se añaden propiedades.

### Trabajo pendiente

#### Aprobación formal del equipo

Registrar la aprobación formal del equipo sobre las propuestas descritas. [Arquitectura](../ARCHITECTURE.md#contratos-y-validación)

#### Implementación y pruebas

- Implementar la validación e inmutabilidad de las entregas en memoria, su identidad y el cotejo de citas sobre la entrega exacta, con cobertura por página o región y desenlace de búsqueda. Probar por separado la validación semántica y la aplicación de reglas del estudio.
- Implementar la gestión de entregas parciales y el resumen del orquestador, el filtrado de diagnósticos y el paquete para verificar ejecuciones sintéticas.
- Aplicar la política común de versiones y probar la compatibilidad entre productores y consumidores. Incorporar soporte simultáneo y migraciones cuando se necesiten.

#### Acuerdos con la entidad

- Confirmar con Ceres Fernández Rozadilla el subconjunto, las definiciones, los sujetos y ámbitos temporales, y los criterios ante discrepancias, repeticiones y selecciones temporales. Acordar las correspondencias autorizadas, códigos, transformaciones, ausencias y dependencias, el formato y mecanismo de incorporación y el procedimiento de revisión humana. [Cuestiones pendientes del proyecto](../README.md#pendiente-de-validación) · [CLI-001](../specs/extraccion-datos-clinicos.md#8-cuestiones-abiertas) · [RCP-001](../specs/exportacion-redcap.md#8-cuestiones-abiertas)
- Acordar el entorno, los accesos y el tratamiento y conservación de materiales, entregas y referencias reales. Los fragmentos, las instantáneas y los errores derivados pueden contener información identificativa. Los ejemplos y evidencias destinados a publicación serán sintéticos. [Privacidad en DOC-001](../specs/ingesta-documentos.md#privacidad-y-decisiones-tecnicas-pendientes)
