---
description: Start a new MVP project - gather requirements, define scope, and create project brief
argument-hint: "<project-name> [client=<client-name>]"
---

# MVP Kickoff

You are starting a new MVP project. Your goal is to gather requirements, define scope, and create a comprehensive project brief.

## Request: $ARGUMENTS

Read the project name and client from the request above. The project name comes first; the client is optional and may be given as `client=<name>` or after the project name. Names can be several words if quoted, for example `/mvp-kickoff "Acme Portal" client="Acme Corp"`. If no project name was given, ask for one before anything else.

## Project Info
- **Project Name**: [project name from the request]
- **Client**: [client from the request, or "not specified"]

## Phase 1: Discovery

Ask the user these questions ONE AT A TIME using the AskUserQuestion tool:

### 1. Core Problem
"What problem does this MVP solve? Who is the target user?"

### 2. Key Features
"What are the 3-5 MUST-HAVE features for launch? (Be ruthless - MVP means minimum)"

### 3. User Authentication
Options:
- Supabase Auth (email/password, magic link, social login) — default, fastest
- Clerk (polished UI, org management, Vercel Marketplace native) — best for multi-tenant SaaS
- No auth needed

### 4. Data Requirements
"What data needs to be stored? (users, products, orders, content, etc.)"

### 5. Third-party Integrations
"Any external services needed?"
Common ones:
- Payments (Stripe — keys already available at ~/.env-keys/)
- Email (Resend)
- AI features (AI SDK + AI Gateway — no API keys needed on Vercel)
- Analytics (Vercel Analytics — zero-config)
- File uploads (Vercel Blob or Supabase Storage)

### 6. Design Direction
Options:
- Minimal / Clean (shadcn/ui defaults, fastest to build)
- Modern / Polished (shadcn/ui + Tremor charts + Motion animations + Phosphor icons)
- Design-first (prototype in Google Stitch first, then implement)
- Custom branded (provide brand guidelines or live site URL for palette extraction)

### 7. AI Features
"Does the MVP need any AI capabilities?"
Options:
- None
- Chat / conversational UI (AI SDK + AI Gateway + AI Elements)
- Content generation (structured output, summaries, etc.)
- Image generation (AI Gateway + Gemini 3.1 Flash Image Preview)

### 8. Timeline Priority
Options:
- Speed (ship in days, iterate later)
- Balance (solid foundation, reasonable timeline)
- Quality (more upfront work, less tech debt)

## Phase 2: Generate Project Brief

After gathering all requirements, create a PROJECT_BRIEF.md file in the current directory with:

```markdown
# [Project Name] - MVP Brief

## Overview
- **Client**: [client name]
- **Project**: [project name]
- **Created**: [date]
- **Timeline Priority**: [speed/balance/quality]

## Problem Statement
[What problem this solves and for whom]

## Target Users
[Primary user persona]

## Core Features (MVP Scope)
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]
...

## Tech Stack
- **Framework**: Next.js 16 (App Router, Turbopack, proxy.ts)
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Extended UI**: Tremor (charts), Motion (animations), Phosphor Icons
- **Auth**: [Supabase Auth / Clerk]
- **AI**: [AI SDK v6 + AI Gateway / None]
- **Hosting**: Vercel
- **Additional**: [any integrations]

## Data Model (Initial)
[List main entities and relationships]

## Authentication
- Type: [chosen auth type]
- Providers: [if social login]

## AI Integration
- [Describe AI features if any]
- Model: [e.g., anthropic/claude-sonnet-4.6 via AI Gateway]

## Third-party Services
- [Service 1]: [purpose]
- [Service 2]: [purpose]

## Design Direction
- Style: [chosen style]
- Key considerations: [notes]

## Out of Scope (v1)
[Features explicitly NOT in MVP]

## Success Metrics
[How we'll know MVP is successful]

## Next Steps
1. Run `/mvp-scaffold` to generate project structure
2. Set up Supabase project
3. Configure Vercel deployment (`vercel link` + `vercel env pull`)
4. Begin feature development
```

## Phase 3: Recommendations

After creating the brief, provide:

1. **Estimated complexity**: Simple / Medium / Complex
2. **Suggested project structure** based on features
3. **Supabase tables** needed (high-level, ordered by FK dependencies)
4. **Recommended order** for building features
5. **Potential risks** or technical challenges
6. **API keys available** at ~/.env-keys/ that are relevant to this project

## Important Notes

- Keep scope MINIMAL - push back on feature creep
- Default to built-in Supabase features over custom solutions
- Prioritize features that validate the core hypothesis
- Suggest what can be manual/admin-only in v1
- Default to AI Gateway for any AI features (no API keys needed on Vercel via OIDC)
- Recommend shadcn/ui for UI components — never build raw HTML controls

When complete, remind the user they can run `/mvp-scaffold <project-name>` to generate the project, using the project name in lowercase with hyphens (it becomes the folder name).
