FROM public.ecr.aws/lambda/python:3.11-arm64
WORKDIR ${LAMBDA_TASK_ROOT}
COPY aggregate_results.py .
COPY pyproject.toml .
COPY poetry.lock .

# Upgraded from 1.5.1 due to https://github.com/python-poetry/poetry/issues/7611
ARG POETRY_VERSION=1.6.1
RUN pip install --upgrade pip \
 && pip install poetry==${POETRY_VERSION} \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --without dev

CMD ["aggregate_results.handler"]