# FamilyDent Storefront

Django + React dentistry storefront with registration, login, catalog, and a staff service portal. Runs behind NGINX via Docker.

## Requirements
- Docker + Docker Compose

## Quick Start (Docker)
```bash
docker compose up --build
```
Open `http://localhost:8080` for the web UI, and `http://localhost:8080/api/docs/` for API docs.

## Service Account
The backend auto-creates a staff account on startup. Defaults are in `backend/.env.example`:
- `SERVICE_ACCOUNT_USERNAME`
- `SERVICE_ACCOUNT_PASSWORD`

Copy and customize for real use:
```bash
cp backend/.env.example backend/.env
```
Update the values, then restart the stack.

## Database
Docker uses Postgres (`postgres` service). Update the `DB_*` values in `backend/.env` if you need different credentials.

## Local Dev (without Docker)
Backend:
```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createserviceaccount
python manage.py runserver
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`. The Vite dev server proxies `/api` to `http://localhost:8000`.

## Useful Endpoints
- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `GET /api/account/profile/`
- `POST /api/account/addresses/`
- `GET /api/cart/`
- `POST /api/orders/`
- `POST /api/orders/{id}/pay/` (staff/manager)
- `GET /api/catalog/products/`
- `POST /api/catalog/products/` (staff only)
