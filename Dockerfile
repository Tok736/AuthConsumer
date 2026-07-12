FROM python:3.12.13-alpine3.24

WORKDIR /app/

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY resources resources
COPY config.json config.json
COPY src src

ENTRYPOINT ["sh", "resources/startup.sh"]
