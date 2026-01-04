---
description: Find available domain names by analyzing your codebase and searching registrars
allowed-tools: Read, Glob, Grep, Bash, Task, AskUserQuestion, mcp__claude-in-chrome__*
---

# Domain Scout Workflow

You are orchestrating a domain name discovery workflow. Follow these steps precisely:

## Step 1: Analyze the Codebase

Use the Task tool to launch the `codebase-analyzer` agent with this prompt:

"Analyze this codebase to understand what the project does. Read the README, package.json, and key source files. Based on your analysis, generate exactly 5 creative, brandable domain name suggestions. Return the names as a simple numbered list."

Wait for the agent to return 5 name suggestions.

## Step 2: Present Names and Collect Preferences

Present the 5 suggested domain names to the user.

Then use the AskUserQuestion tool to collect their preferences with these questions:

**Question 1 - Domain Extensions:**
- Header: "Extensions"
- Question: "Which domain extensions would you like to search?"
- Options: ".com", ".io", ".app", ".dev", ".co", ".ai"
- multiSelect: true

**Question 2 - Registrars:**
- Header: "Registrars"
- Question: "Which domain registrars should I search?"
- Options: "Namecheap", "Porkbun", "GoDaddy", "Google Domains", "Cloudflare"
- multiSelect: true

**Question 3 - Budget:**
- Header: "Budget"
- Question: "What's your maximum budget per domain (first year)?"
- Options: "$15 or less", "$15-30", "$30-50", "No limit"
- multiSelect: false

## Step 3: Confirm Search Parameters

After collecting preferences, summarize the search parameters:
- Names to search (the 5 suggestions)
- Selected extensions
- Selected registrars
- Budget range

Ask the user: "Ready to search these domains? You can also modify the names or add your own before I search."

## Step 4: Search Domains

Once the user confirms, use the Task tool to launch the `domain-searcher` agent with this prompt:

"Search for domain availability and pricing.
Names: [list the names]
Extensions: [list selected extensions]
Registrars: [list selected registrars]
Budget: [selected budget]

Use browser automation to search each registrar and compile results into a table."

## Step 5: Present Results

Present the results from the domain-searcher agent as a clean table showing:
- Domain name
- Registrar
- Price (first year)
- Available (Yes/No)

Sort by price (cheapest first) and highlight any domains within budget.

Offer to:
- Search more name variations
- Try different extensions
- Check a specific registrar in more detail
