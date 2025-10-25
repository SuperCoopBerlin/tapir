# Minimal Dockerfile for a Python 3.13 devcontainer with Poetry installed.
FROM python:3.13-slim

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/root/.local/bin:$PATH \
    POETRY_HOME=/opt/poetry

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
       zlib1g-dev \
       libxml2-dev \
       libxslt1-dev \
       libffi-dev \
       libssl-dev \
       libcairo2 \
       libpango-1.0-0 \
       shared-mime-info \
       poppler-utils \
       fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (official installer)
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry \
    && chmod -R a+rx /opt/poetry \
    && chmod a+rx /usr/local/bin/poetry \
    && poetry --version

# Set poetry to not create virtualenvs by default (so dependencies go into the container python)
RUN poetry config virtualenvs.create false

# Create a non-root user to match VS Code's default "vscode" username
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
    && mkdir -p /workspace && chown ${USERNAME}:${USERNAME} /workspace

WORKDIR /workspace

# Switch to non-root user
USER ${USERNAME}

# By default don't run anything - postCreateCommand will run when container is created
CMD [ "bash" ]