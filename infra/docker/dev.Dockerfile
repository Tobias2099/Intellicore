FROM python:3.11-bookworm

ARG INSTALL_TORCH=true

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV GEM5_ROOT=/opt/gem5
ENV PYTHONPATH=/workspace/services/control-plane/src:/workspace/services/training/src

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
        git \
        libboost-all-dev \
        libgoogle-perftools-dev \
        libpng-dev \
        libprotobuf-dev \
        libprotoc-dev \
        m4 \
        ninja-build \
        pkg-config \
        protobuf-compiler \
        scons \
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
