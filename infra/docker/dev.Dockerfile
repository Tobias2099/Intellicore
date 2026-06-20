FROM python:3.11-bookworm

ARG INSTALL_TORCH=true

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV GEM5_ROOT=/workspace/gem5
ENV GEM5_ISA=X86
ENV GEM5_BUILD_VARIANT=gem5.opt
ENV PYTHONPATH=/workspace/services/control-plane/src:/workspace/services/training/src
ENV PATH=/workspace/gem5/build/X86:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        doxygen \
        g++ \
        gcc \
        gdb \
        gettext \
        git \
        libboost-all-dev \
        libcapstone-dev \
        libelf-dev \
        libgoogle-perftools-dev \
        libhdf5-serial-dev \
        libxi-dev \
        libxmu-dev \
        lld \
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

COPY . .

CMD ["bash"]
