# FamilyDent B2B Web App

Полноценный стартовый стек Django + React для B2B интернет-магазина стоматологических товаров.

## Что внутри

- **Backend**: Django REST API (JWT), импорты товаров из XLSX, корзина, оформление заказов.
- **Frontend**: Vite + React с витриной по мотивам дизайна и блоками популярных товаров.

## Быстрый старт

### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver 0.0.0.0:8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev -- --host --port 5173
```

Frontend ожидает API на `http://localhost:8000/api/` (настраивается в `frontend/src/api.ts`).

### 3) Docker (backend + frontend)
```bash
docker-compose up --build
```

Сервисы:
- Django API: http://localhost:8000/api/
- React витрина (Vite dev): http://localhost:5173

По умолчанию используется SQLite (`./db.sqlite3`). Остановите контейнеры и сохраните файл, чтобы не потерять данные.

> Если сборка контейнера backend упирается в таймауты/прокси при установке `pip`, передайте зеркало PyPI:
> ```bash
> PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
> PIP_TRUSTED_HOST=mirrors.aliyun.com \
> docker-compose build backend
> ```

> Если `npm install` висит из‑за недоступного registry, передайте зеркало:
> ```bash
> NPM_REGISTRY=https://registry.npmmirror.com docker-compose build frontend
> ```

## Основные возможности API

- Регистрация: `POST /api/auth/register/`
- JWT логин: `POST /api/auth/login/`
- Категории/товары: CRUD `categories/`, `products/`
- Корзина: `GET /api/cart/`, `POST /api/cart/add/` (`product_id`, `quantity`)
- Заказы: `POST /api/orders/` с позициями
- Импорт XLSX: `POST /api/import-products/` (столбцы `name, sku, price, inventory, description?, image_url?, category?`)

## Структура проекта

- `backend/` — Django проект и приложение `shop`
- `frontend/` — Vite + React витрина
- `requirements.txt` — зависимости бэкенда
- `frontend/package.json` — зависимости фронтенда

## Направления для доработки

- Подключить объектное хранилище для медиа и превью
- Добавить роли/права и статусы оплаты
- Расширить фильтры каталога и поиск
- Собрать Docker-окружение и CI-пайплайн
