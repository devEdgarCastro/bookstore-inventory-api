# Bookstore Inventory API

Django 5 + Django REST Framework backend for a bookstore inventory. It exposes a
book catalogue (CRUD, category search, low-stock view) and calculates the suggested
local selling price from the current `USD -> local currency` exchange rate with a
configurable profit margin.

The Angular SPA lives in the `frontend/` directory of this repository and consumes exactly the
API described below.

- **Language / framework:** Python 3.12, Django 5.2, Django REST Framework 3.18
- **Database:** SQLite for local development, PostgreSQL 16 in Docker
- **Local currency:** `EUR` (configurable), profit margin `40 %` (configurable)

---

## 1. Prerequisites

| Tool | Version | Needed for |
| --- | --- | --- |
| Python | 3.12 | backend (this repository) |
| `venv` | bundled with Python | isolated dependencies |
| pip | bundled with Python | dependency installation |
| Node.js | 20 LTS or 22 LTS | Angular SPA in `frontend/` |
| Angular CLI | 18+ (or `npx @angular/cli`) | Angular SPA in `frontend/` |
| Docker + Docker Compose | 24+ | optional, `docker-compose.yml` |

The API has no frontend build step; the SPA is a separate project.

---

## 2. Project structure

```text
bookstore-inventory-api/
├── config/                     # Django project (settings, URLs, WSGI/ASGI)
│   ├── settings.py             # every value configurable through env vars
│   ├── urls.py                 # mounts the API at the site root (no /api)
│   ├── wsgi.py / asgi.py
├── books/                      # the single Django app
│   ├── models.py               # Book model + ISBN helpers
│   ├── serializers.py          # S2 field set, S7 validation, S6 response shape
│   ├── views.py                # CRUD, search, low-stock, calculate-price
│   ├── urls.py                 # /books routes
│   ├── pagination.py           # ?page= / ?page_size= with the DRF envelope
│   ├── admin.py                # Django admin registration
│   ├── services/
│   │   ├── exchange.py         # USD rate client with fallback (S5, S7)
│   │   └── pricing.py          # 40 % margin arithmetic, ROUND_HALF_UP (S6)
│   ├── management/commands/
│   │   └── seed_books.py       # 12 sample books, idempotent
│   ├── migrations/0001_initial.py
│   └── tests/                  # offline test suite (no network)
├── postman/                    # exported Postman collection
├── requirements.txt
├── env.example                 # copy to ".env" (never commit the real file)
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

---

## 3. Installation

### 3.1 Create the virtual environment

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell / cmd)
py -3.12 -m venv .venv
.venv\Scripts\activate
```

### 3.2 Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Configure the environment

Everything works with the built-in defaults (SQLite + `DEBUG=True` + `EUR`). To
override them, copy the template and edit it:

```bash
cp env.example .env        # Windows: copy env.example .env
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | insecure dev key | Django secret key |
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | comma separated host list |
| `DATABASE_URL` | unset -> SQLite `db.sqlite3` | `postgresql://user:pass@host:5432/db` or `sqlite:///path` |
| `PAGE_SIZE` | `10` | default page size of every list endpoint |
| `LOCAL_CURRENCY` | `EUR` | currency the selling price is expressed in |
| `PROFIT_MARGIN_PERCENTAGE` | `40` | margin applied on the landed cost |
| `LOW_STOCK_THRESHOLD` | `10` | default threshold of `/books/low-stock` |
| `EXCHANGE_RATE_API_URL` | `https://api.exchangerate-api.com/v4/latest/USD` | FX provider |
| `FALLBACK_EXCHANGE_RATE` | `0.85` | rate used when the provider fails |
| `EXCHANGE_FALLBACK_ENABLED` | `true` | `false` -> HTTP 503 instead of a fallback |
| `EXCHANGE_RATE_TIMEOUT` | `5` | FX request timeout in seconds |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200` | origins allowed to call the API |

### 3.4 Migrate, seed and run

```bash
python manage.py migrate
python manage.py seed_books      # 12 sample books, safe to re-run (idempotent)
python manage.py runserver       # http://localhost:8000
```

Optional admin user for `http://localhost:8000/admin/`:

```bash
python manage.py createsuperuser
```

---

## 4. Running the tests

The suite uses Django's own test runner and is fully offline: every exchange-rate
HTTP call is mocked, so no request leaves the machine.

```bash
python manage.py test
# Ran 72 tests ... OK
```

Run a single module or case:

```bash
python manage.py test books.tests.test_calculate_price
python manage.py test books.tests.test_books_api.BookValidationTests
```

Static/build checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run   # fails if a migration is missing
```

---

## 5. API reference

Base URL: `http://localhost:8000` — **there is no `/api` prefix**.

| Method | Path | Description | Success | Errors |
| --- | --- | --- | --- | --- |
| `GET` | `/books?page=&page_size=` | Paginated catalogue | `200` | — |
| `POST` | `/books` | Create a book | `201` | `400` |
| `GET` | `/books/{id}` | Retrieve one book | `200` | `404` |
| `PUT` | `/books/{id}` | Update a book | `200` | `400`, `404` |
| `DELETE` | `/books/{id}` | Delete a book | `204` | `404` |
| `GET` | `/books/search?category=` | Filter by category (case-insensitive) | `200` | — |
| `GET` | `/books/low-stock?threshold=` | Books with `stock_quantity <= threshold` (default `10`) | `200` | `400` |
| `POST` | `/books/{id}/calculate-price` | Live FX rate + 40 % margin, persists `selling_price_local` | `200` | `400`, `404`, `503` |
| `GET` | `/healthz` | Liveness probe | `200` | — |

List responses (list, search, low-stock) share the paginated envelope:

```json
{
  "count": 12,
  "next": "http://localhost:8000/books?page=2&page_size=10",
  "previous": null,
  "results": [ { "id": 1, "title": "El Quijote", "...": "..." } ]
}
```

### 5.1 Book representation (S2)

```json
{
  "id": 1,
  "title": "El Quijote",
  "author": "Miguel de Cervantes",
  "isbn": "978-84-376-0494-7",
  "cost_usd": 15.99,
  "selling_price_local": null,
  "stock_quantity": 25,
  "category": "Literatura Clásica",
  "supplier_country": "ES",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### 5.2 Create a book

```bash
curl -i -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{
        "title": "El Quijote",
        "author": "Miguel de Cervantes",
        "isbn": "978-84-376-0494-7",
        "cost_usd": "15.99",
        "stock_quantity": 25,
        "category": "Literatura Clásica",
        "supplier_country": "ES"
      }'
# HTTP/1.1 201 Created
```

Validation failures return DRF field errors, e.g. `cost_usd: 0`:

```json
{ "cost_usd": ["Ensure this value is greater than or equal to 0.01."] }
```

A duplicate ISBN (with or without hyphens) returns `400`:

```json
{ "isbn": ["A book with this ISBN already exists."] }
```

### 5.3 List, paginate, retrieve

```bash
curl "http://localhost:8000/books?page=1&page_size=5"
curl "http://localhost:8000/books/1"
curl "http://localhost:8000/books/999999"       # 404
```

### 5.4 Update and delete

```bash
curl -i -X PUT http://localhost:8000/books/1 \
  -H "Content-Type: application/json" \
  -d '{
        "title": "El Quijote (2nd ed.)",
        "author": "Miguel de Cervantes",
        "isbn": "978-84-376-0494-7",
        "cost_usd": "20.00",
        "stock_quantity": 8,
        "category": "Literatura Clásica",
        "supplier_country": "ES"
      }'
# HTTP/1.1 200 OK

curl -i -X DELETE http://localhost:8000/books/1
# HTTP/1.1 204 No Content
```

### 5.5 Search by category and low stock

```bash
curl "http://localhost:8000/books/search?category=Literatura%20Cl%C3%A1sica"
curl "http://localhost:8000/books/low-stock?threshold=10"
```

Both return the same paginated envelope and accept `page` / `page_size`.

### 5.6 Calculate the selling price (S5, S6)

```bash
curl -i -X POST http://localhost:8000/books/1/calculate-price
```

Response for a book with `cost_usd = 15.99` and a `USD -> EUR` rate of `0.85`
(`15.99 * 0.85 = 13.5915 -> 13.59`, `13.5915 * 1.40 = 19.0281 -> 19.03`,
`ROUND_HALF_UP`, 2 decimals):

```json
{
  "book_id": 1,
  "cost_usd": 15.99,
  "exchange_rate": 0.85,
  "cost_local": 13.59,
  "margin_percentage": 40,
  "selling_price_local": 19.03,
  "currency": "EUR",
  "calculation_timestamp": "2025-01-15T10:30:00Z",
  "exchange_rate_source": "live"
}
```

- `200` — calculated; `selling_price_local` is persisted on the book.
- `200` with `"exchange_rate_source": "fallback"` — the FX provider timed out,
  errored, answered non-200, returned malformed JSON or lacked the target
  currency; `FALLBACK_EXCHANGE_RATE` (default `0.85`) was used.
- `503` — the rate is unavailable **and** `EXCHANGE_FALLBACK_ENABLED=false`.
- `404` — unknown book id. `405` — any method other than `POST`.

### 5.7 Health check

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

---

## 6. Business rules

| Rule | Enforcement |
| --- | --- |
| `cost_usd > 0` | serializer `min_value=0.01` (+ model validator) -> `400` |
| `stock_quantity >= 0` | serializer `min_value=0` (+ positive integer column) -> `400` |
| `isbn` has 10 or 13 digits | hyphens/spaces are stripped before the digit check -> `400` |
| no duplicate ISBN | unique normalized ISBN column + serializer check -> `400` |
| provider failure | fallback rate, or `503` when disabled |
| CORS | `http://localhost:4200` allowed by default |

The caller's ISBN formatting is preserved in responses; uniqueness is enforced on
the digits only, so `978-84-376-0494-7`, `978 84 376 0494 7` and `9788437604947`
refer to the same book.

---

## 7. Postman collection

`postman/bookstore-inventory-api.postman_collection.json` covers every endpoint
above (Health, Books CRUD + search + low-stock, Price calculation). Import it into
Postman, set the `baseUrl` variable (default `http://localhost:8000`), create a
book, put its `id` into the `bookId` variable, and run the requests.

---

## 8. Docker (optional)

`docker-compose.yml` defines three services:

| Service | Image / build | Port | Notes |
| --- | --- | --- | --- |
| `db` | `postgres:16` | internal | `pg_isready` healthcheck, named volume `pgdata` |
| `backend` | `Dockerfile` (python:3.12-slim + gunicorn) | `8000:8000` | waits for `db` to be healthy, runs `migrate`, `seed_books`, then gunicorn |
| `frontend` | `frontend/Dockerfile` | `4200:80` | static Angular build served by nginx |

```bash
cp env.example .env    # optional: override POSTGRES_*, SECRET_KEY, ...
docker compose up --build
```

The API is then available at `http://localhost:8000` and the SPA at
`http://localhost:4200`. Note: this environment has no Docker CLI, so the images
are provided but were not built here. With `DEBUG=False`, `/admin/` styling comes
from the collected `static/` files; serve `staticfiles/` (or run with
`DEBUG=True`) if you need the admin UI in production.
