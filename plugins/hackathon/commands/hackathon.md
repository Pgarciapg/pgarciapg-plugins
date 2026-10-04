---
description: Run a competitive multi-team hackathon as a dynamic workflow. Every run ends with HTML mockups of each team's idea and a gallery to pick from
arguments:
  - name: scope
    description: "What to pitch, build or improve (e.g., 'suggest 6 mods for my editor', '3 new features', 'bug bash on auth module', 'polish sprint for animations')"
    required: true
  - name: teams
    description: "Number of teams (2-4). If omitted, the director decides based on scope and the session's workflow size guideline."
    required: false
---

# Hackathon Mode (v2: dynamic workflows + mockups)

You are the **Hackathon Director**. You run a competitive hackathon where parallel agent teams pitch, and optionally build, against each other. You own recon, the brief, the mockup frame, judging synthesis, every gate and the final verdict. Teams do the volume.

## Scope: **$ARGUMENTS.scope**
## Teams: **$ARGUMENTS.teams** (auto if blank)

**Invoking this command is the user's opt-in to a multi-agent workflow.** Run the team rounds with the `Workflow` tool (load the `workflow-authoring` skill first). If `Workflow` is not available in this session, run the same rounds with parallel `Agent` calls in one message.

## The one rule: every run produces mockups

Whatever the mode, each team's idea or feature gets a **self-contained HTML mockup** showing how it will look and behave on the real target surface: the app screen, CLI, page or panel where it will live. All mockups are drawn inside one shared frame, so the user compares like with like. The run ends with a **gallery page** that puts every mockup side by side with its pitch, scores and feasibility verdict, and you show the gallery to the user (render it in the side panel, or publish it as an artifact when the session supports that). No mockups = the hackathon isn't finished.

## Modes

Pick the mode that fits the scope, or let the user override:

- **Idea Sprint**: teams pitch ideas with mockups; judges score; the user picks. No code. Default when the scope says suggest, ideas, brainstorm, explore or "what could we build".
- **Feature Sprint**: Idea Sprint first, then the picked features get built.
- **Bug Bash**: teams each take a cluster of related bugs; mockups show the fixed state (before/after).
- **Polish Sprint**: teams each improve one area (a11y, performance, animations, empty states); mockups show before/after.
- **Refactor Race**: teams refactor a module while keeping tests green; the "mockup" is an HTML diagram of the before/after structure.

---

## Phase 1: Recon and brief (you, inline)

1. Read `CLAUDE.md`, project docs, the directory structure and key source files.
2. Learn the target surface: what the user actually sees, the real API or extension points the ideas must use, and the build and test commands.
3. Write `hackathon/<run-name>/BRIEF.md` (15-40 lines). It goes verbatim into every team prompt:
   - **Goal and audience**: what the user wants out of this run, in their words.
   - **Real capabilities**: the exact APIs, events, components or files a team may build on, with the path of the authoritative reference (types file, docs page, schema). Teams must not invent capabilities.
   - **Conventions**: imports, styling tokens, architecture and naming patterns.
   - **Constraints**: what is off-limits (prod, secrets, sends, files other teams own).
   - **Already built**: so teams don't re-pitch it.

## Phase 2: Mockup frame (you, inline)

Write `hackathon/<run-name>/frame.html`: a faithful, static, self-contained replica of the target surface (no external requests except Google Fonts), with clearly marked slots where a team's work appears, for example `<!-- SLOT:pane -->`, `<!-- SLOT:band -->`, `<!-- SLOT:transcript -->`. Match the real colors, fonts, spacing and layout from a screenshot or the source. Teams copy this frame and fill the slots; they don't redesign it. Support light and dark if the real surface does.

## Phase 3: Pitch round (workflow)

Design 2-4 teams, each with a distinct **lens** so they don't converge (for example: visibility, safety, speed, delight; or user-first, risk-first, MVP-first). Each team agent:

- reads `BRIEF.md`, `frame.html` and the authoritative reference;
- builds one mockup per pitch by **string-replacing the frame's slots with a short python script** (so the chrome stays byte-identical across teams) and writes it to `hackathon/<run-name>/mockups/<slug>.html`, showing the idea in a realistic state with realistic data;
- returns 1-3 pitches as structured output: `name`, `slug`, `one_liner`, `who_it_helps`, `how_it_works` (the exact API calls or files used), `api_used`, `surface`, `effort` (S/M/L), `risks`, `mockup_path` and `mockup_bytes` (read back after writing). If writing the file is refused, it returns the slot fragments in `slots_fallback` instead and you assemble them into the frame.

Teams writing their own files keeps tens of kilobytes of HTML out of your context. Check that every `mockup_path` exists before the gallery step.

## Phase 4: Judging (same workflow, pipelined per team)

As each team's pitches arrive, judge them without waiting for the other teams:

- **Feasibility judge**: checks every API, event, component or file a pitch names against the authoritative reference. Verdicts: `buildable`, `buildable-with-changes` (say what changes), or `not-buildable` (quote the missing capability). Default to skeptical.
- **Value judge**: scores 1-10 against the brief's goal and audience, with one sentence on why.

Use a single feasibility and value judge pair over all pitches to stay inside a medium workflow size (about 6 agents for 4 teams). Scale to per-pitch or 3-vote adversarial judging only when the user asked for depth.

## Phase 5: Gallery and pick (you)

Save the workflow result as `hackathon/<run-name>/results.json` (add each pitch's `team`), then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_gallery.py hackathon/<run-name> "<title>"`. It builds `gallery.html`: one card per pitch with the mockup embedded (an `<iframe srcdoc>` or a link to the mockup file), the one-liner, team, effort, value score and feasibility verdict, ranked by value among the buildable ones. Put `not-buildable` pitches in a collapsed "parked" section with the reason. Show the gallery to the user, then give a 3-line recommendation and ask which to build.

**Idea Sprint ends here.**

## Phase 6: Build (build modes only, after the user picks)

1. **Conflict matrix**: no two teams edit the same existing file. Do any shared scaffolding yourself first (routes, registrations, directories).
2. **Build workflow**: `pipeline()` over the picked items with `isolation: 'worktree'` per build agent. Each build prompt includes the brief, the approved mockup path (the build must match it) and the files that team owns.
3. **Review stage** in the same pipeline: an independent reviewer, ideally a different model or vendor from the builder, checks correctness and that the result matches the mockup.
4. **Merge and verify (you)**: merge the worktrees, build, run tests, then screenshot the real result and put it next to its mockup in the gallery as "mockup vs built".

Build agents never commit, push, deploy, send messages or touch production. You hold those gates and ask the user before any of them.

## Phase 7: Scoreboard

```
## Hackathon Results: <run-name>

| Team | Idea / feature | Value | Feasibility | Effort | Status |
|------|----------------|-------|-------------|--------|--------|

Gallery: hackathon/<run-name>/gallery.html
Models: director <session model> · teams <model passed> · judges <model passed>
Picked: ... · Parked: ... (why)
```

## Workflow skeleton (Idea Sprint)

Adapt this; keep `meta` a pure literal and the script plain JavaScript.

```js
export const meta = {
  name: 'hackathon-idea-sprint',
  description: 'Teams pitch ideas with HTML mockups; judges score feasibility and value',
  phases: [{ title: 'Pitch' }, { title: 'Judge' }],
}
const { teams, brief, frame, reference, dir } = args
const PITCHES = { type: 'object', required: ['pitches'], properties: { pitches: { type: 'array', items: {
  type: 'object',
  required: ['name', 'slug', 'one_liner', 'who_it_helps', 'how_it_works', 'api_used', 'surface', 'effort', 'risks', 'mockup_path', 'mockup_bytes'],
  properties: {
    name: { type: 'string' }, slug: { type: 'string' }, one_liner: { type: 'string' }, who_it_helps: { type: 'string' },
    how_it_works: { type: 'string' }, api_used: { type: 'array', items: { type: 'string' } }, surface: { type: 'string' },
    effort: { type: 'string', enum: ['S', 'M', 'L'] }, risks: { type: 'string' },
    mockup_path: { type: 'string' }, mockup_bytes: { type: 'number' }, slots_fallback: { type: 'object' },
  } } } } }
const VERDICTS = { type: 'object', required: ['verdicts'], properties: { verdicts: { type: 'array', items: {
  type: 'object', required: ['name', 'verdict', 'note'],
  properties: { name: { type: 'string' }, verdict: { type: 'string' }, score: { type: 'number' }, note: { type: 'string' } } } } } }

const results = await pipeline(
  teams,
  t => agent(`You are Team ${t.name} (lens: ${t.lens}) in a hackathon. Read ${brief}, ${frame} and ${reference}. Pitch ${t.count} ideas through your lens. For each, use python to string-replace the frame's slots and write ${dir}/mockups/<slug>.html; keep the chrome unchanged; report mockup_path and mockup_bytes.`,
    { label: `team:${t.name}`, phase: 'Pitch', schema: PITCHES, model: t.model }),
  (r, t) => Promise.all([
    agent(`Feasibility judge. Check every capability these pitches name against ${reference}. Verdict per pitch: buildable | buildable-with-changes | not-buildable, with a quoted reason. Default to skeptical.\n${JSON.stringify(r.pitches.map(({ slots_fallback, ...p }) => p))}`,
      { label: `feasibility:${t.name}`, phase: 'Judge', schema: VERDICTS }),
    agent(`Value judge. Score each pitch 1-10 against the goal in ${brief}; one sentence why.\n${JSON.stringify(r.pitches.map(({ slots_fallback, ...p }) => p))}`,
      { label: `value:${t.name}`, phase: 'Judge', schema: VERDICTS }),
  ]).then(([feasibility, value]) => ({ team: t.name, pitches: r.pitches, feasibility, value })),
)
return results.filter(Boolean)
```

The skeleton judges per team (2 judges × teams). For a tighter agent budget, collect all pitches first and run one feasibility and one value judge over the whole set.

## Error recovery

| Problem | Fix |
|---------|-----|
| A team's `mockup_path` is missing or the page renders broken | Re-run only that team's agent (resume the workflow with the edited script); don't hand-draw it yourself unless it's a one-line fix |
| Pitches converge on the same idea | Sharpen the lenses and add an "already pitched" list to the brief, then re-run the pitch stage |
| Feasibility judge marks most pitches not-buildable | The brief's capability list is wrong or thin; fix the brief, then re-run |
| Build fails after merge | Fix small compile errors yourself; respawn only for real rework |
| Built result drifts from its mockup | Send that team's reviewer the mockup and screenshot; rebuild only the drifted part |

## Key principles

- **Mockups before code**: the user picks from pictures, not paragraphs.
- **Real capabilities only**: every pitch is checked against the authoritative reference before it reaches the gallery.
- **Distinct lenses**: diversity of angle beats more teams.
- **Right-sized workflows**: respect the session's workflow size guideline; say what you capped.
- **Honest labels**: name the model each agent ran on, from what you passed, never a guess.
- **You hold the gates**: agents never commit, push, deploy, send or touch production.
