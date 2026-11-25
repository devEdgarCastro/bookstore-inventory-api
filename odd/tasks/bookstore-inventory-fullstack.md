# Bookstore Inventory — FullStack (Django + Angular)

Source of truth: `prueba_t_cnica_fullstack_nextep_innovation.md` (repo root, read-only).
Backend repo: `bookstore-inventory-api/`. Frontend: `frontend/` (sibling, outside the backend repo).

## Specs

S1. Folder layout: backend project lives in `bookstore-inventory-api/`; frontend SPA lives in `frontend/`. Backend uses **Python + Django**, preferably **Django REST Framework**. Frontend uses **Angular** SPA.

S2. Model `Book` with exactly these serialized fields:
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

S3. CRUD endpoints: `POST /books` create; `GET /books` list all (pagination optional); `GET /books/{id}` retrieve; `PUT /books/{id}` update; `DELETE /books/{id}` delete.

S4. Optional endpoints: `GET /books/search?category={category}` filter by category; `GET /books/low-stock?threshold=10` books with stock below threshold.

S5. `POST /books/{id}/calculate-price` uses `https://api.exchangerate-api.com/v4/latest/USD`, then: (1) take `cost_usd`; (2) get current `USD -> local` rate; (3) apply **40%** profit margin; (4) persist `selling_price_local`; (5) return the detailed calculation.

S6. Expected `calculate-price` response shape:
```json
{
  "book_id": 1,
  "cost_usd": 15.99,
  "exchange_rate": 0.85,
  "cost_local": 13.59,
  "margin_percentage": 40,
  "selling_price_local": 19.03,
  "currency": "EUR",
  "calculation_timestamp": "2025-01-15T10:30:00Z"
}
```
Arithmetic must reproduce it: `15.99 * 0.85 = 13.5915 -> 13.59`; `13.5915 * 1.40 = 19.0281 -> 19.03` (ROUND_HALF_UP, 2 decimals).

S7. Business rules: `cost_usd > 0`; `stock_quantity >= 0`; `isbn` valid format (10 or 13 digits); no duplicate ISBN; when the exchange API fails, use a default (fallback) rate; handle HTTP `400`, `404`, `500`, `503` appropriately.

S8. Angular SPA applies good architecture: services, model interfaces, reactive state handling, reusable components. It must integrate **every** backend endpoint.

S9. Dashboard: catalog as table or grid/cards; backend pagination; filters panel for category search and quick low-stock view.

S10. Book management: validated **Reactive Forms** for create (`POST`) and update (`PUT`), checking ISBN and cost format before sending; delete (`DELETE`) with a confirmation modal or alert.

S11. Price module: an explicit action (e.g. button "Calcular Precio de Venta") in the detail view or main list that calls the integration endpoint; the UI reflects the server response showing the breakdown: original cost, applied exchange rate, profit margin, final local-currency price.

S12. States and errors: loading indicators (loaders/spinners) during async calls; visual notifications (toasts/alerts) for success and for API errors `400`, `404`, `500`, `503`.

S13. Deliverables: (1) repository link with complete structured source (backend + frontend); (2) `README` with prerequisites (Python, Django, Node.js, Angular CLI, dependencies, virtualenv), install/migration/run steps, and endpoint usage examples; (3) exported **Postman collection** `.json` covering all implemented endpoints; (4) working integrated Angular SPA.

S14. PLUS: Dockerize the whole project (backend + frontend + database).

## Decisions taken (agent-owned, to keep the spec exact)

- Local currency = `EUR`, configurable via env `LOCAL_CURRENCY`; fallback rate configurable via env `FALLBACK_EXCHANGE_RATE` (default `0.85`).
- ISBN validation is **format only** (digits after stripping hyphens/spaces, length 10 or 13) — S7 says "10 o 13 dígitos" and does not require a checksum.
- FX failure/timeout -> HTTP `200` with `exchange_rate_source: "fallback"`. HTTP `503` only when the rate is unavailable **and** fallback is disabled.
- Default DB = SQLite for local dev; Postgres via docker-compose (S14). Settings driven by env vars.
- Docker CLI is not installed in this environment, so Docker files ship but are reported unverified.
- **Repo layout (user decision, L8 — supersedes L6):** the SPA now lives at `bookstore-inventory-api/frontend/`, inside the git repository, so one repository link satisfies S13.1. Docker compose builds it from `./frontend` and `.dockerignore` keeps it out of the backend image context. Reverting L6 required regenerating `node_modules` with `npm ci`, because a live `ng serve` held an OS-level lock on the old directory.

## Tasks

Owner `BE` = gentle-ai-worker task `mwwje4gc-1-cisi` (surface `bookstore-inventory-api/**`).
Owner `FE` = gentle-ai-worker task `mwwje4gh-2-0hcw` (surface `frontend/**`).

| ID | Task | Specs | Owner | Route | Commit | State |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Backend scaffold: venv, Django + DRF project, settings/env, CORS, config health | S1 | BE | worker | `97c9ded` | done |
| T2 | `Book` model + validations + migration + serializer + admin | S2, S7 | BE | worker | `97c9ded` | done |
| T3 | CRUD endpoints, pagination, search, low-stock | S3, S4, S7 | BE | worker | `8ec289e` + seed `656f968` | done |
| T4 | Exchange-rate client with fallback + `calculate-price` | S5, S6, S7 | BE | worker | `8ec289e` | done |
| T5 | Backend test suite (rules, endpoints, FX fallback) | S2-S7 | BE | worker | `dbd4c63`, `672eb08` | done |
| T6 | Angular scaffold + structure (core/shared/features) | S1, S8 | FE | worker | n/a (outside repo) | done |
| T7 | Frontend core: models, BookService, interceptor, toast, environment | S8, S12 | FE | worker | n/a | done |
| T8 | Dashboard: grid, backend pagination, category + low-stock filters | S9 | FE | worker | n/a | done |
| T9 | Create/edit reactive forms + delete confirmation | S10 | FE | worker | n/a | done |
| T10 | Price calculation action + breakdown UI | S11 | FE | worker | n/a | done |
| T11 | Postman collection covering all endpoints | S13.3 | BE | worker | `61ccc05` | done |
| T12 | README (backend repo) + full-stack run instructions | S13.2 | BE | worker | `61ccc05` | done |
| T13 | Docker: backend image, frontend image, compose + Postgres | S14 | BE+FE | worker | `00d9fcb` | shipped, unverified (no Docker CLI) |
| T14 | Parent verification: `manage.py test`, live curl smoke, `npm run build` | S1-S12 | parent | inline | evidence in L7 | done |
| T15 | Work-unit commits on `feature/fullstack-implementation` | S13.1 | parent | inline | 7 commits, see history | done |
| T16 | Mirror `odd/` into `bookstore-inventory-api/odd/` so the reviewer sees the tracking (backend repo only, per L6) | S13.1 | parent | inline | mirror commit | done |
| T17 | Integrate `frontend/` into the repo, fix compose/dockerignore/README, prepare the push (L8) | S13.1, S14 | parent | inline | `f1c0433` | done |

## Log

L1 (user, verbatim): "I want you generate the project using the data in prueba_t_cnica_fullstack_nextep_innovation.md. The backend will be in bookstore-inventory-api y the frontend in frontend folder"

L2 (environment evidence): Python 3.12.0 at `C:\Users\Alex\AppData\Local\Programs\Python\Python312\python.exe` (not on bash PATH; use the absolute path). Node v24.18.0 / npm 11.16.0. No global `ng` (use `npx`). No `docker`. Network reachable for pip and npm.

L3 (repo state): `bookstore-inventory-api/` is its own git repo (remote `devEdgarCastro/bookstore-inventory-api`), branch `main`, one commit `3ded2bf`, `README.md` stub, untracked `.idea/` and `Microsoft/`. `frontend/` exists but is empty. Engram memory tools are not available in this session, so no memory mirror is written.

L4 (user, verbatim): "I want you use ODD to this project"

L5 (decision, from L4): ODD was already the active workflow (feature document + todo + branch existed before the first write). L4 is read as an instruction to make ODD *visible and durable* rather than to restart it. Actions taken: the task table gained Owner/Route/Commit/State columns, verification/commit/mirror steps became first-class tasks T14-T16, and the tracking artifacts get mirrored into the deliverable repo (`bookstore-inventory-api/odd/`) so a reviewer who clones only that repo sees the specification, the task ledger, and the commit evidence. The canonical working copy stays at `Nextep/odd/`. Deviation kept explicit: no Engram mirror exists because no memory tools are exposed in this session.

L6 (user decision, from the repo-layout question): "Keep siblings: backend repo + frontend folder where it is". Consequence recorded in `## Decisions taken`: the SPA is not part of the `bookstore-inventory-api` git repo, so S13.1's single-repository link will not contain the frontend; publishing it needs a second remote or a manual add. The layout is not re-litigated later without a new user instruction.

L7 (parent verification evidence, executed by me, not taken from worker reports):
- `manage.py check` exit 0; `makemigrations --check --dry-run` -> "No changes detected"; `manage.py test` -> "Ran 72 tests ... OK".
- Live `runserver` on :8000 with the seeded DB, exercised over HTTP: `GET /healthz` 200; `GET /books?page=1&page_size=3` -> `count:12` with `next` URL and page_size honoured; `POST /books` 201 returning all eleven S2 keys; `GET /books/{id}` 200; `PUT` 200 with `updated_at` advanced; `GET /books/999999` 404; `DELETE` 204 then `GET` 404.
- Validation over HTTP: duplicate ISBN posted in plain form against a stored hyphenated one -> 400 "A book with this ISBN already exists."; `cost_usd: 0` -> 400; `stock_quantity: -3` -> 400; 5-digit ISBN -> 400; `low-stock?threshold=abc` -> 400.
- Real external integration: `POST /books/13/calculate-price` reached exchangerate-api.com and returned `exchange_rate 0.912`, `cost_local 14.58`, `selling_price_local 20.42`, `margin_percentage 40`, `currency EUR`, `exchange_rate_source "live"`. Arithmetic checked by hand: 15.99 x 0.912 = 14.58288 -> 14.58 and x 1.40 = 20.416032 -> 20.42. `selling_price_local` persisted (20.42 read back).
- Method/route semantics: `GET` on calculate-price -> 405; `POST` on an unknown book -> 404; `GET /books/` -> 404 and `GET /api/books` -> 404, confirming the literal no-slash, no-prefix routing the SPA calls.
- Frontend: `npm run build` exit 0, `dist/frontend`, initial 294.15 kB with lazy chunks for book-form (51.88 kB) and book-list (20.38 kB).
- Commit integrity: commits `97c9ded` (C1) and `8ec289e` (C2) were each re-checked by checking them out into an isolated `git worktree` and running `manage.py check` there, so the "every commit boots" claim is observed rather than assumed.
- Corrected during verification (my own harness errors, not product defects): Git Bash mangled UTF-8 in one curl body, and a create used an ISBN already present in the seeded DB, leaving `$ID` empty and turning later URLs into `//calculate-price`. Re-run with a unique ISBN.
- `.env.example` decision (option 1, agent-owned): ship `env.example`; the file name is not part of S1-S14 and the substantive requirement (template shipped, no real `.env`, `.env` gitignored) is met. No repo change made.
- Unverified and reported as such: Docker images and compose (no Docker CLI); the SPA has no live browser integration run, so its flows rest on 33 unit tests, a clean production build and the confirmed route contract.

L8 (user, verbatim): "puedes integrar la carpeta frontend dentro de la carpeta bookstore-inventory-api? y preparar todo para subir a git?"

L9 (decision and evidence, from L8): reverses L6, so S13.1's single repository link now covers both halves.
- Stopped the user's running `ng serve` (PID 5724 + esbuild 28912, spawned by `npm run start`). It must be restarted from the new path. Pi's own harness processes (28060/27128) were identified and left alone.
- The old `Nextep/frontend` refused `mv` and `Move-Item` with "being used by another process" even after `ng serve` died; a hard Windows handle on the directory survived. Rather than force it, the 53 source files (excluding `node_modules`, `dist`, `.angular`) were copied with `tar` and the dependency tree regenerated with `npm ci` from `package-lock.json`.
- Fixed the compose build context `../frontend` -> `./frontend`, added `frontend` to `.dockerignore` (without it the backend image context dragged 283 MB of `node_modules`), corrected four README references, and gitignored the stray `Microsoft/` PowerShell cache instead of deleting a user file.
- Integration commit `f1c0433`: 53 SPA source files plus the compose, `.dockerignore`, README and `.gitignore` corrections. Verified from the new path: `npm ci` exit 0 (288 packages) and `npm run build` exit 0 into `frontend/dist/frontend`.
- Nothing is pushed: publishing stays a human decision. The stale `Nextep/frontend` directory may remain until the locking process is closed; it is outside the repository and harmless.
