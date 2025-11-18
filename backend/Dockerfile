
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Asegurar que el archivo de datos esté disponible
RUN mkdir -p /app/data && \
    if [ -f data/Lista_Punto_Venta.xlsx ]; then cp data/Lista_Punto_Venta.xlsx /app/data/; fi
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
