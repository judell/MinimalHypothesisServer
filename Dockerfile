FROM python:3.7-alpine

WORKDIR /MinimalHypothesisService

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir psycopg2 \
    && pip install --no-cache-dir pyramid \
    && apk del --no-cache .build-deps

COPY ./service.py .

EXPOSE 4000
CMD ["python3", "service.py"]

