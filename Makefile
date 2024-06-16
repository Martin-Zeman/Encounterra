DOCKER = docker
ACCOUNT_NR = ${AWS_ACCOUNT_NR}

API_VERSION := $(shell cat VERSION)
GIT_STATUS := $(shell git status --porcelain)
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-parse --short HEAD)
GIT_BRANCH_SANITIZED := $(subst /,-,${GIT_BRANCH})

DOCKER_CONTAINER = encounterra-core
DOCKER_ECS_CONTAINER = encounterra-core-ecs
DOCKER_SANDBOX_REMOTE = ${ACCOUNT_NR}.dkr.ecr.eu-west-1.amazonaws.com

docker.build:
	@echo ""
	@echo "Building container..."
	aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${DOCKER_SANDBOX_REMOTE}
	docker build -t ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} --build-arg APP_VERSION=${GIT_COMMIT} --network host .
	docker tag ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_CONTAINER}:latest
	@if [ -z "${GIT_STATUS}" ]; then \
        docker tag ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_CONTAINER}:${GIT_COMMIT}; \
        docker tag ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_SANDBOX_REMOTE}/${DOCKER_CONTAINER}:${GIT_COMMIT}; \
    fi
	@echo ""
	@echo "*"
	@echo "*"
	@echo "* Docker container built"
	@echo "*"
	@echo "*  tagged: ${FONT_BOLD}${DOCKER_CONTAINER}:latest${FONT_NORMAL}"
	@echo "*  tagged: ${FONT_BOLD}${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED}${FONT_NORMAL}"
	@if [ -z "${GIT_STATUS}" ]; then \
		docker tag ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_CONTAINER}:${GIT_COMMIT}; \
		docker tag ${DOCKER_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_SANDBOX_REMOTE}/${DOCKER_CONTAINER}:${GIT_COMMIT}; \
	else \
		echo "Workspace is dirty!"; \
	fi
	@echo "*"
	@echo "*"
	@if [ -z "${GIT_STATUS}" ]; then \
		echo "* short commit nr: ${GIT_COMMIT}"; \
	fi

docker.build_ecs:
	@echo ""
	@echo "Building ECS Core container..."
	aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${DOCKER_SANDBOX_REMOTE}
	docker build -t ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} --build-arg APP_VERSION=${GIT_COMMIT} --network host -f Dockerfile_ecs .
	docker tag ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_ECS_CONTAINER}:latest
	@if [ -z "${GIT_STATUS}" ]; then \
        docker tag ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}; \
        docker tag ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_SANDBOX_REMOTE}/${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}; \
    fi
	@echo ""
	@echo "*"
	@echo "*"
	@echo "* Docker container built"
	@echo "*"
	@echo "*  tagged: ${FONT_BOLD}${DOCKER_ECS_CONTAINER}:latest${FONT_NORMAL}"
	@echo "*  tagged: ${FONT_BOLD}${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED}${FONT_NORMAL}"
	@if [ -z "${GIT_STATUS}" ]; then \
		docker tag ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}; \
		docker tag ${DOCKER_ECS_CONTAINER}:${GIT_BRANCH_SANITIZED} ${DOCKER_SANDBOX_REMOTE}/${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}; \
	else \
		echo "Workspace is dirty!"; \
	fi
	@echo "*"
	@echo "*"
	@if [ -z "${GIT_STATUS}" ]; then \
		echo "* short commit nr: ${GIT_COMMIT}"; \
	fi

docker.push:
	@echo ""
	@echo "... pushing containers..."
	@echo ""
	@if [ ! -z "${GIT_STATUS}" ]; then \
        echo "Workspace is dirty, cannot push!"; \
        echo ""; \
        exit 1; \
    fi
	docker push ${DOCKER_SANDBOX_REMOTE}/${DOCKER_CONTAINER}:${GIT_COMMIT}

	@echo ""
	@echo "*"
	@echo "*"
	@echo "* Container pushed"
	@echo "*"
	@echo "*  pushed: ${DOCKER_SANDBOX_REMOTE}/${DOCKER_CONTAINER}:${GIT_COMMIT}"
	@echo "* "
	@if [ -z "${GIT_STATUS}" ]; then \
        echo "* short commit nr: ${GIT_COMMIT}"; \
    fi
	@echo "*"
	@echo ""

docker.push_ecs:
	@echo ""
	@echo "... pushing ECS Core container..."
	@echo ""
	@if [ ! -z "${GIT_STATUS}" ]; then \
        echo "Workspace is dirty, cannot push!"; \
        echo ""; \
        exit 1; \
    fi
	docker push ${DOCKER_SANDBOX_REMOTE}/${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}

	@echo ""
	@echo "*"
	@echo "*"
	@echo "* ECS Core Container pushed"
	@echo "*"
	@echo "*  pushed: ${DOCKER_SANDBOX_REMOTE}/${DOCKER_ECS_CONTAINER}:${GIT_COMMIT}"
	@echo "* "
	@if [ -z "${GIT_STATUS}" ]; then \
        echo "* short commit nr: ${GIT_COMMIT}"; \
    fi
	@echo "*"
	@echo ""
