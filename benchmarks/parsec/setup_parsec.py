#!/usr/bin/env python3
"""Prepare PARSEC workload artifacts for IntelliCore.

The full PARSEC source tree stays in a Docker volume so Linux-only filenames
and build behavior do not leak into the Windows workspace. This script copies
only runnable binaries and selected input sets into benchmarks/parsec/.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


PARSEC_REPO = "https://github.com/darchr/parsec-benchmark.git"
PARSEC_SIM_INPUTS_URL = (
    "https://github.com/cirosantilli/parsec-benchmark/releases/download/3.0/"
    "parsec-3.0-input-sim.tar.gz"
)
PARSEC_NATIVE_INPUTS_URL = (
    "https://github.com/cirosantilli/parsec-benchmark/releases/download/3.0/"
    "parsec-3.0-input-native.tar.gz"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PARSEC_DIR = REPO_ROOT / "benchmarks" / "parsec"


@dataclass(frozen=True)
class WorkloadSpec:
    name: str
    package_group: str = "apps"
    build: bool = True
    input_archives: bool = True

    @property
    def package_root(self) -> str:
        return f"/parsec-source/pkgs/{self.package_group}/{self.name}"

    @property
    def binary(self) -> Path:
        return PARSEC_DIR / "bin" / self.name


WORKLOADS: dict[str, WorkloadSpec] = {
    "blackscholes": WorkloadSpec(name="blackscholes"),
    "bodytrack": WorkloadSpec(name="bodytrack"),
    "canneal": WorkloadSpec(name="canneal", package_group="kernels"),
    "dedup": WorkloadSpec(name="dedup", package_group="kernels"),
    "facesim": WorkloadSpec(name="facesim"),
    "ferret": WorkloadSpec(name="ferret"),
    "fluidanimate": WorkloadSpec(name="fluidanimate"),
    "freqmine": WorkloadSpec(name="freqmine"),
    "raytrace": WorkloadSpec(name="raytrace"),
    "streamcluster": WorkloadSpec(
        name="streamcluster",
        package_group="kernels",
        input_archives=False,
    ),
    "swaptions": WorkloadSpec(name="swaptions", input_archives=False),
    "vips": WorkloadSpec(name="vips"),
    "x264": WorkloadSpec(name="x264"),
}

DEFAULT_ALL_INPUTS = ["simsmall", "simmedium", "simlarge"]

INPUT_ARCHIVES = {
    "simsmall": "simsmall",
    "simmedium": "simmedium",
    "simlarge": "simlarge",
    "native": "native",
}


def quote(value: str) -> str:
    return shlex.quote(value)


def run(command: list[str]) -> None:
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"

    print("+ " + " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, env=env, check=True)


def docker_run(*args: str) -> None:
    run(
        [
            "docker",
            "compose",
            "--profile",
            "gem5",
            "run",
            "--rm",
            "-v",
            "parsec-source:/parsec-source",
            *args,
        ]
    )


def docker_bash(script: str) -> None:
    docker_run("gem5-prebuilt", "bash", "-lc", script)


def ensure_docker() -> None:
    run(["docker", "compose", "version"])


def ensure_parsec_source() -> None:
    docker_bash(
        "set -e; "
        'if [ ! -d /parsec-source/.git ]; then '
        f"git clone {quote(PARSEC_REPO)} /parsec-source; "
        "else "
        "echo 'PARSEC source volume already exists.'; "
        "fi"
    )


def apply_compatibility_patches() -> None:
    docker_bash(
        "set -e; "
        "dedup_makefile=/parsec-source/pkgs/kernels/dedup/src/Makefile; "
        'if [ -f "$dedup_makefile" ] && ! grep -q -- "-fcommon" "$dedup_makefile"; then '
        "sed -i '/^CFLAGS += -Wall/a CFLAGS += -fcommon' \"$dedup_makefile\"; "
        "echo 'Applied dedup GCC -fcommon compatibility patch.'; "
        "else "
        "echo 'PARSEC compatibility patches already applied.'; "
        "fi"
    )


def ensure_input_archives(inputs: list[str], force_download: bool) -> None:
    force = "1" if force_download else "0"
    if any(input_name.startswith("sim") for input_name in inputs):
        docker_bash(
            "set -e; "
            f"force={force}; "
            "sentinel=/parsec-source/pkgs/apps/blackscholes/inputs/input_simsmall.tar; "
            'if [ "$force" = 1 ] || [ ! -f "$sentinel" ]; then '
            "cd /tmp; "
            "rm -f parsec-3.0-input-sim.tar.gz; "
            f"wget -O parsec-3.0-input-sim.tar.gz {quote(PARSEC_SIM_INPUTS_URL)}; "
            "tar -xzf parsec-3.0-input-sim.tar.gz -C /parsec-source --strip-components=1; "
            "else "
            "echo 'PARSEC simulator inputs already exist.'; "
            "fi"
        )

    if "native" in inputs:
        docker_bash(
            "set -e; "
            f"force={force}; "
            "sentinel=/parsec-source/pkgs/apps/blackscholes/inputs/input_native.tar; "
            'if [ "$force" = 1 ] || [ ! -f "$sentinel" ]; then '
            "cd /tmp; "
            "rm -f parsec-3.0-input-native.tar.gz; "
            f"wget -O parsec-3.0-input-native.tar.gz {quote(PARSEC_NATIVE_INPUTS_URL)}; "
            "tar -xzf parsec-3.0-input-native.tar.gz -C /parsec-source --strip-components=1; "
            "else "
            "echo 'PARSEC native inputs already exist.'; "
            "fi"
        )


def copy_runtime_libraries() -> None:
    runtime_dir = PARSEC_DIR / "lib"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    docker_bash(
        "set -e; "
        "src=/parsec-source/pkgs/libs/hooks/inst/amd64-linux.gcc-hooks/lib/libhooks.so.0.0.0; "
        "test -f \"$src\"; "
        "mkdir -p /workspace/benchmarks/parsec/lib; "
        "cp \"$src\" /workspace/benchmarks/parsec/lib/libhooks.so.0.0.0; "
        "cp \"$src\" /workspace/benchmarks/parsec/lib/libhooks.so.0; "
        "cp \"$src\" /workspace/benchmarks/parsec/lib/libhooks.so"
    )


def build_workload(workload: WorkloadSpec, force_build: bool) -> None:
    if not workload.build:
        print(f"Skipping non-buildable workload metadata entry: {workload.name}")
        return

    if workload.binary.exists() and not force_build:
        print(f"PARSEC binary already exists: {workload.binary}")
        return

    docker_run(
        "-e",
        "PARSEC_ROOT=/parsec-source",
        "gem5-prebuilt",
        "bash",
        "/workspace/benchmarks/parsec/build.sh",
        workload.name,
    )


def extract_input(workload: WorkloadSpec, input_name: str) -> None:
    if not workload.input_archives:
        input_dir = PARSEC_DIR / "inputs" / input_name / workload.name
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"{workload.name}/{input_name} does not require external input files.")
        return

    archive = f"{workload.package_root}/inputs/input_{input_name}.tar"
    extracted_dir = f"{workload.package_root}/inputs/input_{input_name}"
    destination = f"/workspace/benchmarks/parsec/inputs/{input_name}/{workload.name}"

    docker_bash(
        "set -e; "
        f"test -f {quote(archive)}; "
        f"rm -rf {quote(extracted_dir)}; "
        f"mkdir -p {quote(extracted_dir)}; "
        f"tar -xf {quote(archive)} -C {quote(extracted_dir)}; "
        f"mkdir -p {quote(destination)}; "
        f"cp -a {quote(extracted_dir)}/. {quote(destination)}/"
    )


def verify_workload(workload: WorkloadSpec, input_name: str) -> None:
    input_dir = PARSEC_DIR / "inputs" / input_name / workload.name
    missing = [path for path in [workload.binary, input_dir] if not path.exists()]
    if missing:
        missing_text = "\n".join(f"  {path}" for path in missing)
        raise RuntimeError(f"Missing expected PARSEC artifact(s):\n{missing_text}")

    if workload.input_archives and not any(input_dir.iterdir()):
        raise RuntimeError(f"Input directory is empty: {input_dir}")

    print()
    print(f"PARSEC workload ready: {workload.name}/{input_name}")
    print(f"  binary: {workload.binary}")
    print(f"  input:  {input_dir}")


def workload_names(value: str) -> list[str]:
    if value == "all":
        return list(WORKLOADS)

    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in WORKLOADS]
    if unknown:
        choices = ", ".join(["all", *sorted(WORKLOADS)])
        raise SystemExit(
            f"Unknown workload(s): {', '.join(unknown)}. Choices: {choices}"
        )
    return names


def input_names(value: str) -> list[str]:
    if value == "all":
        return list(DEFAULT_ALL_INPUTS)

    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in INPUT_ARCHIVES]
    if unknown:
        choices = ", ".join(["all", *sorted(INPUT_ARCHIVES)])
        raise SystemExit(f"Unknown input(s): {', '.join(unknown)}. Choices: {choices}")
    return names


def prepare_input(workload: WorkloadSpec, input_name: str) -> None:
    extract_input(workload, input_name)
    verify_workload(workload, input_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare local PARSEC artifacts for IntelliCore gem5 runs.",
    )
    parser.add_argument(
        "--workload",
        default="blackscholes",
        help=(
            "PARSEC workload to prepare, comma-separated list, or 'all'. "
            f"Known workloads: {', '.join(sorted(WORKLOADS))}."
        ),
    )
    parser.add_argument(
        "--input",
        default="simsmall",
        help=(
            "PARSEC input size to prepare, comma-separated list, or 'all'. "
            "'all' prepares simsmall, simmedium, and simlarge. "
            f"Known inputs: {', '.join(sorted(INPUT_ARCHIVES))}."
        ),
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Download and re-extract the PARSEC simulator input archive.",
    )
    parser.add_argument(
        "--force-build",
        action="store_true",
        help="Rebuild workloads even if local binaries already exist.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue preparing remaining workloads if one workload/input fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_workloads = [WORKLOADS[name] for name in workload_names(args.workload)]
    selected_inputs = input_names(args.input)

    ensure_docker()
    ensure_parsec_source()
    apply_compatibility_patches()
    ensure_input_archives(selected_inputs, args.force_download)
    copy_runtime_libraries()

    failures: list[str] = []
    for workload in selected_workloads:
        try:
            build_workload(workload, args.force_build)
        except subprocess.CalledProcessError as exc:
            label = f"{workload.name}/build"
            if not args.keep_going:
                raise SystemExit(f"Failed to prepare {label}: {exc}") from exc
            failures.append(f"{label}: {exc}")
            print()
            print(f"Failed to prepare {label}; continuing because --keep-going was set.")
            continue

        for input_name in selected_inputs:
            try:
                prepare_input(workload, input_name)
            except (RuntimeError, subprocess.CalledProcessError) as exc:
                label = f"{workload.name}/{input_name}"
                if not args.keep_going:
                    raise SystemExit(f"Failed to prepare {label}: {exc}") from exc
                failures.append(f"{label}: {exc}")
                print()
                print(f"Failed to prepare {label}; continuing because --keep-going was set.")

    if failures:
        print()
        print("PARSEC setup finished with failures:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
