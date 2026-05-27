#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

workload="${1:-blackscholes}"
build_config="${PARSEC_BUILD_CONFIG:-gcc-hooks}"

export MAKEINFO="${MAKEINFO:-true}"

if [ ! -x "$PARSEC_ROOT/bin/parsecmgmt" ]; then
  cat >&2 <<EOF
PARSEC source was not found at:
  $PARSEC_ROOT

Place or extract PARSEC there, or set PARSEC_ROOT before running this script.
Expected executable:
  $PARSEC_ROOT/bin/parsecmgmt
EOF
  exit 2
fi

mkdir -p "$PARSEC_INSTALL" "$PARSEC_BIN"

cd "$PARSEC_ROOT"
./bin/parsecmgmt -a build -p "$workload" -c "$build_config"

package_root="$(find "$PARSEC_ROOT/pkgs" -maxdepth 3 -type d -name "$workload" | head -n 1 || true)"
runconf=""
if [ -n "$package_root" ]; then
  runconf="$package_root/parsec/simsmall.runconf"
fi

run_exec="$(sed -n 's/^run_exec="\([^"]*\)"/\1/p' "$runconf" 2>/dev/null | head -n 1 || true)"
binary_name="$workload"
if [ -n "$run_exec" ]; then
  binary_name="$(basename "$run_exec")"
fi

candidate="$(find "$PARSEC_ROOT/pkgs" -path "*/inst/*/bin/$binary_name" -type f | head -n 1 || true)"
if [ -z "$candidate" ]; then
  candidate="$(find "$PARSEC_ROOT/pkgs" -path "*/inst/*/$binary_name" -type f | head -n 1 || true)"
fi
if [ -z "$candidate" ] && [ "$binary_name" != "$workload" ]; then
  candidate="$(find "$PARSEC_ROOT/pkgs" -path "*/inst/*/bin/$workload" -type f | head -n 1 || true)"
fi

if [ -z "$candidate" ]; then
  cat >&2 <<EOF
Built PARSEC workload '$workload', but could not find its installed binary.
Copy the runnable binary to:
  $PARSEC_BIN/$workload
EOF
  exit 3
fi

cp "$candidate" "$PARSEC_BIN/$workload"
chmod +x "$PARSEC_BIN/$workload"
echo "Installed $workload binary at $PARSEC_BIN/$workload"
