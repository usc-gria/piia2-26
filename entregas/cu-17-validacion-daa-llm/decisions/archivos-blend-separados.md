# ADR 2: usar un `.blend` por escena (mar, montaña, campo) controlado por un único script `generar.py` para crear las imágenes

## Decisión (¿Qué hemos decidido?)

Para el motor de simulación se usan tres archivos `.blend`, uno por cada escenario, y un solo script,
`generar.py`, que sirve para los tres.

| Escena | Archivo | Aeronave | 
|---|---|---|
| Mar | `mar.blend` | Helicóptero ALH Dhruv | 
| Montaña | `montana.blend` | Helicóptero ALH Dhruv | 
| Campo | `campo.blend` | Avioneta Cessna 172 | 

Antes, cada escena tenía un archivo por tiempo (`campo_despejado.blend`, `campo_lluvia.blend`, `campo_niebla.blend`), pero ahora cada escena tiene un único `.blend` y hay un único script de python `generar.py` que funciona para los tres archivos y se encarga, antes de cada foto, de controlar la niebla o la lluvia, así como de ajustar el sol y colocar la aeronave según lo diga el escenario indicado en el JSON de entrada. Por ejemplo, en una imagen con niebla enciende el cubo que funciona como niebla y sube su intensidad, en cambio, en una de despejado lo mantiene oculto.

Cada foto se describe con un JSON igual para las tres escenas (el formato y sus campos se explican en el ADR
`json-por-imagen.md`). En el JSON se indica qué escena es (`domain`), la semilla (`seed`), el tiempo (`environment`) y dónde está la aeronave (`aircraft`). Si `domain` es `"campo"`, se abre `campo.blend`, y se generan las fotos con ese escenario, y así igual con los otros dos.

Para conseguir que ese `generar.py` funcione con los tres `.blend`, este tiene una parte de código común y una que es propia de cada escena. Lo que se hace igual en las tres escenas está escrito una sola vez, como es leer y validar los escenarios, preparar el render y la GPU, calcular la caja de la aeronave en la imagen y guardar la etiqueta. Lo que cambia de una escena a otra va en dos funciones por escena:
-  `preparar_<escena>()` se ejecuta **una vez, al abrir la escena**, busca sus objetos (aeronave, cámara, niebla, lluvia, sol) y la deja lista.
-  `aplicar_<escena>()` se ejecuta **antes de cada foto**, pone la niebla, la lluvia y el sol de ese escenario y coloca la aeronave y la cámara.

Como cada escena es independiente, la niebla y la lluvia no son exactamente equivalentes entre escenarios, así que los resultados de YOLO-X se analizan por escenario. Las métricas se agrupan por escena y tiempo y el criterio de robustez trabaja sobre esos grupos. 


## Motivación (¿Por qué lo hemos decidido?)

1.  **Partíamos de tres escenas hechas por separado:** Cada integrante construyó una escena en el proyecto anterior, con su propia forma de hacer la niebla, la lluvia y de colocar la aeronave en función del tipo de escenario. Además, cada escena estaba partida en varios `.blend`, uno por tiempo (por ejemplo, para campo había `campo_despejado`, `campo_lluvia`y `campo_niebla` y también había un `generar.py`para cada uno). Juntar todo en un único archivo habría obligado a rehacer escenas que ya funcionaban.

2. **En este proyecto el LLM necesita un único formato de entrada:** El ADR `json-por-imagen.md` fija un escenario JSON igual para las tres escenas. Esta decisión hace que un único `generar.py` lo aplique a cualquiera de ellas, así el bucle con LLM no tiene que saber cómo está construida cada escena por dentro, solo tiene que mirar el atributo `domain` y los valores de ambiente y aeronave, y el script se encarga del resto.

3. **El tiempo como parámetro, no como archivo:** Con un `.blend` por tiempo, explorar densidades de niebla intermedias o combinar valores obligaba a tener más archivos. Con un `.blend` por escena, `fog_density` y `rain_particles` son números continuos que el bucle puede variar libremente.

4. **Cada una trabaja en su escena sin romper las de las demás:** Un cambio en uno de los tres escenarios no afecta a los otros dos, y en `generar.py` cada escena está en su propia sección.

5. **Los archivos son grandes:** Un único archivo con las tres escenas pesaría más de 400 MB, cargaría las tres en memoria para renderizar una sola y sería mucho más difícil de subir y bajar de CESGA, así como de realizar cambios desde blender. Además, al tener los archivos independientes, añadir una escena nueva no obliga a tocar las existentes.

## Alternativas consideradas (¿Qué otras opciones había?)

- **Mantener un `.blend` y un script por escena y tiempo** como en el proyecto anterior.

    - Por qué se descartó:
        1. **Demasiados archivos**: había nueve `.blend`, y casi tantos scripts con código repetido.
        2. **Arreglos repetidos**: cada corrección había que hacerla en todos los scripts.

- **Un único `.blend` con las tres escenas**, cada una en una colección, activando solo la que toca.

    - Por qué se descartó:
        1. **Escenas incompatibles**: obligaba a fusionar escenas con nombres de objetos, cámaras y escalas distintas.
        2. **Un archivo enorme**: más de 400 MB, con conflictos cada vez que dos personas tocan la escena.

- **Escena generada entera con código** (terreno, mar, cielo, niebla y lluvia creados por Python)

    - Por qué se descartó:
        1. **Rehacer todo el trabajo**: aunque da el máximo control y reproducibilidad, suponía rehacer desde cero el modelado de las tres escenas.
        2. **Menos realismo**: las escenas hechas a mano tienen un realismo (oleaje, terreno, materiales) difícil de igualar por código en el tiempo del proyecto.

- **Un script por escena** (`generar_mar.py`, `generar_montana.py`, `generar_campo.py`)

    - Por qué se descartó:
        1. **Código repetido**: es más sencillo de escribir, pero repite tres veces la lectura de escenarios, el render, la caja y las etiquetas.
        2. **Cambios en tres sitios**: un cambio de formato (como el de las etiquetas) habría que hacerlo tres veces y podría quedar distinto en cada script.


## Referencias y Evidencia de Implementación (¿Qué información ayuda a aplicarla?)

**Código del proyecto**:
- `generar.py`: parte común  y una sección por escena. El diccionario `DOMINIOS` relaciona cada escena con sus dos funciones.
- `escenarios.py`: formato común del escenario y de la etiqueta, y su validación.


### Fragmentos de `generar.py`

**1. Cómo se elige la escena:** El diccionario `DOMINIOS` relaciona cada escena con sus dos funciones, y `main` usa las de la escena de los escenarios:

```python
DOMINIOS = {
    "mar": (preparar_mar, aplicar_mar),
    "montana": (preparar_montana, aplicar_montana),
    "campo": (preparar_campo, aplicar_campo),
}

def main():
    ...
    preparar, aplicar = DOMINIOS[dominio]
    ...
    ctx = preparar()
    for image_id, esc in enumerate(lista):
        ...
        rng = random.Random(esc["seed"])   # misma semilla -> misma foto
        configurar_render(scene, esc)
        aplicar(ctx, esc, rng)
        bpy.context.view_layer.update()
        caja, visible = caja_coco(scene, ctx["camara"], ctx["aeronave"])
```

**2. Una carpeta, una escena** (en `leer_escenarios()` en la parte común):

```python
dominios = {e["domain"] for e in lista}
if len(dominios) > 1:
    raise SystemExit(f"ERROR: mezcla de dominios {sorted(dominios)}; usa una carpeta por dominio.")
```

**3. La niebla en cada escena.** La niebla se aplica en función del escenario adaptándose a ese archivo:

```python
# Mar: la densidad del JSON se usa tal cual
ctx["niebla"].hide_render = amb["fog_density"] == 0
for n in ctx["niebla"].active_material.node_tree.nodes:
    if n.type == "VOLUME_SCATTER":
        n.inputs["Density"].default_value = amb["fog_density"]

# Montaña: se multiplica por 15 porque el diorama no está a escala
MON_FACTOR_NIEBLA = 15.0
densidad = amb["fog_density"] * MON_FACTOR_NIEBLA

# Campo: si la densidad es 0, se oculta
if densidad <= 0:
    obj.hide_render = True
    return
...
vol = next((n for n in mat.node_tree.nodes if n.type == "VOLUME_SCATTER"), None)
vol.inputs["Density"].default_value = densidad
```

### Documentación de Blender:

- API de Python de Blender (`bpy`): https://docs.blender.org/api/current/
- Sistemas de partículas (lluvia): <https://docs.blender.org/manual/en/latest/physics/particles/index.html>
- Volúmenes y *Volume Scatter* (niebla): <https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_scatter.html>
