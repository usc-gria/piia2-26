# Arena TTS

Votación a ciegas por parejas para elegir el mejor modelo de síntesis por idioma y perfil de voz (spec 01).

Solo necesita Python 3.9 o superior y, para igualar la frecuencia de muestreo, numpy (viene con Anaconda).

## Inicio rápido (Windows)

1. Los audios se leen de la carpeta `audios` del proyecto, la que está al lado de `arena`. Para usar otra, edita `AUDIOS` en `iniciar_votacion.bat`.
2. Rellena la columna `perfil` de `perfiles.csv` para las voces cuya carpeta no se llama como un perfil (ver más abajo).
3. Haz doble clic en `iniciar_votacion.bat`. La ventana negra muestra cuántas parejas hay en cada idioma y perfil, y después se abre el navegador para votar.
4. Cuando hayan votado todos, haz doble clic en `calcular_clasificacion.bat`.

Para cambiar la proporción o la carpeta de audios, abre `iniciar_votacion.bat` con el Bloc de notas y edita las líneas de configuración del principio.

Para sumar los votos de otra persona, copia sus ficheros `votos_*.csv` (y sus `.json`) dentro de `resultados/` y vuelve a ejecutar `calcular_clasificacion.bat`. No copies dos veces el mismo fichero con nombres distintos, porque se contaría dos veces.

## Contenido de la carpeta

| Fichero o carpeta | Para qué sirve |
| --- | --- |
| `iniciar_votacion.bat` | Lanza la votación con doble clic. |
| `calcular_clasificacion.bat` | Calcula la clasificación con doble clic. |
| `votar.py` | Abre la votación en el navegador. |
| `normalizar.py` | Iguala volumen y frecuencia de muestreo al reproducir. |
| `arena.py` | Núcleo: lee los audios, genera y muestrea las parejas, guarda los votos. |
| `clasificacion.py` | Suma los votos de varias personas y calcula los rankings. |
| `frases_prueba.csv` | Texto de las frases, para mostrarlo mientras se vota. |
| `perfiles.csv` | Qué perfil representa cada voz de NOS y supertonic. |
| `audios/` | Carpeta alternativa para los audios (por defecto se usa la del proyecto). |
| `resultados/` | Aquí se guardan los votos de cada sesión. |
| `clasificacion/` | Aquí se guardan los rankings (se crea al calcularlos). |

## Estructura de los audios

```
audios/
  CASTELLANO/
    m1/
      VOZ INFANTIL/   p01_es.wav ... p10_es.wav
      VOZ JOVEN/
      VOZ ADULTA/
      VOZ PERSONA MAYOR/
    m2/ ...
  GALLEGO/
    m1/ ...
```

- La misma frase debe tener **el mismo nombre de fichero** en todos los modelos de un idioma. Así se emparejan.
- Si a un modelo le falta un perfil, no compite en ese perfil.
- Los nombres de las carpetas de idioma, modelo y perfil son libres: se leen tal cual.
- Se ignoran los ficheros que no son `.wav` (por ejemplo, `resultados.csv`).

### Voces que no se llaman como un perfil: `perfiles.csv`

Algunos modelos guardan sus voces en carpetas como `mujer` o `F3`. En `perfiles.csv` se indica en qué perfil compite cada una:

```
idioma,modelo,carpeta,perfil
CASTELLANO,NOS,mujer,VOZ ADULTA
CASTELLANO,NOS,hombre,
CASTELLANO,supertonic3,F3,VOZ JOVEN
```

- Con `perfil` relleno, esa voz compite en ese perfil. Hay que escribirlo exactamente igual que las carpetas de los demás modelos (`VOZ INFANTIL`, `VOZ JOVEN`, `VOZ ADULTA`, `VOZ PERSONA MAYOR`).
- Con `perfil` vacío, esa voz no participa.
- Cada modelo solo puede tener una voz por perfil. Si se ponen dos, el programa avisa y no arranca.
- Las carpetas que no aparecen en el fichero usan su propio nombre como perfil.
- El reparto usado queda guardado en el `.json` de cada sesión.

### Igualado de volumen y frecuencia

Al reproducir, cada audio se pasa a mono y a 24 000 Hz, y se ajusta a un nivel común de −23 dBFS en la parte con voz, sin que el pico pase de −1 dBFS. Así ningún modelo gana por sonar más fuerte ni se delata por tener más agudos. Los ficheros originales no se modifican. Lo hace `normalizar.py`, que necesita numpy (viene con Anaconda); sin numpy solo se iguala el volumen. Con `--sin-igualar` se reproducen tal cual. Los parámetros quedan guardados en el `.json` de cada sesión.

Si se cambia `perfiles.csv` a mitad de la votación, los votos anteriores y los nuevos no son comparables. Conviene fijarlo antes de que vote nadie.

## 1. Votar

```
python votar.py --audios ../audios --proporcion 0.5 --frases frases_prueba.csv --perfiles perfiles.csv
```

| Parámetro | Por defecto | Qué hace |
| --- | --- | --- |
| `--audios` | (obligatorio) | Carpeta raíz de los audios. |
| `--proporcion` | 0.3 | Parte de las parejas posibles de cada idioma y perfil que vota cada persona, entre 0 y 1. |
| `--salida` | `resultados` | Carpeta donde se guardan los votos. |
| `--frases` | ninguno | CSV con columnas `id,frase` para mostrar el texto de la frase. |
| `--semilla` | aleatoria | Fija la muestra de parejas. Sin ella cada persona recibe una muestra distinta. La semilla usada siempre queda guardada. |
| `--puerto` | 8000 | Puerto local. |

Se abre el navegador en `http://127.0.0.1:8000`. Cada persona escribe su nombre y vota:

- **Gana A / Gana B**, o se abstiene con **Ambos suenan bien / Ambos suenan mal**.
- Hay que escuchar los dos audios enteros antes de votar.
- No se muestra qué modelo es cada audio, y el lado izquierdo o derecho es aleatorio.
- Se puede deshacer el último voto.
- Atajos de teclado: `A`, `B`, `S` (ambos bien), `M` (ambos mal) y `Z` (deshacer).
- Para que vote otra persona, se recarga la página. Para cerrar, `Ctrl+C` en la terminal.

Cada sesión crea dos ficheros en la carpeta de salida:

- `votos_<nombre>_<fecha>.csv` tiene una fila por cada pareja posible, con las columnas `idioma, perfil, frase, modelo_a, modelo_b, resultado`. El `resultado` es `0` si no se votó, o bien el modelo ganador, `AMBOS_BIEN` o `AMBOS_MAL`. Se guarda después de cada voto.
- `votos_<nombre>_<fecha>.json` recoge la configuración: semilla, proporción, carpeta de audios, número de parejas y versión de Python.

## 2. Calcular la clasificación

Se le pasan los CSV de todas las personas, o carpetas que los contengan. Los votos se suman.

```
python clasificacion.py resultados resultados_de_otra_persona --min-votos 35
```

Reglas:

- Una **pareja** es un par de modelos dentro de un mismo idioma y perfil, sumando todas las frases y personas.
- Una pareja solo cuenta para el ranking si tiene al menos `--min-votos` participaciones (por defecto 35). Las participaciones incluyen las abstenciones.
- **Porcentaje de victorias** = victorias / (victorias + derrotas). Las abstenciones se registran, pero no cuentan en el porcentaje.
- Se calcula un ranking **por perfil** y otro **general** por idioma, que suma las parejas válidas de todos los perfiles.
- Si dos modelos empatan en el primer puesto, se marca como `empate`.

Genera la carpeta `clasificacion/` con estos ficheros:

| Fichero | Contenido |
| --- | --- |
| `suma_votos_parejas.csv` | Suma global por pareja de modelos y si es válida. |
| `ranking_por_perfil.csv` | Clasificación por idioma y perfil. |
| `ranking_general.csv` | Clasificación por idioma. |
| `resumen.json` | Ficheros usados, parámetros y ganadores. |

Los rankings incluyen el intervalo de confianza del 95 % (Wilson) del porcentaje. Si los intervalos de dos modelos se solapan mucho, la diferencia entre ellos no es fiable.

## ¿Cuántas personas hacen falta?

Cada pareja de modelos de un perfil tiene tantas comparaciones posibles como frases. Con 10 frases y una proporción `p`, cada persona vota unas `10 × p` comparaciones de esa pareja. Para llegar a 35 participaciones hacen falta unas `35 / (10 × p)` personas:

| Proporción | Personas necesarias |
| --- | --- |
| 1.0 | 4 |
| 0.7 | 5 |
| 0.5 | 7 |
| 0.3 | 12 |
