# Use uma imagem oficial do Python como base
FROM python:3.11-alpine

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos para o container
COPY requirements.txt .

# Instala as dependências da aplicação
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação para o container
COPY src/  /app/src/

# Expõe a porta que a aplicação usará
EXPOSE 8000

# Define o comando para rodar a aplicação
CMD ["python", "src/app.py"]