
FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    nano \
    vim \
    git \
    ca-certificates \
    sudo \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh \
    -o /tmp/oci-install.sh \
    && bash /tmp/oci-install.sh --accept-all-defaults \
    && rm /tmp/oci-install.sh

ENV PATH="/root/bin:/root/lib/oracle-cli/bin:/root/.local/bin:${PATH}"

ENV OCI_CLI_CONFIG_FILE="/workspace/OCI/.oci/config"

COPY telegram-gateway/bin/telly /usr/local/bin/telly
RUN chmod +x /usr/local/bin/telly

WORKDIR /workspace

RUN mkdir -p /workspace/OCI

CMD ["/bin/bash"]
