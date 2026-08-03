# ruff: noqa: T201
"""Surface the proper nouns in a story's OCR before the vision pass reads page 1.

*Sheriff of Bullet Valley* established the discipline: grep the whole title's
groups before reading any of it, so a character who is drawn from page 147 but
not named until page 150 is never recorded under a provisional name and renamed
later.  That is Roscoe's ``other:the thug`` / ``other:the workman`` failure, where
one character became two, and it costs one command to remove.

**Two passes, because they fail in opposite ways and neither alone is enough.**

1. *Non-dictionary tokens.*  Every token that is not an ordinary English word,
   printed in full rather than as a frequency head and tail.  The two-ends form
   is what lost ``YEHOOTY`` on *Plenty of Pets* -- three occurrences, too rare
   for the head and too common for the tail.  A dictionary stop list has no
   frequency cutoff to fall through, and the surviving list is small enough to
   read whole: ten pages of *The Big Bin on Killmotor Hill* leave 17 tokens.

2. *Repeated word pairs.*  A name spelled out of ordinary words is invisible to
   pass 1, and that is not a corner case -- Big Bin's antagonists are the
   **Beagle Boys**, and ``BEAGLE`` and ``BOYS`` are both in the dictionary, so
   pass 1 returned nothing at all for the story's whole villain cast.  Casing
   cannot rescue it either, because the lettering is stored in caps throughout.
   Adjacent pairs seen more than once do, and they cost nothing extra.

Pass 2 also earns its place a second way: it surfaces **the comic's own wording**
for things the story names, which is what the capture is supposed to reuse.  Big
Bin's ``FLY PAPER`` and ``PERISCOPE PEEPHOLE`` both came out of it.

What neither pass can buy is *what a name refers to*.  ``JASMINE JOE`` showed up
on *Plenty of Pets* without saying it was the skunk, which only page 204 settled.
The grep buys the spelling, not the identification.

Read-only.
"""

import re
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup
from comic_utils.common_typer_options import TitleArg, VolumesArg

from barks_ocr.utils.title_selection import resolve_titles, title_pages

app = typer.Typer()

# Both spellings, so neither a British nor an American form survives as a "name".
DICTIONARY_FILES = (
    Path("/usr/share/dict/american-english"),
    Path("/usr/share/dict/british-english"),
    Path("/usr/share/dict/words"),
)

# A pair seen twice is worth printing: a story's own name for a thing can be
# rare. "Killmotor Hill" is said twice in ten pages.
DEFAULT_MIN_PAIR = 2

# The dictionary is the ONLY stop list for pass 1, deliberately. Comic
# interjections it does not know -- the barks, growls and clangs -- survive into
# the output as noise, and that is the right trade: the surviving list is short
# enough to read whole (17 tokens on a ten-page title), and every entry added to
# a hand-written stop list is a chance to hide a name, which is the one failure
# this tool exists to prevent. Contractions need no entry either, because the
# tokenizer keeps the apostrophe and the dictionary is loaded with an
# apostrophe-stripped form of every word that has one -- see `_load_dictionary`.

# Pair members that make a phrase merely common rather than a name. This list can
# be freer than pass 1's, because a dropped pair is at worst a name found by the
# other pass, not a name lost.
# fmt: off
PAIR_STOP = frozenset({
    "A", "AN", "AND", "ARE", "AS", "AT", "BE", "BUT", "CAN", "DO", "DON'T",
    "FOR", "FROM", "GET", "GOT", "HAVE", "HE", "HIS", "I", "IF", "IN", "IS",
    "IT", "MY", "NO", "NOT", "OF", "OH", "ON", "OUT", "SO", "THAT", "THE",
    "THEY", "THIS", "TO", "UP", "WE", "WHAT", "WILL", "WITH", "YOU", "YOUR",
})
# fmt: on

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")

# A soft hyphen is a line-break hint inside one word, not a word boundary, and
# the corpus stores real ones -- Plenty of Pets 202 g16 holds "WOOD\xad\nPECKER".
# It is always followed by the newline it licenses, so the whitespace has to go
# with it: dropping only the hyphen still leaves the newline splitting the word,
# and the run reports "PECKER" as a name.
SOFT_HYPHEN_BREAK = re.compile("­\\s*")


def _load_dictionary() -> set[str]:
    """Return the stop list of ordinary English words, upper-cased.

    Returns:
        Every word in whichever system dictionaries exist, plus an
        apostrophe-stripped form of each, so a contraction still matches once
        the apostrophe has been dropped. Empty if no dictionary is installed,
        which the caller reports.

    """
    words: set[str] = set()
    for path in DICTIONARY_FILES:
        try:
            with path.open(encoding="utf-8", errors="ignore") as handle:
                words |= {line.strip().upper() for line in handle if line.strip()}
        except OSError:
            continue
    return words | {word.replace("'", "") for word in words if "'" in word}


def _is_ordinary(token: str, words: set[str]) -> bool:
    """Whether a token is an ordinary word rather than a candidate name."""
    bare = token.replace("'", "").replace("-", "")
    if token in words or bare in words:
        return True
    # A hyphenated compound of ordinary words -- QUICK-GROWING, BURGLAR-PROOF --
    # is not a name even though the whole is absent from the dictionary.
    parts = [part for part in token.split("-") if part]
    return len(parts) > 1 and all(part in words for part in parts)


class Tally:
    """Counts and the pages a token or pair was seen on."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.pages: dict[str, set[str]] = defaultdict(set)

    def add(self, key: str, page: str) -> None:
        """Record one occurrence of ``key`` on ``page``."""
        self.counts[key] += 1
        self.pages[key].add(page)

    def rows(self, minimum: int = 1) -> list[tuple[str, int, str]]:
        """Return (key, count, pages) for keys seen at least ``minimum`` times."""
        return [
            (key, count, " ".join(sorted(self.pages[key])))
            for key, count in self.counts.items()
            if count >= minimum
        ]


def _scan(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, title_str: str, engine: OcrTypes
) -> tuple[Tally, Tally, int, int]:
    """Tally single tokens and adjacent pairs across one title's stored text.

    Restricted to the pages the title really owns: the page map reaches into the
    stories around it, and reporting their names here would reintroduce exactly
    the cross-story drift this tool exists to prevent.
    """
    tokens, pairs = Tally(), Tally()
    total = 0
    owned = set(title_pages(comics_database, speech_groups, title_str, engine))
    title = STR_TITLE_TO_ENUM[title_str]
    for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
        if page_group.ocr_index != engine or page_group.fanta_page not in owned:
            continue
        page = page_group.fanta_page
        for group in page_group.speech_page_json.get("groups", {}).values():
            text = SOFT_HYPHEN_BREAK.sub("", strip_markup(group.get("ai_text") or ""))
            found = [match.upper() for match in WORD_RE.findall(text)]
            total += len(found)
            for token in found:
                tokens.add(token, page)
            for left, right in pairwise(found):
                if left not in PAIR_STOP and right not in PAIR_STOP:
                    pairs.add(f"{left} {right}", page)
    return tokens, pairs, total, len(owned)


def _print_rows(heading: str, rows: list[tuple[str, int, str]], *, by_count: bool) -> None:
    """Print one section, or say it is empty."""
    print(f"\n{heading}")
    if not rows:
        print("  (none)")
        return
    ordered = sorted(rows, key=(lambda r: (-r[1], r[0])) if by_count else (lambda r: r[0]))
    width = max(len(row[0]) for row in ordered)
    for key, count, pages in ordered:
        print(f"  {key:<{width}}  {count:>3}   {pages}")


@app.command(help="Print the proper-noun candidates in a title's OCR, before reading the art.")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    engine_str: Annotated[
        str, typer.Option("--engine", help="Which engine's stored text to scan.")
    ] = OcrTypes.EASYOCR.value,
    min_pair: Annotated[
        int, typer.Option("--min-pair", help="How often a word pair must recur to be printed.")
    ] = DEFAULT_MIN_PAIR,
) -> None:
    try:
        engine = OcrTypes(engine_str)
    except ValueError as exc:
        choices = ", ".join(e.value for e in OcrTypes)
        msg = f'Unknown engine "{engine_str}". One of: {choices}.'
        raise typer.BadParameter(msg) from exc

    words = _load_dictionary()
    if not words:
        print("WARNING: no system dictionary found, so pass 1 cannot filter ordinary words.")
        print(f"         Looked in: {', '.join(str(p) for p in DICTIONARY_FILES)}")

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)

    for title in resolve_titles(comics_database, volumes_str, title_str):
        tokens, pairs, total, pages = _scan(comics_database, speech_groups, title, engine)
        if not pages:
            continue
        unknown = [row for row in tokens.rows() if not _is_ordinary(row[0], words)]
        print(f'\n=== "{title}" — {pages} page(s), {total} token(s), {engine.value}')
        print(f"{len(tokens.counts)} distinct token(s), {len(unknown)} not in the dictionary")
        # Alphabetical, and every one of them: a frequency ranking is what let
        # YEHOOTY fall between the head and the tail of the distribution.
        _print_rows("Non-dictionary tokens — the whole distribution:", unknown, by_count=False)
        # By count, because here the useful signal is what recurs: a name the
        # story leans on outranks an incidental pair.
        _print_rows(
            f"Repeated word pairs (>= {min_pair}) — names made of ordinary words:",
            pairs.rows(min_pair),
            by_count=True,
        )
        print("\nA name here is a spelling to settle on, not an identification:")
        print("  the dialogue can name a character long before the art says which one it is.")


if __name__ == "__main__":
    app()
