# Northstar Supply

A local-first FastAPI storefront for browsing everyday goods, managing customer/admin accounts, and testing checkout without real payments.

## Run & Operate

- `cd ecommerce-fastapi && python -m uvicorn main:app --reload` — run the standalone Python store after setting `JWT_SECRET`
- `cd ecommerce-fastapi && pytest -q` — run the store's automated API tests
- Windows setup, seed data, admin bootstrap, and GitHub instructions are in `ecommerce-fastapi/README.md`
- `Northstar Store` — Replit development workflow (temporary signing key; sessions reset when it restarts)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

## Stack

- Store: Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pydantic, JWT, Argon2
- Store frontend: HTML, CSS, vanilla JavaScript, locally stored SVG illustrations
- Store payments: local simulation only; no payment gateway or card data
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `ecommerce-fastapi/` — standalone student project; SQLite-backed FastAPI app, static storefront, seed script, tests, and Windows guide
- `ecommerce-fastapi/models.py` and `schemas.py` — store data model and API validation
- `ecommerce-fastapi/routers/` — authentication, catalog, cart, order, and admin routes
- `ecommerce-fastapi/static/` — storefront HTML/CSS/JS and original local illustrations
- `ecommerce-fastapi/services/seed.py` — non-destructive 20-product / 5-category sample catalog
- `lib/api-spec/openapi.yaml` — source of truth for the separate shared workspace API

## Architecture decisions

- The store defaults to a local SQLite file and does not inherit the workspace's unrelated database setting.
- Customer sessions use expiring JWTs in HttpOnly cookies; public registration always assigns the customer role.
- Checkout is simulated and never collects payment credentials.
- Local development uses a generated temporary signing key; Windows setup stores a unique key in the ignored `.env` file.

## Product

- Responsive catalog with search, category filtering, sorting, product detail, guest bag, and account-saved cart
- Registration/login, shipping details, simulated successful/declined checkout, order confirmation, and private order history
- Admin overview and catalog, stock, category, and paid-order status management

## User preferences

- Keep the student project fully usable locally on Windows with free/open-source dependencies and SQLite.
- Do not add paid services, external image APIs, real payment gateways, or cloud-hosting requirements.

## Gotchas

- The standalone store must be started from `ecommerce-fastapi/`; its `.env`, SQLite database, and static paths are local to that folder.
- Create the first administrator with `python create_admin.py`; public registration cannot grant admin access.
- Replit's development workflow uses a disposable signing key. Use a persistent random `JWT_SECRET` in `.env` for local Windows runs.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
