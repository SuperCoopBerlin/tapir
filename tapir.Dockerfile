FROM node:lts AS vite-build

# Set working directory
WORKDIR /app

# Install node modules
COPY . /app
RUN npm install

RUN apt-get update -y
RUN apt-get --no-install-recommends install -y default-jre
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64/

RUN npm install
RUN npm run build

FROM python:3.13
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN apt-get update -y
RUN apt-get --no-install-recommends install -y  \
    gettext  \
    libldap2-dev  \
    libsasl2-dev  \
    postgresql-client  \
    postgresql-client-common
RUN rm -rf /var/lib/apt/lists/*

RUN pip install poetry 
RUN poetry install
RUN poetry run python manage.py compilemessages

# fetching the vite build files
COPY --from=vite-build /app/dist /app/dist

