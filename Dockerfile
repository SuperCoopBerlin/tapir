FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt update
RUN apt install libldap2-dev libsasl2-dev

RUN pip install poetry
RUN poetry install


