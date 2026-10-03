# Deployment Notes

This repository now supports two database modes:

- **Local development:** existing SQL Server settings (`DB_SERVER`, `DB_NAME`, `DB_DRIVER`).
- **Cloud:** `DATABASE_URL` takes priority and is intended for PostgreSQL/Neon.

## Render backend

- Root directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `alembic upgrade head && python scripts/bootstrap_admin.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health: `/health`

Set `DATABASE_URL`, `GROQ_API_KEY`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `ADMIN_NAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in Render.

## Render frontend

- Root directory: `frontend`
- Build: `npm ci && npm run build`
- Publish: `dist`
- Set `VITE_API_BASE_URL=https://YOUR-BACKEND.onrender.com/api`.
- React Router requires a rewrite from `/*` to `/index.html` (included in `render.yaml`).

## First deployment order

1. Create the Neon PostgreSQL database and copy its connection string to `DATABASE_URL`.
2. Deploy the backend and verify `/health`.
3. Deploy the frontend with `VITE_API_BASE_URL` pointing to the backend `/api` URL.
4. Put the final frontend origin into backend `CORS_ORIGINS` and redeploy the backend.
5. Log in with the bootstrap admin credentials and change the password after first login.

Never commit real `.env` files, database passwords, API keys, JWT secrets, or admin passwords.
