FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    GASTOS_DB_PATH=/data/gastos.db

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# Usuário sem privilégios; /data guarda o SQLite e deve ser montado como volume persistente.
RUN useradd --create-home --uid 10001 gastos && mkdir /data && chown gastos /data
USER gastos
VOLUME ["/data"]

EXPOSE 8000
CMD ["python", "-m", "app"]
