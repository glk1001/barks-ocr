#!/usr/bin/env python3
r"""Build a standard EPUB3 from LlamaParse structured output across one or more scans.

The per-spread JSON files produced by ``scripts/llama-parse-pdf.py`` are split
into logical left/right book pages (using the ``book_side`` tag on each item);
each book page becomes one XHTML document in the EPUB. A user-supplied
``chapters.toml`` sidecar provides chapter titles and anchor points so the EPUB
TOC reads like a book rather than a list of spread numbers. Printed page numbers
are exposed via the EPUB3 ``page-list`` nav.

Example:
    uv run python scripts/llama-parse-build-epub.py \
        --parse-dirs parse-dirs \
        --chapters chapters.toml \
        --title "Book Title" --author "Editor Name (ed.)" \
        --output cb-conversations.epub

"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import typer
from book_pages import BookPage, iter_book_pages
from ebooklib import epub
from loader import iter_spreads
from loguru import logger
from markdown_it import MarkdownIt

app = typer.Typer(add_completion=False)

_CSS = """\
body {
  font-family: serif;
  line-height: 1.5;
  margin: 1em;
  hyphens: auto;
  -webkit-hyphens: auto;
  -epub-hyphens: auto;
}
div.chapter {
  page-break-before: always;
  break-before: page;
  -webkit-column-break-before: always;
  padding-top: 2em;
}
div.chapter:first-of-type {
  page-break-before: avoid;
  break-before: avoid;
  padding-top: 0;
}
p { margin: 0.5em 0; text-align: justify; }
figure { margin: 1em 0; text-align: center; }
figure img { max-width: 100%; height: auto; }
figcaption { font-style: italic; font-size: 0.9em; margin-top: 0.3em; }
blockquote {
  margin: 0.8em 1.5em;
  padding: 0 0.5em;
  font-size: 0.95em;
}
blockquote p { margin: 0.4em 0; }
h1, h2, h3 { font-family: sans-serif; }
p.index-entry {
  padding-left: 1.5em;
  text-indent: -1.5em;
  margin: 0.2em 0;
  text-align: left;
  page-break-inside: avoid;
}
a { color: inherit; text-decoration: underline; }
p.contents-entry {
  padding-left: 1.5em;
  text-indent: -1.5em;
  margin: 0.4em 0 0.1em 0;
  text-align: left;
  page-break-inside: avoid;
  font-weight: bold;
}
p.contents-credit {
  margin: 0 0 0.5em 1.5em;
  font-size: 0.95em;
  text-align: left;
}
"""


_CHAPTER_KINDS = frozenset({"regular", "index", "contents"})


@dataclass(frozen=True)
class _Chapter:
    title: str
    start_printed_page: str | None = None
    start_heading: str | None = None
    kind: str = "regular"


@dataclass(frozen=True)
class _ChapterSection:
    """One contiguous run of book pages that share a chapter title in the TOC."""

    title: str
    pages: list[BookPage]
    first_page_index: int
    kind: str = "regular"


def _load_chapters(path: Path) -> list[_Chapter]:
    """Parse ``chapters.toml`` into a list of ``_Chapter`` in book order.

    Args:
        path: Path to the TOML file.

    Returns:
        Chapters preserving file order.

    """
    with path.open("rb") as f:
        data = tomllib.load(f)
    entries = data.get("chapters") or []
    chapters: list[_Chapter] = []
    index_seen = False
    contents_seen = False
    for i, entry in enumerate(entries):
        title = entry.get("title")
        start_page = entry.get("start_printed_page")
        start_heading = entry.get("start_heading")
        kind = entry.get("kind", "regular")
        if not isinstance(title, str):
            msg = f"chapters[{i}] must have a string 'title'"
            raise TypeError(msg)
        has_page = isinstance(start_page, str) and start_page != ""
        has_heading = isinstance(start_heading, str) and start_heading != ""
        if has_page == has_heading:
            msg = (
                f"chapters[{i}] must specify exactly one of "
                f"'start_printed_page' or 'start_heading' (got both or neither)"
            )
            raise TypeError(msg)
        if kind not in _CHAPTER_KINDS:
            msg = f"chapters[{i}].kind must be one of {sorted(_CHAPTER_KINDS)}, got {kind!r}"
            raise ValueError(msg)
        if kind == "index":
            if index_seen:
                msg = f"chapters[{i}]: only one chapter may have kind='index'"
                raise ValueError(msg)
            index_seen = True
        if kind == "contents":
            if contents_seen:
                msg = f"chapters[{i}]: only one chapter may have kind='contents'"
                raise ValueError(msg)
            contents_seen = True
        chapters.append(
            _Chapter(
                title=title,
                start_printed_page=start_page if has_page else None,
                start_heading=start_heading if has_heading else None,
                kind=kind,
            )
        )
    return chapters


def _heading_text(item: dict) -> str | None:
    """Return the visible text of a ``type == "heading"`` item, or ``None``."""
    if item.get("type") != "heading":
        return None
    value = item.get("value")
    if isinstance(value, str) and value.strip():
        return value.strip()
    md = item.get("md")
    if isinstance(md, str):
        stripped = re.sub(r"^#+\s*", "", md.strip()).strip()
        if stripped:
            return stripped
    return None


def _match_chapter_to_heading(heading_text: str, pages: list[BookPage]) -> int | None:
    """Return the page index of the first page containing a matching heading."""
    target = heading_text.casefold()
    for page in pages:
        for item in page.items:
            text = _heading_text(item)
            if text is not None and text.casefold() == target:
                return page.page_index_global
    return None


def _match_chapters_to_pages(
    chapters: list[_Chapter], pages: list[BookPage]
) -> dict[int, _Chapter]:
    """Return a mapping from book-page index (1-based) to the chapter starting there.

    Args:
        chapters: Chapter list from the sidecar.
        pages: All book pages in spine order.

    Returns:
        Dict keyed by ``page.page_index_global`` giving the chapter beginning on
        that page. Raises if a chapter's anchor is not found.

    """
    by_printed: dict[str, int] = {
        p.printed_page_number: p.page_index_global for p in pages if p.printed_page_number
    }
    mapping: dict[int, _Chapter] = {}
    missing: list[str] = []
    for chapter in chapters:
        if chapter.start_printed_page is not None:
            idx = by_printed.get(chapter.start_printed_page)
            if idx is None:
                missing.append(f"printed_page={chapter.start_printed_page!r}")
                continue
        else:
            assert chapter.start_heading is not None
            idx = _match_chapter_to_heading(chapter.start_heading, pages)
            if idx is None:
                missing.append(f"heading={chapter.start_heading!r}")
                continue
        mapping[idx] = chapter
    if missing:
        available = sorted(by_printed.keys())
        msg = (
            f"chapters.toml references anchors not found in any parse: {missing}. "
            f"Available printed pages: {available}"
        )
        raise ValueError(msg)
    return mapping


# Minimum bbox left-indent (in LlamaParse's page-space points) required to
# promote a text item to a blockquote. Carl Barks: Conversations uses a ~26pt
# indent on both sides for block quotations; body paragraphs sit within ~5pt
# of each other, so 15 is a comfortable fence.
_BLOCKQUOTE_INDENT_THRESHOLD = 15.0

# The indent heuristic needs at least this many text items on a page to build
# a reliable median baseline.
_MIN_ITEMS_FOR_HEURISTIC = 2


def _item_bbox_x(item: dict) -> float | None:
    """Return the leftmost bbox x for a text item, or ``None`` if unavailable."""
    bbox = item.get("bbox")
    if not isinstance(bbox, list) or not bbox:
        return None
    first = bbox[0]
    if not isinstance(first, dict):
        return None
    x = first.get("x")
    return float(x) if isinstance(x, int | float) else None


def _median(values: list[float]) -> float:
    """Return the median of ``values`` (assumes non-empty list)."""
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return 0.5 * (s[mid - 1] + s[mid])


def _annotate_blockquotes(page: BookPage) -> None:
    """Mark indented text items as ``render_as="blockquote"`` using their bbox.

    The baseline left-x of a page is taken as the median left-x of its text
    items. Any text item whose bbox is indented by more than
    ``_BLOCKQUOTE_INDENT_THRESHOLD`` points gets promoted. If fewer than two
    text items have bbox info, the heuristic is skipped.

    Args:
        page: Book page; its item dicts are updated in place.

    """
    candidates: list[tuple[dict, float]] = []
    for item in page.items:
        if item.get("type") != "text":
            continue
        x = _item_bbox_x(item)
        if x is None:
            continue
        candidates.append((item, x))
    if len(candidates) < _MIN_ITEMS_FOR_HEURISTIC:
        return
    baseline = _median([x for _, x in candidates])
    for item, x in candidates:
        if x - baseline >= _BLOCKQUOTE_INDENT_THRESHOLD:
            item["render_as"] = "blockquote"


@dataclass(frozen=True)
class _Override:
    """One per-item format override loaded from the overrides sidecar."""

    parse_dir: str
    spread: str
    side: str | None
    text_starts_with: str
    as_: str


def _load_overrides(path: Path | None) -> list[_Override]:
    """Parse the overrides sidecar into ``_Override`` records.

    Args:
        path: Path to the overrides TOML file, or ``None`` to skip loading.

    Returns:
        The parsed overrides, preserving file order.

    """
    if path is None:
        return []
    with path.open("rb") as f:
        data = tomllib.load(f)
    entries = data.get("overrides") or []
    out: list[_Override] = []
    for i, entry in enumerate(entries):
        parse_dir = entry.get("parse_dir")
        spread = entry.get("spread")
        text_starts = entry.get("text_starts_with")
        as_val = entry.get("as")
        side = entry.get("side")
        if (
            not isinstance(parse_dir, str)
            or not isinstance(spread, str)
            or not isinstance(text_starts, str)
        ):
            msg = f"overrides[{i}] requires string 'parse_dir', 'spread', and 'text_starts_with'"
            raise TypeError(msg)
        if as_val not in {"blockquote", "paragraph"}:
            msg = f"overrides[{i}].as must be 'blockquote' or 'paragraph'"
            raise ValueError(msg)
        if side is not None and side not in {"left", "right"}:
            msg = f"overrides[{i}].side must be 'left' or 'right' if given"
            raise ValueError(msg)
        out.append(
            _Override(
                parse_dir=parse_dir,
                spread=spread,
                side=side,
                text_starts_with=text_starts,
                as_=as_val,
            )
        )
    return out


def _item_matches_prefix(item: dict, prefix: str) -> bool:
    """Return True if the item's visible text starts with ``prefix``."""
    text = (item.get("value") or item.get("md") or "").lstrip()
    return text.startswith(prefix)


def _last_text_item(page: BookPage) -> dict | None:
    """Return the last ``type == "text"`` item on ``page``, or ``None``."""
    for item in reversed(page.items):
        if item.get("type") == "text":
            return item
    return None


def _first_text_item(page: BookPage) -> dict | None:
    """Return the first ``type == "text"`` item on ``page``, or ``None``."""
    for item in page.items:
        if item.get("type") == "text":
            return item
    return None


_CONTENT_TYPES = {"text", "list"}


def _last_content_item(page: BookPage) -> dict | None:
    """Return the last text-or-list item on ``page``, or ``None``."""
    for item in reversed(page.items):
        if item.get("type") in _CONTENT_TYPES:
            return item
    return None


def _first_content_item(page: BookPage) -> dict | None:
    """Return the first text-or-list item on ``page``, or ``None``."""
    for item in page.items:
        if item.get("type") in _CONTENT_TYPES:
            return item
    return None


def _text_is_open(text: str) -> bool:
    """Return True if ``text`` does not end in sentence-closing punctuation."""
    trimmed = text.rstrip()
    if not trimmed:
        return False
    return not _SENTENCE_END_RE.search(trimmed)


def _merge_list_continuations(pages: list[BookPage]) -> None:
    """Fold a lowercase text continuation on page B into page A's open list.

    LlamaParse sometimes emits a numbered list whose last entry runs into the
    next page as a standalone ``type: "text"`` item (e.g. a footnote that
    breaks mid-sentence at the page boundary). When detected, the text item is
    appended to the list's markdown and dropped from page B, so the reader sees
    a single complete list entry instead of a truncated one plus an orphan
    paragraph.

    Heuristic:
        * Page A's last content item is a list whose text has no
          sentence-ending punctuation.
        * Page B's first content item is a text item beginning with a lowercase
          letter (a continuation marker).
    """
    for i in range(len(pages) - 1):
        a_last = _last_content_item(pages[i])
        b_first = _first_content_item(pages[i + 1])
        if a_last is None or b_first is None:
            continue
        if a_last.get("type") != "list" or b_first.get("type") != "text":
            continue
        a_md = a_last.get("md") or ""
        b_md = b_first.get("md") or ""
        if not _text_is_open(a_md):
            continue
        b_head = b_md.lstrip()
        if not b_head or not b_head[0].islower():
            continue
        a_last["md"] = f"{a_md.rstrip()} {b_md.lstrip()}"
        a_val = (a_last.get("value") or "").rstrip()
        b_val = (b_first.get("value") or "").lstrip()
        if a_val or b_val:
            a_last["value"] = f"{a_val} {b_val}".strip()
        pages[i + 1].items.remove(b_first)


def _align_cross_page_continuations(pages: list[BookPage]) -> None:
    """Align ``render_as`` across paragraphs that split at a soft word-break.

    The blockquote heuristic scores indentation per-page. A paragraph that
    continues from the previous page — detectable by its first half ending with
    a soft word-break hyphen (e.g. ``"contains an ar-"``) — often appears
    heavily indented on the new page because hanging-indent continuation lines
    start below the section's first line. That makes the heuristic mis-promote
    the continuation to a blockquote. This pass copies the first half's
    ``render_as`` onto the second half so both render the same way.
    """
    for i in range(len(pages) - 1):
        prev = _last_text_item(pages[i])
        nxt = _first_text_item(pages[i + 1])
        if prev is None or nxt is None:
            continue
        prev_text = (prev.get("md") or prev.get("value") or "").rstrip()
        if not _ends_with_soft_word_break(prev_text):
            continue
        prev_mode = prev.get("render_as")
        if prev_mode:
            nxt["render_as"] = prev_mode
        else:
            nxt.pop("render_as", None)


def _apply_format_fixes(pages: list[BookPage], overrides: list[_Override]) -> None:
    """Run the blockquote heuristic, then apply user overrides.

    Raises:
        ValueError: If any override did not match a text item. All unmatched
            overrides are logged before raising so the user can fix them in one
            pass.

    """
    _merge_list_continuations(pages)
    for page in pages:
        _annotate_blockquotes(page)
    _align_cross_page_continuations(pages)
    if not overrides:
        return
    unmatched = _apply_overrides(pages, overrides)
    applied = len(overrides) - len(unmatched)
    logger.info(f"Applied {applied}/{len(overrides)} override(s).")
    if unmatched:
        for ov in unmatched:
            logger.error(
                f"Override did not match any item: parse_dir={ov.parse_dir!r} "
                f"spread={ov.spread!r} side={ov.side!r} "
                f"text_starts_with={ov.text_starts_with!r}"
            )
        msg = f"{len(unmatched)} of {len(overrides)} override(s) did not match any item"
        raise ValueError(msg)


def _apply_overrides(pages: list[BookPage], overrides: list[_Override]) -> list[_Override]:
    """Apply each override to matching items. Returns overrides that matched nothing."""
    unmatched: list[_Override] = []
    for ov in overrides:
        matched = False
        for page in pages:
            if page.parse_dir.name != ov.parse_dir:
                continue
            if ov.spread not in page.spread_stem:
                continue
            if ov.side is not None and page.side != ov.side:
                continue
            for item in page.items:
                if not _item_matches_prefix(item, ov.text_starts_with):
                    continue
                if ov.as_ == "blockquote":
                    item["render_as"] = "blockquote"
                else:
                    item.pop("render_as", None)
                matched = True
        if not matched:
            unmatched.append(ov)
    return unmatched


def _render_item_html(parse_dir: Path, item: dict, md_renderer: MarkdownIt) -> str:
    """Render a single LlamaParse item to an XHTML fragment.

    Args:
        parse_dir: The directory containing the items.
        item: The raw item.
        md_renderer: Markdown-it renderer.

    Returns:
        An XHTML fragment (UTF-8 text). Empty string if the item has nothing to
        render.

    """
    item_type = item.get("type")
    if item_type == "image":
        url = item.get("url")
        caption = item.get("caption") or ""
        if not url:
            msg = f"There is an image without an url: '{item}'"
            raise RuntimeError(msg)
        url_path = parse_dir / url
        if not url_path.is_file():
            msg = f'Could not find url: "{url_path}"'
            raise FileNotFoundError(msg)
        basename = Path(url).name
        caption_attr = escape(caption, {'"': "&quot;"})
        caption_html = escape(caption)
        return (
            f'<figure><img src="images/{escape(basename)}" alt="{caption_attr}"/>'
            f"<figcaption>{caption_html}</figcaption></figure>"
        )
    md = item.get("md")
    if not isinstance(md, str) or not md.strip():
        return ""
    rendered = md_renderer.render(md).strip()
    if item.get("render_as") == "blockquote":
        return f"<blockquote>{rendered}</blockquote>"
    return rendered


def _page_anchor_html(page: BookPage) -> str:
    """Return the invisible ``<span epub:type="pagebreak">`` anchor for a page."""
    esc_num = escape(page.printed_page_number or "")
    return (
        f'<span epub:type="pagebreak" id="page-{page.page_index_global}" '
        f'role="doc-pagebreak" aria-label="{esc_num}"></span>'
    )


# A paragraph "ends a sentence" if the visible text (after stripping footnote
# superscripts and inline tags) terminates with sentence-closing punctuation,
# optionally followed by closing quotes / brackets (straight or curly).
_SENTENCE_END_RE = re.compile("[.!?][\")'\\]\u2019\u201d]*\\s*$")
_SUP_TAG_RE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")

# Minimum characters required to test for a soft word-break hyphen (one letter
# before the hyphen, plus the hyphen itself).
_MIN_HYPHEN_CONTEXT = 2


def _paragraph_is_open(prev_html: str) -> bool:
    """Return True if ``prev_html`` ends with an unfinished paragraph (no sentence end)."""
    trimmed = prev_html.rstrip()
    if not trimmed.endswith("</p>"):
        return False
    inner = trimmed[: -len("</p>")]
    cleaned = _SUP_TAG_RE.sub("", inner)
    plain = _TAG_RE.sub("", cleaned).rstrip()
    if not plain:
        return False
    return not _SENTENCE_END_RE.search(plain)


def _next_starts_paragraph(next_html: str) -> bool:
    """Return True if ``next_html`` starts with a ``<p>`` element."""
    return next_html.lstrip().startswith("<p>")


def _is_full_paragraph(html: str) -> bool:
    """Return True if ``html`` starts with ``<p>`` and ends with ``</p>``."""
    s = html.strip()
    return s.startswith("<p>") and s.endswith("</p>")


def _first_index_of_kind(items: list[list[str]], kind: str) -> int | None:
    """Return the first index in ``items`` whose first element equals ``kind``."""
    for idx, entry in enumerate(items):
        if entry[0] == kind:
            return idx
    return None


def _last_index_of_kind(items: list[list[str]], kind: str) -> int | None:
    """Return the last index in ``items`` whose first element equals ``kind``."""
    for idx in range(len(items) - 1, -1, -1):
        if items[idx][0] == kind:
            return idx
    return None


def _merge_paragraph_texts(prev_p: str, next_p: str) -> str:
    """Join two ``<p>...</p>`` fragments into one paragraph.

    Joins with a single space, except when the previous fragment ends with a
    soft word-break hyphen (``"...line-by-"`` + ``"line)..."`` →
    ``"...line-by-line)..."``), in which case the join is seamless.
    """
    prev_body = prev_p.rstrip()[: -len("</p>")]
    next_body = next_p.lstrip()[len("<p>") :]
    prev_tail = prev_body.rstrip()
    # Soft word break: hyphen immediately preceded by a letter/digit and the
    # next page starts with a letter/digit. No space joiner.
    if _ends_with_soft_word_break(prev_tail):
        next_head = next_body.lstrip()
        if next_head and next_head[0].isalnum():
            return f"{prev_tail}{next_head}"
    return f"{prev_body} {next_body}"


def _ends_with_soft_word_break(text: str) -> bool:
    """Return True if ``text`` ends with a hyphen that continues a word."""
    if not text.endswith("-") or len(text) < _MIN_HYPHEN_CONTEXT:
        return False
    return text[-2].isalnum()


def _build_page_blocks(section: _ChapterSection, md_renderer: MarkdownIt) -> list[dict]:
    """Render each page into a block of (anchor, items) where items are [kind, html]."""
    page_blocks: list[dict] = []
    for page in section.pages:
        anchor = _page_anchor_html(page) if page.printed_page_number else ""
        items: list[list[str]] = []
        for item in page.items:
            html = _render_item_html(page.parse_dir, item, md_renderer)
            if not html:
                continue
            kind = "p" if _is_full_paragraph(html) else "other"
            items.append([kind, html])
        page_blocks.append({"anchor": anchor, "items": items})
    return page_blocks


def _is_figure_like(html: str) -> bool:
    """Return True if ``html`` is a figure/image block (safe to skip during merge)."""
    return html.lstrip().startswith("<figure")


def _merge_paragraph_across_pages(a_items: list[list[str]], b_items: list[list[str]]) -> None:
    """Merge A's last paragraph into B's first paragraph if A's is open.

    Only fires when the span between A's last paragraph and B's first paragraph
    contains figures only — a heading or any other non-figure block between them
    indicates the paragraph split is real (e.g. a new chapter/section opens).
    """
    a_last = _last_index_of_kind(a_items, "p")
    b_first = _first_index_of_kind(b_items, "p")
    if a_last is None or b_first is None:
        return
    for entry in a_items[a_last + 1 :]:
        if not _is_figure_like(entry[1]):
            return
    for entry in b_items[:b_first]:
        if not _is_figure_like(entry[1]):
            return
    if not _paragraph_is_open(a_items[a_last][1]):
        return
    if not _next_starts_paragraph(b_items[b_first][1]):
        return
    b_items[b_first][1] = _merge_paragraph_texts(a_items[a_last][1], b_items[b_first][1])
    del a_items[a_last]


# A page reference is a roman numeral (lowercase) or 1-3 digit arabic number,
# optionally a range joined by an en-dash (U+2013) or ASCII hyphen, with no
# whitespace around the dash (confirmed against the source data). Both single
# (``"129"``) and ranged (``"129-30"``, ``"xv-vi"``) tokens match.
_PAGE_REF_TOKEN_RE = re.compile(
    r"\b(?:[ivxlcdm]+|\d{1,3})(?:[–-](?:[ivxlcdm]+|\d{1,3}))?\b"  # noqa: RUF001
)
_RANGE_SEP_RE = re.compile(r"[–-]")  # noqa: RUF001


def _build_page_link_map(
    section_files: list[tuple[str, "_ChapterSection"]],
) -> dict[str, tuple[str, int]]:
    """Build a printed-page to (xhtml_filename, page_index_global) lookup.

    Used by the index renderer to resolve each page reference into an
    intra-EPUB hyperlink target.

    Args:
        section_files: Pairs of (assigned XHTML filename, section), in spine
            order.

    Returns:
        Mapping keyed by ``BookPage.printed_page_number``. Pages without a
        printed page number are skipped. If two pages share a printed number,
        the first one wins.

    """
    mapping: dict[str, tuple[str, int]] = {}
    for file_name, section in section_files:
        for page in section.pages:
            if not page.printed_page_number:
                continue
            if page.printed_page_number in mapping:
                continue
            mapping[page.printed_page_number] = (file_name, page.page_index_global)
    return mapping


def _linkify_index_entry(line: str, page_link_map: dict[str, tuple[str, int]]) -> str:
    r"""Wrap page-reference tokens after the entry's first comma in Markdown links.

    The text before the first comma is the entry term and is passed through
    unchanged. After the first comma, every token matching
    ``_PAGE_REF_TOKEN_RE`` is wrapped in ``[label](file#page-K)`` if its
    *first* endpoint resolves in ``page_link_map``. Non-resolving tokens
    (e.g. the word ``civic`` or a typo'd second range endpoint like the
    ``vi`` in ``xv-vi``) are left as plain text, so we never emit broken
    links.

    Markdown link syntax is used (rather than raw ``<a>`` HTML) so that
    ``markdown-it`` builds the anchor; this side-steps tag-mismatch hazards
    when an entry contains italics like ``*Comic Art*``.

    Args:
        line: One logical index entry (a single ``\n``-split line).
        page_link_map: Mapping of printed page number to its
            ``(xhtml_filename, page_index_global)``.

    Returns:
        Markdown text with resolved page references replaced by
        ``[label](file#page-K)`` links.

    """
    head, sep, tail = line.partition(",")
    if not sep:
        return line

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        first_endpoint = _RANGE_SEP_RE.split(token, maxsplit=1)[0]
        target = page_link_map.get(first_endpoint)
        if target is None:
            return token
        file_name, page_index = target
        return f"[{token}]({file_name}#page-{page_index})"

    return head + sep + _PAGE_REF_TOKEN_RE.sub(_replace, tail)


def _render_index_xhtml(
    section: _ChapterSection,
    md_renderer: MarkdownIt,
    page_link_map: dict[str, tuple[str, int]],
) -> str:
    r"""Render an index chapter section with linkified page references.

    Each book page emits its pagebreak anchor (so the EPUB3 page-list nav
    still picks up index pages), then each ``type: "text"`` item is split on
    ``\n`` and each line becomes one ``<p class="index-entry">`` with page
    references converted to internal hyperlinks.

    The cross-page paragraph-merge logic used by ``_render_section_xhtml`` is
    deliberately skipped: index entries lack sentence-ending punctuation, so
    that merge would glue the last entry of one page onto the first entry of
    the next.

    Args:
        section: Index chapter section.
        md_renderer: Markdown-it renderer.
        page_link_map: Printed-page to (file, anchor) lookup.

    Returns:
        XHTML body for the section (without the outer ``<div class="chapter">``).

    """
    parts: list[str] = [f"<h1>{escape(section.title)}</h1>"]
    for page in section.pages:
        if page.printed_page_number:
            parts.append(_page_anchor_html(page))
        for item in page.items:
            if item.get("type") != "text":
                continue
            md = item.get("md")
            if not isinstance(md, str) or not md.strip():
                continue
            for raw_line in md.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue
                linkified = _linkify_index_entry(line, page_link_map)
                rendered = md_renderer.renderInline(linkified).strip()
                if not rendered:
                    continue
                parts.append(f'<p class="index-entry">{rendered}</p>')
    return "\n".join(parts)


_CONTENTS_TRAILING_PAGE_RE = re.compile(r"(?P<token>\b(?:[ivxlcdm]+|\d{1,3})\b)(?P<bold>\*\*)?\s*$")


def _linkify_contents_title(line: str, page_link_map: dict[str, tuple[str, int]]) -> str:
    """Wrap a Contents title line in a markdown link if its trailing page ref resolves.

    The line may be wrapped in ``**...**`` (bold). Markdown-it correctly renders
    ``[**text**](url)`` as a link wrapping bold, so the entire line is wrapped
    either way. If no trailing page-reference token is found, or the token
    doesn't resolve in ``page_link_map``, the line is returned unchanged.
    """
    match = _CONTENTS_TRAILING_PAGE_RE.search(line)
    if match is None:
        return line
    target = page_link_map.get(match.group("token"))
    if target is None:
        return line
    file_name, page_index = target
    return f"[{line}]({file_name}#page-{page_index})"


def _render_contents_text_item(
    md: str, md_renderer: MarkdownIt, page_link_map: dict[str, tuple[str, int]]
) -> list[str]:
    r"""Render one Contents text item's markdown into a list of <p> fragments.

    Each non-empty line is classified by content: a line ending with a
    page-reference token is a chapter title (linkified if the token resolves);
    any other line is a credit subline. This handles both back-to-back titles
    (e.g. ``"Introduction ix\nChronology xxxv"``) and title+credit blocks
    (``"**The Duck Man 3**\n*Malcolm Willits...*"``) without relying on blank
    lines to separate titles, since the printed Contents only uses blank lines
    between *groups* of entries, not between every entry.
    """
    out: list[str] = []
    for raw_line in md.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if _CONTENTS_TRAILING_PAGE_RE.search(line):
            linkified = _linkify_contents_title(line, page_link_map)
            rendered = md_renderer.renderInline(linkified).strip()
            if rendered:
                out.append(f'<p class="contents-entry">{rendered}</p>')
        else:
            rendered = md_renderer.renderInline(line).strip()
            if rendered:
                out.append(f'<p class="contents-credit">{rendered}</p>')
    return out


def _render_contents_xhtml(
    section: _ChapterSection,
    md_renderer: MarkdownIt,
    page_link_map: dict[str, tuple[str, int]],
) -> str:
    """Render a Contents chapter section with linkified chapter titles.

    Each book page emits its pagebreak anchor (so EPUB3 page-list nav still
    picks up Contents pages). Each ``type: "text"`` item is split on blank lines
    into entries; the first non-empty line of an entry is the chapter title
    (linkified to the chapter's first page anchor if its trailing page-reference
    token resolves), and any subsequent non-empty lines are rendered as italic
    credit sub-lines.

    The original ``# Contents`` heading item is suppressed because we emit our
    own ``<h1>`` from ``section.title``.

    Cross-page paragraph merging is deliberately skipped (same rationale as
    ``_render_index_xhtml``): contents entries lack sentence-ending punctuation
    and would otherwise be glued together at page boundaries.

    Args:
        section: Contents chapter section.
        md_renderer: Markdown-it renderer.
        page_link_map: Printed-page to (file, anchor) lookup.

    Returns:
        XHTML body for the section (without the outer ``<div class="chapter">``).

    """
    parts: list[str] = [f"<h1>{escape(section.title)}</h1>"]
    title_cf = section.title.casefold()
    for page in section.pages:
        if page.printed_page_number:
            parts.append(_page_anchor_html(page))
        for item in page.items:
            heading_text = _heading_text(item)
            if heading_text is not None and heading_text.casefold() == title_cf:
                continue
            if item.get("type") != "text":
                continue
            md = item.get("md")
            if not isinstance(md, str) or not md.strip():
                continue
            parts.extend(_render_contents_text_item(md, md_renderer, page_link_map))
    return "\n".join(parts)


def _render_section_xhtml(section: _ChapterSection, md_renderer: MarkdownIt) -> str:
    """Build the XHTML body for one chapter section.

    LlamaParse often splits a single paragraph at a page boundary — sometimes
    with figures (image crops) sitting between the two halves. This renderer
    detects such splits and merges the two halves into one ``<p>`` so readers
    don't see a mid-paragraph line break. Intervening figures stay in reading
    order and cluster between the two pages' non-text content.

    Args:
        section: Chapter section to render.
        md_renderer: Markdown-it renderer.

    Returns:
        The XHTML body content (without the outer ``<body>`` wrapper).

    """
    page_blocks = _build_page_blocks(section, md_renderer)

    for i in range(len(page_blocks) - 1):
        _merge_paragraph_across_pages(page_blocks[i]["items"], page_blocks[i + 1]["items"])

    parts: list[str] = []
    for block in page_blocks:
        anchor = block["anchor"]
        items = block["items"]
        if anchor and items:
            items[0][1] = anchor + items[0][1]
        elif anchor:
            parts.append(anchor)
        parts.extend(entry[1] for entry in items)
    return "\n".join(parts)


def _group_pages_into_sections(
    pages: list[BookPage], chapters_by_page: dict[int, _Chapter]
) -> list[_ChapterSection]:
    """Group consecutive pages into one ``_ChapterSection`` per chapter.

    A page belongs to the most-recently-opened chapter. Pages before the first
    chapter anchor (if any) go into a synthetic "Front Matter" section so they
    still appear in the spine.

    Args:
        pages: Book pages in spine order.
        chapters_by_page: Mapping from ``page_index_global`` to the chapter
            starting on that page.

    Returns:
        One ``_ChapterSection`` per chapter run, in spine order.

    """
    sections: list[_ChapterSection] = []
    current_title: str | None = None
    current_kind: str = "regular"
    current_pages: list[BookPage] = []
    current_first_idx = 0

    for page in pages:
        chapter_here = chapters_by_page.get(page.page_index_global)
        if chapter_here is not None:
            if current_pages:
                sections.append(
                    _ChapterSection(
                        title=current_title or "Front Matter",
                        pages=current_pages,
                        first_page_index=current_first_idx,
                        kind=current_kind,
                    )
                )
            current_title = chapter_here.title
            current_kind = chapter_here.kind
            current_pages = [page]
            current_first_idx = page.page_index_global
        else:
            if not current_pages:
                current_first_idx = page.page_index_global
            current_pages.append(page)

    if current_pages:
        sections.append(
            _ChapterSection(
                title=current_title or "Front Matter",
                pages=current_pages,
                first_page_index=current_first_idx,
                kind=current_kind,
            )
        )
    return sections


_SUP_NOTE_RE = re.compile(r"<sup>(\d+)</sup>")
_NOTES_HEADING_RE = re.compile(r"<h2>Notes</h2>", re.IGNORECASE)
_OL_BLOCK_RE = re.compile(r"<ol(?P<attrs>\b[^>]*)>(?P<inner>.*?)</ol>", re.DOTALL)
_OL_START_ATTR_RE = re.compile(r'\bstart="(\d+)"')
_LI_OPEN_RE = re.compile(r"<li>")


def _linkify_footnotes(html: str) -> str:
    """Add EPUB3 noteref/endnote semantics to a section's rendered XHTML.

    Finds the first ``<h2>Notes</h2>`` heading and treats every ``<ol>`` block
    after it as a continuation of the endnote list (the printed Notes section
    can be broken into multiple ``<ol>`` blocks at page boundaries — markdown-it
    emits ``<ol start="N">`` for the continuation). Each ``<li>`` gets
    ``id="fn-N"``, where N is taken from the ``<ol>``'s ``start`` attribute (or
    1 for the first block). Each ``<sup>N</sup>`` marker in body text becomes
    ``<a epub:type="noteref" href="#fn-N">``. No-op if there's no Notes block.

    Forward-link only — no backlink from note to body — so readers rely on
    their built-in back gesture to return.
    """
    heading_match = _NOTES_HEADING_RE.search(html)
    if heading_match is None:
        return html
    head = html[: heading_match.end()]
    tail = html[heading_match.end() :]

    def _process_ol(m: re.Match[str]) -> str:
        attrs = m.group("attrs")
        start_match = _OL_START_ATTR_RE.search(attrs)
        counter = int(start_match.group(1)) if start_match else 1

        def _add_id(_: re.Match[str]) -> str:
            nonlocal counter
            i = counter
            counter += 1
            return f'<li id="fn-{i}" epub:type="footnote" role="doc-footnote">'

        new_inner = _LI_OPEN_RE.sub(_add_id, m.group("inner"))
        return f'<ol epub:type="endnotes"{attrs}>{new_inner}</ol>'

    new_tail = _OL_BLOCK_RE.sub(_process_ol, tail)
    html = head + new_tail
    return _SUP_NOTE_RE.sub(
        r'<sup><a epub:type="noteref" href="#fn-\1" role="doc-noteref">\1</a></sup>',
        html,
    )


def _collect_image_paths(pages: list[BookPage]) -> dict[str, Path]:
    """Find every image referenced by any page and return ``basename → source path``.

    Args:
        pages: All book pages.

    Returns:
        Mapping so that the same image referenced from multiple pages is only
        copied once.

    """
    mapping: dict[str, Path] = {}
    for page in pages:
        for item in page.items:
            if item.get("type") != "image":
                continue
            url = item.get("url")
            if not url:
                continue
            basename = Path(url).name
            if basename in mapping:
                continue
            src = page.parse_dir / basename
            if not src.is_file():
                logger.warning(f"Referenced image not found on disk: {src}")
                continue
            mapping[basename] = src
    return mapping


def _build_epub(  # noqa: PLR0913 - arg-per-option is reasonable for an epub builder
    pages: list[BookPage],
    chapters_by_page: dict[int, _Chapter],
    output_path: Path,
    title: str,
    author: str,
    language: str,
    cover_path: Path | None,
) -> None:
    """Assemble and write the EPUB3.

    Args:
        pages: All book pages in spine order.
        chapters_by_page: Mapping from page_index_global → chapter starting there.
        output_path: Where to write the ``.epub``.
        title: Book title.
        author: Book author / editor.
        language: BCP-47 language tag (e.g. ``"en"``).
        cover_path: Optional cover image path.

    """
    book = epub.EpubBook()
    book.set_identifier(f"llama-parse-{output_path.stem}")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    if cover_path is not None:
        if not cover_path.is_file():
            logger.warning(f"--cover path does not exist: {cover_path}")
        else:
            book.set_cover(cover_path.name, cover_path.read_bytes())

    css = epub.EpubItem(
        uid="style-book",
        file_name="styles/book.css",
        media_type="text/css",
        content=_CSS.encode("utf-8"),
    )
    book.add_item(css)

    image_map = _collect_image_paths(pages)
    for basename, src_path in image_map.items():
        media_type = "image/jpeg" if basename.lower().endswith((".jpg", ".jpeg")) else "image/png"
        book.add_item(
            epub.EpubImage(
                uid=f"img-{basename}",
                file_name=f"images/{basename}",
                media_type=media_type,
                content=src_path.read_bytes(),
            )
        )

    sections = _group_pages_into_sections(pages, chapters_by_page)
    md_renderer = MarkdownIt("commonmark", {"html": True}).enable("table")
    section_files = [
        (f"section-{idx:04d}.xhtml", section) for idx, section in enumerate(sections, start=1)
    ]
    page_link_map = _build_page_link_map(section_files)
    xhtml_sections: list[epub.EpubHtml] = []
    toc_entries: list[epub.Link] = []
    for file_name, section in section_files:
        if section.kind == "index":
            inner = _render_index_xhtml(section, md_renderer, page_link_map)
        elif section.kind == "contents":
            inner = _render_contents_xhtml(section, md_renderer, page_link_map)
        else:
            inner = _render_section_xhtml(section, md_renderer)
            inner = _linkify_footnotes(inner)
        body = f'<div class="chapter">\n{inner}\n</div>'
        uid = f"section-{section.first_page_index}"
        item = epub.EpubHtml(
            uid=uid,
            file_name=file_name,
            title=section.title,
            lang=language,
            content=body,
        )
        item.add_item(css)
        book.add_item(item)
        xhtml_sections.append(item)
        toc_entries.append(epub.Link(file_name, section.title, uid))

    book.toc = list(toc_entries)
    book.spine = ["nav", *xhtml_sections]

    # Page-list nav is auto-generated by EpubNav from epub:type="pagebreak"
    # anchors emitted inline at the start of each book page's content.

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)
    logger.info(f"Wrote EPUB: {output_path}")


@app.command()
def main(  # noqa: PLR0913 - one param per CLI flag is the natural shape here
    parse_dirs: Path = typer.Option(  # noqa: B008
        ...,
        "--parse-dirs",
        help="Parent directory containing one LlamaParse output subdirectory per scan.",
    ),
    chapters: Path = typer.Option(  # noqa: B008
        ...,
        "--chapters",
        help="Path to chapters.toml sidecar file.",
    ),
    title: str = typer.Option(..., "--title", help="Book title."),
    author: str = typer.Option(..., "--author", help="Book author / editor."),
    cover: Path | None = typer.Option(  # noqa: B008
        None, "--cover", help="Optional cover image."
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None,
        "--output",
        help="Output .epub path (default: <parse-dirs>/<title-slug>.epub).",
    ),
    language: str = typer.Option("en", "--language", help="BCP-47 language tag."),
    keep_running_headers: bool = typer.Option(
        False,  # noqa: FBT003
        "--keep-running-headers",
        help="Keep running page headers and standalone page-number items in body text.",
    ),
    overrides: Path | None = typer.Option(  # noqa: B008
        None,
        "--overrides",
        help="Optional overrides.toml sidecar with per-item format fixes.",
    ),
) -> None:
    """Build an EPUB3 from LlamaParse parse directories and a chapter sidecar."""
    if not parse_dirs.is_dir():
        logger.error(f"Not a directory: {parse_dirs}")
        raise typer.Exit(1)
    parse_dir_list = sorted(d for d in parse_dirs.iterdir() if d.is_dir())
    if not parse_dir_list:
        logger.error(f"No parse subdirectories found under: {parse_dirs}")
        raise typer.Exit(1)
    if not chapters.is_file():
        logger.error(f"Chapters sidecar not found: {chapters}")
        raise typer.Exit(1)
    if overrides is not None and not overrides.is_file():
        logger.error(f"Overrides sidecar not found: {overrides}")
        raise typer.Exit(1)

    chapter_list = _load_chapters(chapters)
    override_list = _load_overrides(overrides)

    logger.info(f"Loading spreads from {len(parse_dir_list)} parse dir(s) ...")
    spreads = list(iter_spreads(parse_dir_list))
    logger.info(f"Loaded {len(spreads)} spread(s).")

    pages = list(iter_book_pages(spreads, drop_running_headers=not keep_running_headers))
    logger.info(f"Produced {len(pages)} book page(s).")
    if not pages:
        logger.error("No book pages to write.")
        raise typer.Exit(1)

    try:
        _apply_format_fixes(pages, override_list)
    except ValueError as exc:
        logger.error(str(exc))
        raise typer.Exit(1) from exc

    try:
        chapters_by_page = _match_chapters_to_pages(chapter_list, pages)
    except ValueError as exc:
        logger.error(str(exc))
        raise typer.Exit(1) from exc
    logger.info(f"Matched {len(chapters_by_page)} chapter(s) to book pages.")

    if output is None:
        slug = "".join(c if c.isalnum() else "-" for c in title).strip("-").lower()
        output = parse_dirs / f"{slug or 'book'}.epub"

    _build_epub(
        pages=pages,
        chapters_by_page=chapters_by_page,
        output_path=output,
        title=title,
        author=author,
        language=language,
        cover_path=cover,
    )


if __name__ == "__main__":
    app()
