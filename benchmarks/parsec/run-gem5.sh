#!/usr/bin/env bash
set -euo pipefail

workload="${1:-blackscholes}"
input_size="${2:-simsmall}"
policy="${POLICY:-LRU}"
prefetch="${PREFETCH:-delta}"
threads="${THREADS:-1}"
outdir="/workspace/m5out/parsec/$workload/$input_size/$policy/$prefetch"

docker compose --profile gem5 run --rm \
  -e POLICY="$policy" \
  -e PREFETCH="$prefetch" \
  -e THREADS="$threads" \
  -e PARSEC_WORKLOAD="$workload" \
  -e PARSEC_INPUT="$input_size" \
  -e GEM5_OUTDIR="$outdir" \
  gem5-shell bash -lc \
  'cd "$GEM5_ROOT" && build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} \
    --outdir="$GEM5_OUTDIR" \
    /workspace/configs/gem5/multicore_arch.py \
    --benchmark parsec \
    --parsec-workload "$PARSEC_WORKLOAD" \
    --parsec-input "$PARSEC_INPUT" \
    --repl "$POLICY" \
    --prefetch "$PREFETCH" \
    --threads "$THREADS"'
