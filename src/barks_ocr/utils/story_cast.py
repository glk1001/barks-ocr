"""The cast the database already knows a story contains.

The speaker roster in :mod:`barks_ocr.utils.vision_schema` is the main cast and
nothing else -- Donald, the nephews, Scrooge and a handful more.  That is
deliberate, but it leaves the long tail (Bolivar, Magica, Soapy Slick, Argus
McFiendy) with nowhere to go except free text behind ``other:``, where spellings
drift and nothing downstream reconciles them.

The database has already answered this.  Its character tags say which named
supporting and one-off characters appear in which story, so the vision pass need
never identify one from scratch: it is handed a short list and asked which of
them are on the page.  That is a closed-set question rather than an open one,
and a name outside the set becomes an error signal instead of silent drift.

Note what the tags do *not* include: Donald, the nephews and Scrooge are in
nearly every story, so tagging them would be noise.  The tags are the tail, and
the roster is the head; the closed set is the union.
"""

from barks_fantagraphics.barks_tags import (
    BARKS_TAG_CATEGORIES,
    BARKS_TAGGED_TITLES,
    TagCategories,
    TagGroups,
    Tags,
    get_all_tags_in_tag_group,
)
from barks_fantagraphics.barks_titles import Titles

from barks_ocr.utils.vision_schema import DB_CHARACTER_ALIASES, ROSTER

# The tag groups that name people. `PIG_VILLAINS` belongs here as much as the
# other three -- Soapy Slick and Porkman de Lardo are characters, and leaving
# the group out would silently drop six named villains from every closed set.
CHARACTER_TAG_GROUPS: tuple[TagGroups, ...] = (
    TagGroups.PRIMARY_CHARACTERS,
    TagGroups.SECONDARY_CHARACTERS,
    TagGroups.ONE_OFF_CHARACTERS,
    TagGroups.PIG_VILLAINS,
)


def _character_tags() -> set[Tags]:
    """Return every tag in the character groups.

    ``get_all_tags_in_tag_group`` rather than the raw dict: a group's entries
    may be nested groups rather than tags, and flattening that is the database's
    job, not ours.
    """
    return {tag for group in CHARACTER_TAG_GROUPS for tag in get_all_tags_in_tag_group(group)}


def _canonical(tag: Tags) -> str:
    """Return the name to use for a character tag, aliases resolved."""
    return DB_CHARACTER_ALIASES.get(tag.value, tag.value)


def all_character_tags() -> list[str]:
    """Return every character name the database tags, canonicalized.

    Returns:
        The tag names, aliases resolved, sorted and de-duplicated.

    """
    return sorted({_canonical(tag) for tag in _character_tags()})


def story_characters(title: Titles) -> list[str]:
    """Return the named characters the database tags as appearing in *title*.

    Roster names are excluded: they are always available, so repeating them
    would only pad the list the vision pass has to read.

    Args:
        title: The story to look up.

    Returns:
        The extra names for this story, sorted. Empty when the story has no
        character tags, which is common and not an error.

    """
    tagged = {
        _canonical(tag) for tag in _character_tags() if title in BARKS_TAGGED_TITLES.get(tag, [])
    }
    return sorted(tagged - ROSTER)


def story_things(title: Titles) -> list[str]:
    """Return the notable things the database tags as appearing in *title*.

    Not a vocabulary for the ``objects`` field -- there cannot be one, since a
    fly swatter and a legless chair are not enumerable in advance. These are
    *naming anchors* for the handful of props the database considers notable
    (``313``, ``square eggs``, ``HDL driving car``), so that a recurring object
    is written the same way every time instead of arriving as "a car", "the red
    car" and "313" in three different stories.

    The category is narrow and idiosyncratic -- most of it is the chemical names
    from the Gyro stories -- so an empty result is the common case.

    Args:
        title: The story to look up.

    Returns:
        The tagged thing names for this story, sorted.

    """
    tags: set[Tags] = set()
    for entry in BARKS_TAG_CATEGORIES.get(TagCategories.THINGS, []):
        # A category holds groups, but the same nesting the character groups use
        # means an entry can already be a tag. Mirrors the database's own guard.
        if isinstance(entry, TagGroups):
            tags |= get_all_tags_in_tag_group(entry)
        else:
            tags.add(entry)
    return sorted(tag.value for tag in tags if title in BARKS_TAGGED_TITLES.get(tag, []))
