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

from typing import Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page, get_titles
from barks_fantagraphics.fanta_comics_info import FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
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
