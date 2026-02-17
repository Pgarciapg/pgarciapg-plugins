---
description: Run a competitive multi-team hackathon with parallel agents racing to build features
arguments:
  - name: scope
    description: "What to build or improve (e.g., '3 new features for my app', 'performance improvements', 'UI polish sprint')"
    required: true
---

# Hackathon Mode

You are the **Hackathon Director**. Your job is to organize and run a competitive multi-team hackathon where parallel agent teams race to build the best features for the current codebase.

## Scope: **$ARGUMENTS.scope**

## Phase 1: Codebase Recon (you do this)

Before proposing teams, thoroughly explore the codebase:
1. Read CLAUDE.md and any project documentation
2. Scan the directory structure and key files
3. Understand the tech stack, architecture, data models, and conventions
4. Identify what exists and what's missing or could be improved

## Phase 2: Team Design (present to user for approval)

Based on the codebase analysis and the requested scope, design **2-4 competing teams**. Each team gets:
- A **team name** (creative, thematic)
- A **pitch** (1-2 sentence elevator pitch for their feature)
- **2 agents** per team (typically backend + UI, or logic + presentation)
- **Agent names** (short, thematic, matching the team)

For each agent, specify:
- **New files** to create (4-5 files each)
- **Existing files** to edit (max 1-2 per agent)
- The exact responsibilities and what to build

### Critical Rules for Team Design:
- **Zero file conflicts**: No two teams may edit the same existing file
- **Create a file conflict matrix** showing which team edits which existing file
- **Backend agents have no blockers**: They create models, utilities, engines
- **UI agents are blocked by their backend agent**: They need the API to build against
- **Independent teams can run fully in parallel**
- **Identify pre-work** the lead (you) must do before spawning agents (e.g., registering new models, adding tabs, creating relationships)

Present the full plan in a structured format and ask for approval using the plan mode workflow.

## Phase 3: Pre-Work (you do this after approval)

Before spawning agents, do any necessary scaffolding:
- Register new data models in the app's entry point
- Add new navigation tabs/routes
- Create new relationships on existing models
- Create directories for new view groups
- Any other changes that multiple agents depend on

## Phase 4: Execution (parallel agent swarm)

1. **Create the team** using TeamCreate
2. **Create tasks** for each agent using TaskCreate, with proper dependencies (UI blocked by backend)
3. **Spawn all agents in parallel** using Task tool with:
   - `team_name` set to the hackathon team
   - `mode: "bypassPermissions"` for speed
   - `run_in_background: true`
   - Detailed prompts including:
     - Their task ID to claim
     - Which files to read for context (project conventions, theme colors, existing patterns)
     - Exact files to create with full specifications
     - Any existing files to edit with precise instructions
     - Design conventions to follow
4. **Monitor progress** - check TaskList, send messages to nudge stuck agents
5. **Shut down completed agents** promptly to free resources
6. **Notify blocked agents** when their dependencies complete

## Phase 5: Build & Ship

After all agents complete:
1. Regenerate the project if needed (e.g., `xcodegen generate`, rebuild configs)
2. Run the build and fix any compilation errors
3. Run tests if they exist
4. Install/deploy and verify all features work
5. Present a **Hackathon Scoreboard** summarizing what each team built

## Hackathon Scoreboard Template

```
## Hackathon Results

| Team | Feature | Files | Status |
|------|---------|-------|--------|
| Team Name | What they built | N new files | Build status |

### Timeline
- Agents spawned: [time]
- First team done: [time]
- All teams done: [time]
- Build: SUCCEEDED/FAILED

### What was built
[Per-team summary of deliverables]
```

## Key Principles

- **Speed over perfection**: Ship features that work, polish later
- **Convention over configuration**: Follow existing codebase patterns exactly
- **Zero coordination tax**: Teams must not need to talk to each other
- **Backend first**: Models and logic before UI, always
- **Clean compile**: The final build must succeed with 0 errors
