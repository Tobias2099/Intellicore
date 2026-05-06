#!/usr/bin/env bash
#
# Run gem5 architecture simulation through Docker
#
# This script runs IntelliCore's gem5 baseline architecture simulation using Docker.
# The architecture configuration can be customized or replaced with more complex
# multi-core, multi-cache configurations as needed.
#
# Usage:
#   ./scripts/run-gem5-simple.sh
#   ./scripts/run-gem5-simple.sh --config custom.py
#   ./scripts/run-gem5-simple.sh --help

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
CONFIG="configs/gem5/architecture.py"
GEM5_ARGS=""
DOCKER_BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --args)
            GEM5_ARGS="$2"
            shift 2
            ;;
        --build)
            DOCKER_BUILD=true
            shift
            ;;
        --help)
            cat << 'EOF'
Run gem5 architecture simulation through Docker

Usage:
  ./scripts/run-gem5-simple.sh [OPTIONS]

Options:
  --config PATH          Path to gem5 config script (default: configs/gem5/architecture.py)
  --args ARGS           Additional arguments to pass to gem5.opt
  --build               Rebuild Docker image before running (forces gem5 rebuild)
  --help                Show this help message

Examples:
  # Run baseline architecture
  ./scripts/run-gem5-simple.sh

  # Run with a custom architecture config
  ./scripts/run-gem5-simple.sh --config configs/gem5/custom-architecture.py

  # Run with debug flags
  ./scripts/run-gem5-simple.sh --args "--debug-flags=All"

  # Rebuild Docker image (rebuilds gem5, runs on first use only)
  ./scripts/run-gem5-simple.sh --build

Note: The Docker image is built once on first run (~15-30 minutes for gem5 compilation).
Subsequent runs reuse the cached image and complete in seconds.

EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Verify config file exists
if [[ ! -f "$PROJECT_ROOT/$CONFIG" ]]; then
    echo "Error: Config file not found: $CONFIG"
    exit 1
fi

if [[ "$DOCKER_BUILD" == true ]]; then
    echo "=== Rebuilding Docker image (this may take 15-30 minutes) ==="
    docker compose --profile gem5 build gem5-sim
else
    echo "=== Ensuring Docker image is ready ==="
    # Build quietly if image doesn't exist
    docker compose --profile gem5 build --quiet gem5-sim 2>/dev/null || true
fi

echo ""
echo "=== Running gem5 architecture simulation ==="
echo "Configuration: $CONFIG"
echo "Output directory: ./m5out/"
echo ""

# Create output directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/m5out"

# Run the simulation
docker compose --profile gem5 run --rm gem5-sim /bin/bash -c "
set -e
/opt/gem5/build/X86/gem5.opt \
  --outdir=/workspace/m5out \
  $CONFIG $GEM5_ARGS
"

echo ""
echo "=== Simulation completed successfully ==="
echo "Results saved to ./m5out/"
echo ""
echo "Key output files:"
echo "  - ./m5out/config.ini     - Simulation configuration"
echo "  - ./m5out/config.json    - Configuration in JSON format"
echo "  - ./m5out/stats.txt      - Simulation statistics"
echo ""
echo "To analyze results: cat ./m5out/stats.txt"
