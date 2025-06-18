# Usa uma imagem oficial do Python 3.11
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos locais para dentro do container
COPY . .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta (não necessário para bots, mas boa prática)
EXPOSE 8080

# Comando padrão para executar o bot
CMD ["python", "bot_bom_dia.py"]