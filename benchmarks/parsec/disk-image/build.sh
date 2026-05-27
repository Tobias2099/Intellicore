#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'
Full-system PARSEC disk-image builds are intentionally scaffolded but not
enabled yet.

Next implementation step:
  1. Add packer templates under benchmarks/parsec/disk-image/.
  2. Build gem5's m5 utility for the guest image.
  3. Install PARSEC and input sets into the generated image.
  4. Keep generated images ignored by Git.
EOF
exit 2
