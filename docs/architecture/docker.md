# Docker Development Environment

The Docker stack supports the required research toolchain:

- Supabase cloud Postgres connectivity checks
- Python 3.11 service runtime
- CPU PyTorch for MARL training
- C++ compiler, CMake, Ninja, and gdb
- gem5 build dependencies such as SCons, protobuf, Boost, zlib, m4, and gperftools

## Commands

```bash
cp .env.example .env
docker compose --profile dev build dev
docker compose --profile dev up -d dev
docker compose exec dev bash scripts/docker-smoke.sh
docker compose --profile tools run --rm supabase-check
```

To work on gem5 itself, place or clone gem5 under the named `/opt/gem5` volume from inside the dev container:

```bash
docker compose --profile dev exec dev bash
git clone https://gem5.googlesource.com/public/gem5 "$GEM5_ROOT"
cd "$GEM5_ROOT"
scons build/X86/gem5.opt -j"$(nproc)"
```

The repository does not clone gem5 automatically during image build because gem5 is large and changes independently from the IntelliCore scaffold.
