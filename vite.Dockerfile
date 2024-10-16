FROM node:lts AS base

# Set working directory
WORKDIR /app

# Install node modules
COPY \
    "./package.json" \
    "./package-lock.json" \
    ./
RUN npm install && npm cache clean --force

CMD npm run dev

# Note: vite.config.js and src code will be mounted via volumes