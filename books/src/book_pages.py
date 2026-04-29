# ruff: noqa: INP001

"""Split each parse unit into one or two book pages.

For two-page-spread parse output, LlamaParse items carry a ``book_side`` tag
("left" or "right") added by ``scripts/llama-parse-pdf.py``; this module groups
items by side and assigns each side's printed page number. For single-page
parse output (each JSON describes one printed page), items have no
``book_side`` and the whole record becomes one ``BookPage``. Either way,
running page-header / standalone-page-number items can optionally be stripped
so the EPUB body doesn't contain noise that's already captured in the EPUB
page-list nav.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from loader import SpreadRecord

_ROMAN_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)

# Max length of a text item we'll consider as a "standalone page number"
# (e.g. "xxviii" = 6, "4, 5" after strip/trim is 4). Longer strings are
# real body text.
_MAX_PAGE_NUMBER_LEN = 8

# A page-number-like token: a short roman numeral (<= 8 letters) or 1-3 digits.
# We deliberately cap digits at 3 so 4-digit years in interview bylines
# ("Willits / 1962") aren't mistaken for page numbers.
_PAGE_NUM_TOKEN = r"(?:[ivxlcdmIVXLCDM]{1,8}|\d{1,3})"  # noqa: S105 - regex fragment

# Matches a running page header rendered as a heading, where a page-number
# token sits at the start or end with real title text on the other side —
# e.g. "xvi INTRODUCTION", "INTRODUCTION xvii", "6 CARL BARKS: CONVERSATIONS",
# "DONALD AULT / 1973 49", "60 Carl Barks: Conversations".
_HEADING_WITH_PAGE_NUM_RE = re.compile(rf"^(?:{_PAGE_NUM_TOKEN}\s+\S.*|\S.*\s+{_PAGE_NUM_TOKEN})$")

# Cap heading length so a legitimate long section title that happens to end
# with a page-reference is kept.
_MAX_RUNNING_HEADER_LEN = 80

# An all-caps heading is treated as a running header only if its text appears
# on at least this many distinct spreads. Section headings appear on 1-2
# spreads; running headers (e.g. the book title repeated on every page) appear
# on many more.
_RUNNING_HEADER_REPEAT_THRESHOLD = 3


@dataclass(frozen=True)
class BookPage:
    """One logical printed book page extracted from a spread.

    Attributes:
        parse_dir: Parse directory the page came from.
        spread_stem: Source spread filename stem.
        spread_num_global: Spread number across all parse dirs (1-based).
        side: ``"left"`` or ``"right"``.
        printed_page_number: Printed page number string (e.g. ``"xxvi"`` or
            ``"4"``), or ``None`` if the spread had no detected number for this
            side.
        items: Items assigned to this side, in the original reading order.
        page_index_global: 1-based index across all book pages in all parses.

    """

    parse_dir: Path
    spread_stem: str
    spread_num_global: int
    side: str
    printed_page_number: str | None
    items: list[dict]
    page_index_global: int


def _split_printed_pages(raw: str | None) -> list[str | None]:
    """Split a raw ``printed_page_number`` string into per-side entries.

    Args:
        raw: Raw string such as ``"xxvi, xxvii"``, ``"49"``, ``"20, 21"``, or
            ``None``.

    Returns:
        A list of at most two entries, each either a printed page string or
        ``None``. Empty or missing input returns ``[]``.

    """
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p or None for p in parts]


def _heading_text(item: dict) -> str:
    """Return a heading item's plain text, stripped of leading ``#`` markers."""
    text = (item.get("value") or "").strip()
    if text:
        return text
    md = (item.get("md") or "").strip()
    return re.sub(r"^#+\s*", "", md).strip()


_HEADING_PAGE_NUM_PREFIX_RE = re.compile(rf"^{_PAGE_NUM_TOKEN}\s+(.+)$")
_HEADING_PAGE_NUM_SUFFIX_RE = re.compile(rf"^(.+?)\s+{_PAGE_NUM_TOKEN}$")


def _heading_text_without_page_num(text: str) -> str:
    """Strip a single leading or trailing page-number token from heading text.

    Running page headers vary by page (the page number changes from spread to
    spread) but their non-page-number portion ("INTRODUCTION", "Carl Barks:
    Conversations", ...) repeats. Stripping the page-num token gives a
    canonical form that the cross-spread repetition check can count
    consistently.
    """
    m = _HEADING_PAGE_NUM_PREFIX_RE.match(text)
    if m:
        return m.group(1).strip()
    m = _HEADING_PAGE_NUM_SUFFIX_RE.match(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def is_running_header_item(  # noqa: PLR0911 - many reasons to drop
    item: dict, *, repeating_headings: frozenset[str] = frozenset()
) -> bool:
    """Return True if ``item`` is a running header/footer or standalone page number.

    Filters out:
      * ``type == "header"`` or ``type == "footer"`` items (LlamaParse running
        page headers/footers; footer items are typically the standalone page
        number).
      * ``type == "text"`` items whose value contains ``<page_header>`` or
        ``<page_footer>`` markers (LlamaParse sometimes emits running headers as
        text items with explicit tags).
      * ``type == "heading"`` items whose text starts or ends with a short
        page-number token (LlamaParse frequently misclassifies running headers
        such as ``"xvi INTRODUCTION"`` or ``"DONALD AULT / 1973 49"`` as
        markdown headings).
      * ``type == "heading"`` items in all caps whose text is in
        ``repeating_headings`` — i.e. that appear on enough distinct spreads to
        be a running header rather than a section title.
      * Standalone page-number text items whose ``value`` matches digits only or
        lowercase Roman numerals only (length ≤ 8).

    Args:
        item: One LlamaParse item dict.
        repeating_headings: Heading texts known to repeat across multiple
            spreads. The all-caps rule only fires for texts in this set, so a
            unique all-caps section heading is preserved.

    Returns:
        True if the item should be dropped from EPUB body content.

    """
    item_type = item.get("type")
    if item_type in {"header", "footer"}:
        return True
    value = (item.get("value") or "").strip()
    if "<page_header>" in value or "<page_footer>" in value:
        return True
    if item_type == "heading":
        heading_text = _heading_text(item)
        if heading_text and len(heading_text) <= _MAX_RUNNING_HEADER_LEN:
            if _HEADING_WITH_PAGE_NUM_RE.match(heading_text) and (
                heading_text in repeating_headings
                or _heading_text_without_page_num(heading_text) in repeating_headings
            ):
                # Looks like a running header (page-num + title pattern). Only
                # drop if the title portion actually repeats across spreads —
                # a section heading like "20 - 1948 - 24 pages" survives because
                # its normalized form is unique.
                return True
            # ALL-CAPS repeat-header variant (e.g. "CHRONOLOGY",
            # "CARL BARKS: CONVERSATIONS"). Only drop if the text actually
            # repeats across enough spreads to be a running header — a unique
            # all-caps section title in a single book stays in.
            has_letter = any(c.isalpha() for c in heading_text)
            has_lower = any(c.islower() for c in heading_text)
            if has_letter and not has_lower and heading_text in repeating_headings:
                return True
    if not value or len(value) > _MAX_PAGE_NUMBER_LEN:
        return False
    if value.isdigit():
        return True
    return bool(_ROMAN_RE.fullmatch(value))


def split_by_side(
    record: SpreadRecord,
    *,
    drop_running_headers: bool,
    repeating_headings: frozenset[str] = frozenset(),
) -> list[BookPage]:
    """Split one parse record's items into one or two book pages.

    Args:
        record: The spread or single-page record to split.
        drop_running_headers: If True, strip running page-header and standalone
            page-number items before building each ``BookPage``.
        repeating_headings: Forwarded to ``is_running_header_item`` so the
            all-caps heading rule only fires for texts that actually repeat
            across spreads.

    Returns:
        One or two ``BookPage`` instances. For a two-page spread, left first
        then right (with empty sides omitted). For a single-page record (no
        ``book_side`` tags on its items), one ``BookPage`` containing every
        item, labeled ``side="left"``.

    """
    printed = _split_printed_pages(record.printed_page_number)
    left_items: list[dict] = []
    right_items: list[dict] = []
    unsided_items: list[dict] = []
    for item in record.items:
        if drop_running_headers and is_running_header_item(
            item, repeating_headings=repeating_headings
        ):
            continue
        side = item.get("book_side")
        if side == "left":
            left_items.append(item)
        elif side == "right":
            right_items.append(item)
        else:
            unsided_items.append(item)

    # Single-page parse output: each JSON is one printed page, with no
    # left/right split. Emit one BookPage holding every item.
    if not left_items and not right_items and unsided_items:
        return [
            BookPage(
                parse_dir=record.parse_dir,
                spread_stem=record.spread_stem,
                spread_num_global=record.spread_num_global,
                side="left",
                printed_page_number=printed[0] if printed else None,
                items=unsided_items,
                page_index_global=0,
            )
        ]

    # Default to positional assignment (left is index 0, right is index 1).
    # Special case: when only the right side has items and the spread carries
    # exactly one detected printed page, that page belongs to the right - this
    # happens on a recto-only opening like the index heading page where the
    # verso of the previous spread carries no content.
    printed_left = printed[0] if len(printed) > 0 else None
    printed_right = printed[1] if len(printed) > 1 else None
    if right_items and not left_items and len(printed) == 1:
        printed_left, printed_right = None, printed[0]

    pages: list[BookPage] = []
    if left_items:
        pages.append(
            BookPage(
                parse_dir=record.parse_dir,
                spread_stem=record.spread_stem,
                spread_num_global=record.spread_num_global,
                side="left",
                printed_page_number=printed_left,
                items=left_items,
                page_index_global=0,
            )
        )
    if right_items:
        pages.append(
            BookPage(
                parse_dir=record.parse_dir,
                spread_stem=record.spread_stem,
                spread_num_global=record.spread_num_global,
                side="right",
                printed_page_number=printed_right,
                items=right_items,
                page_index_global=0,
            )
        )
    return pages


def _find_repeating_headings(spreads: list[SpreadRecord]) -> frozenset[str]:
    """Return heading texts that appear on enough distinct spreads to be running headers.

    Counts both the raw heading text and its page-num-stripped form, so a
    running header that varies its page number from spread to spread (e.g.
    "xvi INTRODUCTION", "INTRODUCTION xvii") is detected by its repeating
    "INTRODUCTION" portion. A text counts as repeating once it shows up on at
    least ``_RUNNING_HEADER_REPEAT_THRESHOLD`` distinct spreads — section
    headings that legitimately span 1-2 spreads are kept; book-title style
    running headers that repeat across many pages are flagged.
    """
    spreads_per_text: dict[str, set[int]] = {}
    for spread in spreads:
        for item in spread.items:
            if item.get("type") != "heading":
                continue
            text = _heading_text(item)
            if not text:
                continue
            for variant in {text, _heading_text_without_page_num(text)}:
                if variant:
                    spreads_per_text.setdefault(variant, set()).add(spread.spread_num_global)
    return frozenset(
        text
        for text, spread_nums in spreads_per_text.items()
        if len(spread_nums) >= _RUNNING_HEADER_REPEAT_THRESHOLD
    )


def iter_book_pages(
    spreads: Iterable[SpreadRecord], *, drop_running_headers: bool
) -> Iterator[BookPage]:
    """Yield every book page from a sequence of spreads, with global indexing.

    Args:
        spreads: Spread records in parse order.
        drop_running_headers: Passed through to ``split_by_side``.

    Yields:
        Book pages with ``page_index_global`` set (1-based).

    """
    spreads_list = list(spreads)
    repeating_headings = (
        _find_repeating_headings(spreads_list) if drop_running_headers else frozenset()
    )
    counter = 0
    for spread in spreads_list:
        for page in split_by_side(
            spread,
            drop_running_headers=drop_running_headers,
            repeating_headings=repeating_headings,
        ):
            counter += 1
            yield BookPage(
                parse_dir=page.parse_dir,
                spread_stem=page.spread_stem,
                spread_num_global=page.spread_num_global,
                side=page.side,
                printed_page_number=page.printed_page_number,
                items=page.items,
                page_index_global=counter,
            )
