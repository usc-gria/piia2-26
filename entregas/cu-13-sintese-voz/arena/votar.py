"""
Arena TTS: votación a ciegas por parejas, en el navegador.

Solo usa la biblioteca estándar de Python (>= 3.9): no hay que instalar nada.

Uso:
    python votar.py --audios RUTA_AUDIOS --proporcion 0.3
    python votar.py --audios audios --proporcion 0.3 --frases frases_prueba.csv --salida resultados

Se abre el navegador en http://127.0.0.1:8000. Cada persona escribe su nombre,
escucha parejas de audios (misma frase, idioma y perfil, de dos modelos
distintos) y vota cuál suena mejor, o se abstiene ("ambos suenan bien" /
"ambos suenan mal"). Hay que escuchar los dos audios enteros antes de votar.

Prueba a ciegas: el navegador nunca recibe el nombre del modelo ni la ruta del
fichero; cada audio se sirve con un identificador aleatorio de un solo uso
y el lado izquierda/derecha se decide al azar.

Los votos se guardan después de cada clic en RESULTADOS/votos_<nombre>_<fecha>.csv
(una fila por cada pareja posible; "0" = no votada), junto a un .json con la
configuración de la sesión (semilla, proporción, versiones...).
Para que vote otra persona, basta con recargar la página.
Para cerrar el programa, Ctrl+C en la terminal.
"""
from __future__ import annotations

import argparse
import json
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import normalizar
from arena import AMBOS_BIEN, AMBOS_MAL, SesionVotacion, leer_correspondencias, leer_frases

# ---------------------------------------------------------------------------
# Página web (HTML + CSS + JavaScript en un único fichero)
# ---------------------------------------------------------------------------
PAGINA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arena TTS</title>
<style>
  :root { --fondo:#f6f5f2; --tarjeta:#fff; --texto:#1d1d1f; --suave:#6b6b70; --borde:#e2e0da;
          --acento:#2f5d50; --acento-texto:#fff; --aviso:#9a3412; }
  @media (prefers-color-scheme: dark) {
    :root { --fondo:#18191b; --tarjeta:#222326; --texto:#ececec; --suave:#a0a0a6; --borde:#34353a;
            --acento:#7fbfa8; --acento-texto:#10231d; --aviso:#fdba74; } }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--fondo); color:var(--texto);
         font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
  main { max-width:820px; margin:0 auto; padding:32px 16px 48px; }
  h1 { font-size:1.6rem; margin:0 0 4px; }
  .sub { color:var(--suave); margin:0 0 24px; }
  .tarjeta { background:var(--tarjeta); border:1px solid var(--borde); border-radius:14px; padding:20px; }
  .oculto { display:none !important; }
  label { display:block; font-weight:600; margin-bottom:6px; }
  input[type=text] { width:100%; padding:10px 12px; font:inherit; border-radius:8px;
                     border:1px solid var(--borde); background:var(--fondo); color:var(--texto); }
  button { font:inherit; border-radius:10px; padding:12px 16px; cursor:pointer;
           border:1px solid var(--borde); background:var(--fondo); color:var(--texto); }
  button.principal { background:var(--acento); color:var(--acento-texto); border-color:var(--acento); font-weight:600; }
  button:disabled { opacity:.45; cursor:not-allowed; }
  .fila { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
  @media (max-width:600px) { .fila { grid-template-columns:1fr; } }
  .cabecera { display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap; }
  .barra { height:6px; background:var(--borde); border-radius:3px; overflow:hidden; margin:10px 0 16px; }
  .barra > div { height:100%; background:var(--acento); width:0; transition:width .2s; }
  .etiqueta { color:var(--suave); font-size:.9rem; }
  blockquote { margin:12px 0 0; padding:10px 14px; border-left:3px solid var(--acento);
               background:var(--fondo); border-radius:0 8px 8px 0; }
  .audio { border:1px solid var(--borde); border-radius:10px; padding:12px; }
  .audio h3 { margin:0 0 8px; font-size:1rem; display:flex; justify-content:space-between; }
  .audio audio { width:100%; }
  .check { color:var(--acento); font-weight:600; font-size:.85rem; }
  .aviso { color:var(--aviso); margin-top:12px; min-height:1.5em; }
  .pie { display:flex; justify-content:space-between; align-items:center; margin-top:16px; gap:12px; flex-wrap:wrap; }
  .atajos { color:var(--suave); font-size:.85rem; }
  kbd { border:1px solid var(--borde); border-radius:4px; padding:0 5px; font-size:.8rem; }
  code { word-break:break-all; }
</style>
</head>
<body>
<main>
  <h1>Arena TTS</h1>
  <p class="sub">Escucha los dos audios y elige el que suena mejor. No se indica qué modelo ha generado cada uno.</p>

  <section id="inicio" class="tarjeta">
    <label for="nombre">Nombre del evaluador</label>
    <input id="nombre" type="text" placeholder="Por ejemplo: Mara" autocomplete="off">
    <div style="margin-top:12px"><button id="empezar" class="principal">Empezar</button></div>
    <div id="aviso-inicio" class="aviso"></div>
  </section>

  <section id="voto" class="tarjeta oculto">
    <div class="cabecera">
      <strong id="progreso"></strong>
      <span class="etiqueta" id="contexto"></span>
    </div>
    <div class="barra"><div id="barra"></div></div>
    <blockquote id="texto" class="oculto"></blockquote>
    <div class="fila">
      <div class="audio"><h3>Audio A <span id="ok-a" class="check oculto">✓ escuchado</span></h3>
        <audio id="audio-a" controls preload="auto"></audio></div>
      <div class="audio"><h3>Audio B <span id="ok-b" class="check oculto">✓ escuchado</span></h3>
        <audio id="audio-b" controls preload="auto"></audio></div>
    </div>
    <div class="fila">
      <button class="principal voto" data-opcion="izquierda">Gana A</button>
      <button class="principal voto" data-opcion="derecha">Gana B</button>
    </div>
    <div class="fila">
      <button class="voto" data-opcion="AMBOS_BIEN">Ambos suenan bien</button>
      <button class="voto" data-opcion="AMBOS_MAL">Ambos suenan mal</button>
    </div>
    <div id="aviso-voto" class="aviso">Escucha los dos audios enteros para poder votar.</div>
    <div class="pie">
      <button id="deshacer">↩ Deshacer último voto</button>
      <span class="atajos">Atajos: <kbd>A</kbd> gana A · <kbd>B</kbd> gana B · <kbd>S</kbd> ambos bien · <kbd>M</kbd> ambos mal · <kbd>Z</kbd> deshacer</span>
    </div>
  </section>

  <section id="fin" class="tarjeta oculto">
    <h2 id="fin-titulo" style="margin-top:0"></h2>
    <p id="fin-texto"></p>
    <p>Votos guardados en <code id="fin-ruta"></code></p>
    <p class="etiqueta">Para que vote otra persona, recarga la página.</p>
    <button id="deshacer-fin">↩ Deshacer último voto</button>
  </section>
</main>

<script>
"use strict";
const $ = (id) => document.getElementById(id);
let sesion = null;          // id de sesión que devuelve el servidor
let ocupado = false;        // evita dobles clics mientras responde el servidor
const escuchado = { a: false, b: false };

async function llamar(ruta, datos) {
  const r = await fetch(ruta, { method: "POST", headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(datos) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || ("Error " + r.status));
  return j;
}

function mostrar(seccion) {
  for (const id of ["inicio", "voto", "fin"]) $(id).classList.toggle("oculto", id !== seccion);
}

function actualizarBotones() {
  const listo = escuchado.a && escuchado.b && !ocupado;
  document.querySelectorAll("button.voto").forEach((b) => (b.disabled = !listo));
  $("ok-a").classList.toggle("oculto", !escuchado.a);
  $("ok-b").classList.toggle("oculto", !escuchado.b);
  $("aviso-voto").textContent = listo ? "" : (ocupado ? "" : "Escucha los dos audios enteros para poder votar.");
}

function pintar(e) {
  sesion = e.sesion;
  if (e.terminada) {
    mostrar("fin");
    $("fin-titulo").textContent = "¡Gracias, " + e.evaluador + "!";
    $("fin-texto").textContent = "Has votado las " + e.total + " parejas.";
    $("fin-ruta").textContent = e.ruta_csv;
    return;
  }
  mostrar("voto");
  $("progreso").textContent = "Pareja " + e.numero + " de " + e.total;
  $("contexto").textContent = e.idioma + " · " + e.perfil;
  $("barra").style.width = (100 * (e.numero - 1) / e.total) + "%";
  $("texto").classList.toggle("oculto", !e.texto);
  $("texto").textContent = e.texto || "";
  escuchado.a = escuchado.b = false;
  $("audio-a").src = e.audio_a;
  $("audio-b").src = e.audio_b;
  actualizarBotones();
}

async function empezar() {
  $("aviso-inicio").textContent = "";
  try { pintar(await llamar("/api/empezar", { nombre: $("nombre").value })); }
  catch (err) { $("aviso-inicio").textContent = "⚠️ " + err.message; }
}

async function accion(ruta, extra) {
  if (!sesion || ocupado) return;
  ocupado = true; actualizarBotones();
  $("audio-a").pause(); $("audio-b").pause();
  try { const e = await llamar(ruta, Object.assign({ sesion }, extra || {})); ocupado = false; pintar(e); }
  catch (err) { ocupado = false; actualizarBotones(); $("aviso-voto").textContent = "⚠️ " + err.message; }
}

function votar(opcion) {
  if (!(escuchado.a && escuchado.b)) return;
  accion("/api/votar", { opcion });
}

$("empezar").addEventListener("click", empezar);
$("nombre").addEventListener("keydown", (ev) => { if (ev.key === "Enter") empezar(); });
document.querySelectorAll("button.voto").forEach((b) =>
  b.addEventListener("click", () => votar(b.dataset.opcion)));
$("deshacer").addEventListener("click", () => accion("/api/deshacer"));
$("deshacer-fin").addEventListener("click", () => accion("/api/deshacer"));
$("audio-a").addEventListener("ended", () => { escuchado.a = true; actualizarBotones(); });
$("audio-b").addEventListener("ended", () => { escuchado.b = true; actualizarBotones(); });
// Al empezar a reproducir uno, se pausa el otro
$("audio-a").addEventListener("play", () => $("audio-b").pause());
$("audio-b").addEventListener("play", () => $("audio-a").pause());

document.addEventListener("keydown", (ev) => {
  if ($("voto").classList.contains("oculto") || ev.target.tagName === "INPUT") return;
  const tecla = ev.key.toLowerCase();
  const mapa = { a: "izquierda", b: "derecha", s: "AMBOS_BIEN", m: "AMBOS_MAL" };
  if (mapa[tecla]) votar(mapa[tecla]);
  else if (tecla === "z") accion("/api/deshacer");
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------
class EstadoServidor:
    """Sesiones abiertas (una por pestaña del navegador) y audios anonimizados."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.textos = leer_frases(args.frases) if args.frases else {}
        self.correspondencias = leer_correspondencias(args.perfiles) if args.perfiles else {}
        self.sesiones: dict[str, SesionVotacion] = {}
        self.audios: dict[str, Path] = {}          # identificador aleatorio -> ruta real
        self.audios_sesion: dict[str, list[str]] = {}
        self.cerrojo = threading.Lock()            # el servidor atiende peticiones en paralelo

    def _token_audio(self, id_sesion: str, ruta: Path) -> str:
        token = secrets.token_urlsafe(16)
        self.audios[token] = ruta
        self.audios_sesion.setdefault(id_sesion, []).append(token)
        return token

    def vista(self, id_sesion: str) -> dict:
        """Lo que el navegador necesita para pintar la pantalla, sin revelar los modelos."""
        s = self.sesiones[id_sesion]
        # Los audios de la pareja anterior dejan de estar disponibles
        for t in self.audios_sesion.pop(id_sesion, []):
            self.audios.pop(t, None)
        base = {"sesion": id_sesion, "evaluador": s.evaluador, "total": s.total,
                "ruta_csv": str(s.ruta_csv.resolve())}
        if s.terminada:
            return {**base, "terminada": True}
        act = s.actual()
        p = act["pareja"]
        return {**base, "terminada": False, "numero": act["numero"],
                "idioma": p.idioma, "perfil": p.perfil, "texto": self.textos.get(p.frase, ""),
                "audio_a": "/audio/" + self._token_audio(id_sesion, act["ruta_izquierda"]),
                "audio_b": "/audio/" + self._token_audio(id_sesion, act["ruta_derecha"])}

    def empezar(self, datos: dict) -> dict:
        s = SesionVotacion(self.args.audios, self.args.proporcion, datos.get("nombre", ""),
                           self.args.salida, semilla=self.args.semilla,
                           info_extra={"interfaz": "votar.py (http.server)",
                                       "igualado_audio": ({"igualado": False} if self.args.sin_igualar
                                                          else normalizar.descripcion(self.args.frecuencia))},
                           correspondencias=self.correspondencias)
        id_sesion = secrets.token_urlsafe(12)
        self.sesiones[id_sesion] = s
        return self.vista(id_sesion)

    def _sesion(self, datos: dict) -> tuple[str, SesionVotacion]:
        id_sesion = datos.get("sesion", "")
        if id_sesion not in self.sesiones:
            raise KeyError("Sesión no encontrada. Recarga la página y vuelve a empezar.")
        return id_sesion, self.sesiones[id_sesion]

    def votar(self, datos: dict) -> dict:
        id_sesion, s = self._sesion(datos)
        opcion = datos.get("opcion")
        if opcion not in ("izquierda", "derecha", AMBOS_BIEN, AMBOS_MAL):
            raise ValueError(f"Opción de voto no válida: {opcion}")
        s.votar(opcion)
        return self.vista(id_sesion)

    def deshacer(self, datos: dict) -> dict:
        id_sesion, s = self._sesion(datos)
        s.deshacer()
        return self.vista(id_sesion)


def crear_manejador(estado: EstadoServidor):
    rutas_api = {"/api/empezar": estado.empezar, "/api/votar": estado.votar,
                 "/api/deshacer": estado.deshacer}

    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):  # silencia el registro de cada petición
            pass

        def _enviar(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(cuerpo)

        def _enviar_audio(self, datos: bytes) -> None:
            """Envía el wav. Atiende peticiones parciales (Range), que algunos
            navegadores (Safari) necesitan para reproducir y avanzar en el audio."""
            rango = self.headers.get("Range", "")
            total = len(datos)
            if rango.startswith("bytes="):
                inicio_txt, _, fin_txt = rango[6:].split(",")[0].partition("-")
                try:
                    if inicio_txt:
                        inicio = int(inicio_txt)
                        fin = min(int(fin_txt), total - 1) if fin_txt else total - 1
                    else:  # "bytes=-N": los últimos N bytes
                        inicio, fin = max(0, total - int(fin_txt)), total - 1
                except ValueError:
                    inicio, fin = 0, total - 1
                if inicio > fin or inicio >= total:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self.send_header("Content-Range", f"bytes */{total}")
                    self.end_headers()
                    return
                trozo = datos[inicio:fin + 1]
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-Range", f"bytes {inicio}-{fin}/{total}")
            else:
                trozo = datos
                self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(trozo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(trozo)

        def _json(self, codigo: int, datos: dict) -> None:
            self._enviar(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                         "application/json; charset=utf-8")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._enviar(HTTPStatus.OK, PAGINA.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path.startswith("/audio/"):
                with estado.cerrojo:
                    ruta = estado.audios.get(self.path[len("/audio/"):])
                if ruta is None:
                    self._enviar(HTTPStatus.NOT_FOUND, b"", "text/plain")
                elif estado.args.sin_igualar:
                    self._enviar_audio(ruta.read_bytes())
                else:
                    self._enviar_audio(normalizar.audio_igualado(ruta, estado.args.frecuencia))
            else:
                self._enviar(HTTPStatus.NOT_FOUND, b"", "text/plain")

        def do_POST(self):
            funcion = rutas_api.get(self.path)
            if funcion is None:
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta desconocida"})
            try:
                longitud = int(self.headers.get("Content-Length", 0))
                datos = json.loads(self.rfile.read(longitud) or b"{}")
                with estado.cerrojo:
                    respuesta = funcion(datos)
                self._json(HTTPStatus.OK, respuesta)
            except Exception as e:  # el error se muestra en la página
                mensaje = e.args[0] if isinstance(e, KeyError) and e.args else str(e)
                self._json(HTTPStatus.BAD_REQUEST, {"error": mensaje})

    return Manejador


def leer_argumentos() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Arena TTS: votación a ciegas por parejas en el navegador")
    ap.add_argument("--audios", required=True,
                    help="Carpeta raíz con la estructura IDIOMA/MODELO/PERFIL/*.wav")
    ap.add_argument("--proporcion", type=float, default=0.3,
                    help="Proporción (0-1] de las parejas posibles de cada idioma y perfil que vota cada persona")
    ap.add_argument("--salida", default="resultados",
                    help="Carpeta donde se guardan los CSV de votos (por defecto: resultados)")
    ap.add_argument("--frases", default=None,
                    help="CSV opcional con columnas id,frase para mostrar el texto de cada frase")
    ap.add_argument("--perfiles", default=None,
                    help="CSV opcional (idioma,modelo,carpeta,perfil) que asigna un perfil a carpetas de voz "
                         "con otro nombre (p. ej. 'mujer' -> 'VOZ ADULTA') o las excluye (perfil vacío)")
    ap.add_argument("--semilla", type=int, default=None,
                    help="Semilla fija (opcional). Sin ella, cada sesión recibe una muestra distinta "
                         "y la semilla usada queda guardada en el .json")
    ap.add_argument("--frecuencia", type=int, default=24000,
                    help="Frecuencia de muestreo común a la que se pasan todos los audios (por defecto 24000)")
    ap.add_argument("--sin-igualar", action="store_true",
                    help="Reproducir los audios tal cual, sin igualar volumen ni frecuencia")
    ap.add_argument("--puerto", type=int, default=8000, help="Puerto local (por defecto 8000)")
    ap.add_argument("--sin-navegador", action="store_true", help="No abrir el navegador automáticamente")
    return ap.parse_args()


def main() -> None:
    args = leer_argumentos()
    if not 0 < args.proporcion <= 1:
        raise SystemExit("--proporcion debe estar entre 0 (excluido) y 1")
    if not Path(args.audios).is_dir():
        raise SystemExit(f"No existe la carpeta de audios: {args.audios}")

    estado = EstadoServidor(args)

    # Comprobación inicial: cuántas parejas hay en cada idioma y perfil
    from collections import Counter
    from arena import descubrir_audios, generar_parejas
    try:
        parejas = generar_parejas(descubrir_audios(args.audios, estado.correspondencias))
    except Exception as e:
        raise SystemExit(f"Error al leer los audios: {e}")
    if not parejas:
        raise SystemExit("No hay ninguna pareja que votar: cada frase necesita al menos dos modelos "
                         "con el mismo perfil. Revisa los nombres de las carpetas o perfiles.csv.")
    print("Parejas posibles por idioma y perfil:")
    for (idioma, perfil), n in sorted(Counter((p.idioma, p.perfil) for p in parejas).items()):
        modelos = sorted({m for p in parejas if (p.idioma, p.perfil) == (idioma, perfil)
                          for m in (p.modelo_a, p.modelo_b)})
        print(f"  {idioma} / {perfil}: {n} parejas ({len(modelos)} modelos: {', '.join(modelos)})")
    idiomas = sorted(d.name for d in Path(args.audios).iterdir()
                     if d.is_dir() and not d.name.startswith("."))
    sin_parejas = [i for i in idiomas if i not in {p.idioma for p in parejas}]
    if sin_parejas:
        print(f"  ⚠️  Sin ninguna pareja: {', '.join(sin_parejas)}")
    if args.sin_igualar:
        print("Audios sin igualar: se reproducen tal cual.")
    elif normalizar.np is None:
        print("⚠️  numpy no está instalado: se iguala el volumen, pero no la frecuencia de muestreo. "
              "Instálalo con: pip install numpy")
    else:
        print(f"Audios igualados: volumen común y {args.frecuencia} Hz.")
    # Solo escucha en este ordenador (127.0.0.1), no es accesible desde la red.
    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), crear_manejador(estado))
    url = f"http://127.0.0.1:{args.puerto}"
    print(f"Arena TTS en {url}  (Ctrl+C para cerrar)")
    if not args.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado. Los votos ya están guardados.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
