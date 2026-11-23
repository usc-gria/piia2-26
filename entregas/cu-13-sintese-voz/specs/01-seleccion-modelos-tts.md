# Selección de modelos de síntesis de voz

## Qué construir

Un proceso para comparar modelos de síntesis de voz y elegir el que se usará en cada idioma, español y gallego, a partir de la valoración de varias personas mediante el método Arena. Es la primera funcionalidad del sistema: el modelo elegido es el que generará el audio del dataset (spec 05) y el punto de partida para adaptar y clonar voces (spec 04).

**Entradas**

- La lista de modelos candidatos proporcionada por Balidea.
- Un conjunto de frases de prueba de temática médica en español y en gallego.
- Un grupo de personas evaluadoras.

**Salidas**

- Los audios de prueba generados por cada modelo.
- Los votos y las abstenciones de cada evaluación.
- Una clasificación de los modelos por idioma y perfil de voz, y el modelo o modelos elegidos para cada idioma y perfil.

**Funcionamiento**

1. Se parte de la lista de modelos candidatos de Balidea.
2. Cada modelo sintetiza las mismas frases de prueba.
3. Cada persona evaluadora escucha parejas de audios con la misma frase generada por dos modelos distintos y vota el que suena mejor. También puede abstenerse si los dos suenan bien o si los dos suenan mal.
4. Se cuentan los votos por separado para cada idioma y perfil, y se elige el modelo más votado. El equipo puede combinar varios modelos en un perfil para ganar variabilidad, y lo justifica en un ADR.
5. Se guardan los audios, los votos, las abstenciones y la clasificación.

## Por qué

La calidad del dataset depende directamente de la calidad de la voz sintética: si el audio suena artificial o pronuncia mal, el reconocedor entrenado con él aprenderá de ejemplos poco realistas. Los resultados publicados de los modelos no siempre reflejan cómo suenan con vocabulario médico ni en gallego. Por eso queremos compararlos nosotros mismos, con frases de nuestro dominio y con el criterio de personas que los escuchan, y elegir el que mejor suena en cada idioma.

## Restricciones

- Solo se evalúan los modelos de la lista proporcionada por Balidea. Se da por supuesto que sus licencias están aprobadas para el uso que hará la empresa.
- Todos los modelos sintetizan exactamente las mismas frases.
- Las abstenciones se registran indicando su motivo (ambos suenan bien o ambos suenan mal), pero no suman votos a ningún modelo.
- Puede elegirse un modelo distinto en cada idioma y en cada perfil de voz, y un perfil puede repartirse entre varios modelos.
- Si un modelo solo admite uno de los dos idiomas, compite solo en ese idioma.
- Si un modelo dice admitir un idioma pero en la escucha no lo habla de verdad (por ejemplo, un gallego que suena a portugués), se descarta para ese idioma.
- No depende de otras funcionalidades: las frases de prueba se preparan a mano, sin esperar al corpus de la spec 02.

## Criterios de aceptación

- Se han usado al menos 5 frases de prueba por idioma.
- Todos los modelos de un mismo idioma tienen un audio para cada una de esas frases.
- Han votado al menos tres personas.
- Cada abstención registrada indica su motivo: «ambos suenan bien» o «ambos suenan mal».
- Existe una clasificación con el número de votos y de abstenciones de cada modelo para cada idioma en el que compiten al menos dos modelos válidos.
- Cada idioma y perfil tiene al menos un modelo elegido. Si no es el más votado, o si no hubo votación porque solo quedaba un modelo válido, el motivo queda registrado en un ADR.

## Resultado (2026-11-18)

El Arena se dio por terminado el 2026-11-18. La elección por idioma y perfil está en [ADR-005](../decisions/005-modelos-por-perfil.md) y en `codigo/corpus/config.yaml` (sección `modelos`):

- **Castellano:** OmniVoice ganó en los cuatro perfiles: 89,2 % de victorias en total en la clasificación del 2026-11-17. Se usa en las voces infantil, joven y adulta. La voz adulta se reparte además con NOS, por su acento gallego, y con supertonic 3. La persona mayor se hace con clonación de voz con Chatterbox Multilingual V3, porque en la escucha del equipo ningún modelo genera bien esa voz a partir de una descripción.
- **Gallego:** no se votó. En la escucha del equipo, solo OmniVoice y NOS hablan gallego de verdad; los demás modelos que dicen admitirlo suenan a portugués. Se usan los dos.
