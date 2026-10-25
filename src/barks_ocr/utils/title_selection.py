"""Selecting the titles a run covers, and the pages a title really owns.

Shared by the read-only corpus tools.  They all want the same thing — a title
list, defaulting to the whole corpus when neither option is given — and
``get_titles`` cannot supply that on its own: it asserts on an empty volume
list, so "everything" has to be spelled out as an explicit range rather than
left implicit.

``title_pages`` is here for a sharper reason.  Two database accessors disagree
about which pages a story owns, and walking the page map alone reaches past the
story into the ones around it — *Sheriff of Bullet Valley* comes back with 103,
176 and 177 on top of its real 144-175.  Every tool that walks the map hits
this, so the filter belongs in one place rather than in whichever tool noticed
it first.
"""

from pathlib import Path
from typing import Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comic_book_info import (
    ONE_PAGERS,
    get_one_pager_fanta_vol_and_page,
    get_one_pager_file,
)
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page, get_titles
from barks_fantagraphics.fanta_comics_info import FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER
from barks_fantagraphics.ocr_file_paths import get_ocr_prelim_groups_json_filename
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from comic_utils.comic_consts import SVG_FILE_EXT
from intspan import intspan
from loguru import logger


def resolve_titles(comics_database: ComicsDatabase, volumes_str: str, title_str: str) -> list[str]:
    """Return the titles selected by ``--volume`` / ``--title``.

    An unqualified run means the whole corpus, which is the useful default for a
    census or an export.

    Args:
        comics_database: The database to look titles up in.
        volumes_str: The ``--volume`` value, e.g. ``"1-3"``. Empty if unset.
        title_str: The ``--title`` value. Empty if unset.

    Returns:
        The canonical title strings, comics only.

    Raises:
        typer.BadParameter: If both options are given.

    """
    if volumes_str and title_str:
        msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(msg)

    if volumes_str:
        volumes: list[Any] = list(intspan(volumes_str))
    elif title_str:
        volumes = []
    else:
        volumes = list(range(FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER + 1))

    return get_titles(comics_database, volumes, title_str, exclude_non_comics=True)


def title_pages(
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    title_str: str,
    engine: OcrTypes,
    *,
    warn: bool = True,
) -> list[str]:
    """Return every page of one title that has OCR for this engine.

    Two database accessors disagree here and the difference matters, so both are
    consulted rather than one trusted.  ``get_speech_page_groups`` walks the
    comic's page map, which can reach past the story into the ones around it --
    "Sheriff of Bullet Valley" comes back with 103, 176 and 177 alongside its
    real 144-175, and those three pages belong to *Sorry to be Safe*, *Best Laid
    Plans* and *The Genuine Article*.

    Taking them would mean cropping another story's art into this story's
    directory, or reporting another story's names as this one's, so a page is
    kept only when ``get_title_from_volume_page`` agrees it belongs here.

    Args:
        comics_database: The database to resolve page ownership against.
        speech_groups: The speech-group reader to walk.
        title_str: The story whose pages are wanted.
        engine: Which OCR engine's pages to return.
        warn: Whether to log the pages dropped as belonging elsewhere.

    Returns:
        The fanta page strings this title really owns, sorted.

    """
    title = STR_TITLE_TO_ENUM[title_str]
    volume = comics_database.get_fanta_volume_int(title_str)
    claimed = sorted(
        {
            page_group.fanta_page
            for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True)
            if page_group.ocr_index == engine
        }
    )

    pages, foreign = [], []
    for fanta_page in claimed:
        try:
            owner, _ = get_title_from_volume_page(comics_database, volume, fanta_page)
        except Exception:  # noqa: BLE001 -- unresolvable means "not this story".
            owner = None
        if owner == title_str:
            pages.append(fanta_page)
        else:
            foreign.append((fanta_page, owner))

    if foreign and warn:
        listed = ", ".join(f"{p} ({o or 'unresolvable'})" for p, o in foreign)
        logger.warning(
            f'Dropped {len(foreign)} page(s) the page map claims for "{title_str}"'
            f" but which belong elsewhere: {listed}."
        )
    return pages


def _one_pager_location(title_str: str) -> tuple[int, str] | None:
    """Return a one-pager's host volume and page, or None for any other title.

    One-pagers have no ``.ini``, so ``get_comic_book`` cannot resolve them; their
    page lives in the host volume under its own number, which ``ONE_PAGER_LOCATIONS``
    holds.  An unlocated one-pager raises rather than falling through to
    ``get_comic_book`` and its less helpful error.
    """
    title = STR_TITLE_TO_ENUM[title_str]
    if title not in ONE_PAGERS:
        return None
    volume, page = get_one_pager_fanta_vol_and_page(title)
    if volume is None or page is None:
        msg = f'One-pager "{title_str}" has no location in ONE_PAGER_LOCATIONS.'
        raise typer.BadParameter(msg)
    return volume, get_page_str(page)


def restored_svg_and_raw_ocr_files(
    comics_database: ComicsDatabase, title_str: str
) -> list[tuple[Path, tuple[Path, Path]]]:
    """Return each restorable page's svg file and its (easyocr, paddleocr) raw OCR files.

    A one-pager's raw OCR files sit where a story's would, ``NNN.<engine>.json`` in its
    home volume's raw OCR directory. Its svg is wherever ``get_one_pager_file`` finds
    it: a one-pager that belongs to no story has its svg only in "All One-Pagers",
    under the collection page number - so take a page's number from its raw OCR files,
    never from the svg's name.

    Args:
        comics_database: The database to resolve the title against.
        title_str: The story or located one-pager.

    Returns:
        One (svg file, raw OCR pair) per page, in page order.

    """
    located = _one_pager_location(title_str)
    if located is None:
        comic = comics_database.get_comic_book(title_str)
        return list(
            zip(
                comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES),
                comic.get_srce_restored_ocr_raw_story_files(RESTORABLE_PAGE_TYPES),
                strict=True,
            )
        )
    volume, page = located
    svg_file = get_one_pager_file(
        STR_TITLE_TO_ENUM[title_str],
        comics_database.get_fantagraphics_restored_svg_volume_image_dir,
        SVG_FILE_EXT,
    )
    raw_dir = comics_database.get_fantagraphics_restored_ocr_raw_volume_dir(volume)
    raw_pair = (raw_dir / f"{page}.easyocr.json", raw_dir / f"{page}.paddleocr.json")
    return [(svg_file, raw_pair)]


def prelim_groups_file(
    comics_database: ComicsDatabase, title_str: str, page: str, engine: str
) -> Path:
    """Return the prelim groups JSON file of one page and engine, one-pagers included.

    Args:
        comics_database: The database to resolve the title against.
        title_str: The story or located one-pager.
        page: The fanta page, e.g. ``"030"``.
        engine: The OCR engine's name, e.g. ``"easyocr"``.

    Returns:
        The file's path, whether or not it exists.

    """
    located = _one_pager_location(title_str)
    if located is None:
        return comics_database.get_comic_book(title_str).get_ocr_prelim_groups_json_file(
            page, engine
        )
    volume = located[0]
    prelim_dir = comics_database.get_fantagraphics_restored_ocr_prelim_volume_dir(volume)
    return Path(prelim_dir) / get_ocr_prelim_groups_json_filename(page, engine)
