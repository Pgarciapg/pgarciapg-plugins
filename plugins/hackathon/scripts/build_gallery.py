#!/usr/bin/env python3
"""Builds gallery.html for a hackathon run.

Usage: python3 build_gallery.py <run-dir> ["Gallery title"] [--artifact "Page name"]
--artifact also writes gallery.artifact.html, ready to publish as a claude.ai artifact.
The run dir holds results.json ({"pitches": [...]}, each pitch with name, slug, team,
one_liner, surface, effort, how_it_works, api_used, who_it_helps, risks, mockup_path,
optional slots_fallback, feasibility {verdict, note}, value {score, note}) and frame.html.
"""
import html
import json
import pathlib
import sys

RUN = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
TITLE = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "Ideas, ranked"
results = json.loads((RUN / "results.json").read_text())
frame = (RUN / "frame.html").read_text()


def assemble(p):
    """Mockup HTML for a pitch: its file, or its slot fragments filled into the frame."""
    path = p.get("mockup_path")
    if path and pathlib.Path(path).exists():
        return pathlib.Path(path).read_text()
    slots = p.get("slots_fallback") or {}
    out = frame.replace("<!-- SLOT:title -->", html.escape(p["name"]))
    caption = f"<h1>{html.escape(p['name'])}</h1><p>{html.escape(p['one_liner'])} · Team {html.escape(p['team'])}</p>"
    out = out.replace("<!-- SLOT:caption -->", caption)
    for key in ("sidebar", "transcript", "spinner", "band", "status", "pane_title", "pane"):
        out = out.replace(f"<!-- SLOT:{key} -->", slots.get(key, ""))
    out = out.replace("/* SLOT:css */", slots.get("css", ""))
    if not slots.get("pane"):
        out = out.replace('id="pane"', 'id="pane" hidden')
    return out


def feas(p):
    return ((p.get("feasibility") or {}).get("verdict") or "unjudged").strip().lower()


def score(p):
    v = p.get("value") or {}
    return v.get("score") if isinstance(v.get("score"), (int, float)) else 0


pitches = results["pitches"]
live = sorted([p for p in pitches if not feas(p).startswith("not")], key=score, reverse=True)
parked = [p for p in pitches if feas(p).startswith("not")]
PILL = {"buildable": "ok", "buildable-with-changes": "warn"}


def card(p, rank=None):
    doc = assemble(p)
    f = feas(p)
    fnote = html.escape((p.get("feasibility") or {}).get("note", ""))
    vnote = html.escape((p.get("value") or {}).get("note", ""))
    apis = "".join(f"<code>{html.escape(a)}</code>" for a in p.get("api_used", []))
    badge = f'<span class="rank">#{rank}</span>' if rank else ""
    return f"""
<article class="card">
  <div class="shot"><iframe loading="lazy" srcdoc="{html.escape(doc, quote=True)}" title="{html.escape(p['name'])} mockup"></iframe></div>
  <div class="meta">
    <div class="head">{badge}<h2>{html.escape(p['name'])}</h2><span class="score">{score(p)}<small>/10</small></span></div>
    <p class="one">{html.escape(p['one_liner'])}</p>
    <div class="pills"><span class="pill {PILL.get(f, 'bad')}">{html.escape(f)}</span>
      <span class="pill">{html.escape(p['surface'])}</span><span class="pill">effort {html.escape(p['effort'])}</span>
      <span class="pill team">{html.escape(p['team'])}</span></div>
    <p class="why"><b>Why it scores:</b> {vnote}</p>
    <details><summary>How it works, feasibility, risks</summary>
      <p>{html.escape(p['how_it_works'])}</p>
      <div class="apis">{apis}</div>
      <p><b>Feasibility:</b> {fnote}</p>
      <p><b>Helps:</b> {html.escape(p['who_it_helps'])}</p>
      <p><b>Risks:</b> {html.escape(p['risks'])}</p>
    </details>
    <button class="open" data-slug="{html.escape(p['slug'])}" data-name="{html.escape(p['name'])}">Open full size</button>
    <template id="doc-{html.escape(p['slug'])}">{html.escape(doc)}</template>
  </div>
</article>"""


cards = "".join(card(p, i + 1) for i, p in enumerate(live))
parked_cards = "".join(card(p) for p in parked)
n_build = sum(1 for p in pitches if feas(p) == "buildable")
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
<style>
:root {{ --bg:#f4f2ed; --card:#fff; --text:#1a1915; --muted:#77756e; --line:#e3e0d8; --ok:#2f9e5b; --warn:#b97c0c; --bad:#c9443a; --accent:#2b6de8; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#181817; --card:#232321; --text:#ecebe6; --muted:#9c9a92; --line:#3a3936; color-scheme:dark; }} }}
:root[data-theme="dark"] {{ --bg:#181817; --card:#232321; --text:#ecebe6; --muted:#9c9a92; --line:#3a3936; color-scheme:dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 -apple-system,BlinkMacSystemFont,system-ui,sans-serif; }}
header {{ max-width:1200px; margin:0 auto; padding:28px 16px 8px; }}
header h1 {{ margin:0; font-size:26px; }}
header p {{ margin:4px 0 0; color:var(--muted); }}
main {{ max-width:1200px; margin:0 auto; padding:8px 16px 40px; display:grid; gap:18px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; display:grid; grid-template-columns:minmax(0,1.35fr) minmax(0,1fr); }}
.shot {{ max-width:100%; position:relative; aspect-ratio:1352/860; overflow:hidden; border-right:1px solid var(--line); background:#e9e6df; }}
.shot iframe {{ position:absolute; top:0; left:0; width:1352px; height:860px; border:0; transform-origin:0 0; pointer-events:none; }}
.meta {{ padding:16px 18px; }}
.head {{ display:flex; align-items:baseline; gap:10px; }}
.head h2 {{ margin:0; font-size:19px; flex:1; }}
.rank {{ color:var(--muted); font-weight:600; }}
.score {{ font-size:24px; font-weight:700; }} .score small {{ font-size:13px; color:var(--muted); font-weight:500; }}
.one {{ margin:6px 0 10px; }}
.pills {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }}
.pill {{ font-size:12px; padding:2px 9px; border-radius:99px; border:1px solid var(--line); color:var(--muted); }}
.pill.ok {{ color:var(--ok); border-color:var(--ok); }} .pill.warn {{ color:var(--warn); border-color:var(--warn); }} .pill.bad {{ color:var(--bad); border-color:var(--bad); }}
.why {{ font-size:14px; margin:0 0 8px; }}
details {{ font-size:13.5px; color:var(--muted); }} details p {{ margin:6px 0; }} summary {{ cursor:pointer; color:var(--text); }}
.apis {{ display:flex; flex-wrap:wrap; gap:4px; }} .apis code {{ font-size:11.5px; background:var(--bg); padding:1px 6px; border-radius:5px; }}
.open {{ margin-top:10px; font:inherit; font-size:13px; padding:6px 12px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--text); cursor:pointer; }}
#viewer {{ position:fixed; inset:0; z-index:10; background:var(--bg); display:grid; grid-template-rows:auto 1fr; }}
#viewer[hidden] {{ display:none; }}
.vbar {{ display:flex; align-items:center; gap:12px; padding:10px 16px; padding-top:calc(10px + env(safe-area-inset-top, 0px)); border-bottom:1px solid var(--line); }}
.vbar .vt {{ flex:1; font-weight:600; }}
.vbar button, .open {{ font:inherit; font-size:13px; padding:6px 12px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--text); cursor:pointer; }}
.vbar button:focus-visible, .open:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
#viewer iframe {{ width:100%; height:100%; border:0; }}
h3.parked {{ max-width:1200px; margin:10px auto 0; padding:0 16px; color:var(--muted); font-size:15px; }}
@media (max-width: 820px) {{ .card {{ grid-template-columns:1fr; }} .shot {{ border-right:0; border-bottom:1px solid var(--line); }} }}
</style></head><body>
<header><h1>{html.escape(TITLE)}</h1>
<p>{len(pitches)} pitches from {len({p['team'] for p in pitches})} teams · {n_build} buildable as-is · ranked by value among buildable · {len(parked)} parked</p></header>
<main>{cards}</main>
{f'<h3 class="parked">Parked: not buildable as pitched</h3><main>{parked_cards}</main>' if parked else ''}
<div id="viewer" hidden><div class="vbar"><span class="vt"></span><button type="button">Close</button></div><iframe title="Full-size mockup"></iframe></div>
<script>
function fit() {{ document.querySelectorAll('.shot').forEach(s => {{ const f = s.querySelector('iframe'); f.style.transform = 'scale(' + (s.clientWidth / 1352) + ')'; }}); }}
addEventListener('resize', fit); addEventListener('load', fit); fit();
const viewer = document.getElementById('viewer'), vframe = viewer.querySelector('iframe');
document.querySelectorAll('.open').forEach(b => b.addEventListener('click', () => {{
  vframe.srcdoc = document.getElementById('doc-' + b.dataset.slug).content.textContent;
  viewer.querySelector('.vt').textContent = b.dataset.name;
  viewer.hidden = false; viewer.querySelector('button').focus();
}}));
const closeViewer = () => {{ viewer.hidden = true; vframe.srcdoc = ''; }};
viewer.querySelector('button').addEventListener('click', closeViewer);
addEventListener('keydown', e => {{ if (e.key === 'Escape' && !viewer.hidden) closeViewer(); }});
</script>
</body></html>"""
(RUN / "gallery.html").write_text(page)
if "--artifact" in sys.argv:
    body = page.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    style = page.split("<style>", 1)[1].split("</style>", 1)[0]
    name = sys.argv[sys.argv.index("--artifact") + 1] if len(sys.argv) > sys.argv.index("--artifact") + 1 else TITLE
    (RUN / "gallery.artifact.html").write_text(f"<title>{html.escape(name)}</title>\n<style>{style}</style>\n{body}")
print(f"gallery.html: {len(page)} bytes, {len(live)} ranked, {len(parked)} parked")
