# Minimal Dockerfile for a Python 3.13 devcontainer with Poetry installed.
FROM python:3.13-slim

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/root/.local/bin:$PATH

# Install system dependencies commonly required for building packages used in this repo
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       git \
       ca-certificates \
       gcc \
       libpq-dev \
       libjpeg-dev \
       libldap2-dev \
       libsasl2-dev \
       zlib1g-dev \
       libxml2-dev \
       libxslt1-dev \
       libffi-dev \
       libssl-dev \
       libcairo2 \
       libpango-1.0-0 \
       python3-poetry \
       shared-mime-info \
       poppler-utils \
       fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to match VS Code's default "vscode" username
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
    && mkdir -p /workspace && chown ${USERNAME}:${USERNAME} /workspace

WORKDIR /workspace

# Switch to non-root user
USER ${USERNAME}

# By default don't run anything - postCreateCommand will run when container is created
CMD [ "bash" ]