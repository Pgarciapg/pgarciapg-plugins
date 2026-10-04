---
description: Manage Supabase database - create tables, generate types, run migrations
argument-hint: "<init|migrate|types|seed|reset>"
---

# MVP Database Management

Manage your Supabase database for the MVP.

## Action: $ARGUMENTS

Run the section below that matches the action above. If the action is missing or is not one of `init`, `migrate`, `types`, `seed` or `reset`, ask which one to run before doing anything else.

---

## Action: init

Initialize Supabase in the project.

### Steps:
1. Install Supabase CLI if needed:
```bash
npm install -D supabase
```

2. Initialize Supabase:
```bash
npx supabase init
```

3. Link to remote project:
```bash
npx supabase link --project-ref YOUR_PROJECT_REF
```

Guide user to find project ref in Supabase dashboard URL.

**Note**: `supabase db push` uses the linked project automatically — do NOT pass `--project-ref` flag (it doesn't exist on db push).

---

## Action: migrate

Create and run database migrations.

### Interactive Migration Builder

Ask user: "What do you need to add to the database?"

Based on response, generate appropriate SQL migration.

### CRITICAL: Table Ordering

Schema SQL files MUST order tables by FK dependencies — create referenced tables first. If table B has a foreign key to table A, table A's CREATE must come before table B's.

### Common Patterns:

#### User Profiles Table
```sql
-- Create profiles table
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  email text,
  full_name text,
  avatar_url text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Enable RLS
alter table public.profiles enable row level security;

-- Policies
create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

#### Generic CRUD Table
```sql
-- Create [table_name] table
create table public.[table_name] (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  [columns],
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Index for user queries (always add for user-owned data)
create index [table_name]_user_id_idx on public.[table_name](user_id);

-- Enable RLS
alter table public.[table_name] enable row level security;

-- Policies
create policy "Users can view own [table_name]"
  on public.[table_name] for select
  using (auth.uid() = user_id);

create policy "Users can create own [table_name]"
  on public.[table_name] for insert
  with check (auth.uid() = user_id);

create policy "Users can update own [table_name]"
  on public.[table_name] for update
  using (auth.uid() = user_id);

create policy "Users can delete own [table_name]"
  on public.[table_name] for delete
  using (auth.uid() = user_id);

-- Updated at trigger
create extension if not exists moddatetime;
create trigger handle_updated_at before update on public.[table_name]
  for each row execute procedure moddatetime (updated_at);
```

#### Multi-tenant (Team-based) Table
```sql
create table public.teams (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  created_at timestamptz default now() not null
);

create table public.team_members (
  team_id uuid references public.teams on delete cascade,
  user_id uuid references auth.users on delete cascade,
  role text default 'member' check (role in ('owner', 'admin', 'member')),
  joined_at timestamptz default now() not null,
  primary key (team_id, user_id)
);

-- RLS: team members can view their team's data
alter table public.teams enable row level security;
alter table public.team_members enable row level security;

create policy "Team members can view team"
  on public.teams for select
  using (
    exists (
      select 1 from public.team_members
      where team_id = teams.id and user_id = auth.uid()
    )
  );
```

**Multi-tenant gotcha**: Schema changes must be backward-compatible. If adding org_id or team_id to existing tables, make the column nullable first, backfill, then add NOT NULL constraint in a separate migration.

### Create Migration File:
```bash
npx supabase migration new [migration_name]
```

Then write SQL to the generated file.

### Push Migration:
```bash
npx supabase db push
```

### Cherry-Pick Safety Check

Before cherry-picking migrations from feature branches:
1. Grep the diff for `from('table_name')`, `.from(`, `org_id`, and schema references
2. If it references tables that only exist on the feature branch, DO NOT cherry-pick
3. Missing tables cause cascading `PGRST205` errors in production

---

## Action: types

Generate TypeScript types from database schema.

```bash
npx supabase gen types typescript --linked > src/types/database.ts
```

Then show user how to use typed client:

```typescript
import { createClient } from "@/lib/supabase/client";
import type { Database } from "@/types/database";

type Item = Database["public"]["Tables"]["items"]["Row"];

const supabase = createClient();

// Now fully typed!
const { data } = await supabase
  .from("items")
  .select("*")
  .returns<Item[]>();
```

**Always regenerate types after every migration** — stale types cause silent runtime errors.

---

## Action: seed

Create seed data for development.

### Create seed file:
Create `supabase/seed.sql`:

```sql
-- Seed data for development
-- This runs after migrations

-- Example: Insert test data
-- insert into public.profiles (id, email, full_name)
-- values ('test-uuid', 'test@example.com', 'Test User');
```

Ask user what seed data they need and generate appropriate SQL.

**Note**: `.local` TLD emails are rejected by Supabase cloud auth signup — use `.com` or `.test` emails in seed data.

### Run seed:
```bash
npx supabase db reset
```
(This resets DB and runs all migrations + seed)

---

## Action: reset

Reset database to clean state.

WARNING: This will delete all data!

Ask for confirmation before proceeding.

```bash
npx supabase db reset
```

This will:
1. Drop all tables
2. Run all migrations
3. Run seed.sql

**Note**: Supabase local dev requires Docker/OrbStack running. Only one instance at a time on default ports (54321/54322). For multiple local projects, configure port offsets in `supabase/config.toml`.

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `npx supabase start` | Start local Supabase (needs Docker) |
| `npx supabase stop` | Stop local Supabase |
| `npx supabase db push` | Push migrations to remote (uses linked project) |
| `npx supabase db pull` | Pull schema from remote |
| `npx supabase db reset` | Reset local database |
| `npx supabase gen types typescript --linked` | Generate types |

## Best Practices

1. **Always use RLS** - Enable row level security on all tables
2. **Use UUIDs** - Default to UUID primary keys
3. **Add timestamps** - Include created_at and updated_at
4. **Foreign keys** - Reference auth.users for user ownership
5. **Add indexes** - Always index user_id and frequently filtered columns
6. **Policies first** - Write RLS policies before any data access code
7. **Type safety** - Regenerate types after every schema change
8. **FK ordering** - Schema SQL must create referenced tables before referencing tables
9. **One change per migration** - Easier to debug and rollback
10. **Test locally first** - Use `supabase db reset` before pushing to remote
