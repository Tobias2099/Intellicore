# Docker Quick Reference

Quick commands for common IntelliCore Docker tasks. See [DOCKER-GUIDE.md](DOCKER-GUIDE.md) for detailed explanations.

## ⚡ First Time Setup

```bash
# Clone repo
git clone <repo-url> Intellicore
cd Intellicore

# Copy environment
cp .env.example .env

# Run first simulation (builds gem5, takes ~15-30 min)
./scripts/run-gem5-simple.sh

# Check results
cat m5out/stats.txt
```

**On first run, gem5 is compiled inside Docker (15-30 min). Subsequent runs are fast (~30-60 sec).**

## 🎯 Running Simulations

```bash
# Run baseline architecture (fastest)
./scripts/run-gem5-simple.sh

# Create and run a custom architecture
cp configs/gem5/architecture.py configs/gem5/my-custom-arch.py
# (edit my-custom-arch.py to add cores, caches, etc.)
./scripts/run-gem5-simple.sh --config configs/gem5/my-custom-arch.py

# With gem5 debug flags
./scripts/run-gem5-simple.sh --args "--debug-flags=All"

# Force rebuild (rebuilds gem5)
./scripts/run-gem5-simple.sh --build

# Direct docker-compose
docker compose --profile gem5 run --rm gem5-sim
```

## 💻 Development Environment

```bash
# Start persistent dev container
docker compose --profile dev up --build -d dev

# Open shell
docker compose exec dev bash

# Run Python script
docker compose exec dev python services/control-plane/src/intellicore_control/cli.py

# Run tests
docker compose exec dev pytest

# Stop container
docker compose stop dev
```

## 🔧 Interactive gem5 Shell

```bash
# Start interactive shell (gem5 already compiled)
docker compose --profile gem5 run --rm gem5-prebuilt bash

# Inside container:
/opt/gem5/build/X86/gem5.opt --help
/opt/gem5/build/X86/gem5.opt --outdir=m5out configs/gem5/architecture.py
```

## 📦 Images & Cleanup

```bash
# View images
docker image ls | grep intellicore

# Export image
docker save -o intellicore-gem5.tar intellicore/gem5:local

# Load image
docker load -i intellicore-gem5.tar

# Stop all containers
docker compose down

# Remove everything (be careful!)
docker compose down --rmi all

# Clean unused images
docker image prune -a
```

## 🐛 Troubleshooting

```bash
# Check container status
docker compose ps

# View logs
docker compose logs dev

# Check gem5 is working
docker compose --profile gem5 run --rm gem5-prebuilt \
  /opt/gem5/build/X86/gem5.opt --help

# Increase Docker memory (if "Cannot allocate memory")
# Open Docker Desktop → Resources → Memory → increase to 4GB+
```

## 📋 Key Concepts

- **No local gem5 needed**: Docker handles everything
- **gem5 builds once**: First run (~15-30 min), then cached
- **Architecture as code**: `configs/gem5/architecture.py` is in GitHub
- **gem5 itself**: NOT in GitHub, downloaded from official source during Docker build

## 📚 Full Guide

See [DOCKER-GUIDE.md](DOCKER-GUIDE.md) for:
- Detailed workflows
- Custom builds
- Advanced topics
- Troubleshooting
