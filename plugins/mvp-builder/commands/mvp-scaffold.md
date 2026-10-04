---
description: Scaffold a new Next.js 16 + Supabase MVP project with best practices baked in
argument-hint: "<project-name> [--skip-install]"
---

# MVP Scaffold

You are scaffolding a new MVP project with the standard tech stack (Next.js 16 + Supabase + Tailwind v4).

## Request: $ARGUMENTS

Read the project name from the request above. It becomes the folder name, so use it in lowercase with hyphens (for example `acme-portal`) and put it wherever this guide shows `<project-name>`. On the home page, replace `[Project Name]` with the readable name. If no project name was given, ask for one before anything else.

If the request includes `--skip-install` (useful for CI), add `--skip-install` to the `create-next-app` command and skip every `npm install` and `npx shadcn` command. List the skipped commands in the final setup instructions instead.

## Pre-flight Checks

1. Check if PROJECT_BRIEF.md exists in current directory
   - If yes, read it and use the requirements
   - If no, ask user for basic requirements or suggest running `/mvp-kickoff` first

2. Check if target directory already exists
   - If yes, ask user how to proceed (overwrite, different name, cancel)

## Step 1: Create Next.js Project

Run:
```bash
npx create-next-app@latest <project-name> --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```

Wait for completion before proceeding.

## Step 2: Install Dependencies

Core:
```bash
cd <project-name> && npm install @supabase/supabase-js @supabase/ssr clsx tailwind-merge
```

Extended UI toolkit (always include):
```bash
npm install @tremor/react motion @phosphor-icons/react
```

shadcn/ui setup:
```bash
npx shadcn@latest init -d
```

Then add essential shadcn components:
```bash
npx shadcn@latest add button input card table badge dialog sheet alert-dialog dropdown-menu tabs separator skeleton toast
```

Dev dependencies:
```bash
npm install -D @types/node prettier prettier-plugin-tailwindcss
```

## Step 3: Tailwind v4 Light-Mode Fix

Since macOS is in dark mode, Tailwind v4 will activate dark utilities via `prefers-color-scheme`. For light-mode-only projects, add this to `src/app/globals.css` BEFORE any other directives:

```css
@custom-variant dark (&:is(.dark *));
```

This prevents dark mode from activating unless explicitly toggled with a `.dark` class on `<html>`.

**IMPORTANT**: Any `@import url(...)` statements (Google Fonts, etc.) MUST come BEFORE `@tailwind` directives. CSS import order matters.

## Step 4: Create Project Structure

Create these directories:
```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   └── dashboard/
│   ├── api/
│   └── globals.css
├── components/
│   ├── ui/          (populated by shadcn)
│   └── layout/
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── middleware.ts
│   └── utils.ts
├── hooks/
├── types/
│   └── database.ts
└── proxy.ts          (Next.js 16 — NOT middleware.ts)
```

## Step 5: Create Core Files

### lib/utils.ts
```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### lib/supabase/client.ts
```typescript
import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

### lib/supabase/server.ts
```typescript
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing sessions.
          }
        },
      },
    }
  );
}
```

### lib/supabase/middleware.ts
```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // MUST call getUser() — refreshes the session token.
  // Using getSession() instead will cause silent auth failures after token expiry.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Protect dashboard routes
  if (!user && request.nextUrl.pathname.startsWith("/dashboard")) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
```

### src/proxy.ts (Next.js 16 — replaces middleware.ts)
```typescript
import { type NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
```

**IMPORTANT**: Place `proxy.ts` at `src/proxy.ts` (same level as `app/`) when using `--src-dir`. This is the Next.js 16 replacement for `middleware.ts`. It runs on Node.js runtime (not Edge), so you get full Node.js API access.

### types/database.ts
```typescript
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

// Generate with: npx supabase gen types typescript --linked > src/types/database.ts
export interface Database {
  public: {
    Tables: {
      // Your tables will be generated here
    };
    Views: {};
    Functions: {};
    Enums: {};
  };
}
```

### .env.local.example
```
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Site URL (set to production domain when deploying)
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### .prettierrc
```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

## Step 6: Set Up Environment Variables

Check `~/.env-keys/` for any keys relevant to the project brief:
- If Stripe is needed: read STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY from ~/.env-keys/
- If AI is needed: skip — AI Gateway uses OIDC (auto-provisioned by `vercel env pull`)
- If other keys are needed: check ~/.env-keys/ first before asking the user

Create `.env.local` with Supabase credentials (ask user) and any keys found in ~/.env-keys/.

## Step 7: Create Auth Pages

### app/(auth)/login/page.tsx
```typescript
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-6 p-4">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-bold">Welcome back</h1>
          <p className="text-zinc-500">Sign in to your account</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
```

### app/(auth)/login/login-form.tsx
```typescript
"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
    router.refresh(); // Force Server Components to re-render with new auth state
  };

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      <div className="space-y-2">
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
```

## Step 8: Create Dashboard Layout

### app/(dashboard)/layout.tsx
```typescript
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <h1 className="text-lg font-semibold">Dashboard</h1>
          <form action="/api/auth/signout" method="POST">
            <button type="submit" className="text-sm text-zinc-500 hover:text-zinc-900">
              Sign out
            </button>
          </form>
        </div>
      </header>
      <main className="mx-auto max-w-7xl p-4">{children}</main>
    </div>
  );
}
```

### app/(dashboard)/dashboard/page.tsx
```typescript
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Welcome back!</h2>
        <p className="text-zinc-500">{user?.email}</p>
      </div>

      <div className="rounded-lg border bg-white p-6">
        <p className="text-zinc-500">Your dashboard content goes here.</p>
      </div>
    </div>
  );
}
```

### app/api/auth/signout/route.ts
```typescript
import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function POST() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  return NextResponse.redirect(new URL("/login", process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"));
}
```

## Step 9: Update Home Page

### app/page.tsx
```typescript
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-4">
      <h1 className="text-4xl font-bold">[Project Name]</h1>
      <p className="text-zinc-500">Your MVP starts here.</p>
      <div className="flex gap-4">
        <Button asChild>
          <Link href="/login">Sign in</Link>
        </Button>
        <Button variant="secondary" asChild>
          <Link href="/signup">Sign up</Link>
        </Button>
      </div>
    </div>
  );
}
```

## Step 10: Git Init & First Commit

```bash
cd <project-name>
git init
git add -A
git commit -m "Initial MVP scaffold: Next.js 16 + Supabase + shadcn/ui + Tailwind v4"
```

## Step 11: Final Setup Instructions

After scaffold completes, display:

```
Project scaffolded successfully!

Next steps:

1. Set up Supabase:
   - Go to https://supabase.com/dashboard
   - Create new project
   - Copy URL and anon key to .env.local

2. Configure environment:
   cp .env.local.example .env.local
   # Add your Supabase credentials

3. Enable auth in Supabase:
   - Go to Authentication > Providers
   - Enable Email provider (or others as needed)

4. Link to Vercel (for AI Gateway + env management):
   vercel link
   vercel env pull

5. Start development:
   npm run dev

6. When ready to deploy:
   /mvp-ship

Useful commands:
- /mvp-db          Manage Supabase database & migrations
- /mvp-ship        Deploy to Vercel
- /mvp-status      Check project health

Stack included:
- Next.js 16 (App Router, proxy.ts, Turbopack)
- Supabase (Auth + DB + Storage)
- Tailwind v4 (light-mode safe)
- shadcn/ui (Button, Input, Card, Table, Dialog, Sheet, etc.)
- Tremor (charts & analytics)
- Motion (animations)
- Phosphor Icons (9000+ icons)
```

## Important Notes

- All files use TypeScript strict mode
- Tailwind v4 is configured with light-mode fix for macOS dark mode
- Uses `proxy.ts` (Next.js 16) not `middleware.ts`
- All request APIs are async: `await cookies()`, `await headers()`, etc.
- shadcn/ui provides the component library — never build raw HTML controls
- Supabase SSR is set up for both client and server components
- Proxy handles auth session refresh via getUser() (not getSession())
- Protected routes redirect to login
- `@supabase/auth-helpers-nextjs` is deprecated — we use `@supabase/ssr`
