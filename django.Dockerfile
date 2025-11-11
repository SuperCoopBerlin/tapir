FROM python:3.13
ENV PYTHONUNBUFFERED=1

ARG UID=1000
ARG GID=$UID
ARG USERNAME=noroot

RUN apt-get update -y  \
    && apt-get --no-install-recommends install -y  \
        gettext  \
        libldap2-dev  \
        libsasl2-dev  \
        postgresql-client  \
        postgresql-client-common  \
        python3-poetry  \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$UID" -ne 0 ]; then  \
      addgroup --gid "$GID" "$USERNAME"  \
      && adduser --disabled-password --gecos "" --uid "$UID" --gid "$GID" "$USERNAME";  \
    fi

WORKDIR /app
COPY --chown=$UID:$GID . /app
# change ownership of the app dir itself
RUN chown $UID:$GID /app

USER ${UID}:${GID}

RUN poetry config virtualenvs.in-project true

CMD bash -c "poetry install && poetry run python manage.py compilemessages --ignore '.venv' && poetry run python manage.py runserver_plus 0.0.0.0:80"
