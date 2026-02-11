.PHONY: lint format health

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
