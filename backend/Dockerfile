
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Asegurar que el archivo de datos esté disponible en /app/app/data
RUN mkdir -p /app/app/data && \
    if [ -f data/Lista_Punto_Venta.xlsx ]; then cp data/Lista_Punto_Venta.xlsx /app/app/data/; fi
EXPOSE 8000
# Usar el puerto que Railway asigna dinámicamente (variable $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
