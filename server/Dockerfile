FROM python:3.10-slim

WORKDIR /app

# Instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto del servidor
EXPOSE 5000

# Ejecutar el servidor Uvicorn con Socket.io
CMD ["python", "-m", "app.main"]