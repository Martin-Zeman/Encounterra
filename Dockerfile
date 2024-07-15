#FROM public.ecr.aws/lambda/python:3.11-arm64
#WORKDIR ${LAMBDA_TASK_ROOT}
#COPY . .
#
## Upgraded from 1.5.1 due to https://github.com/python-poetry/poetry/issues/7611
#ARG POETRY_VERSION=1.6.1
#RUN pip install --upgrade pip \
# && pip install poetry==${POETRY_VERSION} \
# && poetry config virtualenvs.create false \
# && poetry install --no-interaction --without dev
#
#CMD ["core_entrypoint.handler"]


# Use multiarch/qemu-user-static to install QEMU
#FROM multiarch/qemu-user-static as qemu
#FROM public.ecr.aws/lambda/python:3.11-arm64
#
## Copy QEMU static binary
#COPY --from=qemu /usr/bin/qemu-aarch64-static /usr/bin/
#
## Set the working directory
#WORKDIR ${LAMBDA_TASK_ROOT}
#
## Copy all files to the working directory
#COPY . .
#
## Upgrade pip and install poetry
#ARG POETRY_VERSION=1.6.1
#RUN pip install --upgrade pip \
# && pip install poetry==${POETRY_VERSION} \
# && poetry config virtualenvs.create false \
# && poetry install --no-interaction --without dev
#
## Set environment variables for Numba cache
#ENV NUMBA_CACHE_DIR=${LAMBDA_TASK_ROOT}/numba_cache
#
## Create the Numba cache directory
#RUN mkdir -p ${NUMBA_CACHE_DIR}
#
## Install pytest and pytest-xdist, run tests to generate Numba cache, then uninstall them and remove the test directory
#RUN pip install pytest pytest-xdist \
# && pytest -n 6 -m "not mcts and not slow" ./simulator/test \
# && pip uninstall -y pytest pytest-xdist \
# && rm -rf /root/.cache/pip \
# && rm -rf ./simulator/test
#
## Set the command to run the Lambda function
#CMD ["core_entrypoint.handler"]



# Stage 1: Build and generate Numba cache
FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.11-arm64 AS cache_builder
WORKDIR ${LAMBDA_TASK_ROOT}
COPY . .

ARG POETRY_VERSION=1.6.1
RUN pip install --upgrade pip \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction

# Set Numba cache directory
ENV NUMBA_CACHE_DIR=/tmp/numba_cache
RUN mkdir -p ${NUMBA_CACHE_DIR}

# Run tests to generate Numba cache, then uninstall them and remove the test directory
RUN pytest -n 7 -m "not mcts and not slow" ./simulator/test || true

# Stage 2: Final image
FROM public.ecr.aws/lambda/python:3.11-arm64
WORKDIR ${LAMBDA_TASK_ROOT}
COPY . .

ARG POETRY_VERSION=1.6.1
RUN pip install --upgrade pip \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --without dev \
    && rm -rf ./simulator/test

# Set Numba cache directory
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

# Copy the Numba cache from the builder stage
COPY --from=cache_builder /tmp/numba_cache /tmp/numba_cache

CMD ["core_entrypoint.handler"]

