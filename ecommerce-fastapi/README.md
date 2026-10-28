# Northstar Supply — FastAPI E-Commerce Demo

A complete local-first storefront and REST API for a student portfolio. It uses FastAPI, SQLite, SQLAlchemy, HTML, CSS, and vanilla JavaScript. It does not need a paid service, cloud database, external image API, or real payment account.

## What is included

- Responsive storefront, product search/filter/sorting, product details, and pagination.
- Customer registration and sign-in with Argon2 password hashes and expiring JWT sessions in HttpOnly cookies.
- Persistent per-account carts, plus a browser-saved guest bag that syncs after sign-in.
- Shipping form and simulated successful/declined checkout. No card number, CVV, or bank details are requested.
- Customer order history and shipping details.
- Admin dashboard, category creation, product create/edit/delete, inventory visibility, and order-status management.
- SQLite setup and non-destructive seed data: 20 products across 5 categories.
- REST API under `/api/v1`, health check, Swagger UI, ReDoc, and automated API tests.
- Original local SVG product illustrations; no product-image API.

The storefront displays USD prices as sample portfolio data. Adjust the sample catalog and copy in `services/seed.py` for your project.

## Requirements

- Windows 10 or 11
- Python 3.10 or newer
- Internet access for the first install of the free Python libraries (the running app does not call external services)

## Run on Windows PowerShell

Open PowerShell in the project folder (`ecommerce-fastapi`) and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
$secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
Set-Content -Path .env -Value "JWT_SECRET=$secret`nAPP_ENV=development"
python seed_database.py
uvicorn main:app --reload
```

If PowerShell blocks virtual-environment activation, either open a new terminal configured for local scripts or run Uvicorn with the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The database is `store.db` in this folder. It is created once and is not erased on application restarts. Seeding is idempotent; existing catalog records are left in place. The app uses `NORTHSTAR_DATABASE_URL` for an optional database override so unrelated workspace-level database settings cannot silently replace the local SQLite default.

Open:

- Storefront: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health check: <http://127.0.0.1:8000/health>

## Create the first administrator

Keep `.env` in this folder so the script can read the same JWT settings. Stop the server, open another PowerShell window in `ecommerce-fastapi`, activate `.venv`, then run:

```powershell
python create_admin.py
```

The script prompts for a name, email, and password without putting the password in shell history. Public registration always creates a customer; there is no admin-role field in the registration API.

Sign in with that account and open **The back room** at `http://127.0.0.1:8000/#/admin`.

## Simulated checkout

At checkout choose either test outcome:

- **Successful order** — creates a paid demonstration order, reduces the sample stock, and clears the cart.
- **Declined payment** — records a failed demonstration order, does not reduce stock, and keeps the cart.

Both outcomes are local-only. There is no payment provider and no payment credential input.

## API overview

All data routes are prefixed with `/api/v1`.

| Area | Routes |
| --- | --- |
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| Products | `GET /products`, `GET /products/{id}`, `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}` |
| Categories | `GET /categories`, `POST /categories` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{id}`, `DELETE /cart/items/{id}` |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{id}` |
| Admin | `GET /admin/dashboard`, `GET /admin/orders`, `PATCH /admin/orders/{id}/status` |

Product listing accepts `q`, `category_id`, `sort`, `page`, and `page_size`. Supported sort values are `featured`, `price_asc`, `price_desc`, `newest`, and `name`.

Customer endpoints only return the signed-in customer's own cart and orders. Product/category writes and administration routes require an administrator session.

## Run the tests

Activate the virtual environment and run:

```powershell
pytest -q
```

Tests use a temporary SQLite database and do not modify your local sample database.

## GitHub Free

From the project folder:

```powershell
git init
git add .
git commit -m "Build local FastAPI ecommerce demo"
```

Create an empty repository on GitHub, then use the repository URL GitHub gives you:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Before pushing, confirm `.env`, `.venv`, and `store.db` are not staged. The included `.gitignore` excludes them. GitHub Free is used only to host source code; it is not required to run the store.

## Configuration and safety notes

- Never commit `.env`. Generate a separate random `JWT_SECRET` for each local copy.
- SQLite and all sample data stay on your computer by default.
- This is a demonstration storefront, not a production commerce or payment system.
- The simulated checkout must not be used to accept real payments.
