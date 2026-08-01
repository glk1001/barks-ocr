"""Resolving ``--volume`` / ``--title`` into a list of story titles.

Shared by the read-only corpus tools.  They all want the same thing — a title
list, defaulting to the whole corpus when neither option is given — and
``get_titles`` cannot supply that on its own: it asserts on an empty volume
list, so "everything" has to be spelled out as an explicit range rather than
left implicit.
"""

from typing import Any

import typer
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.fanta_comics_info import FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER
from intspan import intspan


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
