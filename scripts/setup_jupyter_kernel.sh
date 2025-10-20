chmod +x scripts/setup_jupyter_kernel.sh#!/usr/bin/env bash
# setup_jupyter_kernel.sh
# Usage: ./setup_jupyter_kernel.sh [env-name] [display-name]
# Example: ./setup_jupyter_kernel.sh mi_env "Python (mi_env)"

set -euo pipefail

ENV_NAME=${1:-myenvironment}
DISPLAY_NAME=${2:-"Python (${ENV_NAME})"}
# By default install requirements.txt unless third arg is --no-requirements
INSTALL_REQUIREMENTS=true
if [ "${3:-}" = "--no-requirements" ]; then
  INSTALL_REQUIREMENTS=false
fi

echo "Using conda environment: ${ENV_NAME}"

# Try to locate conda base; prefer conda in PATH
if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda command not found in PATH. Please install Anaconda/Miniconda or ensure conda is available." >&2
  exit 2
fi

# Activate conda environment in a bash-friendly way
# Use 'conda activate' by leveraging conda's shell hook
# shellcheck disable=SC1091
__conda_setup="$(conda shell.zsh hook 2>/dev/null || conda shell.bash hook 2>/dev/null || true)"
if [ -n "$__conda_setup" ]; then
  eval "$__conda_setup"
else
  # fallback: try to source conda.sh from known locations
  if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    . "$HOME/miniconda3/etc/profile.d/conda.sh"
  elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    . "$HOME/anaconda3/etc/profile.d/conda.sh"
  fi
fi

# Check if env exists; if not, offer to create it
if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Environment ${ENV_NAME} exists. Activating..."
else
  echo "Environment ${ENV_NAME} does not exist. Creating with Python 3.10..."
  conda create -n "${ENV_NAME}" python=3.10 -y
fi

conda activate "${ENV_NAME}"

echo "Installing jupyter and ipykernel into ${ENV_NAME}..."
# Use conda to install if available
conda install -y jupyter ipykernel -c conda-forge

# Install project requirements via pip if requested and file exists
if [ "$INSTALL_REQUIREMENTS" = true ]; then
  if [ -f "requirements.txt" ]; then
    echo "Installing project requirements from requirements.txt using pip..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo "Installing opencv-python-headless (preferred for headless/server environments)..."
    pip install opencv-python-headless
  else
    echo "requirements.txt not found in current directory; skipping pip install." >&2
  fi
else
  echo "Skipping installation from requirements.txt (user requested)."
fi

# Register the kernel for the current environment
python -m ipykernel install --user --name "${ENV_NAME}" --display-name "${DISPLAY_NAME}"

echo "Kernel installed as '${DISPLAY_NAME}' (name: ${ENV_NAME})."

echo "To run Jupyter Lab:"
echo "  conda activate ${ENV_NAME} && jupyter lab"

echo "To see kernels: jupyter kernelspec list"

exit 0
