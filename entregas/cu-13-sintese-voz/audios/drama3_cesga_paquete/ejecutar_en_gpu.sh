#!/usr/bin/env bash
# Paquete Drama 3 para CESGA FinisTerrae III.
#
#   1) NODO LOGIN (tiene Internet, sin GPU):   PREPARAR=1 bash ejecutar_en_gpu.sh
#      Clona fish-speech, crea el entorno y descarga los pesos. No genera audio.
#   2) NODO GPU (sbatch/salloc):               MODO=prueba bash ejecutar_en_gpu.sh
#      Si el paso 1 ya se hizo, no necesita red. Se puede relanzar: los WAV
#      válidos ya generados no se repiten.
#
# El paquete debe estar en $LUSTRE o $STORE: entorno + pesos superan la cuota de $HOME.
set -Eeuo pipefail
cd "$(dirname "$0")"
BASE="$PWD"
REPO="$BASE/fish-speech"
export HF_HOME="${HF_HOME:-$BASE/cache_hf}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$BASE/cache_uv}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$BASE/cache_xdg}"
export PATH="$HOME/.local/bin:$PATH"
CUDA_EXTRA="${CUDA_EXTRA:-cu126}"
MODO="${MODO:-completo}"     # prueba | completo
PUERTO="${PUERTO:-18080}"
PREPARAR="${PREPARAR:-0}"    # 1 = solo descargar (nodo login)

case "$BASE/" in
  "$HOME"/*)
    if [[ "${FORZAR_HOME:-0}" != 1 ]]; then
      echo "ERROR: el paquete está dentro de \$HOME ($BASE)."
      echo "La cuota de \$HOME en FT3 es 10 GB / 100.000 ficheros y no cabe el entorno ni los pesos."
      echo "Muévelo:  mv \"$BASE\" \"\$LUSTRE/\"   (o usa FORZAR_HOME=1 bajo tu responsabilidad)"
      exit 1
    fi;;
esac

listo_entorno() { [[ -f "$REPO/.venv/.sync_ok" && "$(cat "$REPO/.venv/.sync_ok")" == "$CUDA_EXTRA" ]]; }
listo_pesos()   { [[ -f "$REPO/checkpoints/drama-3/.descarga_ok" ]] && \
                  [[ -f "$REPO/checkpoints/drama-3/codec.pth" || -f "$REPO/checkpoints/s2-pro/codec.pth" ]]; }

descargar() {
  if [[ ! -d "$REPO/.git" ]]; then git clone https://github.com/fishaudio/fish-speech.git "$REPO"; fi
  if ! command -v uv >/dev/null 2>&1; then
    echo 'Falta uv: instalándolo en el directorio personal.'
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  cd "$REPO"
  if ! listo_entorno; then
    uv sync --python 3.12 --extra "$CUDA_EXTRA"
    echo "$CUDA_EXTRA" > .venv/.sync_ok
  fi
  if [[ ! -f checkpoints/drama-3/.descarga_ok ]]; then
    uv run --no-sync hf download fishaudio/drama-3 --local-dir checkpoints/drama-3
    touch checkpoints/drama-3/.descarga_ok
  fi
  if [[ ! -f checkpoints/drama-3/codec.pth && ! -f checkpoints/s2-pro/codec.pth ]]; then
    uv run --no-sync hf download fishaudio/s2-pro codec.pth --local-dir checkpoints/s2-pro
  fi
  cd "$BASE"
}

if [[ "$PREPARAR" == 1 ]]; then
  descargar
  echo "Preparación terminada. Espacio usado:"; du -sh "$BASE" 2>/dev/null || true
  echo "Ahora lanza el trabajo GPU:  sbatch --export=ALL,MODO=prueba trabajo_slurm_ejemplo.sh"
  exit 0
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then echo 'ERROR: nvidia-smi no disponible (¿estás en el nodo login?)'; exit 1; fi
nvidia-smi
echo "Driver: $(nvidia-smi | grep -o 'CUDA Version: [0-9.]*' || echo 'desconocido') | extra PyTorch: $CUDA_EXTRA"
if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then echo 'AVISO: CUDA_VISIBLE_DEVICES no definido; comprueba la reserva CESGA.'; fi

if listo_entorno && listo_pesos; then
  echo 'Entorno y pesos ya presentes: modo sin red.'
  export UV_OFFLINE=1 HF_HUB_OFFLINE=1
else
  echo 'AVISO: faltan entorno o pesos; se intentará descargar desde el nodo GPU (puede no tener Internet).'
  descargar
fi

cd "$REPO"
# Se usarán todas las GPU visibles que soporte el programa (hasta cuatro).
uv run --no-sync python tools/api_server.py \
  --listen "127.0.0.1:$PUERTO" \
  --llama-checkpoint-path checkpoints/drama-3 \
  --device cuda > "$BASE/servidor_drama3.log" 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
LISTO=0
for i in $(seq 1 180); do
  if curl -fsS "http://127.0.0.1:$PUERTO/v1/health" >/dev/null 2>&1; then LISTO=1; break; fi
  if ! kill -0 "$PID" 2>/dev/null; then echo 'ERROR: servidor detenido'; tail -n 100 "$BASE/servidor_drama3.log"; exit 1; fi
  sleep 5
done
if [[ "$LISTO" != 1 ]]; then echo 'ERROR: timeout al iniciar servidor'; tail -n 100 "$BASE/servidor_drama3.log"; exit 1; fi
ARGS=(--csv "$BASE/frases_prueba.csv" --salida "$BASE/resultados_drama3" --url "http://127.0.0.1:$PUERTO/v1/tts")
if [[ "$MODO" == prueba ]]; then ARGS+=(--prueba); fi
"$REPO/.venv/bin/python" "$BASE/generar_audios.py" "${ARGS[@]}"
echo 'Resultados:'
ls -lh "$BASE"/resultados_drama3/*.zip
