# Generic single-database configuration.

## Migration Commands (using Poetry)

Always run these commands from the `backend/` directory.

### Upgrade

Apply all pending migrations:

```bash
poetry run alembic upgrade head
```

### Downgrade

Roll back migrations:

- **One step:** `poetry run alembic downgrade -1`
- **To a specific revision:** `poetry run alembic downgrade <revision_id>`
- **To the very beginning:** `poetry run alembic downgrade base`

### Create a New Migration

Generate a new migration script based on model changes:

```bash
poetry run alembic revision --autogenerate -m "description of changes"
```
