FROM node:lts AS base

# Set working directory
WORKDIR /app

# Install node modules
COPY \
    "./package.json" \
    "./package-lock.json" \
    ./
RUN npm install && npm cache clean --force

RUN apt-get update -y && apt-get --no-install-recommends install -y default-jre
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64/

CMD npm run dev

# Note: vite.config.js and src code will be mounted via volumes