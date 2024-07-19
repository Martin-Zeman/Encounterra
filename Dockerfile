# Stage 1: Build and compile Numba functions
FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.11-arm64 AS numba_stage

WORKDIR ${LAMBDA_TASK_ROOT}
COPY . .

ARG POETRY_VERSION=1.6.1

RUN #yum update -y && yum groupinstall -y "Development Tools"
RUN yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    make \
    && yum clean all && rm -rf /var/cache/yum

RUN pip install --upgrade pip \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --without dev

RUN python numba_functions.py

# Stage 2: Final image
FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.11-arm64

WORKDIR ${LAMBDA_TASK_ROOT}
COPY . .

ARG POETRY_VERSION=1.6.1

RUN pip install --upgrade pip \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --without dev

# Copy the compiled .so files from the build stage
COPY --from=numba_stage ${LAMBDA_TASK_ROOT}/numba_functions.so ${LAMBDA_TASK_ROOT}/

CMD ["core_entrypoint.handler"]
