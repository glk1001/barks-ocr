from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import ENUM_FROM_BARKS_TITLE
from barks_fantagraphics.comics_consts import PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_comic_titles
from barks_fantagraphics.speech_groupers import OcrTypes, get_speech_page_group
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from barks_ocr.cli_setup import init_logging

APP_LOGGING_NAME = "gttl"

TICK = "✓"
CROSS = "✗"

_console = Console()


def _queue_line(volume: int, fanta_page: str, title: str) -> str:
    return f'{volume} {fanta_page} easyocr 0 title_page "{title}"'


def get_title_pages(
    comics_database: ComicsDatabase, titles: list[str]
) -> list[tuple[int, str, str, PageType]]:
    vol_page_list: list[tuple[int, str, str, PageType]] = []

    for title in titles:
        comic = comics_database.get_comic_book(title)
        volume = comic.get_fanta_volume()

        front_matter = [
            p for p in comic.page_images_in_order if p.page_type == PageType.FRONT_MATTER
        ]
        body_pages = [p for p in comic.page_images_in_order if p.page_type == PageType.BODY]
        back_matter = [p for p in comic.page_images_in_order if p.page_type == PageType.BACK_MATTER]

        if not body_pages:
            msg = f'No BODY page found for "{title}".'
            raise ValueError(msg)

        vol_page_list.extend((volume, p.page_filenames, title, p.page_type) for p in front_matter)
        first_body = body_pages[0]
        vol_page_list.append((volume, first_body.page_filenames, title, first_body.page_type))
        vol_page_list.extend((volume, p.page_filenames, title, p.page_type) for p in back_matter)

    return vol_page_list


def write_queue(
    title_pages: list[tuple[int, str, str, PageType]],
    queue_file: Path | None,
) -> None:
    if queue_file is None:
        return

    lines = [_queue_line(vol, page, title) for vol, page, title, _ in title_pages]

    queue_file.write_text("\n".join(lines) + "\n")
    _console.print(f"[dim]Wrote {len(lines)} queue entries to[/] [cyan]{queue_file}[/]")


def print_title_summary(
    comics_database: ComicsDatabase,
    title_pages: list[tuple[int, str, str, PageType]],
    keep_newlines: bool = False,
) -> None:
    table = Table(
        title="Title Page Summary",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Vol", justify="right", style="bold")
    table.add_column("Page", justify="right")
    table.add_column("Type")
    table.add_column("", justify="center", width=3)
    table.add_column("Title")
    table.add_column("Title bubbles")

    for volume, fanta_page, title_str, page_type in title_pages:
        comic = comics_database.get_comic_book(title_str)
        is_barks = comic.is_barks_title()

        title_enum = ENUM_FROM_BARKS_TITLE[title_str]
        try:
            page_group = get_speech_page_group(
                comics_database,
                volume,
                title_enum,
                OcrTypes.EASYOCR,
                fanta_page,
                fanta_page,
            )
            title_bubbles = [st for st in page_group.speech_groups.values() if st.type == "title"]
            ocr_loaded = True
        except (OSError, ValueError) as e:
            title_bubbles = []
            ocr_loaded = False
            ocr_error = str(e)

        if is_barks and page_type == PageType.BODY:
            needle = " ".join(title_str.split()).lower()
            matched = any(
                needle in " ".join(bubble.ai_text.split()).lower() for bubble in title_bubbles
            )
            marker = Text(TICK, style="bold green") if matched else Text(CROSS, style="bold red")
            title_cell = Text(title_str, style="white")
        elif is_barks:
            marker = Text("")
            title_cell = Text(title_str, style="white")
        else:
            marker = Text("")
            title_cell = Text(f"({title_str})", style="dim italic")

        if not ocr_loaded:
            bubbles_cell: Text = Text(f"(no OCR data: {ocr_error})", style="dim red")
        elif not title_bubbles:
            bubbles_cell = Text("(no `title` bubbles found)", style="dim yellow")
        elif keep_newlines:
            bubbles_cell = Text("\n".join(b.ai_text for b in title_bubbles))
        else:
            bubbles_cell = Text("\n".join(" ".join(b.ai_text.split()) for b in title_bubbles))

        type_cell = Text(
            page_type.name,
            style="green" if page_type == PageType.BODY else "yellow",
        )
        table.add_row(str(volume), fanta_page, type_cell, marker, title_cell, bubbles_cell)

    _console.print()
    _console.print(table)


app = typer.Typer()


@app.command(help="Get title pages for Fanta volume")
def main(
    volumes_str: VolumesArg,
    title_str: TitleArg = "",
    queue_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--queue-file",
        "-q",
        help="If given, write queue lines to this file instead of stdout.",
    ),
    keep_newlines: bool = typer.Option(
        default=False,
        help="Keep newlines in title bubble text (default: collapse to spaces).",
    ),
    log_level_str: LogLevelArg = "ERROR",
) -> None:
    init_logging(APP_LOGGING_NAME, "get-title-pages.log", log_level_str)

    comics_database, title_list = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)

    title_pages = get_title_pages(comics_database, title_list)

    write_queue(title_pages, queue_file)

    print_title_summary(comics_database, title_pages, keep_newlines=keep_newlines)


if __name__ == "__main__":
    app()
