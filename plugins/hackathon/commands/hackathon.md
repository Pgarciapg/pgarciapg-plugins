---
description: Run a competitive multi-team hackathon as a dynamic workflow. Every run ends with HTML mockups of each team's idea and a gallery to pick from
argument-hint: "<scope> [teams=2-4]"
---

# Hackathon Mode (v2.1: dynamic workflows + mockups)

You are the **Hackathon Director**. You run a competitive hackathon where parallel agent teams pitch, and optionally build, against each other. You own recon, the brief, the mockup frame, judging synthesis, every gate and the final verdict. Teams do the volume.

## Request: $ARGUMENTS

Read the scope from the request above. If it names a team count ("teams=3", "3 teams"), use it (2-4); otherwise pick 2-4 from the scope and the session's workflow size guideline. If the request is empty, ask for a scope before doing anything else.

**Invoking this command is the user's opt-in to a multi-agent workflow.** Run the team rounds with the `Workflow` tool (load the `workflow-authoring` skill first). If `Workflow` is not available in this session, run the same rounds with parallel `Agent` calls in one message.

Workflow agents also receive the user's most recent chat message as an instruction that outranks their task. If the user sends a side remark while a run is in flight ("check how it looks on my phone"), every agent launched afterwards treats it as its mandate. Check that each agent's output stayed on task, and re-run any that drifted.

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
3. Create the run directory `hackathon/<run-name>/` with a `mockups/` folder, in the target project. In a git repo, add `hackathon/` and `.claude/worktrees/` to `.git/info/exclude` (local only, never committed) so run files and build worktrees never show up in diffs or get swept into a commit.
4. Write `hackathon/<run-name>/BRIEF.md` (15-40 lines). Every team reads it:
   - **Goal and audience**: what the user wants out of this run, in their words.
   - **Real capabilities**: the exact APIs, events, components or files a team may build on, with the path of the authoritative reference (types file, docs page, schema). Teams must not invent capabilities.
   - **Conventions**: imports, styling tokens, architecture and naming patterns.
   - **Constraints**: what is off-limits (prod, secrets, sends, files other teams own).
   - **Already built**: so teams don't re-pitch it.
   - **Mockup surface**: every slot in the frame, what goes in it, and any default content to start from.

## Phase 2: Mockup frame (you, inline)

Write `hackathon/<run-name>/frame.html`: a faithful, static, self-contained replica of the target surface (no external requests except Google Fonts), with clearly marked slots where a team's work appears, for example `<!-- SLOT:caption -->`, `<!-- SLOT:pane -->`, `/* SLOT:css */`. Match the real colors, fonts, spacing and layout from a screenshot or the source (reusing the real stylesheet is best). Teams copy this frame and fill the slots; they don't redesign it. Support light and dark if the real surface does.

- Give the frame a fixed size and declare it: `<meta name="hackathon:size" content="1200x780">`. The gallery scales each mockup from that size; without it, 1352x860 is assumed.
- For Bug Bash and Polish Sprint, put two copies of the surface side by side labelled Before and After, each with its own slots (`SLOT:before_list`, `SLOT:after_list`).
- Render the frame once with default content and look at it before any team sees it.

## Phase 3: Pitch round (workflow)

Design 2-4 teams, each with a distinct **lens** so they don't converge (for example: visibility, safety, speed, delight; or user-first, risk-first, MVP-first). Each team agent:

- reads `BRIEF.md`, `frame.html` and the authoritative reference;
- builds one mockup per pitch by **string-replacing the frame's slots with a short python script** (so the chrome stays byte-identical across teams) and writes it to `hackathon/<run-name>/mockups/<slug>.html`, showing the idea in a realistic state with realistic data. Slugs start with the team name, so they never collide;
- keeps scratch files in `hackathon/<run-name>/work/<team>/`, and does not open a browser or use browser tools (you render and look at the mockups);
- returns 1-3 pitches as structured output: `name`, `slug`, `one_liner`, `who_it_helps`, `how_it_works` (the exact API calls or files used), `api_used`, `surface`, `effort` (S/M/L), `risks`, `mockup_path` and `mockup_bytes` (read back after writing). If writing the file is refused, it returns `mockup_path: ""`, `mockup_bytes: 0` and the slot fragments in `slots_fallback`; the gallery builder fills them into the frame.

Teams writing their own files keeps tens of kilobytes of HTML out of your context.

## Phase 4: Judging (same workflow)

- **Feasibility judge**: checks every API, event, component or file a pitch names against the authoritative reference. Verdicts: `buildable`, `buildable-with-changes` (say what changes), or `not-buildable` (quote the missing capability). Default to skeptical.
- **Value judge**: scores each pitch 1-10 (an integer) against the brief's goal and audience, with one sentence on why.

The skeleton runs **one feasibility judge and one value judge over all pitches**, after every team has pitched. That barrier is deliberate: each judge sees the whole set, so scores are calibrated across teams. Agent count = teams + 2 (6 for 4 teams), inside a medium workflow size. Per-pitch or 3-vote adversarial judging only when the user asks for depth and the size guideline allows it; say what you capped.

## Phase 5: Gallery and pick (you)

1. Save the workflow's return value as-is to `hackathon/<run-name>/results.json` (it is already `{pitches, teams_missing}` with team, feasibility and value joined onto each pitch).
2. Check every `mockup_path` exists, open two or three mockups, and re-run any team whose mockup is missing or broken (see Error recovery).
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_gallery.py hackathon/<run-name> "<title>" --artifact "<page name>"`. It writes `gallery.html` and `gallery.artifact.html`: one card per pitch with the mockup embedded in a sandboxed `<iframe srcdoc>`, the one-liner, team, effort, value score and feasibility verdict, ranked by value. `not-buildable` pitches go in a "parked" section with the reason. It tolerates missing fields and prints warnings for missing mockups; read them.
4. Show the gallery to the user (publish `gallery.artifact.html` as a private artifact when the session supports artifacts, else render `gallery.html`), then give a 3-line recommendation and ask which to build.

**Idea Sprint ends here.**

## Phase 6: Build (build modes only, after the user picks)

1. **Conflict matrix**: write down which files each pick creates or edits. No two builders may edit the same existing file. In a small codebase most UI features touch the same central file; either do shared scaffolding yourself first (an extension point, a registration, new empty files each builder owns), or build those picks one after another instead of in parallel. Files are not the only shared surface: two features that restructure the same DOM element, CSS selector, event or storage key collide at runtime even with disjoint files, and their tests still pass. List those surfaces in the matrix too and give each feature its own mount point in the scaffolding.
2. **Commit the scaffolding first, on a local branch, after asking the user.** Build worktrees start from the last commit of the repo the session is in, so uncommitted scaffolding and the untracked run directory are not in them. Pass every run-dir path to builders as an absolute path into the main checkout. Make sure the session's working directory is the target repo before starting the build workflow.
3. **Build workflow**: `pipeline()` over the picks with `isolation: 'worktree'` per build agent (skeleton below). Create `logs/` and `patches/` in the run directory first. Each build prompt includes the brief, the approved mockup path (the build must match it) and the files that builder owns.
4. **Review stage** in the same pipeline: an independent reviewer on a different model from the builder (and, when the `codex` CLI is installed, a read-only Codex pass as a second vendor) runs the tests against the worktree, checks that nothing outside the owned files changed, and compares the result with the mockup. Logs go in `hackathon/<run-name>/logs/`, never inside a folder a builder or Codex owns.
5. **Merge and verify (you)**: for each item the reviewer passed, stage inside its worktree and apply the patch to the main checkout:
   `git -C <worktree> add -A && git -C <worktree> diff --cached --binary > hackathon/<run-name>/patches/<slug>.patch`, then `git apply --check` and `git apply` it in the main checkout. Run the build and tests once on the merged result, and render it: features that each pass review alone can still overlap once merged.
6. **Mockup vs built**: screenshot the real result at the frame's size (for phone widths use device emulation; headless Chrome's `--window-size` won't go below about 500 px), add `built_screenshot` (path), `built_note` and `status: "built"` to that pitch in `results.json`, and rebuild the gallery. Each built card then shows the mockup and the built screenshot side by side.
7. Clean up only after the user is happy: `git worktree remove <worktree>` and delete its `worktree-*` branch.

Build agents never commit, push, deploy, send messages, install packages or touch production. You hold those gates and ask the user before any of them.

## Phase 7: Scoreboard

```
## Hackathon Results: <run-name>

| Team | Idea / feature | Value | Feasibility | Effort | Status |
|------|----------------|-------|-------------|--------|--------|

Gallery: hackathon/<run-name>/gallery.html (artifact link if published)
Models: director <session model> · teams <model passed> · judges <model passed> · builders/reviewers <model passed>
Picked: ... · Parked: ... (why)
```

Label each role with the model you passed in `model`; a role you didn't pass a model for ran on the session model.

## Workflow skeleton (Idea Sprint)

Pass `args` as a JSON object (not a string), with absolute paths:
`{ teams: [{ name, lens, count, model? }], brief, frame, reference, dir, judge_model? }`. Keep `meta` a pure literal and the script plain JavaScript.

```js
export const meta = {
  name: 'hackathon-idea-sprint',
  description: 'Teams pitch ideas with HTML mockups; one feasibility judge and one value judge score every pitch',
  phases: [{ title: 'Pitch' }, { title: 'Judge' }],
}
const { teams, brief, frame, reference, dir, judge_model } = args
const PITCHES = { type: 'object', required: ['pitches'], properties: { pitches: { type: 'array', items: {
  type: 'object',
  required: ['name', 'slug', 'one_liner', 'who_it_helps', 'how_it_works', 'api_used', 'surface', 'effort', 'risks', 'mockup_path', 'mockup_bytes'],
  properties: {
    name: { type: 'string' }, slug: { type: 'string' }, one_liner: { type: 'string' }, who_it_helps: { type: 'string' },
    how_it_works: { type: 'string' }, api_used: { type: 'array', items: { type: 'string' } }, surface: { type: 'string' },
    effort: { type: 'string', enum: ['S', 'M', 'L'] }, risks: { type: 'string' },
    mockup_path: { type: 'string' }, mockup_bytes: { type: 'number' }, slots_fallback: { type: 'object' },
  } } } } }
const FEASIBILITY = { type: 'object', required: ['verdicts'], properties: { verdicts: { type: 'array', items: {
  type: 'object', required: ['slug', 'verdict', 'note'],
  properties: { slug: { type: 'string' }, verdict: { type: 'string', enum: ['buildable', 'buildable-with-changes', 'not-buildable'] }, note: { type: 'string' } } } } } }
const VALUE = { type: 'object', required: ['scores'], properties: { scores: { type: 'array', items: {
  type: 'object', required: ['slug', 'score', 'note'],
  properties: { slug: { type: 'string' }, score: { type: 'integer', minimum: 1, maximum: 10 }, note: { type: 'string' } } } } } }

const key = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
const pitched = await parallel(teams.map(t => () => agent(
  `You are Team ${t.name} in a hackathon. Your lens: ${t.lens}. Read ${brief} (goal, real capabilities, mockup slots), ${frame} and ${reference}. ` +
  `Pitch ${t.count} distinct ideas through your lens, using only capabilities the reference proves. For each idea: slug = "${key(t.name)}-<short-name>"; ` +
  `with a short python script, copy the frame and string-replace only the slots the brief names (everything else stays byte-identical), ` +
  `then write ${dir}/mockups/<slug>.html showing the idea in a realistic state with realistic data. Read the file back and report its absolute mockup_path and mockup_bytes. ` +
  `Keep scratch files in ${dir}/work/${key(t.name)}/. Do not open a browser or use browser tools. ` +
  `If a file write is refused, put the slot fragments in slots_fallback ({slot_name: html}) and report mockup_path "" and mockup_bytes 0.`,
  { label: `team:${t.name}`, phase: 'Pitch', schema: PITCHES, model: t.model })
  .then(r => r && r.pitches.map(p => ({ ...p, team: t.name })))))
const missing = teams.filter((t, i) => !pitched[i]).map(t => t.name)
if (missing.length) log(`No result from: ${missing.join(', ')}`)
const pitches = pitched.filter(Boolean).flat()

// Deliberate barrier: each judge sees every pitch, so verdicts and scores are calibrated across teams.
// Fragments are dropped when a mockup file exists, and kept so judges can see a fallback pitch.
const slim = JSON.stringify(pitches.map(({ slots_fallback, ...p }) => (p.mockup_bytes ? p : { ...p, slots_fallback })))
const [feas, value] = await parallel([
  () => agent(`Feasibility judge. For each pitch below, check every API, file or capability it names against ${reference} and ${brief}. ` +
    `Verdict: buildable | buildable-with-changes (say what changes) | not-buildable (quote the missing capability). Default to skeptical. Key each verdict by slug. Work from the text and files only: no browser, no servers.\n${slim}`,
    { label: 'judge:feasibility', phase: 'Judge', schema: FEASIBILITY, model: judge_model }),
  () => agent(`Value judge. Score each pitch below 1-10 against the goal and audience in ${brief}; one sentence why. Use the whole range; key each score by slug. Work from the text only: no browser, no servers.\n${slim}`,
    { label: 'judge:value', phase: 'Judge', schema: VALUE, model: judge_model }),
])
const find = (rows, slug) => (rows || []).find(r => key(r.slug) === key(slug)) || null
return {
  pitches: pitches.map(p => ({ ...p, feasibility: find(feas && feas.verdicts, p.slug), value: find(value && value.scores, p.slug) })),
  teams_missing: missing,
}
```

## Workflow skeleton (Build)

`args`: `{ items: [{ slug, name, mockup_path, owns: [paths], notes? }], brief, test_cmd, run_dir, builder_model?, reviewer_model? }` with absolute paths. Use a different `reviewer_model` from `builder_model`.

```js
export const meta = {
  name: 'hackathon-build',
  description: 'Build each picked feature in its own worktree, then a different model reviews it against its mockup',
  phases: [{ title: 'Build' }, { title: 'Review' }],
}
const { items, brief, test_cmd, run_dir, builder_model, reviewer_model } = args
const BUILT = { type: 'object', required: ['worktree', 'files_changed', 'shell', 'tests', 'summary'], properties: {
  worktree: { type: 'string' }, files_changed: { type: 'array', items: { type: 'string' } },
  shell: { type: 'string', enum: ['worked', 'refused'] }, tests: { type: 'string' }, summary: { type: 'string' } } }
const REVIEW = { type: 'object', required: ['verdict', 'tests', 'matches_mockup', 'outside_owned', 'issues', 'reviewers'], properties: {
  verdict: { type: 'string', enum: ['pass', 'fix', 'fail'] }, tests: { type: 'string' }, matches_mockup: { type: 'boolean' },
  outside_owned: { type: 'array', items: { type: 'string' } }, issues: { type: 'array', items: { type: 'string' } },
  reviewers: { type: 'string' } } }

const results = await pipeline(items,
  it => agent(`Build "${it.name}" in your isolated git worktree (your working directory). Read the brief ${brief} and match the approved mockup ${it.mockup_path}. ` +
    `You own only: ${it.owns.join(', ')}. Do not edit anything else. ${it.notes || ''} ` +
    `Report worktree = the absolute path of your working directory. If shell commands work, run \`${test_cmd}\` until green and report the result; ` +
    `if shell commands are refused, keep going with the file tools, set shell to "refused" and tests to "not run" (the reviewer runs them). ` +
    `Never commit, push, install packages or open a browser.`,
    { label: `build:${it.slug}`, phase: 'Build', isolation: 'worktree', schema: BUILT, model: builder_model }),
  (b, it) => agent(`Review the build of "${it.name}" in the git worktree ${b.worktree}. Do not edit it. ` +
    `1) git -C ${b.worktree} status --short and git -C ${b.worktree} diff: list every changed path outside [${it.owns.join(', ')}] in outside_owned. ` +
    `2) Run \`${test_cmd}\` with that worktree as its working directory, in a subshell, and report the result. ` +
    `3) Compare what the code renders with the mockup ${it.mockup_path}. ` +
    `4) If the codex CLI is on PATH, also run a read-only second-vendor review: codex exec --sandbox read-only --skip-git-repo-check --cd ${b.worktree} "<your review question>" < /dev/null > ${run_dir}/logs/review-${it.slug}.log 2>&1, and fold in its findings. ` +
    `Set reviewers to the models that actually ran. Verdict: pass | fix | fail.`,
    { label: `review:${it.slug}`, phase: 'Review', schema: REVIEW, model: reviewer_model })
    .then(r => ({ slug: it.slug, build: b, review: r })),
)
return results.filter(Boolean)
```

## Error recovery

| Problem | Fix |
|---------|-----|
| A team's `mockup_path` is missing or the page renders broken | Re-run only that team's agent (resume the workflow with the edited script); don't hand-draw it yourself unless it's a one-line fix |
| A team returned no result (`teams_missing`) | Re-run that team alone, then re-run the judges; the gallery notes missing teams until then |
| Pitches converge on the same idea | Sharpen the lenses and add an "already pitched" list to the brief, then re-run the pitch stage |
| Feasibility judge marks most pitches not-buildable | The brief's capability list is wrong or thin; fix the brief, then re-run |
| Shell commands are refused inside worktree builders ("isolation context lost") | Builders keep working with the file tools (the skeleton already allows this) and the reviewer runs the tests; or, when the conflict matrix gives every builder disjoint files, build without isolation in the main checkout |
| Agents drift into side work (opening a browser, starting servers, long self-checks) | Usually a user message sent mid-run (see the note at the top). Keep the agent's output if it is on task; otherwise re-run it once the user's latest message is about the run |
| A reviewer is refused for writing security bypass probes | Ask for a static review of the diff instead (a read-only Codex pass works) |
| Build fails after merge | Fix small compile errors yourself; respawn only for real rework |
| Built result drifts from its mockup | Send that team's reviewer the mockup and screenshot; rebuild only the drifted part |

## Key principles

- **Mockups before code**: the user picks from pictures, not paragraphs.
- **Real capabilities only**: every pitch is checked against the authoritative reference before it reaches the gallery.
- **Distinct lenses**: diversity of angle beats more teams.
- **Right-sized workflows**: respect the session's workflow size guideline; say what you capped.
- **Honest labels**: name the model each agent ran on, from what you passed, never a guess.
- **You hold the gates**: agents never commit, push, deploy, send or touch production.
