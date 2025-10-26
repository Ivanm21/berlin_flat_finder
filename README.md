# Flat Finder Monorepo

## Structure
- `backend/` – Python 3.11 services managed with Poetry  
- `frontend/` – Next.js 14 (TypeScript, App Router, Tailwind) client  

## Prerequisites
- Python 3.11 + Poetry
- Node.js 18+
- Supabase project (URL & keys)

## Repository Setup
1. `git init`
2. `git add .`
3. `git commit -m "chore: initial scaffold"`
4. `git branch -M main`
5. `git remote add origin <your-remote-url>`
6. `git push -u origin main`

## Backend Setup
1. `cd backend`
2. `poetry install`
3. Copy `.env.example` to `.env` and supply Supabase credentials.
4. `poetry run python -m backend` *(placeholder entrypoint)*

## Frontend Setup
1. `cd frontend`
2. `npm install`
3. Create `.env.local` with `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
4. `npm run dev`

## Development Tips
- Use separate terminals for backend (`poetry run ...`) and frontend (`npm run dev`).
- Commit generated lockfiles for reproducible environments.
# berlin_flat_finder
