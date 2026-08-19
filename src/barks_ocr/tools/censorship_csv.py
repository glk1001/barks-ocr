"""Derive the volume/image/page columns of the censorship-fixes CSV.

The CSV at ``CSV_DIR / "censorship-fixes-simple.csv"`` is hand-maintained: GLK adds a row
naming a story, a ``comic_page.panel`` reference and the before/after text, and classifies
each row as an error or a censorship fix. Everything else - the Fantagraphics volume, the
scan image stem and the printed book page - is derived here.

The tool is idempotent, so it can be re-run after rows are added. It reads either the
original four-column layout (``Story, Change_From, Change_To, Page_Panel``, with a ``"``
cell meaning "same as the row above") or the nine-column layout it writes, and always
emits the nine-column layout with every value written out in full.
"""

import csv
import io
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import ENUM_TO_STR_TITLE
from barks_fantagraphics.comic_book_info import COVERS_SET
from barks_fantagraphics.comics_consts import PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.pages import get_page_num_str, get_srce_and_dest_pages_in_order
from comic_utils.common_typer_options import LogLevelArg
from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from barks_ocr.cli_setup import init_logging

APP_LOGGING_NAME = "cscsv"

ROOT_DIR = Path.home() / "Books" / "Carl Barks"
CSV_DIR = ROOT_DIR / "Projects" / "Barks Reader"
CSV_FILE = CSV_DIR / "censorship-fixes-simple.csv"

# The printed book page of every CCBDL story, generated from INDUCKS by the barks-wiki
# repo. Nothing in `barks_fantagraphics` records it: the DB knows only scan image stems,
# which lead the printed page by a per-volume offset that also steps mid-volume. Sibling
# repo paths are the established pattern here - see `[tool.uv.sources]` in pyproject.toml
# and the shared word list in cspell.config.yaml.
_SIBLING_REPOS_DIR = Path(__file__).parents[4]
CCBDL_CONTENTS_FILE = (
    _SIBLING_REPOS_DIR / "barks-wiki" / "okf" / "reference" / "data" / "ccbdl-contents.md"
)

# Vol | Pg | Type | Title | Pp | INDUCKS code | DB title (stories) | DB body | delta
CONTENTS_TABLE_COLUMNS = 9

LEGACY_HEADER = ["Story", "Change_From", "Change_To", "Page_Panel"]
HEADER = [
    "Volume",
    "Image",
    "Fanta_page",
    "Comic_page",
    "Panel",
    "Story",
    "Error_type",
    "Change_From",
    "Change_To",
]

DITTO = '"'

# Story names in the CSV that predate the canonical title spellings. The curly
# apostrophe is the CSV's, and has to be matched exactly.
TITLE_ALIASES = {
    "The Mummy’s Ring": "Donald Duck and the Mummy's Ring",  # noqa: RUF001
    "Race to the South Seas": "Race to the South Seas!",
}

# Fantagraphics censored one page out of the ten-page `The Bill Collectors`, so CCBDL
# vol 4 prints nine pages while the DB carries the restored ten. The restored page is
# the story's page 3, spliced in as the out-of-sequence image `227`, and the scan of it
# carries the printed folio "188a". Every page after it is therefore one behind the
# usual `Pg + n - 1`. See ../barks-wiki/okf/source/notes/bill-collectors-ccbdl-censored-page.md
_BILL_COLLECTORS = "The Bill Collectors"
_BILL_COLLECTORS_RESTORED_PAGE = 3
_BILL_COLLECTORS_RESTORED_FOLIO = "188a"

_console = Console()


class CensorshipCsvError(Exception):
    """A row could not be resolved to a volume, image or printed page."""


@dataclass(frozen=True, slots=True)
class ContentsEntry:
    """One `comic story` row of the barks-wiki CCBDL contents table.

    Attributes:
        volume: The Fantagraphics volume number.
        printed_page: The story's first page as printed in the book.
        db_title: The canonical DB title the wiki reconciled the story to.
        db_body: The story's first BODY image stem, as recorded by the DB.

    """

    volume: int
    printed_page: str
    db_title: str
    db_body: str


@dataclass(frozen=True, slots=True)
class StoryLocation:
    """Where a story sits in its Fantagraphics volume.

    Attributes:
        title: The canonical DB title.
        volume: The Fantagraphics volume number.
        images: Comic page number to scan image stem, for BODY pages only.
        printed_page: The story's first printed book page, or None if the story does
            not appear in the printed volume at all.

    """

    title: str
    volume: int
    images: dict[str, str]
    printed_page: int | None


def parse_ccbdl_contents(contents_file: Path) -> dict[str, list[ContentsEntry]]:
    """Read the barks-wiki CCBDL contents table, indexed by canonical DB title.

    Args:
        contents_file: Path to `okf/reference/data/ccbdl-contents.md`.

    Returns:
        Every `comic story` row that names a DB title, grouped by that title.

    Raises:
        CensorshipCsvError: If the file is missing or holds no usable rows.

    """
    if not contents_file.is_file():
        msg = (
            f'CCBDL contents file not found: "{contents_file}".'
            " It lives in the sibling barks-wiki repo; pass --contents-file to override."
        )
        raise CensorshipCsvError(msg)

    entries: dict[str, list[ContentsEntry]] = {}
    for line in contents_file.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != CONTENTS_TABLE_COLUMNS or cells[0] == "Vol" or set(cells[0]) <= set("-:"):
            continue
        volume, printed_page, _type, _title, _pp, _code, db_title, db_body, _delta = cells
        if not db_title or not db_body:
            continue
        entries.setdefault(db_title, []).append(
            ContentsEntry(int(volume), printed_page, db_title, db_body)
        )

    if not entries:
        msg = f'No usable contents rows found in "{contents_file}".'
        raise CensorshipCsvError(msg)

    return entries


def resolve_title(comics_database: ComicsDatabase, story: str, covers: set[str]) -> str:
    """Resolve a CSV story name to its canonical DB title.

    Handles the CSV's padded issue strings ("WDCS  34"), issue strings that match both a
    story and that issue's cover, and the two legacy title spellings.

    Args:
        comics_database: The comics database.
        story: The `Story` cell as written in the CSV.
        covers: Canonical titles that are covers, to be discarded from issue matches.

    Returns:
        The canonical DB title.

    Raises:
        CensorshipCsvError: If the story does not resolve to exactly one title.

    """
    if story in TITLE_ALIASES:
        return TITLE_ALIASES[story]

    issue = re.sub(r"\s+", " ", story).strip()
    found, titles, _closest = comics_database.get_story_title_from_issue(issue)
    if found:
        story_titles = [t for t in titles if t not in covers]
        if len(story_titles) == 1:
            return story_titles[0]
        msg = f'Issue "{story}" matches {len(story_titles)} stories: {story_titles}.'
        raise CensorshipCsvError(msg)

    is_title, closest = comics_database.is_story_title(story)
    if is_title:
        return story

    msg = f'Story "{story}" is not a known title or issue. Closest match: "{closest}".'
    raise CensorshipCsvError(msg)


def _body_images(comics_database: ComicsDatabase, title: str) -> tuple[int, dict[str, str]]:
    """Map a story's comic page numbers to their scan image stems.

    `comics_helpers.get_volume_and_page` is not used here: it derives the stem
    arithmetically as `first_stem + page - 1`, which is wrong wherever a story's BODY
    stems are not contiguous - `The Bill Collectors` maps page 3 to `227` and page 4
    to `195`.
    """
    comic = comics_database.get_comic_book(title)
    srce_and_dest = get_srce_and_dest_pages_in_order(comic, get_full_paths=False)
    images = {
        get_page_num_str(dest): Path(srce.page_filename).stem
        for srce, dest in zip(srce_and_dest.srce_pages, srce_and_dest.dest_pages, strict=True)
        if dest.page_type == PageType.BODY
    }
    return comic.get_fanta_volume(), images


def _printed_page(
    contents: dict[str, list[ContentsEntry]], title: str, volume: int, first_image: str
) -> int | None:
    """Find a story's first printed book page in the CCBDL contents table.

    A story can appear twice - a volume sometimes reprints story pages in its back
    matter - so candidates are narrowed to the run whose DB body start matches the
    story's own first image, and then to the lowest printed page. A story censored out
    of its volume has no row at all.
    """
    candidates = [e for e in contents.get(title, []) if int(e.db_body) == int(first_image)]
    if not candidates:
        logger.info(f'No CCBDL contents row for "{title}" - it has no printed page.')
        return None

    candidates.sort(key=lambda e: int(re.sub(r"\D", "", e.printed_page) or 0))
    chosen = candidates[0]
    for other in candidates[1:]:
        logger.debug(
            f'"{title}": using printed page {chosen.printed_page},'
            f" ignoring reprint at {other.printed_page}."
        )

    if chosen.volume != volume:
        msg = (
            f'"{title}": CCBDL contents says volume {chosen.volume}'
            f" but the comics database says volume {volume}."
        )
        raise CensorshipCsvError(msg)

    return int(re.sub(r"\D", "", chosen.printed_page))


def locate_story(
    comics_database: ComicsDatabase,
    contents: dict[str, list[ContentsEntry]],
    story: str,
    covers: set[str],
) -> StoryLocation:
    """Resolve one CSV story name to its volume, page images and printed start page.

    Args:
        comics_database: The comics database.
        contents: The parsed CCBDL contents table, from `parse_ccbdl_contents`.
        story: The `Story` cell as written in the CSV.
        covers: Canonical titles that are covers.

    Returns:
        The story's location in its Fantagraphics volume.

    Raises:
        CensorshipCsvError: If the story cannot be resolved or has no BODY pages.

    """
    title = resolve_title(comics_database, story, covers)
    volume, images = _body_images(comics_database, title)
    if not images:
        msg = f'No BODY pages found for "{title}".'
        raise CensorshipCsvError(msg)

    first_image = images[min(images, key=int)]
    return StoryLocation(title, volume, images, _printed_page(contents, title, volume, first_image))


def split_page_panel(page_panel: str) -> tuple[str, str]:
    """Split a `Page_Panel` cell into its comic page and panel parts.

    Most cells are `page.panel`, but three other forms appear: `all` for a whole-story
    fix, `3.*` for a whole page, and `6.7.8` for two panels of one page.

    Args:
        page_panel: The `Page_Panel` cell.

    Returns:
        The comic page and the panel, either of which may be empty.

    Raises:
        CensorshipCsvError: If the cell is in none of the known forms.

    """
    cell = page_panel.strip()
    if cell in ("", "all"):
        return "", ""

    parts = cell.split(".")
    if not all(p.isdigit() for p in parts[:1]):
        msg = f'Unrecognised Page_Panel value: "{page_panel}".'
        raise CensorshipCsvError(msg)

    page = parts[0]
    panels = parts[1:]
    if panels == ["*"]:
        return page, ""
    if all(p.isdigit() for p in panels):
        return page, ",".join(panels)

    msg = f'Unrecognised Page_Panel value: "{page_panel}".'
    raise CensorshipCsvError(msg)


def fanta_page_for(location: StoryLocation, comic_page: str) -> str:
    """Return the printed book page for one comic page of a story.

    Args:
        location: The story's location, from `locate_story`.
        comic_page: The comic page number within the story, or "" for a whole-story row.

    Returns:
        The printed page as a string, or "" where the page has none - a whole-story row,
        or a story censored out of its printed volume.

    """
    if not comic_page or location.printed_page is None:
        return ""

    page = int(comic_page)
    if location.title != _BILL_COLLECTORS:
        return str(location.printed_page + page - 1)

    if page == _BILL_COLLECTORS_RESTORED_PAGE:
        return _BILL_COLLECTORS_RESTORED_FOLIO
    if page < _BILL_COLLECTORS_RESTORED_PAGE:
        return str(location.printed_page + page - 1)
    return str(location.printed_page + page - 2)


def expand_dittos(rows: list[list[str]]) -> list[list[str]]:
    """Replace every ditto cell with the value it stands in for.

    Args:
        rows: The CSV data rows, a ditto cell being a lone double-quote.

    Returns:
        The same rows with every ditto resolved against the rows above it.

    """
    expanded: list[list[str]] = []
    previous: list[str] = []
    for row in rows:
        filled = [
            prev if cell == DITTO else cell for cell, prev in zip(row, previous or row, strict=True)
        ]
        expanded.append(filled)
        previous = filled

    return expanded


@dataclass(frozen=True, slots=True)
class FixRecord:
    """One censorship-fix row, independent of which CSV layout it was read from.

    Attributes:
        story: The `Story` cell, kept verbatim.
        comic_page: The comic page within the story, or "".
        panel: The panel within that page, or "".
        error_type: GLK's classification, or "" if not yet filled in.
        change_from: The text or artwork as Fantagraphics printed it.
        change_to: The text or artwork as restored.

    """

    story: str
    comic_page: str
    panel: str
    error_type: str
    change_from: str
    change_to: str


def read_fix_records(file: Path) -> list[FixRecord]:
    """Read the censorship-fixes CSV in either of its layouts.

    Args:
        file: The CSV file.

    Returns:
        One record per data row, with dittos expanded and `Page_Panel` split.

    Raises:
        CensorshipCsvError: If the header is neither layout, or a cell is unparsable.

    """
    with file.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        rows = expand_dittos([row for row in reader if row])

    if header == LEGACY_HEADER:
        return [
            FixRecord(story, *split_page_panel(page_panel), "", change_from, change_to)
            for story, change_from, change_to, page_panel in rows
        ]

    if header == HEADER:
        return [
            FixRecord(
                row[HEADER.index("Story")],
                row[HEADER.index("Comic_page")],
                row[HEADER.index("Panel")],
                row[HEADER.index("Error_type")],
                row[HEADER.index("Change_From")],
                row[HEADER.index("Change_To")],
            )
            for row in rows
        ]

    msg = f'Unrecognised CSV header in "{file}": {header}.'
    raise CensorshipCsvError(msg)


def build_rows(records: list[FixRecord], locations: dict[str, StoryLocation]) -> list[list[str]]:
    """Turn fix records into the nine-column output rows.

    Args:
        records: The rows read from the CSV.
        locations: Story name to resolved location, from `locate_story`.

    Returns:
        One output row per record, in `HEADER` order, sorted by `row_sort_key`.

    Raises:
        CensorshipCsvError: If a record names a comic page the story does not have.

    """
    rows = []
    for record in records:
        location = locations[record.story]
        image = ""
        if record.comic_page:
            image = location.images.get(record.comic_page, "")
            if not image:
                msg = f'"{record.story}" ({location.title}) has no comic page {record.comic_page}.'
                raise CensorshipCsvError(msg)

        rows.append(
            [
                str(location.volume),
                image,
                fanta_page_for(location, record.comic_page),
                record.comic_page,
                record.panel,
                record.story,
                record.error_type,
                record.change_from,
                record.change_to,
            ]
        )

    return sorted(rows, key=row_sort_key)


def row_sort_key(row: list[str]) -> tuple:
    """Order one output row by where its fix sits in the printed books.

    Volume first, then the printed page, so stories come out in book order and a page's
    panels in reading order. `Fanta_page` is the right key rather than `Image`: a
    restored page can be spliced in out of sequence (`The Bill Collectors` page 3 is
    image 227, folio "188a"), and the folio sorts into place where the image stem would
    not. A row with no printed page at all - a story censored out of its volume - leads
    its volume, since it stands for the whole story rather than a page of it.

    Args:
        row: One output row, in `HEADER` order.

    Returns:
        A sort key.

    """

    def cell(name: str) -> str:
        return row[HEADER.index(name)]

    fanta_page = cell("Fanta_page")
    folio = re.fullmatch(r"(\d+)([a-z]*)", fanta_page)
    page_key = (int(folio[1]), folio[2]) if folio else (0, "")

    return (
        int(cell("Volume")),
        bool(fanta_page),
        page_key,
        int(cell("Comic_page") or 0),
        tuple(int(p) for p in cell("Panel").split(",") if p),
    )


def render_csv(rows: list[list[str]]) -> str:
    """Render the nine-column CSV, quoting every field as the original does.

    Args:
        rows: The data rows, in `HEADER` order.

    Returns:
        The complete file content.

    """
    out = io.StringIO(newline="")
    # The file this replaces is LF-terminated; csv.writer defaults to CRLF.
    writer = csv.writer(out, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return out.getvalue()


def print_story_summary(records: list[FixRecord], locations: dict[str, StoryLocation]) -> None:
    """Print how every distinct story in the CSV was resolved.

    Args:
        records: The rows read from the CSV.
        locations: Story name to resolved location, from `locate_story`.

    """
    counts: dict[str, int] = {}
    for record in records:
        counts[record.story] = counts.get(record.story, 0) + 1

    table = Table(
        title="Censorship CSV story resolution",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold magenta",
    )
    table.add_column("Story")
    table.add_column("Rows", justify="right")
    table.add_column("DB title")
    table.add_column("Vol", justify="right")
    table.add_column("Images")
    table.add_column("Printed pg", justify="right")

    for story, count in counts.items():
        location = locations[story]
        stems = sorted(location.images.values(), key=int)
        printed = "-" if location.printed_page is None else str(location.printed_page)
        table.add_row(
            story,
            str(count),
            location.title if location.title != story else "",
            str(location.volume),
            f"{stems[0]}-{stems[-1]}",
            printed,
        )

    _console.print()
    _console.print(table)


app = typer.Typer()


@app.command(help="Derive the volume/image/page columns of the censorship-fixes CSV")
def main(
    csv_file: Annotated[
        Path, typer.Option("--csv-file", help="The censorship fixes CSV to rewrite.")
    ] = CSV_FILE,
    contents_file: Annotated[
        Path,
        typer.Option("--contents-file", help="The barks-wiki CCBDL contents markdown table."),
    ] = CCBDL_CONTENTS_FILE,
    check: Annotated[
        bool, typer.Option("--check", help="Resolve and report only; write nothing.")
    ] = False,
    log_level_str: LogLevelArg = "ERROR",
) -> None:
    """Rewrite the censorship-fixes CSV with its derived columns filled in."""
    init_logging(APP_LOGGING_NAME, "censorship-csv.log", log_level_str)

    contents = parse_ccbdl_contents(contents_file)
    comics_database = ComicsDatabase(for_building_comics=False)
    covers = {ENUM_TO_STR_TITLE[t] for t in COVERS_SET}

    records = read_fix_records(csv_file)
    locations = {
        record.story: locate_story(comics_database, contents, record.story, covers)
        for record in records
    }
    rows = build_rows(records, locations)

    print_story_summary(records, locations)

    if check:
        _console.print(f"[dim]--check: {len(rows)} rows resolved, nothing written.[/]")
        return

    content = render_csv(rows)
    if content == csv_file.read_text(encoding="utf-8", newline=""):
        # Nothing derived has changed, so leave the backup alone - re-running the tool
        # must never overwrite a backup that still holds real earlier content.
        _console.print(f"[dim]{csv_file} is already up to date - nothing written.[/]")
        return

    backup_file = csv_file.with_suffix(csv_file.suffix + ".bak")
    shutil.copy2(csv_file, backup_file)
    csv_file.write_text(content, encoding="utf-8", newline="")
    _console.print(f"[dim]Backed up to[/] [cyan]{backup_file}[/]")
    _console.print(f"[dim]Wrote {len(rows)} rows to[/] [cyan]{csv_file}[/]")


if __name__ == "__main__":
    app()
