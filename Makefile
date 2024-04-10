# Makefile for Anterion project

build-open-devin:
	@echo 1. Building OpenDevin...
	@cd ./OpenDevin && make build
	@cd ./OpenDevin && make setup-config

build-swe-agent:
	@echo 2. Building SWE-agent...
	@cd ./SWE-agent && ./setup.sh

build-microservice:
	@echo 3. Building microservice...
	@cd ./microservice && pip install -r requirements.txt

run-frontend:
	@cd ./OpenDevin && make start-frontend

run-backend:
	@cd ./microservice && python -m uvicorn app:app --port 3000