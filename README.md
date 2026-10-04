# Pablo's Claude Code Plugins

A marketplace of plugins for Claude Code.

## Installation

Add this marketplace to Claude Code:

```
/plugins marketplace add https://github.com/Pgarciapg/pgarciapg-plugins
```

Then browse and install plugins with `/plugins`.

## Available Plugins

### design-team
A multi-agent design department for Claude Code: UX, visual, copy, accessibility, tokens, and implementation.

**Commands:** `/kickoff`, `/critique`, `/spec`, `/tokens`

**Skills:** mobile-polish, vercel-design-guidelines

**Agents:** a11y-reviewer, copywriter, design-lead, fe-implementer, ux-designer, visual-designer

---

### domain-scout
AI-powered domain name finder that analyzes your codebase, generates creative name suggestions, and searches registrars for availability and pricing.

**Commands:** `/domain-scout`

**Skills:** name-generation

**Agents:** codebase-analyzer, domain-searcher

Searches Namecheap, Porkbun, GoDaddy, Squarespace Domains, and Cloudflare. Requires Chrome + Claude in Chrome extension.

---

### hackathon
Run competitive multi-team hackathons as dynamic workflows. Teams pitch with HTML mockups, one feasibility judge and one value judge score every pitch, and you pick from a gallery before anything gets built. Build modes use isolated worktrees and a second-model review, and the gallery then shows each mockup next to a screenshot of what was built. Modes: Idea Sprint, Feature Sprint, Bug Bash, Polish Sprint, Refactor Race.

**Commands:** `/hackathon <scope> [teams=2-4]`

---

### mvp-builder
End-to-end MVP builder for client projects using Next.js, Supabase, and Vercel. Orchestrates design, scaffolding, development, and deployment workflows.

**Commands:** `/mvp-kickoff`, `/mvp-scaffold`, `/mvp-db`, `/mvp-ship`, `/mvp-status`

**Skills:** nextjs-supabase-stack

**Agents:** feature-builder, supabase-expert

---

### whiteboard
Generate a single self-contained HTML whiteboard that visually recaps the current work — Mermaid diagrams + tables + a where-we-are header — and opens it in the browser.

**Skills:** whiteboard

---

### teach-session
A rigorous tutor skill that verifies you deeply understand a coding session, PR, or concept — restate-first, drill-the-why, quiz with AskUserQuestion, and a color-coded HTML mastery checklist. Great for onboarding and for understanding agent-written code before you ship it.

**Skills:** teach-session

---

## License

MIT
