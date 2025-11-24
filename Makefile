SHELL := /bin/bash

.DEFAULT_GOAL := up

help:
	@echo ""
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Targets:"
	@echo "  up           Build images if necessary and start all services in detached mode."
	@echo "  down         Stop and remove all services, networks."
	@echo "  build        Build or rebuild all service images."
	@echo "  logs         Follow logs for all services."
	@echo "  logs-backend Follow logs specifically for the backend service."
	@echo "  logs-frontend Follow logs specifically for the frontend service."
# 	@echo "  logs-ollama  Follow logs specifically for the ollama service."
	@echo "  restart      Restart all services."
	@echo "  pull         Pull the latest base images used by services."
	@echo "  ps           List running containers for this project."
	@echo "  clean        Stop and remove containers, networks, AND volumes (USE WITH CAUTION)."
	@echo "  help         Show this help message."
	@echo ""


up:
	@echo "Starting services..."
	docker compose up --build -d
	@echo "Services started. Frontend available at http://localhost:3000"

down:
	@echo "Stopping services..."
	docker compose down
	@echo "Services stopped."

build:
	@echo "Building images..."
	docker compose build
	@echo "Images built."

logs:
	@echo "Following logs for all services... (Press Ctrl+C to stop)"
	docker compose logs -f

logs-backend:
	@echo "Following logs for backend service... (Press Ctrl+C to stop)"
	docker compose logs -f backend

logs-frontend:
	@echo "Following logs for frontend service... (Press Ctrl+C to stop)"
	docker compose logs -f frontend

###
# logs-ollama:
# 	@echo "Following logs for ollama service... (Press Ctrl+C to stop)"
# 	docker compose logs -f ollama
###

restart: down up

pull:
	@echo "Pulling latest base images..."
	docker compose pull
	@echo "Images pulled."

ps:
	@echo "Listing project containers..."
	docker compose ps

clean:
	@echo "WARNING: This will stop containers AND remove associated volumes (including downloaded Ollama models)!"
	@read -p "Are you sure you want to continue? (y/N) " confirm && [[ $$confirm == [yY] || $$confirm == [yY][eE][sS] ]] || exit 1
	docker compose down --volumes
	@echo "Containers and volumes removed."

.PHONY: help up down build logs logs-backend logs-frontend restart pull ps clean