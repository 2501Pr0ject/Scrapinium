# Makefile pour Scrapinium

.PHONY: help install dev build test clean docker-dev docker-prod

# Variables
PYTHON = python3
PIP = pip3
POETRY = poetry

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	$(POETRY) install
	$(POETRY) run playwright install chromium

dev: ## Lance l'application en mode développement
	$(POETRY) run python -m scrapinium.main

build: ## Build l'image Docker
	docker build -t scrapinium:latest .

test: ## Lance les tests
	$(POETRY) run pytest tests/ -v

lint: ## Lance le linting
	$(POETRY) run ruff check src/
	$(POETRY) run ruff format --check src/

format: ## Formate le code
	$(POETRY) run ruff format src/

clean: ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

docker-dev: ## Lance l'environnement de développement avec Docker
	docker-compose up --build

docker-prod: ## Lance l'environnement de production avec Docker
	docker-compose -f docker-compose.prod.yml up -d

docker-down: ## Arrête les conteneurs Docker
	docker-compose down
	docker-compose -f docker-compose.prod.yml down

docker-logs: ## Affiche les logs Docker
	docker-compose logs -f

setup-ollama: ## Configure Ollama avec le modèle par défaut
	docker exec -it scrapinium-ollama-1 ollama pull llama3.1:8b

health: ## Vérifie la santé de l'application
	curl -f http://localhost:8000/health || echo "Service non accessible"

backup-db: ## Sauvegarde la base de données
	docker exec scrapinium-postgres-1 pg_dump -U scrapinium scrapinium > backup_$(shell date +%Y%m%d_%H%M%S).sql

init-db: ## Initialise la base de données
	$(POETRY) run python -c "from scrapinium.config import init_database; init_database()"

shell: ## Lance un shell Python avec le contexte Scrapinium
	$(POETRY) run python -c "from scrapinium import *; import IPython; IPython.start_ipython()"