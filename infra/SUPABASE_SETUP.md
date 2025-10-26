# Supabase Setup Guide

## 1. Create Project
1. Sign in at [app.supabase.com](https://app.supabase.com/).
2. Click **New project**, choose org, enter project name (e.g. `flat-finder`).
3. Select **Region: eu-central-1**, **Password** (store securely), **Database Size: Free**.
4. Wait for provisioning to complete.

## 2. Enable Auth & Configure Settings
1. Navigate to **Authentication → Providers**.
2. Toggle **Email** on, leave **Confirm email** enabled.
3. (Optional) Set custom email templates under **Authentication → Templates**.
4. Under **Authentication → URL Configuration**, add:
   - **Site URL**: `http://localhost:3000`
   - **Redirect URLs**: `http://localhost:3000/auth/callback`

## 3. Capture API Keys Locally
1. Go to **Project Settings → API**.
2. Copy values:
   - **Project URL**
   - **anon public** key
   - **service role** key
3. Save to files (keep service key out of version control):
   ```bash
   echo "SUPABASE_URL=..." > backend/.env
   echo "SUPABASE_SERVICE_KEY=..." >> backend/.env
   echo "NEXT_PUBLIC_SUPABASE_URL=..." > frontend/.env.local
   echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=..." >> frontend/.env.local
   ```
4. Optionally store keys in `backend/.secrets/supabase-service-role.key` and update `.gitignore`.

## 4. Database & Row Level Security
1. Open **SQL Editor**, create migration from snippet below.
2. Ensure **Row Level Security** is enabled (default) for each table.
3. After running SQL, verify tables under **Table Editor**.

```sql
-- Users are managed via Supabase Auth (auth.users). Convenience mirror table:
create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text unique not null,
    full_name text,
    created_at timestamp with time zone default now()
);
alter table public.users enable row level security;
create policy "Users can manage self"
    on public.users for all
    using (auth.uid() = id)
    with check (auth.uid() = id);

create table if not exists public.user_preferences (
    id bigserial primary key,
    user_id uuid not null references public.users(id) on delete cascade,
    price_min integer,
    price_max integer,
    districts text[],
    property_types text[],
    min_rooms numeric(3,1),
    min_size_sqm integer,
    pets_allowed boolean,
    furnished boolean,
    auto_apply boolean default false,
    auto_apply_threshold integer default 80,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
alter table public.user_preferences enable row level security;
create policy "Owner access to preferences"
    on public.user_preferences for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create table if not exists public.listings (
    id bigserial primary key,
    external_id text unique not null,
    source text not null,
    title text,
    detail_url text,
    price_eur integer,
    rooms numeric(3,1),
    size_sqm integer,
    district text,
    raw_payload jsonb,
    first_seen_at timestamptz default now(),
    last_seen_at timestamptz default now(),
    is_active boolean default true
);
alter table public.listings enable row level security;
create policy "Service role manage listings"
    on public.listings for all
    using (auth.jwt() ->> 'role' = 'service_role')
    with check (auth.jwt() ->> 'role' = 'service_role');

create table if not exists public.applications (
    id bigserial primary key,
    user_id uuid not null references public.users(id) on delete cascade,
    listing_id bigint not null references public.listings(id) on delete cascade,
    status text default 'pending',
    auto_submitted boolean default false,
    submitted_at timestamptz,
    created_at timestamptz default now()
);
alter table public.applications enable row level security;
create policy "Owner access to applications"
    on public.applications for select using (auth.uid() = user_id);
create policy "Users insert own applications"
    on public.applications for insert with check (auth.uid() = user_id);
create policy "Users update own applications"
    on public.applications for update using (auth.uid() = user_id);

create table if not exists public.application_events (
    id bigserial primary key,
    application_id bigint not null references public.applications(id) on delete cascade,
    user_id uuid not null references public.users(id) on delete cascade,
    event_type text not null,
    payload jsonb,
    occurred_at timestamptz default now()
);
alter table public.application_events enable row level security;
create policy "Owner access to application events"
    on public.application_events for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
```

## 5. Generate Service Role Access Files
1. Create secure storage (e.g. 1Password, Doppler) for the service key.
2. For local development:
   ```bash
   mkdir -p backend/.secrets
   echo "<service-role-key>" > backend/.secrets/supabase-service-role.key
   chmod 600 backend/.secrets/supabase-service-role.key
   ```
3. Reference the service key in backend config (e.g. `SUPABASE_SERVICE_KEY_FILE=backend/.secrets/supabase-service-role.key`).

## 6. Verify Connectivity
1. Run `cd backend && poetry run python -m httpx get "$SUPABASE_URL/rest/v1/"` to test access.
2. From frontend, run `npm run dev` and ensure Supabase auth UI loads without errors.

## 7. Production Checklist
- Rotate service keys regularly via **Project Settings → API**.
- Enforce **JWT expiry** under **Authentication → Settings**.
- Configure **Storage** policies if storing documents.
- Enable **Log Drains** for auditing (optional).
