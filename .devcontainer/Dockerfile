# Minimal Dockerfile for a Python 3.13 devcontainer with Poetry installed.
FROM python:3.13

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/root/.local/bin:$PATH

# Install system dependencies commonly required for building packages used in this repo
RUN apt-get update \
    && apt-get --no-install-recommends install -y  \
        gettext  \
        libldap2-dev  \
        libsasl2-dev  \
        postgresql-client  \
        postgresql-client-common \
        python3-poetry \
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