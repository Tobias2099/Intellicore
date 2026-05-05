FROM python:3.11-bookworm

ARG INSTALL_TORCH=false
ARG GEM5_REPO=https://gem5.googlesource.com/public/gem5
ARG GEM5_REF=
ARG GEM5_CLONE_DEPTH=1
ARG GEM5_ISA=X86
ARG GEM5_BUILD_VARIANT=gem5.opt
ARG GEM5_BUILD_JOBS=2

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV GEM5_ROOT=/opt/gem5
ENV PYTHONPATH=/workspace/services/control-plane/src:/workspace/services/training/src
ENV PATH=/opt/gem5/build/${GEM5_ISA}:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        clang-format \
        cmake \
        curl \
        doxygen \
        g++ \
        gcc \
        gdb \
        git \
        libboost-all-dev \
        libcapstone-dev \
        libelf-dev \
        libgoogle-perftools-dev \
        libhdf5-serial-dev \
        libpng-dev \
        libprotobuf-dev \
        libprotoc-dev \
        m4 \
        mypy \
        ninja-build \
        pkg-config \
        protobuf-compiler \
        python3-dev \
        python3-pydot \
        python3-tk \
        python3-venv \
        scons \
        wget \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements-dev.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r requirements-dev.txt \
    && if [ "$INSTALL_TORCH" = "true" ]; then \
        python -m pip install --index-url https://download.pytorch.org/whl/cpu torch; \
    fi

RUN git clone --depth "$GEM5_CLONE_DEPTH" "$GEM5_REPO" "$GEM5_ROOT" \
    && if [ -n "$GEM5_REF" ]; then \
        git -C "$GEM5_ROOT" fetch --depth "$GEM5_CLONE_DEPTH" origin "$GEM5_REF" \
        && git -C "$GEM5_ROOT" checkout FETCH_HEAD; \
    fi \
    && if [ -f "$GEM5_ROOT/requirements.txt" ]; then \
        python -m pip install -r "$GEM5_ROOT/requirements.txt"; \
    fi \
    && cd "$GEM5_ROOT" \
    && scons "build/$GEM5_ISA/$GEM5_BUILD_VARIANT" -j"$GEM5_BUILD_JOBS"

RUN test -x "$GEM5_ROOT/build/$GEM5_ISA/$GEM5_BUILD_VARIANT" \
    && "$GEM5_ROOT/build/$GEM5_ISA/$GEM5_BUILD_VARIANT" --help >/dev/null

COPY . .

CMD ["bash"]
