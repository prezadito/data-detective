## Backend Development Setup

```bash
cd backend

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run server
uvicorn app.main:app --reload
```