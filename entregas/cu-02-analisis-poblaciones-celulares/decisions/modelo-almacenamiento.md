# ADR: SQLite como almacenamiento persistente

## Decisión
Guardamos datasets, ficheros, rutas, preferencias y ajustes en **SQLite**, en el directorio de datos del usuario. Además guardamos las **filas originales** de cada fichero (como texto) para poder cambiar el mapeo de columnas sin volver a subirlo. El esquema está versionado con migraciones.

## Motivación
- Es una aplicación de escritorio con **un solo usuario** y poca concurrencia; SQLite serializa las escrituras y ofrece transacciones ACID, más que suficientes sin instalar ni gestionar un servidor.
- Es un único fichero, sin proceso aparte, y encaja con el enfoque *local-first*: los datos no salen del equipo.
- El backend necesita acceder a los datos para analizarlos, algo que el navegador no permite de forma fiable.
- **Filas originales como texto:** al reprocesar con otro mapeo se obtiene exactamente el resultado que daría el fichero original. El volumen (decenas de filas por fichero) hace despreciable el coste.

## Alternativas
- **LocalStorage o cookies:** el backend no puede acceder a ellos y tienen una cuota pequeña (en torno a 5 MB).
- **PostgreSQL, MySQL u otro SGBD:** necesitan su propio proceso y destacan en backends compartidos por muchos usuarios.
- **Ficheros planos (JSON, Parquet):** sin consultas, sin actualizaciones atómicas y sin versionado de esquema.
- **Solo memoria:** se pierde todo al cerrar la aplicación.
- **Guardar el fichero original** en lugar de las filas: obligaría a volver a interpretar formatos distintos en cada remapeo.

## Consecuencias
- La base de datos no está cifrada; las claves API no están en ella, sino en el keyring del sistema.
- Cada cambio de esquema exige una migración.
- Con muy alta concurrencia no escalaría, pero no es un caso de uso.

## Referencias
- SQLite, usos apropiados: https://www.sqlite.org/whentouse.html
- SQLite, confirmación atómica: https://www.sqlite.org/atomiccommit.html
- SQLite, modo WAL: https://www.sqlite.org/wal.html
- Almacenamiento máximo en LocalStorage: https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria#how_much_data_can_be_stored