DOCKER = docker
ACCOUNT_NR = ${AWS_ACCOUNT_NR}

API_VERSION := $(shell cat VERSION)
GIT_STATUS := $(shell git status --porcelain)
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-parse --short HEAD)
GIT_BRANCH_SANITIZED := $(subst /,-,${GIT_BRANCH})

DOCKER_CONTAINER = encounterra_backend
DOCKER_SANDBOX_REMOTE = ${ACCOUNT_NR}.dkr.ecr.eu-west-1.amazonaws.com

#$ aws configure
#AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
#AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
#Default region name [None]: us-west-2
#Default output format [None]: json
#$ aws configure set aws_session_token fcZib3JpZ2luX2IQoJb3JpZ2luX2IQoJb3JpZ2luX2IQoJb3JpZ2luX2IQoJb3JpZVERYLONGSTRINGEXAMPLE

# IQoJb3JpZ2luX2VjEDkaCWV1LXdlc3QtMSJIMEYCIQD2TRf4RWHlSWcocfk9BmgmM38UPvjCg6FwnwEvhDUMBQIhAImaEwq0XlLNxxORXxwPDZj7BIfkl2QIUDEYCXmxLviKKvoCCPL//////////wEQABoMMjk3OTQ1MzA3NTgwIgwlgetdcVeVyZf7G70qzgLU0uUkEh7G4rH9HnTKivwc8oGOeMqCT+v3vM3kiP3Bo0eMJMDZzfcik9nBEzxoY83T+n+QUaRFEdUzp/hb2JXeJt+gHYEyRVtCwA8Q5wi7gH001llY9uXxB6EO5Y5n75CqMBPe+llU/4ez3tt3G1ZIPJWXDIf9My3EwK7/OAFfIC5BEVTgoRuLvrN23n4pjCZS4N1hZbGsgjEe49/aAjgkgOXokDIyfWJ2Eo43Ds0mkxBB7WOjQzC3kKB/6eB6CI8N9Q+OyGSOYVaBatiZZgv7NZ3FDYe0jqz0R0ESPgWkvG22HmVnnm2egadAtTekAWtBw9gET3V6RI9MVdlZFbw4YcKQ7ZVaW/DDkRFMNKXSUBJTaTzs1JwrX+inAZ5hU+aAnnePsTLEhkef/Kj4FRsOseHPiKEBMOZlt0jmSvVP6EuwwlFJn3n8/VQmY0bUMO3Vk6cGOqYBmTO69H/ne5JcoOfcOA3/dyno1aU3T2fyg4m7hOiBKFFH8VzKmJDU+YSS4k76QN+eqh+1RvEmhocDeEAc5SAfQPeOREZAI8eACESruHtvhefENYGDrH4zcbp6g4gMAHZd4RtNr+ZisbqDRtQxPZEUcVqhfeGBAjBFXYrt2uIOIf6MzfdagKfpVi02CAKVAkxQpu+rPQZwcu9sK6obh4kh1e2Pgw8/Qg==
# SSO Start URL https://d-93675b97f6.awsapps.com/start#
# SSO Region eu-west-1

# aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 728464280382.dkr.ecr.eu-west-1.amazonaws.com
# docker build -t encounterra_backend .
# docker tag encounterra_backend:latest 728464280382.dkr.ecr.eu-west-1.amazonaws.com/encounterra_backend:latest
# docker push 728464280382.dkr.ecr.eu-west-1.amazonaws.com/encounterra_backend:latest

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

docker.push:
	@echo ""
	@echo "... pushing containers..."
	@echo ""
	@if [ ! -z "${GIT_STATUS}" ]; then \
        echo "Workspace is dirty, cannot push!"; \
        echo ""; \
        exit 1; \
    fi
    # docker push 728464280382.dkr.ecr.eu-west-1.amazonaws.com/encounterra_backend:latest
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
