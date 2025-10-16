FROM node:20-alpine

WORKDIR /app

# Instalar dependencias
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el resto del código
COPY . .

# Exponer el puerto de desarrollo
EXPOSE 5173

CMD ["npm", "run", "dev"]
