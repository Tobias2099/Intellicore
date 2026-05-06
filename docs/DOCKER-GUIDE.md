# Docker Environment Guide

This guide explains how to use Docker for IntelliCore development and gem5 simulation. **No local gem5 installation is required.**

## Overview

The IntelliCore Docker setup provides:

- **Development environment** (`dev`): For Python/C++ work
- **gem5 simulation** (`gem5-sim`, `gem5-prebuilt`): Pre-compiled gem5 with IntelliCore configs

| Service           | Purpose                                          | Use Case                                  |
| ----------------- | ------------------------------------------------ | ----------------------------------------- |
| `dev`             | Python 3.11 + PyTorch + C++ build tools          | Day-to-day development                    |
| `gem5-sim`        | Auto-running gem5 simulation                     | One-shot `architecture.py` execution      |
| `gem5-prebuilt`   | Interactive shell with pre-compiled gem5         | Manual experimentation and debugging      |
| `gem5-shell`      | Interactive shell with gem5 source mounted       | Advanced gem5 hacking (requires build)    |

## Key Design Decision: No gem5 in GitHub

gem5 is **not** stored in this repository. Instead:

1. **Docker clones gem5** from the official repository during image build
2. **gem5 is compiled** inside the Docker image
3. **Result is cached** as a Docker image for fast reuse

**Benefits**:
- Repository stays small (no 2GB+ gem5 source tree)
- Reproducible builds everywhere (Linux, macOS, Windows, cloud)
- Version pinning (currently v25.1.0.0)
- No dependency hell on local systems

**For users**: Install Docker once, then `./scripts/run-gem5-simple.sh` handles everything.

## Prerequisites

1. **Docker installed**: Download from [Docker's official site](https://www.docker.com/products/docker-desktop)
2. **Docker Compose**: Usually included with Docker Desktop
3. **At least 5GB disk space**: For Docker images and gem5 compilation
4. **~15-30 minutes on first run**: Only for gem5 compilation, then cached

## Getting Started

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url> Intellicore
cd Intellicore

# Copy the example environment file
cp .env.example .env
```

### 2. Run Your First Simulation

The easiest way to verify Docker is working:

```bash
# This will:
# - Build the Docker image (includes gem5 build on first run)
# - Run the baseline architecture from configs/gem5/architecture.py
# - Save results to ./m5out/
./scripts/run-gem5-simple.sh

# Check the results
cat m5out/stats.txt
```

**First-time timing**: 15-30 minutes (includes gem5 compilation). Subsequent runs: 30-60 seconds.

### 3. Launch the Development Environment

For ongoing development:

```bash
# Build and start the dev container in the background
docker compose --profile dev up --build -d dev

# Open a shell in the container
docker compose exec dev bash

# Run tests, Python scripts, etc.
docker compose exec dev pytest services/control-plane/tests

# Later, stop the container
docker compose stop dev
```

## Common Workflows

### Workflow 1: One-Off Simulation

**Goal**: Run gem5 once and get results.

```bash
./scripts/run-gem5-simple.sh
cat m5out/stats.txt
```

**First run**: ~20 minutes (includes gem5 build)  
**Subsequent runs**: ~30-60 seconds

### Workflow 2: Custom Architecture Experiments

**Goal**: Create and test new architecture configurations.

```bash
# 1. Copy the baseline architecture as a template
cp configs/gem5/architecture.py configs/gem5/my-experiment.py

# 2. Edit your copy to add cores, L2 caches, etc.
# Example: add more CPU cores, increase cache sizes
vim configs/gem5/my-experiment.py

# 3. Run your custom architecture
./scripts/run-gem5-simple.sh --config configs/gem5/my-experiment.py

# 4. Analyze results
cat m5out/stats.txt

# 5. Commit your experiment to git
git add configs/gem5/my-experiment.py
git commit -m "Add multi-core experiment"
```

### Workflow 3: Interactive gem5 Shell

**Goal**: Experiment with gem5 interactively.

```bash
# Start an interactive shell
docker compose --profile gem5 run --rm gem5-prebuilt bash

# Inside the container, you have access to:
# /opt/gem5 - Compiled gem5 binary at /opt/gem5/build/X86/gem5.opt
# /workspace - Project files
# Python packages - All gem5 dependencies

# Example: run a simulation manually
/opt/gem5/build/X86/gem5.opt \
  --outdir=/workspace/m5out \
  configs/gem5/architecture.py

# Example: explore gem5
ls /opt/gem5/configs
$GEM5_ROOT/build/X86/gem5.opt --help

# Exit the container
exit
```

### Workflow 4: Python Development with Dependencies

**Goal**: Develop Python code with all IntelliCore dependencies.

```bash
# Start the dev container persistently
docker compose --profile dev up --build -d dev

# Run your Python scripts
docker compose exec dev python services/control-plane/src/intellicore_control/cli.py

# Run tests
docker compose exec dev pytest services/control-plane/tests

# Install additional packages (in the running container)
docker compose exec dev pip install <package-name>

# When done
docker compose stop dev
```

### Workflow 5: Building a Different gem5 Configuration

**Goal**: Compile gem5 for a different ISA or with different options.

Edit `docker-compose.yml` build args:

```yaml
gem5-sim:
  build:
    args:
      GEM5_ISA: ARM                     # Change ISA
      GEM5_BUILD_VARIANT: gem5.fast     # Change variant
      GEM5_REF: v26.0.0.0               # Update gem5 version
```

Then rebuild:

```bash
docker compose --profile gem5 build --no-cache gem5-sim
./scripts/run-gem5-simple.sh --build
```

## Understanding Docker Build Caching

The first time you build the gem5 image, Docker:

1. Installs dependencies (~5 min)
2. Clones gem5 (~1 min)
3. **Compiles gem5** (~15-25 min) ← This is the slow part
4. Caches the result as `intellicore/gem5:local`

On subsequent runs, Docker **reuses the cached image**, skipping all of the above.

To force a rebuild (e.g., after updating gem5 version):

```bash
./scripts/run-gem5-simple.sh --build
```

## Managing Docker

### View Running Containers

```bash
# List running containers
docker compose ps

# List all containers (including stopped)
docker compose ps -a
```

### View Images

```bash
# List IntelliCore images
docker image ls | grep intellicore
```

### Clean Up

```bash
# Stop all containers
docker compose down

# Stop and remove containers + networks (keeps images)
docker compose down

# Stop, remove containers, networks, AND images
docker compose down --rmi all

# Remove everything including volumes (⚠️ data loss!)
docker compose down --rmi all -v

# Clean unused images system-wide
docker image prune -a
```

### Export/Import Images

Useful for sharing pre-built images or backups.

```bash
# Export the gem5 image to a tar file
docker save -o intellicore-gem5.tar intellicore/gem5:local

# Transfer the file to another machine, then load it:
docker load -i intellicore-gem5.tar

# Verify it's available
docker image ls intellicore/gem5:local
```

## Troubleshooting

### Problem: "Permission denied" or "sudo required"

**Solution**: Add your user to the docker group (Linux):

```bash
sudo usermod -aG docker $USER
newgrp docker
# Log out and back in, or run: exec bash
```

### Problem: Docker build is very slow

**Expected behavior**. gem5 compilation takes 15-30 minutes. Subsequent runs use the cached image and are fast.

To see build progress:

```bash
docker compose --profile gem5 build --no-cache gem5-sim
# Watch the output for gem5 compilation
```

### Problem: "Error response from daemon: Cannot allocate memory"

**Solution**: Increase Docker's memory allocation:

1. Open Docker Desktop settings
2. Go to Resources > Memory
3. Increase to at least 4GB (8GB recommended)
4. Click "Apply & Restart"

Or on Linux, edit `/etc/docker/daemon.json`:

```json
{
  "memory": 8589934592
}
```

Then restart Docker.

### Problem: "gem5.opt: command not found"

The Docker image didn't build successfully. Rebuild:

```bash
docker compose --profile gem5 build --no-cache gem5-sim
```

Watch for compilation errors in the output.

### Problem: Simulation results not saved to ./m5out/

Check volume mounting:

```bash
docker compose --profile gem5 run --rm gem5-sim ls -la /workspace/m5out
```

If empty, verify `docker-compose.yml` has the correct volume mount for `m5out`.

### Problem: "Disk space" errors

Clean up Docker artifacts:

```bash
docker system prune -a --volumes
```

Or manually remove images:

```bash
docker image rm intellicore/gem5:local
docker image rm intellicore/dev:local
```

## Architecture as Code

IntelliCore stores gem5 architectures as Python configuration files:

- **Location**: `configs/gem5/`
- **Baseline**: `configs/gem5/architecture.py` (single-core, basic caches)
- **Creating variants**: Copy and modify to add more cores, caches, RL integration, etc.

The architecture.py file is versioned in GitHub. gem5 itself is not.

## Docker Compose Profiles

Profiles organize services into logical groups. Use `--profile <name>` with docker-compose:

```bash
# Activate a profile
docker compose --profile dev up

# Activate multiple profiles
docker compose --profile dev --profile tools run ...

# Without --profile, only services without a profile are active
docker compose up
```

Available profiles:

- **dev**: Development (`dev` service)
- **gem5**: Simulation (`gem5-sim`, `gem5-prebuilt`, `gem5-shell`)
- **tools**: One-shot utilities (`supabase-*` services)

## Environment Variables

Configure behavior with `.env` file (copied from `.env.example`):

| Variable       | Purpose                                          | Example              |
| -------------- | ------------------------------------------------ | -------------------- |
| `DATABASE_URL` | Supabase Postgres connection (for telemetry)    | `postgresql://...`   |
| `GEM5_ROOT`    | Path to gem5 inside containers                   | `/opt/gem5`          |
| `PYTHONPATH`   | Python module search paths inside containers    | `services/control-plane/src:...` |

## Advanced Topics

### Customizing the Docker Build

Edit `infra/docker/gem5-prebuilt.Dockerfile` to:
- Add system packages
- Change dependency versions
- Modify gem5 build flags

Then rebuild:

```bash
docker compose --profile gem5 build --no-cache gem5-sim
```

### Adding a New Docker Service

Edit `docker-compose.yml`:

```yaml
my-experiment:
  image: intellicore/gem5:local
  working_dir: /workspace
  volumes:
    - ./:/workspace
  profiles:
      - gem5
  command: |
    /opt/gem5/build/X86/gem5.opt \
      --outdir=/workspace/m5out \
      configs/gem5/my-experiment.py
```

Run it:

```bash
docker compose --profile gem5 run --rm my-experiment
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [gem5 Learning Guides](https://www.gem5.org/documentation/learning_gem5/)
- [gem5 Building](https://www.gem5.org/documentation/learning_gem5/part1/building/)
