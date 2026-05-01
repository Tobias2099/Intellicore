#!/usr/bin/env bash
set -euo pipefail

python --version
python - <<'PY'
import torch
print(f"torch {torch.__version__}")
PY

cmake --version | head -n 1
g++ --version | head -n 1
scons --version | head -n 1
protoc --version

cmake -S sim/gem5-intellicore -B build/gem5-intellicore -G Ninja
cmake --build build/gem5-intellicore
./build/gem5-intellicore/gem5_intellicore_smoke

python -m intellicore_control.cli runs plan --config configs/gem5/baseline-x86.yaml
python -m intellicore_training.cli train --config configs/agents/baseline-dqn.yaml
