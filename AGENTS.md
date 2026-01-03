# Repository Guidelines

## Project Structure & Module Organization
- `backend/` contains the Django project (`backend/`) and the `store` app with catalog models and API endpoints.
- `frontend/` hosts the React (Vite) single-page app, including pages for auth, catalog, and service portal.
- `nginx/` holds the NGINX config and Dockerfile that serves the React build and proxies `/api/` to Django.
- `docker-compose.yml` orchestrates the backend and web gateway.

## Build, Test, and Development Commands
- `docker compose up --build` builds the frontend, backend, and NGINX image and starts the stack on `http://localhost:8080`.
- `docker compose down` stops containers.
- `cd backend && python manage.py migrate` applies database migrations (already run on container start).
- `cd frontend && npm install && npm run dev` runs the React dev server at `http://localhost:5173` (for local UI work).

## Coding Style & Naming Conventions
- Python: 4-space indentation, follow Django conventions for apps, models, and serializers.
- JavaScript/JSX: 2-space indentation, `PascalCase` for components, `camelCase` for variables.
- Keep API endpoints under `/api/` and group Django views/serializers by domain (`store`).

## Testing Guidelines
- No automated tests are included yet. If you add tests, keep them in `backend/store/tests.py` or `backend/store/tests/` and name files `test_*.py`.
- Prefer API tests for catalog and auth flows when extending the backend.

## Commit & Pull Request Guidelines
- No established commit history yet; follow Conventional Commits (e.g., `feat:`, `fix:`) unless the team specifies otherwise.
- Pull requests should include a concise summary, screenshots for UI changes, and any API contract updates.

## Security & Configuration Tips
- Copy `backend/.env.example` to a local `.env` and set a strong `DJANGO_SECRET_KEY`.
- The service account credentials (`SERVICE_ACCOUNT_*`) are used for product card management; do not commit real secrets.
