FROM alpine:3.18 as alpine_stage
WORKDIR /opt/backend
COPY . .

FROM python:3.10-alpine3.18

HEALTHCHECK --interval=20s --timeout=20s --start-period=30s \
    CMD curl -f --insecure https://localhost:6000/healthcheck || exit 1

RUN addgroup -S terra && adduser -S terra -G terra

WORKDIR /opt/backend

ENV PYCURL_SSL_LIBRARY=openssl
ARG POETRY_VERSION=1.5.1
COPY poetry.lock pyproject.toml ./
RUN apk update --no-cache \
 && apk add --no-cache --virtual .build-deps build-base openssl openssl-dev \
 && pip install --upgrade pip \
 && pip install poetry==${POETRY_VERSION} \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-dev \
 && mkdir -p ssl \
 && openssl req -subj '/CN=localhost' -x509 -newkey rsa:4096 -nodes -keyout ssl/key.pem -out ssl/cert.pem -days 40000 \
 && apk del --no-cache .build-deps

COPY --chown=terra:terra --from=alpine_stage /opt/backend .

ARG APP_VERSION=unknown
RUN echo "$APP_VERSION" > VERSION

CMD [ "gunicorn", "--config", "gunicorn.conf.py", "--keyfile", "ssl/key.pem", "--certfile", "ssl/cert.pem", "entrypoint:app"]
