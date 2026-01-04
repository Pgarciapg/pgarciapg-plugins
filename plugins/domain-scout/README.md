# Domain Scout

AI-powered domain name finder for Claude Code. Analyzes your codebase to understand your project, generates creative domain name suggestions, and searches multiple registrars for availability and pricing.

## Features

- **Codebase Analysis**: Automatically analyzes your project's README, package.json, and source files to understand what you're building
- **Smart Name Generation**: Generates 5 creative, brandable domain name suggestions based on your project
- **Multi-Registrar Search**: Searches Namecheap, Porkbun, GoDaddy, Google Domains, and Cloudflare simultaneously
- **Price Comparison**: Presents results in a simple table showing availability and prices across registrars
- **Preference Memory**: Saves your preferred extensions and registrars for future searches

## Usage

```
/domain-scout
```

The plugin will:
1. Analyze your codebase to understand the project
2. Generate 5 domain name suggestions
3. Ask for your preferences (extensions, registrars, budget)
4. Search registrars using browser automation
5. Present a comparison table of available domains and prices

## Default Settings

- **Extensions**: .com, .io, .app, .dev, .co, .ai
- **Registrars**: Namecheap, Porkbun, GoDaddy, Google Domains, Cloudflare

## Requirements

- Chrome browser with Claude in Chrome extension installed
- Claude Code CLI

## Components

- **Command**: `/domain-scout` - Main entry point
- **Agents**:
  - `codebase-analyzer` - Analyzes project and generates names
  - `domain-searcher` - Searches registrars via browser automation
- **Skill**: `name-generation` - Domain naming best practices

## Customization

Create `.claude/domain-scout.local.md` in your project to save default preferences:

```yaml
---
extensions:
  - .io
  - .app
  - .dev
registrars:
  - namecheap
  - porkbun
budget: 50
---
```
