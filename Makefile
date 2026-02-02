.PHONY: help build up down restart logs clean setup-ollama backup restore

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-ollama: ## View Ollama logs
	docker-compose logs -f ollama

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

setup-ollama: ## Pull Ollama model (run after first start)
	docker exec -it schedule-manager-ollama ollama pull llama3:8b

health: ## Check health of all services
	@echo "Backend health:"
	@curl -s http://localhost:8765/health | python -m json.tool || echo "Backend not responding"
	@echo "\nOllama health:"
	@curl -s http://localhost:11434/api/tags | python -m json.tool || echo "Ollama not responding"
	@echo "\nFrontend health:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:4200 || echo "Frontend not responding"

backup: ## Backup schedule data
	@mkdir -p backups
	docker run --rm -v schedule-manager_schedule-data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/schedule-data-$(shell date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "Backup created in ./backups/"

restore: ## Restore from latest backup (USE WITH CAUTION)
	@echo "This will restore from the latest backup and overwrite current data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker run --rm -v schedule-manager_schedule-data:/data -v $(PWD)/backups:/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/$$(ls -t backups/schedule-data-*.tar.gz | head -1) -C /"; \
		echo "Restore completed!"; \
	fi

dev-backend: ## Run backend in development mode (local)
	cd backend && poetry run uvicorn app.main:app --reload --port 8765

dev-frontend: ## Run frontend in development mode (local)
	cd frontend && npm start

dev-ollama: ## Start Ollama locally
	ollama serve
