# Use uma imagem oficial do Node.js como base
FROM node:21-alpine

# Define o diretório de trabalho no container
WORKDIR /app

# Copia o arquivo package.json (e possivelmente package-lock.json) para o container
COPY package*.json ./

# Instala as dependências da aplicação
RUN npm install --production

# Copia o código da aplicação para o container
COPY . .

# Expõe a porta que a aplicação usará
EXPOSE 8000

# Define o comando para rodar a aplicação
CMD ["node", "app.js"]
