# Bookstore Inventory — Angular SPA

Angular (standalone components, strict TypeScript, signals) front-end for the bookstore inventory
API built with Django REST Framework.

## Features

- **Dashboard `/books`**: catalog table, backend pagination (`count` / `next` / `previous` +
  `page_size`), category filter (`/books/search`), low-stock filter (`/books/low-stock`) and the
  per-row **Calcular Precio de Venta** action with a full breakdown of the server calculation.
- **Book management `/books/new` and `/books/:id/edit`**: validated reactive forms for `POST` and
  `PUT`, inline field errors plus per-field `400` messages from the API, and a reusable
  confirmation modal for `DELETE`.
- **States**: spinners for every async call, empty states and toasts for success and for
  `400` / `404` / `500` / `503` errors (`core/interceptors/error.interceptor.ts`).

## Requirements

- Node.js 22.22.3+ or 24.15+ (Angular 22 engine range; verified on 24.18.0)
- npm 8+

The Angular CLI is a local dev dependency, so no global install is needed — `npm install` brings it
in and the `npm` scripts below use it.

## Install and run

```bash
npm install
npm start                      # dev server on http://localhost:4200
npm run build                  # production bundle in dist/frontend/browser
npm test -- --watch=false      # unit tests once (plain `npm test` stays in watch mode)
```

The API base URL lives in `src/environments/environment.ts`
(`environment.production.ts` is used by the production build through
`fileReplacements` in `angular.json`) and defaults to `http://localhost:8000` **without** an
`/api` prefix.

## Structure

```
src/app
├── core
│   ├── interceptors   error.interceptor.ts (HTTP status -> toast, error re-thrown)
│   ├── models         book.model.ts (Book, BookPayload, PaginatedResponse, PriceCalculation)
│   ├── services       book.service.ts (one typed method per endpoint)
│   └── validators     book-validators.ts (ISBN, supplier country, integer stock)
├── shared
│   ├── confirm-dialog confirm-dialog.component.ts
│   └── toast          toast.service.ts (signal queue) + toast-container.component.ts
├── features/books
│   ├── book-form        book-form.component.ts
│   ├── book-list        book-list.component.ts
│   └── price-breakdown  price-breakdown.component.ts
├── app.routes.ts
└── app.config.ts
```

## Docker

```bash
docker build -t bookstore-frontend .
docker run --rm -p 4200:80 bookstore-frontend
```

Multi-stage build: Node compiles the production bundle, nginx serves it on port 80 with SPA
history fallback (`nginx.conf`). The Docker files were not executed in this environment (no Docker
CLI available).
