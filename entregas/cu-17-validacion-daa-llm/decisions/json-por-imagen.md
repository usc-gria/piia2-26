# ADR 1: Crear un archivo JSON individual para cada imagen, con un formato de campos común y fijo

## Decisión (¿Qué hemos decidido?)

La decisión tomada consiste en que cada imagen creada tenga su propio archivo JSON (1 archivo JSON para cada foto). Además, hemos acordado usar los mismos nombres de datos siempre en los JSON para que los programas que crean los escenarios y el motor de renderizado en Blender tengan un formato común.

Cada archivo JSON define una foto en concreto y se divide en varias partes:
- **`scenario_id`** (Identificador de la foto), `domain` (Escenario) y `seed` (Semilla).
- **`environment`** (Entorno): Los datos del tiempo `weather` y la luz (si hay lluvia `rain_particles`, cuánta niebla hay `fog_density`, la fuerza del sol `sun_energy` y hacia dónde apunta `sun_rot_y` `sun_rot_z`).
- **`aircraft`** (Aeronave): Los datos de posición y movimiento del helicóptero (la distancia a la cámara `distance_m`, el desplazamiento horizontal `offset_x_m`, el ajuste de altura `altitude_offset_m`, el cabeceo o inclinación vertical `pitch_rad`, el alabeo o inclinación lateral `roll_rad` y la dirección o rumbo `heading_rad`).
- **`render`** (opcional): `samples` y `resolution`. Si falta, `generar.py` usa 64 muestras y 1920×1080.

Blender no decide los valores de la campaña: lee el JSON y renderiza la foto. Solo sortea, con la seed del JSON, la posición del helicóptero en la imagen, la posición de la avioneta, el ángulo de la cámara y el fotograma de la lluvia en campo; así que el mismo JSON da siempre la misma foto. Los 3 escenarios leen el mismo formato, cada uno con su .blend propio.

Los JSON no se escriben manualmente, ya que los crea un archivo de Python a partir de una rejilla (un plan de pruebas).


## Motivación (¿Por qué lo hemos decidido?)

1. **Encaja con el bucle con LLM**: el bucle con LLM (uso previsto, todavía no construido) analiza las métricas del detector y propone una rejilla nueva (por ejemplo, niebla entre 0,010 y 0,020 a 800 m, de frente). Un script la convierte en un JSON por imagen, sortea los valores dentro de los rangos con una semilla y los valida antes de renderizar. Así el LLM solo decide qué zona explorar, sin conocer el formato interno de Blender ni escribir cada foto, y Blender no cambia: sigue leyendo un JSON por foto. Si el LLM propone algo inválido (un tiempo que no existe, una distancia negativa), `validar` lo rechaza antes de gastar GPU.

2. **Trazabilidad (sabemos exactamente qué falló)**: si el detector YOLO falla una foto en concreto, tenemos un archivo individual con su configuración exacta antes de renderizar para así poder repetirla al momento y ver qué pasó. 

3. **Repartir y relanzar en el CESGA**: con un JSON por foto, `generar.py` puede procesar un trozo de la carpeta de los JSON y salta las fotos que ya existen; si una falla, se relanza solo lo que falta. 

4. **Mismo formato para los tres escenarios**: tanto las escenas de mar, campo y montaña utilizan las mismas instrucciones JSON, aunque por dentro cada una tenga su propio modelo en Blender.

5. **Nombres de datos fijos**: el creador de escenarios, el LLM y Blender usan exactamente los mismos nombres de variables. Al no tener que andar traduciendo datos de un programa a otro, evitamos fallos y errores tontos.


## Alternativas Descartadas (¿Qué otras opciones había?)

- **Que Blender lea directamente de la rejilla** (un plan de pruebas del tipo "HO y CR, con despejado, lluvia y niebla, a 100, 500 y 2000 m, con la niebla entre 0,005 y 0,055") y sortee los valores a medida que renderiza

    - Por qué se descartó:
        1. **Falta de trazabilidad anterior al render**: los valores exactos no existen como archivo hasta que la foto ya se ha renderizado, por lo que no hay un archivo de configuración claro que alegar si una imagen falla.
        2. **Dificultad para relanzar fallos**: si una sola imagen falla en el CESGA, obliga a repetir toda la combinación y el sorteo de números aleatorios en lugar de ir directamente al archivo afectado.
        3. **Mezcla de responsabilidades**: Blender tendría que combinar, sortear y validar además de renderizar, y un error de la rejilla (un rango mal puesto, un tiempo inexistente) se descubriría a mitad del render, no antes de empezar.

- **Un único JSON con todos los escenarios de la campaña**, que Blender recorre entero.

    - Por qué se descartó:
        1. **Reparto del trabajo en el CESGA**: para repartirlo por lotes habría que partir o indexar el archivo grande; con un JSON por imagen cada tarea recibe directamente su archivo.
        2. **Dificultad para relanzar fallos**: si una foto falla, habría que localizar su entrada dentro del archivo grande, en lugar de relanzar simplemente su archivo.

## Referencias y Evidencia de Implementación (¿Qué información ayuda a aplicarla?)

Ejemplo de JSON (`TMON001-HO-DES-R50`), con los nombres de campo fijos:

```json
{
    "scenario_id": "TMON001-HO-DES-R50",
    "domain": "montana",
    "seed": 1,
    "environment": {
        "weather": "despejado",
        "fog_density": 0.0,
        "rain_particles": 0,
        "sun_energy": 1.24,
        "sun_rot_y": 2.22,
        "sun_rot_z": 4.778
    },
    "aircraft": {
        "distance_m": 50.0,
        "offset_x_m": -0.137,
        "altitude_offset_m": 0.398,
        "pitch_rad": 0.128,
        "roll_rad": 0.028,
        "heading_rad": 3.189
    },
    "render": {"samples": 16, "resolution": [960, 540]}
}
```

| Bloque | Campo | Qué representa | Tipo | Unidad |
|---|---|---|---|---|
| (raíz) | `scenario_id` | Identificador único del escenario | texto | — |
| (raíz) | `domain` | Fondo o escena (`mar`, `montana`, `campo`) | texto | — |
| (raíz) | `seed` | Semilla, para poder repetir la misma foto | entero | — |
| `environment` | `weather` | Tiempo: `despejado`, `lluvia` o `niebla` | texto | — |
| `environment` | `fog_density` | Cuánta niebla hay (`0.0` es sin niebla) | decimal | 1/m |
| `environment` | `rain_particles` | Lluvia (partículas) (`0` es sin lluvia) | entero | nº de partículas |
| `environment` | `sun_energy` | Fuerza del sol | decimal | W/m² |
| `environment` | `sun_rot_y`, `sun_rot_z` | Hacia dónde apunta el sol | decimal | rad |
| `aircraft` | `distance_m` | Distancia del helicóptero a la cámara | decimal | m |
| `aircraft` | `offset_x_m` | Desplazamiento horizontal | decimal | m |
| `aircraft` | `altitude_offset_m` | Ajuste de altura | decimal | m |
| `aircraft` | `pitch_rad` | Inclinación vertical | decimal | rad |
| `aircraft` | `roll_rad` | Inclinación lateral | decimal | rad |
| `aircraft` | `heading_rad` | Dirección o rumbo | decimal | rad |
| `render` (opcional) | `samples` | Muestras de Cycles por foto (por defecto 64) | entero | — |
| `render` (opcional) | `resolution` | Ancho y alto de la imagen (por defecto 1920×1080) | lista de 2 enteros | píxeles |


### Patrón de `scenario_id` y validación (`escenarios.py`)

`TMON001-HO-DES-R50` = prefijo y número (`TMON001`), tipo de encuentro (`HO`: head-on, `CR`: crossing u `OT`: overtaking), tiempo (`DES`: despejado, `LLU`: lluvia o `NIE`: niebla) y `R` seguida de la distancia en metros (`R50`). El script rechaza los identificadores que no siguen el formato común establecido.

```python
PATRON_ID = re.compile(r"^[A-Z]+\d{3,}-(HO|CR|OT)-(?P<tiempo>DES|LLU|NIE)-R(?P<distancia>\d+)$")

def validar(esc):
    """Lista de problemas de un escenario (vacía si es correcto)."""
    errores = []
    for campo, tipo in (("scenario_id", str), ("domain", str), ("seed", int),
                        ("environment", dict), ("aircraft", dict)):
        if not isinstance(esc.get(campo), tipo) or isinstance(esc.get(campo), bool):
            errores.append(f"falta '{campo}' o no es {tipo.__name__}")
    if errores:
        return errores
    m = PATRON_ID.match(esc["scenario_id"])
    if not m:
        errores.append("scenario_id no sigue PREFIJO000-TRAY-TIEMPO-R<distancia>")
    if esc["domain"] not in DOMINIOS:
        errores.append(f"domain '{esc['domain']}' no es uno de {DOMINIOS}")
    for bloque, campos in (("environment", ENVIRONMENT), ("aircraft", AIRCRAFT)):
        for campo, tipo in campos.items():
            valor = esc[bloque].get(campo)
            if not isinstance(valor, tipo) or isinstance(valor, bool):
                errores.append(f"falta '{bloque}.{campo}' o no es del tipo correcto")
    if errores:
        return errores
    amb, aer = esc["environment"], esc["aircraft"]
    if amb["weather"] not in TIEMPOS.values():
        errores.append(f"weather debe ser uno de {list(TIEMPOS.values())}")
    for campo in ("fog_density", "rain_particles", "sun_energy"):
        if amb[campo] < 0:
            errores.append(f"environment.{campo} no puede ser negativo")
    if aer["distance_m"] <= 0:
        errores.append("aircraft.distance_m tiene que ser positivo")
    # el scenario_id tiene que decir lo mismo que el contenido del escenario
    if m:
        if TIEMPOS.get(m["tiempo"]) != amb["weather"]:
            errores.append(f"scenario_id dice {m['tiempo']} pero weather es '{amb['weather']}'")
        if int(m["distancia"]) != round(aer["distance_m"]):
            errores.append(f"scenario_id dice R{m['distancia']} pero distance_m es {aer['distance_m']}")
    return errores
```

**Aclaración**: Las constantes `DOMINIOS`, `TIEMPOS`, `ENVIRONMENT` y `AIRCRAFT` se definen al principio de `escenarios.py`.

### Ejemplo de rejilla que genera los JSON
 
```json
{
  "prefix": "TMON", "domain": "montana",
  "trajectory": ["HO", "CR"], "weather": ["DES", "LLU", "NIE"],
  "distance_m": [200], "images_per_combination": 1, "seed": 1,
  "render": {"samples": 16, "resolution": [960, 540]},
  "ranges": {"fog_density": [0.005, 0.02], "sun_rot_y": [0.5, 1.2]}
}
```

#### Evidencia
 
Con esa rejilla salen **6 escenarios** (`TMON001-HO-DES-R200` … `TMON006-CR-NIE-R200`) y, tras
renderizar, obtenemos **6 fotos**, cada una con su JSON de entrada y su etiqueta de salida. Se puede localizar
y repetir cualquier foto por su `scenario_id`.

**Etiqueta de salida de una foto de otro escenario** (`TCAM006-CR-NIE-R100`, `campo`): `generar.py` copia el escenario de entrada y le añade los datos de la imagen y de la caja del helicóptero.

```json
{
    "file_name": "TCAM006-CR-NIE-R100.png",
    "image_id": 5,
    "width": 960,
    "height": 540,
    "category_id": 1,
    "bbox": [391.59, 241.48, 69.84, 21.25],
    "area": 1484.1,
    "visible": true,
    "scenario_id": "TCAM006-CR-NIE-R100",
    "domain": "campo",
    "seed": 6,
    "environment": { "weather": "niebla", "fog_density": 0.0169, "rain_particles": 0,
                     "sun_energy": 2.644, "sun_rot_y": 0.8395, "sun_rot_z": 1.6438 },
    "aircraft": { "distance_m": 100, "offset_x_m": -9.99, "altitude_offset_m": 0.98,
                  "pitch_rad": -0.0101, "roll_rad": 0.1351, "heading_rad": 1.5327 }
}
```

`bbox` es `[x, y, ancho, alto]` en píxeles, `area` es ancho por alto, `visible` indica si el helicóptero queda dentro de la imagen e `image_id` sale del número del escenario.

### Repartir y relanzar en el CESGA

`generar.py` acepta, después de la carpeta de escenarios, un `inicio` y un `fin` para procesar solo un trozo (por orden alfabético), y salta las fotos cuyo `.png` ya existe:

```bash
# solo los escenarios 0 a 5 de la carpeta
blender -b escenas/montana.blend -noaudio -P generar.py -- escenarios/MON/ 0 6
```

```python
# generar.py: trozo de la carpeta y fotos ya renderizadas
inicio = int(args[1]) if len(args) > 1 else 0 
fin = int(args[2]) if len(args) > 2 else None
# inicio y fin leen el 0 y el 6
...
fin = len(lista) if fin is None else min(fin, len(lista)) # si no hay fin se usan todos los escenarios de la carpeta
for image_id, esc in enumerate(lista): # renderizamos el trozo solicitado
    if not inicio <= image_id < fin:
        continue
    ...
    if os.path.exists(ruta_png) and not solo_etiquetas: # comprueba si existe la imagen
        print(f"  {nombre} ya existe, lo salto")
        continue
```

Si una tarea falla, se vuelve a lanzar el mismo comando y solo se renderizan las fotos que faltan.

### Documentación
 
- API de Python de Blender (`bpy`): https://docs.blender.org/api/current/
- Slurm, el gestor de trabajos del CESGA con el que se lanzan los renders: https://slurm.schedmd.com/job_array.html



