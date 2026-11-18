FROM node:20-alpine

WORKDIR /app

# Dependencias primero: Docker reutiliza esta capa si package*.json no cambia
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src
COPY openapi.yaml ./

# Usuario sin privilegios (viene incluido en la imagen de Node)
USER node

EXPOSE 3000

CMD ["node", "src/server.js"]
