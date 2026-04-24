#!/usr/bin/env python3
"""Spellcheck LlamaParse JSON text fields via ``cspell`` and report findings.

For each spread JSON in the supplied parse directories this script extracts every
text-bearing field (``value`` on text-type items, ``caption`` on image-type
items), feeds them to ``cspell`` (run via ``bunx``), and writes a JSON report of
unknown words with exact locations (parse dir, spread stem, item index, field).

The cspell run uses the project's ``cspell-words.txt`` dictionary so character
names and project-specific words already in that file won't be flagged.
"""

import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import typer
from loader import SpreadRecord, iter_spreads
from loguru import logger

app = typer.Typer(add_completion=False)

_REPO_ROOT = Path(__file__).parent.parent.parent
_PROJECT_WORDS = _REPO_ROOT / "cspell-words.txt"
_BARKS_BOOKS_WORDS = Path(__file__).parent.parent / "cspell-words-barks-books.txt"

_CSPELL_LINE_RE = re.compile(
    r":(?P<line>\d+):(?P<col>\d+)\s+-\s+Unknown word \((?P<word>[^)]+)\)"
    r"(?:\s+fix:\s+\((?P<fix>[^)]+)\))?\s*$"
)

_TEXT_FIELDS = (("text", "value"), ("image", "caption"))


@dataclass(frozen=True)
class _ItemMeta:
    parse_dir: str
    spread_stem: str
    item_index: int
    field: str
    content: str


@dataclass(frozen=True)
class _Finding:
    parse_dir: str
    spread_stem: str
    item_index: int
    field: str
    word: str
    fix: str | None
    context: str


def _collect_items(spreads: list[SpreadRecord]) -> list[_ItemMeta]:
    """Return one ``_ItemMeta`` per spellcheckable text field, in reading order.

    Args:
        spreads: Spread records from ``iter_spreads``.

    Returns:
        Flat list of items; each becomes one line in the cspell input.

    """
    metas: list[_ItemMeta] = []
    for rec in spreads:
        for idx, item in enumerate(rec.items):
            for wanted_type, wanted_field in _TEXT_FIELDS:
                if item.get("type") != wanted_type:
                    continue
                content = item.get(wanted_field)
                if not isinstance(content, str) or not content.strip():
                    continue
                metas.append(
                    _ItemMeta(
                        parse_dir=str(rec.parse_dir),
                        spread_stem=rec.spread_stem,
                        item_index=idx,
                        field=wanted_field,
                        content=content,
                    )
                )
    return metas


def _write_cspell_input(metas: list[_ItemMeta], path: Path) -> None:
    """Write one meta per line to ``path`` with newlines/tabs squashed to spaces.

    cspell reports 1-based line numbers; line N corresponds to ``metas[N-1]``.
    """
    with path.open("w", encoding="utf-8") as f:
        for meta in metas:
            one_line = re.sub(r"\s+", " ", meta.content).strip()
            f.write(one_line + "\n")


def _write_cspell_config(config_path: Path) -> None:
    """Write a minimal cspell config that uses the project word list.

    Args:
        config_path: Destination for the generated JSON config.

    """
    config = {
        "version": "0.2",
        "language": "en",
        "dictionaryDefinitions": [
            {
                "name": "project",
                "path": str(_PROJECT_WORDS),
                "addWords": True,
            },
            {
                "name": "barks-books",
                "path": str(_BARKS_BOOKS_WORDS),
                "addWords": True,
            },
        ],
        "dictionaries": ["en_us", "project", "barks-books"],
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _run_cspell(input_path: Path, config_path: Path) -> list[tuple[int, int, str, str | None]]:
    """Invoke ``bunx cspell lint`` and parse its findings.

    Args:
        input_path: Temp file containing one item-per-line.
        config_path: Temp cspell config JSON.

    Returns:
        ``(line, col, word, fix)`` for each Unknown-word line.

    """
    bunx = shutil.which("bunx")
    if bunx is None:
        msg = "bunx (bun) not found on PATH; cannot run cspell"
        raise RuntimeError(msg)
    cmd = [
        bunx,
        "cspell",
        "lint",
        "--no-color",
        "--no-summary",
        "--no-progress",
        "--no-config-search",
        "--config",
        str(config_path),
        f"file://{input_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.stderr and (result.stderr.strip() != ""):
        msg = f'cspell stderr: "{result.stderr.strip()}"'
        raise RuntimeError(msg)
    findings: list[tuple[int, int, str, str | None]] = []
    for line in result.stdout.splitlines():
        match = _CSPELL_LINE_RE.search(line)
        if match is None:
            continue
        findings.append(
            (
                int(match.group("line")),
                int(match.group("col")),
                match.group("word"),
                match.group("fix"),
            )
        )
    if not findings and result.returncode != 0 and result.stderr:
        logger.warning(f"cspell stderr: {result.stderr.strip()}")
    return findings


def _context_for(content: str, col: int, word: str, *, pad: int = 40) -> str:
    """Extract ``pad`` characters around the unknown word in its original text.

    The column from cspell refers to the squashed single-line input, so we prefer
    to locate the word in the original ``content`` by substring match to preserve
    any original newlines in the displayed context. Falls back to col-based
    slicing of a squashed copy.
    """
    idx = content.find(word)
    if idx == -1:
        squashed = re.sub(r"\s+", " ", content).strip()
        start = max(0, col - 1 - pad)
        end = min(len(squashed), col - 1 + len(word) + pad)
        return squashed[start:end]
    start = max(0, idx - pad)
    end = min(len(content), idx + len(word) + pad)
    snippet = content[start:end]
    return re.sub(r"\s+", " ", snippet).strip()


def _build_findings(
    metas: list[_ItemMeta], raw: list[tuple[int, int, str, str | None]]
) -> list[_Finding]:
    findings: list[_Finding] = []
    for line, col, word, fix in raw:
        if not 1 <= line <= len(metas):
            logger.warning(f"cspell reported line {line} outside expected range; skipping")
            continue
        meta = metas[line - 1]
        findings.append(
            _Finding(
                parse_dir=meta.parse_dir,
                spread_stem=meta.spread_stem,
                item_index=meta.item_index,
                field=meta.field,
                word=word,
                fix=fix,
                context=_context_for(meta.content, col, word),
            )
        )
    return findings


def _print_summary(findings: list[_Finding]) -> None:
    if not findings:
        logger.info("No unknown words found.")
        return
    by_word: Counter[str] = Counter(f.word for f in findings)
    logger.info(f"Found {len(findings)} unknown-word occurrence(s); {len(by_word)} unique word(s).")
    logger.info("Top unknown words:")
    for word, count in by_word.most_common(25):
        logger.info(f"  {count:>4}  {word}")


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
        help="Where to write the JSON report (default: <parse-dirs>/spellcheck-report.json).",
    ),
) -> None:
    """Spellcheck JSON text fields across one or more parse directories."""
    if not parse_dirs.is_dir():
        logger.error(f"Not a directory: {parse_dirs}")
        raise typer.Exit(1)
    parse_dir_list = sorted(d for d in parse_dirs.iterdir() if d.is_dir())
    if not parse_dir_list:
        logger.error(f"No parse subdirectories found under: {parse_dirs}")
        raise typer.Exit(1)

    if not _PROJECT_WORDS.is_file():
        logger.error(f"Expected project dictionary not found: {_PROJECT_WORDS}")
        raise typer.Exit(1)

    logger.info(f"Loading spreads from {len(parse_dir_list)} parse dir(s) ...")
    spreads = list(iter_spreads(parse_dir_list))
    logger.info(f"Loaded {len(spreads)} spread(s).")

    metas = _collect_items(spreads)
    logger.info(f"Collected {len(metas)} spellcheckable field(s).")
    if not metas:
        logger.warning("Nothing to spellcheck.")
        raise typer.Exit(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / "spellcheck-input.txt"
        #        input_path = Path("/tmp") / "spellcheck-input.txt"
        config_path = tmp / "cspell.config.json"
        _write_cspell_input(metas, input_path)
        _write_cspell_config(config_path)
        raw = _run_cspell(input_path, config_path)

    findings = _build_findings(metas, raw)
    _print_summary(findings)

    resolved_report = (
        report_file if report_file is not None else parse_dirs / "spellcheck-report.json"
    )
    by_word_counts: Counter[str] = Counter(f.word for f in findings)
    report = {
        "num_parse_dirs": len(parse_dir_list),
        "num_spreads": len(spreads),
        "num_items_checked": len(metas),
        "num_findings": len(findings),
        "by_word": dict(by_word_counts.most_common()),
        "findings": [asdict(f) for f in findings],
    }
    resolved_report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Wrote report to {resolved_report}")


if __name__ == "__main__":
    app()
