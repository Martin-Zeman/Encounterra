FROM python:3.10
WORKDIR /app
COPY aggregate_results.py .
COPY pyproject.toml .
COPY poetry.lock .

# Upgraded from 1.5.1 due to https://github.com/python-poetry/poetry/issues/7611
ARG POETRY_VERSION=1.6.1
RUN pip install --upgrade pip \
 && pip install poetry==${POETRY_VERSION} \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --without dev

CMD ["python3", "./aggregate_results.py"]
