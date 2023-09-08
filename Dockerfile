FROM python:3.10
WORKDIR /app
COPY . .

# Upgraded from 1.5.1 due to https://github.com/python-poetry/poetry/issues/7611
ARG POETRY_VERSION=1.6.1
RUN pip install --upgrade pip \
 && pip install poetry==${POETRY_VERSION} \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --without dev

ENTRYPOINT ["python", "batch_entrypoint.py"]
