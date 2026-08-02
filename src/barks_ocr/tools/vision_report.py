# ruff: noqa: T201
"""Render a Claude Code vision pass as a browsing HTML report.

Reads a ``vision_prep`` output directory and writes ``report.html`` beside the
page folders.  Images are referenced by relative path rather than embedded, so
the file stays small and opens instantly -- it is meant to be opened straight
from disk, not served.

The report is organized page -> panel -> group, so each panel crop sits directly
above its description and the speech groups drawn in it.  ``ai_text`` is rendered
with its inline emphasis markup turned into real ``<strong>``/``<em>``, which is
the only place the bold detection is actually visible.  Nothing here reads or
writes the prelim OCR JSON, so the report can be produced before
``vision_apply`` has been run.
"""

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.speech_markup import (
    has_markup,
    strip_markup,
    unescape_markup,
)
from loguru import logger

from barks_ocr.utils.vision_schema import EMPHASIS_MARKUP_KEY

app = typer.Typer()

REPORT_NAME = "report.html"
# Nephew identity colours, used for the speaker dot.
CAP_SWATCH = {"red": "#d7263d", "blue": "#1b7ced", "green": "#0f9d58"}
CONFIDENCE_ORDER = ("high", "medium", "low")

_CSS = """
:root {
  --bg:#f6f5f1; --fg:#1c1b19; --muted:#6b6862; --line:#dcd8ce;
  --card:#fffefb; --accent:#8a5a2b; --flag:#b3261e; --flag-bg:#fdeceb;
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#16150f; --fg:#eceae3; --muted:#9a968c; --line:#332f26;
          --card:#1f1d16; --accent:#d9a066; --flag:#f2b8b5; --flag-bg:#3a1f1d; }
}
:root[data-theme="light"] {
  --bg:#f6f5f1; --fg:#1c1b19; --muted:#6b6862; --line:#dcd8ce;
  --card:#fffefb; --accent:#8a5a2b; --flag:#b3261e; --flag-bg:#fdeceb;
}
:root[data-theme="dark"] {
  --bg:#16150f; --fg:#eceae3; --muted:#9a968c; --line:#332f26;
  --card:#1f1d16; --accent:#d9a066; --flag:#f2b8b5; --flag-bg:#3a1f1d;
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 Georgia, serif; }
header { position:sticky; top:0; z-index:5; background:var(--bg);
         border-bottom:1px solid var(--line); padding:.7rem 1.2rem; }
header h1 { margin:0 0 .2rem; font-size:1.15rem; }
.wrap { max-width:1100px; margin:0 auto; padding:0 1.2rem 4rem; }
.stats { color:var(--muted); font-size:.85rem; }
.stats b { color:var(--fg); }
nav a { color:var(--accent); text-decoration:none; margin-right:.6rem; font-size:.85rem; }
nav a:hover { text-decoration:underline; }
.page-head { display:flex; gap:1.2rem; align-items:flex-start;
             margin:2.5rem 0 1rem; padding-top:1rem; border-top:2px solid var(--line); }
.page-head img { width:150px; border:1px solid var(--line); border-radius:3px; }
.page-head h2 { margin:0 0 .2rem; font-size:1.3rem; }
.panel { background:var(--card); border:1px solid var(--line); border-radius:6px;
         margin:1.2rem 0; overflow:hidden; }
.panel > img { display:block; width:100%; height:auto; }
.panel-body { padding:1rem 1.15rem 1.15rem; }
.panel-no { font:600 .72rem/1 system-ui, sans-serif; letter-spacing:.09em;
            text-transform:uppercase; color:var(--muted); margin-bottom:.5rem; }
.desc { margin:0 0 1rem; }
.group { border-top:1px solid var(--line); padding:.8rem 0 .2rem; }
.group.flagged { background:var(--flag-bg); margin:0 -1.15rem; padding-left:1.15rem;
                 padding-right:1.15rem; }
.meta { display:flex; flex-wrap:wrap; gap:.45rem; align-items:center;
        font:.78rem/1 system-ui, sans-serif; color:var(--muted); margin-bottom:.45rem; }
.gid { font-weight:700; color:var(--fg); }
.dot { width:.62rem; height:.62rem; border-radius:50%; display:inline-block;
       border:1px solid rgba(0,0,0,.35); }
.badge { border:1px solid var(--line); border-radius:10px; padding:.1rem .45rem; }
.badge.low { color:var(--flag); border-color:var(--flag); }
.speech { white-space:pre-line; margin:0; font-size:1.02rem; }
.speech strong { background:rgba(217,160,102,.28); padding:0 .1em; }
.note { margin:.45rem 0 0; font-size:.83rem; color:var(--muted); font-style:italic; }
.fix { margin:.5rem 0 0; font:.83rem/1.5 ui-monospace, monospace; }
.fix div { white-space:pre-wrap; }
.fix .was { color:var(--flag); text-decoration:line-through; }
table.tally { border-collapse:collapse; font-size:.85rem; margin:.4rem 0 0; }
table.tally td { padding:.1rem .8rem .1rem 0; }
"""

_JS = """
const t=document.documentElement;
document.getElementById('theme').onclick=()=>{
  const cur=t.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  t.dataset.theme=cur==='dark'?'light':'dark';};
document.getElementById('only').onchange=e=>{
  document.querySelectorAll('.group').forEach(g=>{
    g.style.display=(e.target.checked && !g.classList.contains('flagged'))?'none':'';});
  document.querySelectorAll('.panel').forEach(p=>{
    const any=[...p.querySelectorAll('.group')].some(g=>g.style.display!=='none');
    p.style.display=(e.target.checked && !any)?'none':'';});};
"""


_TAG_TO_HTML = {"b": ("<strong>", "</strong>"), "i": ("<em>", "</em>")}


def _render_text(markup: str) -> str:
    """Escape the text for HTML and turn its Kivy emphasis tags into elements.

    Everything outside a tag is escaped, so a literal bracket in the lettering --
    Gemini writes annotations like ``[Chinese Characters]`` -- shows as itself
    rather than being read as markup.
    """
    out: list[str] = []
    cursor = 0
    for match in re.finditer(r"\[(/?)([a-z]+)\]", markup):
        tag = match.group(2)
        if tag not in _TAG_TO_HTML:
            continue
        out.append(html.escape(unescape_markup(markup[cursor : match.start()])))
        out.append(_TAG_TO_HTML[tag][1 if match.group(1) else 0])
        cursor = match.end()
    out.append(html.escape(unescape_markup(markup[cursor:])))
    return "".join(out)


def _speaker_dot(cap_colour: str | None) -> str:
    if cap_colour not in CAP_SWATCH:
        return ""
    return f'<span class="dot" style="background:{CAP_SWATCH[cap_colour]}"></span>'


def _group_html(gid: str, src: dict, res: dict) -> str:
    """Render one speech group: metadata line, text, note and any correction."""
    # The report normally runs before `vision_apply`, so the proposed markup is
    # still only in the result; after applying, it is on the group. Prefer the
    # result so the report shows what is about to be written.
    stored = res.get(EMPHASIS_MARKUP_KEY) or (src.get("ai_text") or "")
    emphasized = has_markup(stored)
    flagged = (not res.get("text_ok")) or res.get("speaker_confidence") == "low" or emphasized
    conf = res.get("speaker_confidence", "?")

    badges = [
        f'<span class="badge{" low" if conf == "low" else ""}">{html.escape(conf)}</span>',
        f'<span class="badge">{html.escape(str(src.get("type", "?")))}</span>',
    ]
    if not res.get("text_ok"):
        badges.append('<span class="badge low">text differs</span>')
    if emphasized:
        badges.append('<span class="badge">emphasis</span>')

    group_class = "group flagged" if flagged else "group"
    parts = [f'<div class="{group_class}">']
    parts.append(
        '<div class="meta">'
        f'<span class="gid">g{html.escape(gid)}</span>'
        f"{_speaker_dot(res.get('cap_colour'))}"
        f"<span>{html.escape(str(res.get('speaker', '?')))}</span>"
        f"{''.join(badges)}"
        "</div>"
    )
    parts.append(f'<p class="speech">{_render_text(stored)}</p>')

    if not res.get("text_ok") and res.get("corrected_text"):
        parts.append(
            '<div class="fix">'
            f'<div class="was">stored: {html.escape(strip_markup(stored))}</div>'
            f"<div>art:&nbsp;&nbsp;&nbsp; {html.escape(res['corrected_text'])}</div>"
            "</div>"
        )
    if res.get("note"):
        parts.append(f'<p class="note">{html.escape(res["note"])}</p>')
    parts.append("</div>")
    return "".join(parts)


def _page_html(page: str, entry: dict, src_groups: dict, result: dict) -> str:
    """Render one page: header, then each panel with its description and groups."""
    by_panel: dict[str, list[str]] = defaultdict(list)
    for gid, src in src_groups.items():
        by_panel[str(src.get("panel_num", -1))].append(gid)

    head = (
        f'<div class="page-head" id="p{page}">'
        f'<img src="{page}/page.png" alt="page {page} overview">'
        f"<div><h2>Page {page}</h2>"
        f'<div class="stats">{html.escape(entry.get("title", ""))} · '
        f"{len(entry.get('panels', []))} panels · "
        f"{len(src_groups)} groups</div></div></div>"
    )
    parts = [head]

    panel_nums = sorted(result.get("panels", {}), key=int)
    for panel_no in panel_nums:
        panel_group_ids = sorted(by_panel.get(panel_no, []), key=int)
        parts.append('<div class="panel">')
        parts.append(f'<img src="{page}/panel-{int(panel_no):02d}.png" alt="panel {panel_no}">')
        parts.append('<div class="panel-body">')
        parts.append(f'<div class="panel-no">Panel {panel_no}</div>')
        parts.append(
            f'<p class="desc">{html.escape(result["panels"][panel_no]["description"])}</p>'
        )
        parts.extend(
            _group_html(gid, src_groups[gid], result["groups"].get(gid, {}))
            for gid in panel_group_ids
        )
        parts.append("</div></div>")

    orphans = sorted((g for p, gs in by_panel.items() if p not in panel_nums for g in gs), key=int)
    if orphans:
        parts.append('<div class="panel"><div class="panel-body">')
        parts.append('<div class="panel-no">Not assigned to a panel</div>')
        parts.extend(
            _group_html(gid, src_groups[gid], result["groups"].get(gid, {})) for gid in orphans
        )
        parts.append("</div></div>")

    return "".join(parts)


def _tally(pages: list[tuple[str, dict, dict]]) -> str:
    """Build the summary block shown under the report title."""
    groups = corrections = bolds = 0
    conf: dict[str, int] = dict.fromkeys(CONFIDENCE_ORDER, 0)
    speakers: dict[str, int] = defaultdict(int)
    for _page, src_groups, result in pages:
        for gid, res in result["groups"].items():
            groups += 1
            corrections += not res.get("text_ok")
            # Emphasis is read off the prepped group text, not the result: the
            # result carries the proposed markup only until it is applied.
            emphasis_source = res.get(EMPHASIS_MARKUP_KEY) or (
                src_groups.get(gid, {}).get("ai_text") or ""
            )
            bolds += has_markup(emphasis_source)
            conf[res.get("speaker_confidence", "low")] = (
                conf.get(res.get("speaker_confidence", "low"), 0) + 1
            )
            speakers[str(res.get("speaker"))] += 1
    top = ", ".join(
        f"{html.escape(k)} {v}" for k, v in sorted(speakers.items(), key=lambda kv: -kv[1])[:6]
    )
    conf_str = ", ".join(f"{k} {conf.get(k, 0)}" for k in CONFIDENCE_ORDER)
    return (
        f'<div class="stats"><b>{len(pages)}</b> pages · <b>{groups}</b> groups · '
        f"<b>{bolds}</b> group(s) with emphasis · <b>{corrections}</b> proposed text corrections"
        f"<br>confidence: {conf_str}<br>speakers: {top}</div>"
    )


@app.command(help="Render a vision_prep directory as a browsing HTML report.")
def main(
    out_dir: Annotated[
        Path, typer.Option("--out-dir", "-o", help="The vision_prep output directory.")
    ],
    report_file: Annotated[
        Path | None,
        typer.Option("--report", help=f"Report path (default: <out-dir>/{REPORT_NAME})"),
    ] = None,
) -> None:
    queue_file = out_dir / "queue.json"
    if not queue_file.is_file():
        msg = f'No queue file at "{queue_file}". Run barks-ocr-vision-prep first.'
        raise typer.BadParameter(msg)

    queue = json.loads(queue_file.read_text())
    pages: list[tuple[str, dict, dict]] = []
    entries: dict[str, dict] = {}
    for entry in queue["pages"]:
        page = entry["fanta_page"]
        result_file = out_dir / page / "result.json"
        if not result_file.is_file():
            logger.warning(f"Page {page}: no result.json yet, skipping.")
            continue
        entries[page] = entry
        pages.append(
            (
                page,
                json.loads((out_dir / page / "groups.json").read_text()),
                json.loads(result_file.read_text()),
            )
        )

    if not pages:
        msg = f'No result.json files found under "{out_dir}".'
        raise typer.BadParameter(msg)

    nav = "".join(f'<a href="#p{p}">{p}</a>' for p, _s, _r in pages)
    body = "".join(_page_html(p, entries[p], src, res) for p, src, res in pages)
    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Vision report - volume {queue['volume']}</title>"
        f"<style>{_CSS}</style></head><body>"
        f"<header><h1>Vision report · volume {queue['volume']} "
        f"({html.escape(str(queue['engine']))})</h1>"
        f"{_tally(pages)}"
        f"<nav>{nav}</nav>"
        '<label class="stats"><input type="checkbox" id="only"> only flagged groups</label> '
        '<button id="theme" class="stats">theme</button>'
        "</header>"
        f'<div class="wrap">{body}</div>'
        f"<script>{_JS}</script></body></html>"
    )

    report = report_file or (out_dir / REPORT_NAME)
    report.write_text(doc, encoding="utf-8")
    print(f'Wrote "{report}" ({len(pages)} pages, {report.stat().st_size // 1024}KB).')
    print(f"Open with:  xdg-open {report}")


if __name__ == "__main__":
    app()
