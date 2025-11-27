FROM node:20

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# Für dev: Source kommt per Volume-Mount
CMD ["npm", "run", "dev"]
