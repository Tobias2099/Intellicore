#!/usr/bin/env bash
set -euo pipefail

export INTELLICORE_ROOT="${INTELLICORE_ROOT:-/workspace}"
export PARSEC_ROOT="${PARSEC_ROOT:-$INTELLICORE_ROOT/benchmarks/parsec/source}"
export PARSEC_INSTALL="${PARSEC_INSTALL:-$INTELLICORE_ROOT/benchmarks/parsec/install}"
export PARSEC_BIN="${PARSEC_BIN:-$INTELLICORE_ROOT/benchmarks/parsec/bin}"
export PARSEC_INPUTS="${PARSEC_INPUTS:-$INTELLICORE_ROOT/benchmarks/parsec/inputs}"
