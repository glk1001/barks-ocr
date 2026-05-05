#!/usr/bin/env python3
"""Grammar-check LlamaParse JSON text fields via LanguageTool.

For each spread JSON in the supplied parse directories this script joins
consecutive text-item ``value`` fields into one chunk per spread (so
LanguageTool sees full sentence context), runs LanguageTool locally, and
writes a JSON report mapping each match back to its source item.

Joining mirrors the simplest part of llama-parse-build-epub.py:
soft word-break hyphens at end-of-item join seamlessly to the next item;
otherwise items are separated by a single space.
"""

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import language_tool_python
import typer
from loader import SpreadRecord, iter_spreads
from loguru import logger

app = typer.Typer(add_completion=False)

_BARKS_BOOKS_WORDS = Path(__file__).parent.parent / "cspell-words-barks-books.txt"

# Two chars: one alnum + a trailing hyphen.
_MIN_HYPHEN_CONTEXT = 2

# Rules that are noisy on this corpus; refine after a first pass.
_DEFAULT_DISABLED_RULES = (
    "MORFOLOGIK_RULE_EN_US",  # spelling — already covered by cspell
    "EN_QUOTES",  # curly-vs-straight quote preference
    "WHITESPACE_RULE",  # column joins introduce odd spacing
    "DASH_RULE",
)

_TEXT_FIELDS = (("text", "value"), ("image", "caption"))


@dataclass(frozen=True)
class _ItemRef:
    parse_dir: str
    spread_stem: str
    item_index: int
    field: str


@dataclass(frozen=True)
class _Chunk:
    """One joined string per spread plus a per-character map back to items."""

    text: str
    # char_owner[i] gives the _ItemRef that contributed character i, or None
    # for join-spaces that weren't part of any source field.
    char_owner: list[_ItemRef | None]
    parse_dir: str
    spread_stem: str


@dataclass(frozen=True)
class _Finding:
    parse_dir: str
    spread_stem: str
    item_index: int | None  # None if the match straddles a join
    field: str | None
    rule_id: str
    category: str
    message: str
    matched_text: str
    suggestions: list[str]
    context: str


def _ends_with_soft_word_break(text: str) -> bool:
    """Return True if ``text`` ends with a hyphen that continues a word."""
    return len(text) >= _MIN_HYPHEN_CONTEXT and text.endswith("-") and text[-2].isalnum()


def _build_chunk(rec: SpreadRecord) -> _Chunk | None:
    """Concat all text/image-caption fields in reading order, tracking owners.

    Args:
        rec: One spread's parse record.

    Returns:
        A ``_Chunk`` whose ``text`` is the joined string and whose
        ``char_owner`` array maps each character back to its source item, or
        ``None`` if the spread has no spellcheckable text.

    """
    pieces: list[str] = []
    owners: list[list[_ItemRef | None]] = []
    for idx, item in enumerate(rec.items):
        for wanted_type, wanted_field in _TEXT_FIELDS:
            if item.get("type") != wanted_type:
                continue
            content = item.get(wanted_field)
            if not isinstance(content, str) or not content.strip():
                continue
            ref = _ItemRef(
                parse_dir=str(rec.parse_dir),
                spread_stem=rec.spread_stem,
                item_index=idx,
                field=wanted_field,
            )
            squashed = re.sub(r"\s+", " ", content).strip()

            if pieces:
                # Decide joiner: soft word-break → no space, else single space.
                prev_tail = pieces[-1].rstrip()
                if _ends_with_soft_word_break(prev_tail) and squashed[:1].isalnum():
                    # Strip the trailing hyphen + any whitespace, join seamlessly.
                    drop = len(pieces[-1]) - len(prev_tail) + 1
                    pieces[-1] = pieces[-1][:-drop]
                    owners[-1] = owners[-1][:-drop]
                else:
                    pieces.append(" ")
                    owners.append([None])

            pieces.append(squashed)
            owners.append([ref] * len(squashed))

    if not pieces:
        return None
    flat_owners: list[_ItemRef | None] = [o for sub in owners for o in sub]
    text = "".join(pieces)
    assert len(text) == len(flat_owners)
    return _Chunk(
        text=text,
        char_owner=flat_owners,
        parse_dir=str(rec.parse_dir),
        spread_stem=rec.spread_stem,
    )


def _owner_at(chunk: _Chunk, offset: int, length: int) -> _ItemRef | None:
    """Return the item that owns the matched span, or ``None`` if it straddles items."""
    span = chunk.char_owner[offset : offset + length]
    refs = {o for o in span if o is not None}
    if len(refs) == 1:
        return next(iter(refs))
    return None


def _load_ignore_words(path: Path) -> set[str]:
    """Load casefold ignore-words from a one-word-per-line file."""
    if not path.is_file():
        return set()
    return {
        ln.strip().casefold()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    }


def _check_chunk(
    tool: language_tool_python.LanguageTool,
    chunk: _Chunk,
    ignore_words: set[str],
) -> list[_Finding]:
    """Run LanguageTool on one chunk and map matches back to source items."""
    findings: list[_Finding] = []
    for m in tool.check(chunk.text):
        matched = chunk.text[m.offset : m.offset + m.error_length]
        if matched.strip().casefold() in ignore_words:
            continue
        owner = _owner_at(chunk, m.offset, m.error_length)
        findings.append(
            _Finding(
                parse_dir=chunk.parse_dir,
                spread_stem=chunk.spread_stem,
                item_index=owner.item_index if owner else None,
                field=owner.field if owner else None,
                rule_id=m.rule_id,
                category=m.category,
                message=m.message,
                matched_text=matched,
                suggestions=list(m.replacements[:5]),
                context=m.context,
            )
        )
    return findings


def _print_summary(findings: list[_Finding]) -> None:
    if not findings:
        logger.info("No grammar issues found.")
        return
    by_rule: Counter[str] = Counter(f.rule_id for f in findings)
    logger.info(f"Found {len(findings)} grammar match(es); {len(by_rule)} unique rule(s).")
    logger.info("Top rules:")
    for rule, count in by_rule.most_common(25):
        logger.info(f"  {count:>4}  {rule}")


@app.command()
def main(
    parse_dirs: Path = typer.Option(  # noqa: B008
        ...,
        "--parse-dirs",
        help="Parent directory containing one LlamaParse output subdirectory per scan.",
    ),
    report_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--report-file",
        help="Where to write the JSON report (default: <parse-dirs>/grammar-report.json).",
    ),
    disable_rule: list[str] = typer.Option(  # noqa: B008
        list(_DEFAULT_DISABLED_RULES),
        "--disable-rule",
        help="LanguageTool rule IDs to disable (repeatable).",
    ),
    language: str = typer.Option("en-US", "--language"),
) -> None:
    """Grammar-check joined text from one or more parse directories."""
    if not parse_dirs.is_dir():
        logger.error(f"Not a directory: {parse_dirs}")
        raise typer.Exit(1)
    parse_dir_list = sorted(d for d in parse_dirs.iterdir() if d.is_dir())
    if not parse_dir_list:
        logger.error(f"No parse subdirectories found under: {parse_dirs}")
        raise typer.Exit(1)

    ignore_words = _load_ignore_words(_BARKS_BOOKS_WORDS)
    logger.info(f"Loaded {len(ignore_words)} project ignore-words.")

    logger.info(f"Loading spreads from {len(parse_dir_list)} parse dir(s) ...")
    spreads = list(iter_spreads(parse_dir_list))
    chunks = [c for c in (_build_chunk(r) for r in spreads) if c is not None]
    logger.info(f"Built {len(chunks)} chunk(s) from {len(spreads)} spread(s).")

    # Local server-mode tool; first run downloads ~250MB LT JAR under the
    # user's cache dir. Use LanguageToolPublicAPI() instead to hit the public
    # endpoint (rate-limited; not for batch runs).
    tool = language_tool_python.LanguageTool(language)
    for rule_id in disable_rule:
        tool.disabled_rules.add(rule_id)

    findings: list[_Finding] = []
    try:
        for i, chunk in enumerate(chunks, 1):
            findings.extend(_check_chunk(tool, chunk, ignore_words))
            if i % 50 == 0:
                logger.info(f"  checked {i}/{len(chunks)} chunks ...")
    finally:
        tool.close()

    _print_summary(findings)

    resolved_report = report_file if report_file is not None else parse_dirs / "grammar-report.json"
    by_rule_counts: Counter[str] = Counter(f.rule_id for f in findings)
    report = {
        "language": language,
        "disabled_rules": sorted(disable_rule),
        "num_parse_dirs": len(parse_dir_list),
        "num_spreads": len(spreads),
        "num_chunks": len(chunks),
        "num_findings": len(findings),
        "by_rule": dict(by_rule_counts.most_common()),
        "findings": [asdict(f) for f in findings],
    }
    resolved_report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Wrote report to {resolved_report}")


if __name__ == "__main__":
    app()
