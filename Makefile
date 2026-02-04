.PHONY: help build up down logs shell migrate superuser clean local-setup local-db

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

logs-web: ## Show logs for web service
	docker-compose logs -f web

logs-celery: ## Show logs for celery service
	docker-compose logs -f celery

shell: ## Open Django shell
	docker-compose exec web python manage.py shell

dbshell: ## Open database shell
	docker-compose exec db psql -U postgres -d django_fullstack

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose exec web python manage.py makemigrations

superuser: ## Create Django superuser
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec web python manage.py collectstatic --noinput

check-celery: ## Check Celery and Redis connectivity
	docker-compose exec web python scripts/check_celery_redis.py

restart-web: ## Restart web service
	docker-compose restart web

restart-celery: ## Restart celery service
	docker-compose restart celery

clean: ## Clean up Docker containers and images
	docker-compose down -v --rmi all

status: ## Show status of all services
	docker-compose ps

flower: ## Open Flower UI (Celery monitoring)
	@echo "Flower UI available at: http://localhost:5555"

dev: ## Quick development setup
	@echo "Setting up development environment..."
	docker-compose build
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 10
	docker-compose exec web python manage.py migrate
	docker-compose exec web python manage.py collectstatic --noinput
	@echo ""
	@echo "🎉 Development environment is ready!"
	@echo "📱 Web app: http://localhost:8000"
	@echo "🌸 Flower: http://localhost:5555"
	@echo "📊 Database: localhost:5432"
	@echo "🔴 Redis: localhost:6379"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs-web     - View web app logs"
	@echo "  make logs-celery  - View Celery logs"
	@echo "  make shell        - Open Django shell"
	@echo "  make superuser    - Create admin user"

# Local development commands (for local PostgreSQL)
local-setup: ## Setup local PostgreSQL environment
	@echo "Setting up local PostgreSQL development..."
	@if [ ! -f .env ]; then cp .env.local .env; echo "Created .env from .env.local"; fi
	@echo "Make sure PostgreSQL is running on localhost:5432"
	@echo "Run: make local-migrate"

local-migrate: ## Run migrations for local PostgreSQL
	python manage.py migrate

local-makemigrations: ## Create migrations for local development
	python manage.py makemigrations

local-superuser: ## Create superuser for local development
	python manage.py createsuperuser

local-shell: ## Open Django shell for local development
	python manage.py shell

local-dbshell: ## Open local PostgreSQL shell
	psql -h localhost -U postgres -d django_fullstack

local-run: ## Run development server locally
	python manage.py runserver

local-check: ## Check local PostgreSQL connection
	@echo "Checking PostgreSQL connection..."
	@pg_isready -h localhost -p 5432 && echo "✅ PostgreSQL is running" || echo "❌ PostgreSQL is not running"
