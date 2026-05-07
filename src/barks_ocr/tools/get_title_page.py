# ruff: noqa: T201

import typer
from barks_fantagraphics.comics_consts import PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_comic_titles
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg

from barks_ocr.cli_setup import init_logging

APP_LOGGING_NAME = "gttl"


def get_title_pages(
    comics_database: ComicsDatabase, titles: list[str]
) -> list[tuple[int, str, str]]:
    vol_page_list: list[tuple[int, str, str]] = []

    for title in titles:
        comic = comics_database.get_comic_book(title)
        valid_page_list = [
            p.page_filenames for p in comic.page_images_in_order if p.page_type == PageType.BODY
        ]

        volume = comic.get_fanta_volume()
        first_page = valid_page_list[0]

        vol_page_list.append((volume, first_page, title))

    return vol_page_list


app = typer.Typer()


@app.command(help="Get title pages for Fanta volume")
def main(
    volumes_str: VolumesArg,
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "ERROR",
) -> None:
    init_logging(APP_LOGGING_NAME, "get-title-pages.log", log_level_str)

    comics_database, title_list = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)

    title_pages = get_title_pages(comics_database, title_list)

    for title_page in title_pages:
        print(f'{title_page[0]} {title_page[1]} easyocr 0 title_page "{title_page[2]}"')


if __name__ == "__main__":
    app()
