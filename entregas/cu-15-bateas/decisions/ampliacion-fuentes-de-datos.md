# Ampliación de las fuentes de datos

Estado: aceptada. Cambia el alcance que pusimos en la entrega 1. Relacionada con el
[README](../README.md), con la [spec de predicción](../specs/prediccion-supervivencia.md), con la
[spec del informe](../specs/informe-dependencia-datos.md) y con C1 y C4 de la
[arquitectura](../ARCHITECTURE.md).

## Decisión

Añadimos fuentes de datos que en la entrega 1 habíamos dejado fuera, pero solo las que pasan una regla
que fijamos antes de ver los resultados. Una fuente entra si, en la validación año a año (las 24
pruebas del [ADR de evaluación](evaluacion-ria-no-vista.md)), el intervalo de confianza del 95 % de lo
que cambia el AUC queda entero por encima de 0 en el cierre o en la reapertura, y en ninguno de los
dos queda entero por debajo. Para el calendario de muestreo miramos el AUC a 1 día, que es lo que
quiere mejorar; para el resto, a 7 días. Cada fuente se prueba sobre el modelo que teníamos elegido en
ese momento, en el orden en que la conseguimos.

Así quedó (cambio medio del AUC en las 24 pruebas; entre paréntesis, el intervalo de las que entran):

| Fuente | De dónde sale | Cierre | Reapertura | ¿Entra? |
|---|---|---|---|---|
| Polígonos vecinos | Excel de INTECMAR | −0,001 | +0,026 (+0,009 a +0,046) | Sí |
| Otras rías | Excel de INTECMAR | +0,004 | +0,012 | Sí, por los pelos (ver abajo) |
| Calendario de muestreo (a 1 día) | Fechas de las analíticas | +0,026 (+0,021 a +0,030) | +0,072 (+0,057 a +0,083) | Sí |
| Viento y temperatura por polígono | Meteo horaria de los 44 polígonos | +0,018 (+0,009 a +0,028) | +0,029 (+0,013 a +0,051) | Sí |
| Índice de afloramiento | Viento ERA5 en mar abierto (Open-Meteo) | +0,006 (+0,001 a +0,011) | +0,002 | Sí |
| Fitoplancton y nitrato | Modelo IBI de Copernicus | −0,002 | +0,013 (+0,001 a +0,030) | Sí |
| Exposición del polígono | Excel de INTECMAR | +0,003 | −0,007 | No |
| Lluvia, humedad y radiación | ERA5 (Open-Meteo) | +0,003 | +0,001 | No |
| Caudal de los ríos | GloFAS (Open-Meteo) | −0,002 | −0,008 | No |
| Clorofila por satélite | ESA Ocean Colour (NOAA) | −0,003 | −0,004 | No |
| Temperatura del mar por satélite | NOAA OISST | −0,001 | 0,000 | No |
| Temperatura, salinidad y estratificación | Modelo IBI de Copernicus | −0,001 | 0,000 | No |
| Clorofila de 1 km | Copernicus | +0,001 | +0,005 | No |
| Retardo de las otras rías | Excel de INTECMAR | −0,002 | +0,005 | No, por los pelos |
| Cómo va la temporada | Excel de INTECMAR | +0,007 | +0,005 | No, empeora el Brier |

Las cuatro fuentes de la entrega 1 (toxinas propias, contexto de la ría, historial y estacionalidad)
siguen como estaban.

## Por qué

El plan de la entrega 1 no funcionaba con tres rías. En la spec 2 teníamos un grupo de "meteorología y
agua" con las estaciones de MeteoGalicia que venían con los datos de Arousa. Cuando llegaron los Excel
de Vigo y Pontevedra vimos que solo traían toxinas, y esas estaciones solo cubren Arousa. Si nos
quedábamos con el alcance original, el modelo de las tres rías no tenía ningún dato del ambiente.

El prototipo ya nos decía qué faltaba: ordenaba bien, pero las probabilidades fallaban en los años
raros, porque nada le decía si el año venía fuerte o tranquilo. El viento, el afloramiento y el
fitoplancton los habíamos dejado fuera porque pensábamos que conseguirlos nos iba a llevar mucho
tiempo. Al final eran públicos, gratis y se bajan con una API, y además conseguimos la meteo horaria
de los 44 polígonos. Los vecinos, las otras rías y el calendario ni siquiera son datos nuevos: salen
de los mismos Excel de INTECMAR, mirados de otra forma.

La regla la pusimos porque probamos muchas fuentes, y si aceptas cualquiera que suba la media alguna
acaba entrando por casualidad. Ya nos había pasado con la exposición del polígono.

Comparado con el modelo de la entrega 1 (el "modelo base", sin la meteo de Arousa):

| AUC a 7 días | Base | Definitivo |
|---|---|---|
| Cierre, año a año | 0,849 | 0,873 (+0,024, mejora en 21 de 24 pruebas) |
| Reapertura, año a año | 0,710 | 0,793 (+0,083, mejora en 23 de 24 pruebas) |
| Cierre, prueba estricta | 0,864 | 0,879 |
| Reapertura, prueba estricta | 0,734 | 0,818 |

## Alternativas que descartamos

- **Quedarnos con el alcance de la entrega 1.** Es el modelo base: 0,849 y 0,710 frente a 0,873 y
  0,793. Y la meteo de MeteoGalicia no existe fuera de Arousa.
- **Usar las estaciones de MeteoGalicia solo en Arousa.** El modelo tiene que ser el mismo para todas
  las rías, y una fuente que solo tiene una ría no se puede evaluar dejándola fuera.
- **Meterlo todo.** Con tantas fuentes y tan pocos episodios por año el modelo se sobreajusta. Por
  ejemplo, meter todo Copernicus junto bajaba el cierre −0,005.
- **Fijarnos solo en la media, sin intervalo.** Varias fuentes suben unas milésimas por azar.
- **Decidir con un único periodo de validación.** Lo probamos con 2019-2021 y no se mantenía en
  2022-2025.
- **Los conteos de fitoplancton tóxico de INTECMAR.** Seguramente sería lo que más ayudaría, pero no
  son públicos (solo publican la semana actual). Tenemos un borrador para pedírselos.
- **El histórico oficial de aperturas y cierres.** INTECMAR solo publica los últimos 6 meses.

## Consecuencias

Cambia el alcance: en el README, las nuevas fuentes de datos dejan de estar "fuera del alcance", la
tabla de variables de la spec 2 incluye los grupos nuevos y la restricción de la spec 3 de "no ampliar
el alcance" pasa a remitir a esta regla. Aparece un componente nuevo, la descarga de datos externos
(C1). Para Copernicus hace falta una cuenta gratuita (`copernicusmarine login`); para lo demás, nada.

Hay cuatro decisiones que quedaron en el límite. Cuando cambiamos los datos de Arousa por el Excel
original de INTECMAR (igual que los de las otras dos rías), el panel perdió unos 4.800 días vacíos y
algunos cambios de AUC se movieron unas milésimas. Con eso "otras rías" ya no pasaría la regla, y ERA5,
el retardo de las otras rías y "cómo va la temporada" la pasarían por muy poco. Decidimos no tocar el
modelo: si quitar días sin datos cambia el veredicto, esas diferencias no son reales. Además, "otras
rías" sigue ayudando en la reapertura (si se quita del modelo definitivo, el AUC baja 0,020).

También hay que reconocer que elegimos las fuentes con la misma validación que usamos para medir el
resultado. La prueba limpia serán los datos de 2026.

Para una ría nueva, aparte de sus toxinas con la `Zona`, conviene tener viento. Con el índice de
afloramiento basta, y sirve el mismo para todas las Rías Baixas.

## Referencias

El código está en `bateas/datos_externos.py` (descargas) y en `bateas/multiria.py`
(`anadir_vecinos`, `tabla_otras_rias`, `anadir_meteo_poligono`, `anadir_datos_externos`,
`intervalo_mejora` y `MODELO_MEJORADO`). El calendario está en `bateas/supervivencia.py`
(`expandir` con `calendario=True`).

El índice de afloramiento (Bakun) a partir del viento horario frente a cabo Silleiro (42° N 10° O):

```python
rho_aire, cd, rho_agua = 1.22, 1.3e-3, 1025.0
v = -w * np.cos(np.deg2rad(direccion))           # componente norte del viento (m/s)
f = 2 * 7.2921e-5 * np.sin(np.deg2rad(lat))       # parámetro de Coriolis
tau_y = rho_aire * cd * w * v                    # tensión del viento
ia = -(tau_y / (rho_agua * f)) * 1000            # m³/s por km de costa; > 0 = afloramiento
```

La descarga de Copernicus, solo los primeros 12 m, que es lo que cuelgan las cuerdas:

```python
import copernicusmarine as cm
cm.subset(dataset_id='cmems_mod_ibi_bgc-plankton_my_0.027deg_P1D-m', variables=['chl', 'phyc'],
          minimum_latitude=42.05, maximum_latitude=42.80, minimum_longitude=-9.15, maximum_longitude=-8.55,
          minimum_depth=0, maximum_depth=12, start_datetime='2014-11-01', end_datetime='2025-12-31',
          output_filename='ibi_bgc_plancton.nc')
```

Cómo queda el modelo definitivo en el código:

```python
MODELO_MEJORADO = dict(fuentes=['toxinas', 'contexto_ria', 'historial', 'estacionalidad',
                                'vecinos', 'otras_rias', 'meteo_poligono', 'afloramiento', 'bgc_ibi'],
                       calendario=True, monotono=False)
```

Fuentes y documentación:

- Open-Meteo, API histórica (ERA5): <https://open-meteo.com/en/docs/historical-weather-api>
- Open-Meteo, API de caudales (GloFAS): <https://open-meteo.com/en/docs/flood-api>
- Catálogo de Copernicus Marine (modelo IBI): <https://data.marine.copernicus.eu/products>
- Librería `copernicusmarine`: <https://pypi.org/project/copernicusmarine/>
- NOAA ERDDAP (clorofila y temperatura del mar): <https://coastwatch.pfeg.noaa.gov/erddap/>
- Bakun (1973), *Coastal upwelling indices, west coast of North America, 1946-71*, NOAA Technical
  Report NMFS SSRF-671. De ahí sale la fórmula del índice.

Los números de este ADR salen de `resultados/validacion_anios.csv` y de las secciones 4.3 y 4.4 del
notebook final. Lo que se pierde al quitar cada fuente está en `docs/informe_dependencia_datos.md`.
