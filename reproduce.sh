#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKSPACE="$ROOT/workspace"
IMAGE=ghcr.io/riscv/act4-build@sha256:117d9d4ed85cf6f564d21d1ee030546416d4737c024f6a1608c53a1bd9c71ca0

python3 -m unittest discover -s "$ROOT/tests" -v
python3 "$ROOT/setup.py" "$WORKSPACE"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/home/shared \
  -v "$ROOT:/repo" "$IMAGE" sh -lc \
  'cd /repo/workspace/act4 && mise trust .mise.toml && mise install && mise exec -- make clean && mise exec -- make CONFIG_FILES=config/cores/cve4/cv32e40p-v2-rv32imc/test_config.yaml'
python3 "$ROOT/setup.py" "$WORKSPACE" --build
python3 "$ROOT/run.py" "$WORKSPACE"
