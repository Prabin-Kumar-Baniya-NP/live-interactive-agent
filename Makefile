.PHONY: lint format health seed

lint:
	cd backend && python3 -m poetry run ruff check .
	cd backend && python3 -m poetry run black --check .
	cd agent-runtime && python3 -m poetry run ruff check .
	cd agent-runtime && python3 -m poetry run black --check .
	pnpm --filter frontend lint

format:
	cd backend && python3 -m poetry run ruff check . --fix
	cd backend && python3 -m poetry run black .
	cd agent-runtime && python3 -m poetry run ruff check . --fix
	cd agent-runtime && python3 -m poetry run black .
	pnpm --filter frontend format

health:
	bash ./scripts/health-check.sh

seed:
	cd backend && python3 -m poetry run python scripts/seed.py

api:
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

agent-dev:
	cd agent-runtime && poetry run python main.py dev

agent-install:
	cd agent-runtime && poetry install

agent-lint:
	cd agent-runtime && poetry run ruff check .

agent-format:
	cd agent-runtime && poetry run black .
	cd agent-runtime && poetry run ruff check . --fix

frontend-dev:
	pnpm --filter frontend dev

frontend-build:
	pnpm --filter frontend build

frontend-lint:
	pnpm --filter frontend lint

frontend-format:
	pnpm --filter frontend format
