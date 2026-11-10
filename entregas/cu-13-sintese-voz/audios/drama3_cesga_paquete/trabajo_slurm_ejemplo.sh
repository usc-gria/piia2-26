#!/usr/bin/env bash
#SBATCH --job-name=drama3_es_gl
#SBATCH --output=drama3_%j.out
#SBATCH --error=drama3_%j.err
#SBATCH --gres=gpu:a100:4      # nodo 5x A100: backbone bf16 (~70 GB) no cabe en 2 x 40 GB
#SBATCH -c 48                  # 12 CPU por GPU en el nodo 5x A100
#SBATCH --mem=128G
#SBATCH --time=04:00:00        # relanzable: no repite los WAV ya generados
# Lanzar desde la carpeta del paquete (en $LUSTRE), tras PREPARAR=1 en el nodo login:
#   sbatch --export=ALL,MODO=prueba   trabajo_slurm_ejemplo.sh
#   sbatch --export=ALL,MODO=completo trabajo_slurm_ejemplo.sh
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export MODO="${MODO:-prueba}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
bash ejecutar_en_gpu.sh
