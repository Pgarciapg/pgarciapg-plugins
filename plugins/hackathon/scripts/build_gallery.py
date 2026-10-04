#!/usr/bin/env python3
"""Build a self-contained gallery for a hackathon run.

Usage: python3 build_gallery.py <run-dir> ["Gallery title"] [--artifact ["Page name"]] [--size WxH]

<run-dir>/results.json may be the Idea Sprint workflow's return value as-is ({"pitches": [...],
"teams_missing": [...]}), a list of team objects ({team, pitches, feasibility, value}), or {"teams": [...]}.
Each pitch: name, slug, team, one_liner, who_it_helps, how_it_works, api_used, surface, effort, risks,
mockup_path (absolute, or relative to the run dir), optional slots_fallback {slot: html},
feasibility {verdict, note}, value {score, note}, and after a build: built_screenshot, built_note, status.
Missing or odd fields degrade to placeholders instead of crashing. frame.html is only needed for
slots_fallback. Mockup size comes from <meta name="hackathon:size" content="WxH"> (default 1352x860).
--artifact also writes gallery.artifact.html, ready to publish as a claude.ai artifact.
"""

import argparse
import base64
import html
from html.parser import HTMLParser
import json
import math
import pathlib
import re
import sys

DEFAULT_SIZE = (1352, 860)
SLOT_MARKER = r"<!--\s*SLOT:\w+\s*-->|/\*\s*SLOT:\w+\s*\*/"
PILL = {"buildable": "ok", "buildable-with-changes": "warn", "not-buildable": "bad"}
VERDICT_ORDER = {"buildable": 0, "buildable-with-changes": 1, "unjudged": 2}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def string(value, default=""):
    return default if value is None else str(value)


def escape(value):
    return html.escape(string(value), quote=True)


def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "pitch"


def numeric_score(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return max(0.0, min(10.0, number)) if math.isfinite(number) else None


def score_label(value):
    return "–" if value is None else (str(int(value)) if value.is_integer() else str(value))


def verdict(value):
    # Whole words only: "buildable (see note)" must not read as "not buildable".
    words = re.findall(r"[a-z]+", string(value).lower())
    if "unbuildable" in words or ("buildable" in words and ("not" in words or "non" in words)):
        return "not-buildable"
    if "buildable" in words and "with" in words and any(w.startswith("change") for w in words):
        return "buildable-with-changes"
    return "buildable" if words[:1] == ["buildable"] else "unjudged"


def judge_rows(value):
    if isinstance(value, dict):
        value = value.get("verdicts", value.get("scores", []))
    return value if isinstance(value, list) else []


def join_judges(pitches, feasibility, value):
    for pitch in pitches:
        if not isinstance(pitch, dict):
            continue
        for field, rows in (("feasibility", judge_rows(feasibility)), ("value", judge_rows(value))):
            if field in pitch:
                continue
            slug = string(pitch.get("slug")).strip().lower()
            name = string(pitch.get("name")).strip().lower()
            match = next((row for row in rows if isinstance(row, dict) and slug and
                          string(row.get("slug")).strip().lower() == slug), None)
            if match is None:
                match = next((row for row in rows if isinstance(row, dict) and name and
                              string(row.get("name")).strip().lower() == name), None)
            if match is not None:
                pitch[field] = match


def normalize_pitch(raw, index):
    raw = raw if isinstance(raw, dict) else {}
    name = string(raw.get("name")).strip() or "Untitled pitch {}".format(index + 1)
    slug = string(raw.get("slug")).strip() or slugify(name)
    pitch = {key: string(raw.get(key)) for key in
             ("one_liner", "who_it_helps", "how_it_works", "surface", "risks",
              "mockup_path", "built_screenshot", "built_note", "status")}
    pitch.update(name=name, slug=slug, team=string(raw.get("team")).strip() or "Unassigned",
                 effort=string(raw.get("effort")).strip() or "?")
    apis = raw.get("api_used")
    pitch["api_used"] = [string(item) for item in apis] if isinstance(apis, list) else (
        [apis] if isinstance(apis, str) else [])
    feasibility = raw.get("feasibility")
    pitch["feasibility_note"] = string(feasibility.get("note")) if isinstance(feasibility, dict) else ""
    pitch["verdict"] = verdict(feasibility.get("verdict") if isinstance(feasibility, dict) else feasibility)
    value = raw.get("value")
    pitch["value_note"] = string(value.get("note")) if isinstance(value, dict) else ""
    pitch["score"] = numeric_score(value.get("score") if isinstance(value, dict) else value)
    pitch["slots_fallback"] = raw.get("slots_fallback") if isinstance(raw.get("slots_fallback"), dict) else {}
    pitch["index"] = index
    return pitch


def load_results(run_dir):
    try:
        data = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot load results.json: {}".format(exc)) from exc
    if isinstance(data, list):
        teams, missing = data, []
    elif isinstance(data, dict):
        missing = data.get("teams_missing") if isinstance(data.get("teams_missing"), list) else []
        if isinstance(data.get("pitches"), list):
            if any(not isinstance(p, dict) for p in data["pitches"]):
                raise ValueError("Invalid results.json: pitch must be an object")
            pitches = [dict(p) for p in data["pitches"]]
            join_judges(pitches, data.get("feasibility"), data.get("value"))
            return [normalize_pitch(p, i) for i, p in enumerate(pitches)], [string(x) for x in missing]
        teams = data.get("teams")
    else:
        teams, missing = None, []
    if not isinstance(teams, list):
        raise ValueError("Invalid results.json: expected pitches or teams list")
    pitches = []
    for team in teams:
        if not isinstance(team, dict) or not isinstance(team.get("pitches"), list):
            raise ValueError("Invalid results.json: each team needs a pitches list")
        for raw in team["pitches"]:
            if not isinstance(raw, dict):
                raise ValueError("Invalid results.json: pitch must be an object")
            pitch = dict(raw)
            pitch["team"] = string(team.get("team") or team.get("name"), "Unassigned")
            join_judges([pitch], team.get("feasibility"), team.get("value"))
            pitches.append(pitch)
    return [normalize_pitch(p, i) for i, p in enumerate(pitches)], [string(x) for x in missing]


def parse_size(value):
    match = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", string(value))
    if not match:
        return None
    width, height = int(match.group(1)), int(match.group(2))
    return (width, height) if width > 0 and height > 0 else None


class SizeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.size = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "meta":
            attributes = dict(attrs)
            if string(attributes.get("name")).lower() == "hackathon:size":
                self.size = parse_size(attributes.get("content")) or self.size


def document_size(document):
    parser = SizeParser()
    parser.feed(document)
    return parser.size


def resolve_path(run_dir, path, slug=None):
    candidates = []
    if path:
        target = pathlib.Path(path)
        candidates = [target] if target.is_absolute() else [run_dir / target, pathlib.Path.cwd() / target]
        for candidate in candidates:
            if candidate.is_file():
                return candidate, candidates
    if slug is not None:
        fallback = run_dir / "mockups" / (slug + ".html")
        candidates.append(fallback)
        if fallback.is_file():
            return fallback, candidates
    return None, candidates


def mockup_document(pitch, run_dir, frame):
    path, candidates = resolve_path(run_dir, pitch["mockup_path"], pitch["slug"])
    if path is not None:
        try:
            return path.read_text(encoding="utf-8"), "file"
        except (OSError, UnicodeError):
            pass
    slots = pitch["slots_fallback"]
    if slots and frame is not None:
        document = frame
        defaults = {"title": escape(pitch["name"]),
                    "caption": "<h1>{}</h1><p>{} · Team {}</p>".format(
                        *(escape(pitch[key]) for key in ("name", "one_liner", "team")))}
        for key, value in slots.items():
            key = string(key)
            content = string(value)
            document = document.replace("<!-- SLOT:{} -->".format(key), content)
            document = document.replace("/* SLOT:{} */".format(key), content)
        for key, content in defaults.items():
            if key not in slots:
                document = document.replace("<!-- SLOT:{} -->".format(key), content)
                document = document.replace("/* SLOT:{} */".format(key), content)
        return re.sub(SLOT_MARKER, "", document), "fallback"
    if slots and frame is None:
        print("Warning: frame.html missing for fallback: {}".format(pitch["name"]), file=sys.stderr)
    tried = ", ".join(str(candidate) for candidate in candidates) or "no mockup path"
    print("Warning: mockup missing for {} ({})".format(pitch["name"], tried), file=sys.stderr)
    return "<!doctype html><html><body><h1>Mockup missing</h1><p>{}</p></body></html>".format(escape(tried)), "missing"


def built_image(pitch, run_dir):
    path = pitch["built_screenshot"]
    if not path or pathlib.Path(path).suffix.lower() not in IMAGE_TYPES:
        return None
    resolved, _ = resolve_path(run_dir, path)
    if resolved is None:
        print("Warning: built screenshot missing for {} ({})".format(pitch["name"], path), file=sys.stderr)
        return None
    try:
        image = resolved.read_bytes()
    except OSError as exc:
        print("Warning: built screenshot unreadable for {} ({})".format(pitch["name"], exc), file=sys.stderr)
        return None
    if len(image) > 2 * 1024 * 1024:
        print("Warning: built screenshot over 2 MB for {}".format(pitch["name"]), file=sys.stderr)
    return "data:{};base64,{}".format(IMAGE_TYPES[resolved.suffix.lower()], base64.b64encode(image).decode("ascii"))


def card(pitch, doc, size, index, rank=None, mode="file", image=None):
    width, height = size
    shot = ('<div class="shot" data-w="{}" data-h="{}" style="aspect-ratio:{}/{}">'
            '<iframe loading="lazy" sandbox="allow-scripts" width="{}" height="{}" srcdoc="{}" title="{} mockup"></iframe></div>').format(
                width, height, width, height, width, height, escape(doc), escape(pitch["name"]))
    if image is not None:
        shot = ('<div class="comparison" aria-label="Mockup vs built"><figure>{}<figcaption>Mockup</figcaption></figure>'
                '<figure><img src="{}" alt="Built screenshot for {}"><figcaption>Built</figcaption></figure></div>').format(
                    shot, image, escape(pitch["name"]))
    apis = "".join("<code>{}</code>".format(escape(api)) for api in pitch["api_used"])
    badge = '<span class="rank">#{}</span>'.format(rank) if rank is not None else ""
    assembled = '<span class="pill">assembled from slot fragments</span>' if mode == "fallback" else ""
    status = '<span class="pill">{}</span>'.format(escape(pitch["status"])) if pitch["status"] else ""
    built_note = '<p class="built-note">{}</p>'.format(escape(pitch["built_note"])) if pitch["built_note"] else ""
    return '''
<article class="card">
  <div class="media">{shot}</div>
  <div class="meta">
    <div class="head">{badge}<h2>{name}</h2><span class="score">{score}<small>/10</small></span></div>
    <p class="one">{one}</p>
    <div class="pills"><span class="pill {pill}">{verdict}</span>
      <span class="pill">{surface}</span><span class="pill">effort {effort}</span>
      <span class="pill team">{team}</span>{status}{assembled}</div>
    <p class="why"><b>Why it scores:</b> {value_note}</p>{built_note}
    <details><summary>How it works, feasibility, risks</summary>
      <p>{how}</p><div class="apis">{apis}</div>
      <p><b>Feasibility:</b> {feasibility_note}</p>
      <p><b>Helps:</b> {helps}</p><p><b>Risks:</b> {risks}</p>
    </details>
    <button class="open" data-doc="{index}" data-name="{name}" data-w="{width}" data-h="{height}">Open full size</button>
    <template id="doc-{index}">{doc}</template>
  </div>
</article>'''.format(
        shot=shot, badge=badge, name=escape(pitch["name"]), score=score_label(pitch["score"]),
        one=escape(pitch["one_liner"]), pill=PILL.get(pitch["verdict"], ""), verdict=escape(pitch["verdict"]),
        surface=escape(pitch["surface"]), effort=escape(pitch["effort"]), team=escape(pitch["team"]),
        status=status, assembled=assembled, value_note=escape(pitch["value_note"]), built_note=built_note,
        how=escape(pitch["how_it_works"]), apis=apis, feasibility_note=escape(pitch["feasibility_note"]),
        helps=escape(pitch["who_it_helps"]), risks=escape(pitch["risks"]), index=index,
        width=width, height=height, doc=escape(doc))


STYLE = """
:root { --bg:#f4f2ed; --card:#fff; --text:#1a1915; --muted:#77756e; --line:#e3e0d8; --ok:#2f9e5b; --warn:#b97c0c; --bad:#c9443a; --accent:#2b6de8; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#181817; --card:#232321; --text:#ecebe6; --muted:#9c9a92; --line:#3a3936; color-scheme:dark; } }
:root[data-theme="dark"] { --bg:#181817; --card:#232321; --text:#ecebe6; --muted:#9c9a92; --line:#3a3936; color-scheme:dark; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 -apple-system,BlinkMacSystemFont,system-ui,sans-serif; }
header { max-width:1200px; margin:0 auto; padding:28px 16px 8px; }
header h1 { margin:0; font-size:26px; overflow-wrap:anywhere; }
header p { margin:4px 0 0; color:var(--muted); overflow-wrap:anywhere; }
main { max-width:1200px; margin:0 auto; padding:8px 16px 40px; display:grid; gap:18px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; display:grid; grid-template-columns:minmax(0,1.35fr) minmax(0,1fr); }
.media { min-width:0; background:var(--bg); }
.shot { width:100%; max-width:100%; position:relative; overflow:hidden; border-right:1px solid var(--line); background:var(--bg); }
.shot iframe { position:absolute; top:0; left:0; border:0; transform-origin:0 0; pointer-events:none; }
.comparison { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; padding:10px; }
.comparison figure { min-width:0; margin:0; }
.comparison .shot { border:0; }
.comparison img { width:100%; height:auto; display:block; }
figcaption { color:var(--muted); font-size:12px; margin-top:4px; }
.meta { min-width:0; padding:16px 18px; }
.head { display:flex; align-items:baseline; gap:10px; min-width:0; }
.head h2 { margin:0; font-size:19px; flex:1; min-width:0; overflow-wrap:anywhere; }
.rank { color:var(--muted); font-weight:600; }
.score { font-size:24px; font-weight:700; flex:none; } .score small { font-size:13px; color:var(--muted); font-weight:500; }
.one, .why, .built-note, details p { overflow-wrap:anywhere; }
.one { margin:6px 0 10px; }
.pills { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
.pill { font-size:12px; padding:2px 9px; border-radius:99px; border:1px solid var(--line); color:var(--muted); overflow-wrap:anywhere; }
.pill.ok { color:var(--ok); border-color:var(--ok); } .pill.warn { color:var(--warn); border-color:var(--warn); } .pill.bad { color:var(--bad); border-color:var(--bad); }
.why { font-size:14px; margin:0 0 8px; }
details { font-size:13.5px; color:var(--muted); } details p { margin:6px 0; } summary { cursor:pointer; color:var(--text); }
.apis { display:flex; flex-wrap:wrap; gap:4px; } .apis code { font-size:11.5px; background:var(--bg); padding:1px 6px; border-radius:5px; overflow-wrap:anywhere; min-width:0; }
.open, .vbar button { margin-top:10px; font:inherit; font-size:13px; padding:6px 12px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--text); cursor:pointer; }
#viewer { position:fixed; inset:0; z-index:10; background:var(--bg); display:grid; grid-template-rows:auto minmax(0,1fr); }
#viewer[hidden] { display:none; }
.vbar { display:flex; align-items:center; gap:12px; padding:10px 16px; padding-top:calc(10px + env(safe-area-inset-top, 0px)); border-bottom:1px solid var(--line); }
.vbar .vt { flex:1; font-weight:600; overflow-wrap:anywhere; }
.vbar button { margin:0; }
.vbar button:focus-visible, .open:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.vstage { overflow:auto; min-width:0; }
.vwrap { position:relative; margin:0 auto; }
.vwrap iframe { position:absolute; top:0; left:0; border:0; transform-origin:0 0; }
h3.parked { max-width:1200px; margin:10px auto 0; padding:0 16px; color:var(--muted); font-size:15px; }
@media (max-width: 820px) { .card { grid-template-columns:1fr; } .shot { border-right:0; border-bottom:1px solid var(--line); } .comparison { grid-template-columns:1fr; } }
"""

SCRIPT = """
function fit() {
  document.querySelectorAll('.shot').forEach(s => {
    const f = s.querySelector('iframe');
    f.style.transform = 'scale(' + (s.clientWidth / Number(s.dataset.w)) + ')';
  });
}
addEventListener('resize', fit); addEventListener('load', fit); fit();
const viewer = document.getElementById('viewer');
const stage = viewer.querySelector('.vstage');
const wrap = viewer.querySelector('.vwrap');
const vframe = viewer.querySelector('iframe');
let opener = null;
function fitViewer() {
  if (viewer.hidden) return;
  const w = Number(vframe.dataset.w), h = Number(vframe.dataset.h);
  const scale = Math.min(1, stage.clientWidth / w);
  wrap.style.width = (w * scale) + 'px';
  wrap.style.height = (h * scale) + 'px';
  vframe.style.transform = 'scale(' + scale + ')';
}
document.querySelectorAll('.open').forEach(b => b.addEventListener('click', () => {
  opener = b;
  vframe.srcdoc = document.getElementById('doc-' + b.dataset.doc).content.textContent;
  vframe.dataset.w = b.dataset.w; vframe.dataset.h = b.dataset.h;
  vframe.width = b.dataset.w; vframe.height = b.dataset.h;
  viewer.querySelector('.vt').textContent = b.dataset.name;
  viewer.hidden = false; stage.scrollTop = 0; fitViewer(); viewer.querySelector('button').focus();
}));
function closeViewer() { viewer.hidden = true; vframe.srcdoc = ''; if (opener) opener.focus(); }
viewer.querySelector('button').addEventListener('click', closeViewer);
addEventListener('keydown', e => { if (e.key === 'Escape' && !viewer.hidden) closeViewer(); });
addEventListener('resize', fitViewer);
"""


def make_page(title, pitches, missing_teams, run_dir, frame, forced_size):
    live = sorted((p for p in pitches if p["verdict"] != "not-buildable"),
                  key=lambda p: (p["score"] is None, -(p["score"] or 0),
                                 VERDICT_ORDER[p["verdict"]], p["index"]))
    parked = [p for p in pitches if p["verdict"] == "not-buildable"]
    cards, counts = [], {"missing": 0, "fallback": 0, "built": 0}
    frame_size = document_size(frame) if frame is not None else None
    for index, pitch in enumerate(live + parked):
        doc, mode = mockup_document(pitch, run_dir, frame)
        if mode in counts:
            counts[mode] += 1
        size = forced_size or document_size(doc) or frame_size or DEFAULT_SIZE
        image = built_image(pitch, run_dir)
        if image is not None:
            counts["built"] += 1
        rank = index + 1 if index < len(live) else None
        cards.append(card(pitch, doc, size, index, rank, mode, image))
    header = "{} pitches from {} teams · {} buildable as-is · ranked by value · {} parked".format(
        len(pitches), len({p["team"] for p in pitches}),
        sum(p["verdict"] == "buildable" for p in pitches), len(parked))
    for key, label in (("missing", "mockups missing"), ("fallback", "assembled from fragments"), ("built", "built")):
        if counts[key]:
            header += " · {} {}".format(counts[key], label)
    team_note = '<p class="missing-teams">Teams with no result: {}</p>'.format(
        ", ".join(escape(team) for team in missing_teams)) if missing_teams else ""
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{style}</style></head><body>
<header><h1>{title}</h1><p>{header}</p>{team_note}</header>
<main>{live_cards}</main>
{parked_cards}
<div id="viewer" hidden><div class="vbar"><span class="vt"></span><button type="button">Close</button></div><div class="vstage"><div class="vwrap"><iframe title="Full-size mockup" sandbox="allow-scripts"></iframe></div></div></div>
<script>{script}</script>
</body></html>'''.format(
        title=escape(title), style=STYLE, header=header, team_note=team_note,
        live_cards="".join(cards[:len(live)]), parked_cards=(
            '<h3 class="parked">Parked: not buildable as pitched</h3><main>{}</main>'.format(
                "".join(cards[len(live):])) if parked else ""), script=SCRIPT)
    return page, len(live), len(parked), counts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a self-contained hackathon gallery")
    parser.add_argument("run_dir", type=pathlib.Path, help="directory containing results.json")
    parser.add_argument("title", nargs="?", default="Ideas, ranked")
    parser.add_argument("--artifact", nargs="?", const="", metavar="PAGE_NAME", help="also write gallery.artifact.html")
    parser.add_argument("--size", metavar="WxH", help="override all mockup sizes")
    args = parser.parse_args(argv)
    forced_size = parse_size(args.size) if args.size is not None else None
    if args.size is not None and forced_size is None:
        parser.error("--size must be positive WIDTHxHEIGHT")
    try:
        pitches, missing_teams = load_results(args.run_dir)
        try:
            frame = (args.run_dir / "frame.html").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            frame = None
        page, ranked, parked, counts = make_page(args.title, pitches, missing_teams,
                                                 args.run_dir, frame, forced_size)
        (args.run_dir / "gallery.html").write_text(page, encoding="utf-8")
        if args.artifact is not None:
            body = page.split("<body>", 1)[1].rsplit("</body>", 1)[0].lstrip("\n")
            style = page.split("<style>", 1)[1].split("</style>", 1)[0]
            name = args.artifact or args.title
            (args.run_dir / "gallery.artifact.html").write_text(
                "<title>{}</title>\n<style>{}</style>\n{}".format(escape(name), style, body), encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("gallery.html: {} bytes, {} ranked, {} parked, {} missing, {} fallback, {} built".format(
        len(page.encode("utf-8")), ranked, parked, counts["missing"], counts["fallback"], counts["built"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
