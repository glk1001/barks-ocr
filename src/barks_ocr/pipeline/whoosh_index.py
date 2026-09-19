# ruff: noqa: T201

import json
from collections import Counter, defaultdict
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comic_book_info import NON_COMIC_TITLES
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.entity_types import EntityType
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT, OcrTypes, SpeechGroups
from barks_fantagraphics.speech_speakers import is_character_speaker
from barks_fantagraphics.whoosh_barks_terms import (
    ALL_CAPS,
    BARKSIAN_ENTITY_TYPE_MAP,
    BARKSIAN_EXTRA_TERMS,
    BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS,
    CAPITALIZATION_MAP,
    FRAGMENTS_TO_SUPPRESS,
)
from barks_fantagraphics.whoosh_search_engine import SearchEngine, SearchEngineCreator, TitleDict
from comic_utils.common_typer_options import LogLevelArg, VolumesArg
from intspan import intspan
from loguru import logger

from barks_ocr.cli_setup import init_logging
from barks_ocr.pipeline.entity_store import get_merged_entity_provider, save_auto_entities
from barks_ocr.pipeline.entity_tagger import EntityTagger
from barks_ocr.utils.story_cast import story_characters
from barks_ocr.utils.vision_schema import is_valid_speaker

APP_LOGGING_NAME = "whoi"

# The last volume the vision pass has finished attributing speakers for. Below
# this an index without speakers is a broken build; above it, absent speakers
# are simply work not yet done.
LAST_SPEAKER_VOLUME = 18
# Known gaps: a few pages in the finished volumes were never attributed, so the
# finished band is held to "nearly all" rather than "all".
SPEAKER_COVERAGE_WARN_PCT = 95.0
# Whose lines the filter check runs on: the most-spoken characters in the index.
SPEAKER_FILTER_SAMPLE = 3
SPEAKER_FILTER_TERM = "money"


def get_volumes_index_dir(ocr_index: int) -> Path:
    """Return the reader's index dir for an engine.

    The paddleocr index is the one the reader ships, so it is plain ``Indexes``;
    the easyocr index sits beside it.

    Args:
        ocr_index: A key of ``OCR_TYPE_DICT``.

    Returns:
        The index directory under the reader files.

    """
    indexes_dirname = "Indexes" if ocr_index == 1 else "Indexes-easyocr"
    return BARKS_ROOT_DIR / ("Compleat Barks Disney Reader/Reader Files/" + indexes_dirname)


def check_index_integrity(
    comics_database: ComicsDatabase,
    volumes: list[int],
    checks_output: Path | None,
    volumes_index_dir: Path,
) -> None:
    search_engine = SearchEngine(volumes_index_dir)

    print("Checking CAPITALIZATION_MAP...")
    check_capitalization_map(search_engine)

    print("Checking FRAGMENTS_TO_SUPPRESS...")
    check_fragments_to_suppress(search_engine)

    print("Checking ALL_CAPS...")
    check_all_caps(search_engine)

    print("Checking BARKSIAN_EXTRA_TERMS...")
    check_barksian_terms(search_engine)

    print("Checking all titles included in index...")
    check_all_titles_included(comics_database, search_engine, volumes)

    print("Checking cleaned terms...")
    check_cleaned_terms(search_engine, checks_output)

    print("Checking speakers...")
    check_speakers(search_engine, volumes)

    print()


def check_all_titles_included(
    comics_database: ComicsDatabase, search_engine: SearchEngine, volumes: list[int]
) -> None:
    all_indexed_titles = search_engine.get_all_titles()
    all_volume_titles = {
        t[0]
        for t in comics_database.get_all_titles_in_fantagraphics_volumes(volumes)
        if t[1].comic_book_info.title not in NON_COMIC_TITLES
    }

    not_indexed = all_volume_titles - all_indexed_titles
    if not_indexed:
        print("Titles not indexed:")
        for title in not_indexed:
            print(f'    "{title}"')


def check_capitalization_map(search_engine: SearchEngine) -> None:
    assert "ele-phant" in CAPITALIZATION_MAP

    for key, value in CAPITALIZATION_MAP.items():
        found = search_engine.find_words(key)
        if not found:
            msg = f'"{key}" not found'
            raise ValueError(msg)
        if key.lower() == "ele-phant":  # special case
            continue

        for ttl_info in found.values():
            for pg_info in ttl_info.fanta_pages.values():
                for speech_info in pg_info.speech_info_list:
                    speech_lower = speech_info.speech_text.lower()
                    speech_lower = speech_lower.replace("\u00ad\n", "")
                    speech_lower = speech_lower.replace("-\n", "-")
                    speech_lower = speech_lower.replace("\n", " ")
                    speech_lower = speech_lower.replace("$crooge", "scrooge")
                    if value.lower() not in speech_lower:
                        msg = f'"{value.lower()}":\n{speech_lower}\n\n{speech_info.speech_text}'
                        raise ValueError(msg)


def check_fragments_to_suppress(search_engine: SearchEngine) -> None:
    for key in FRAGMENTS_TO_SUPPRESS:
        found = search_engine.find_words(key)
        if not found:
            msg = f'Fragment "{key}" not found'
            raise ValueError(msg)


def check_all_caps(search_engine: SearchEngine) -> None:
    for word in ALL_CAPS:
        found = search_engine.find_words(word)
        if not found:
            msg = f'"{word}" not found'
            raise ValueError(msg)

        for ttl_info in found.values():
            for pg_info in ttl_info.fanta_pages.values():
                for speech_info in pg_info.speech_info_list:
                    speech_lower = speech_info.speech_text.lower()
                    speech_lower = speech_lower.replace("-\n", "-")
                    speech_lower = speech_lower.replace("\n", " ")
                    if word.lower() not in speech_lower:
                        msg = f'"{word.lower()}":\n{speech_lower}\n\n{speech_info.speech_text}'
                        raise ValueError(msg)


def check_barksian_terms(search_engine: SearchEngine) -> None:
    for term in BARKSIAN_EXTRA_TERMS:
        found = search_engine.find_words(term)
        if not found:
            logger.error(f'Barksian extra term "{term}" not found')


def check_cleaned_terms(search_engine: SearchEngine, checks_output: Path | None) -> None:
    # spell = SpellChecker()  # noqa: ERA001
    all_issues: list[tuple[str, TitleDict]] = []
    for term in search_engine.get_cleaned_terms():
        error = False
        if "-" in term:
            term_with_no_hyphen = term.replace("-", "")
            if (
                search_engine.find_words(term_with_no_hyphen)
                and term not in BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS
            ):
                logger.error(f'Hyphenated term has non-hyphenated term as well: "{term}"')
                error = True

        found = search_engine.find_words(term)
        if not found:
            logger.error(f'Could not find any content for term: "{term}"')

        if error:
            all_issues.append((term, found))

    if all_issues and checks_output:
        _write_queue_file(all_issues, checks_output)


def check_speakers(search_engine: SearchEngine, volumes: list[int]) -> None:
    """Check the index's speaker field and its ``speakers.json`` sidecar agree and make sense.

    Four things, in the order they would fail on a bad build: the sidecar exists
    where finished volumes are indexed; its counts match what the documents hold;
    every stored value is one ``vision_apply`` would have accepted for that story;
    and a speaker-filtered search is a subset of the unfiltered one. Coverage per
    volume is printed, and warned about where a finished volume falls short.

    Args:
        search_engine: The engine over the index under test.
        volumes: The volumes the index was asked to hold.

    Raises:
        ValueError: On a missing sidecar, a count mismatch, an invalid speaker, or
            a filtered result that is not a subset.

    """
    sidecar = search_engine.get_speakers()
    if not sidecar and any(v <= LAST_SPEAKER_VOLUME for v in volumes):
        msg = "speakers.json is missing or empty, but finished volumes are indexed."
        raise ValueError(msg)

    counted: Counter[str] = Counter()
    per_volume: dict[int, list[int]] = defaultdict(lambda: [0, 0])  # [groups, with speaker]
    per_title: dict[str, set[str]] = defaultdict(set)
    for fields in search_engine.iter_all_stored_fields():
        vol = int(fields["fanta_vol"])
        per_volume[vol][0] += 1
        speaker = fields.get("speaker")
        if speaker:
            per_volume[vol][1] += 1
            counted[speaker] += 1
            per_title[fields["title"]].add(speaker)

    if dict(counted) != sidecar:
        only_docs = set(counted) - set(sidecar)
        only_sidecar = set(sidecar) - set(counted)
        differing = sum(1 for s in counted if s in sidecar and counted[s] != sidecar[s])
        msg = (
            f"speakers.json disagrees with the documents:"
            f" {len(only_docs)} only in documents, {len(only_sidecar)} only in sidecar,"
            f" {differing} counts differ."
        )
        raise ValueError(msg)

    invalid = [
        (title, speaker)
        for title, speakers in sorted(per_title.items())
        for speaker in sorted(speakers)
        if not is_valid_speaker(speaker, story_characters(STR_TITLE_TO_ENUM[title]))
    ]
    if invalid:
        for title, speaker in invalid:
            print(f'    invalid speaker "{speaker}" in "{title}"')
        msg = f"{len(invalid)} speaker value(s) the vision pass would have rejected."
        raise ValueError(msg)

    print("    vol  groups  with speaker")
    for vol in sorted(per_volume):
        groups, with_speaker = per_volume[vol]
        pct = 100.0 * with_speaker / groups if groups else 0.0
        print(f"    {vol:3d}  {groups:6d}  {with_speaker:6d}  {pct:5.1f}%")
        if vol <= LAST_SPEAKER_VOLUME and pct < SPEAKER_COVERAGE_WARN_PCT:
            logger.warning(f"Volume {vol} has speakers on only {pct:.1f}% of its groups.")

    _check_speaker_filter(search_engine, sidecar)


def _check_speaker_filter(search_engine: SearchEngine, sidecar: dict[str, int]) -> None:
    """Check a filtered search is a subset of the unfiltered one, all by that speaker."""

    def hit_keys(found: TitleDict) -> set[tuple[str, str, str]]:
        return {
            (title, page, speech.group_id)
            for title, title_info in found.items()
            for page, page_info in title_info.fanta_pages.items()
            for speech in page_info.speech_info_list
        }

    everyone = search_engine.find_words(SPEAKER_FILTER_TERM)
    all_keys = hit_keys(everyone)
    sample = [s for s in sidecar if is_character_speaker(s)][:SPEAKER_FILTER_SAMPLE]
    for speaker in sample:
        found = search_engine.find_words(SPEAKER_FILTER_TERM, speaker=speaker)
        keys = hit_keys(found)
        if not keys <= all_keys:
            msg = (
                f'Filtering "{SPEAKER_FILTER_TERM}" by "{speaker}"'
                " returned hits not in the unfiltered result."
            )
            raise ValueError(msg)
        others = {
            speech.speaker
            for title_info in found.values()
            for page_info in title_info.fanta_pages.values()
            for speech in page_info.speech_info_list
            if speech.speaker != speaker
        }
        if others:
            msg = f'Filtering by "{speaker}" returned lines by {sorted(str(o) for o in others)}.'
            raise ValueError(msg)
        print(f'    "{SPEAKER_FILTER_TERM}" by {speaker}: {len(keys)} of {len(all_keys)} groups')


def _write_queue_file(all_issues: list[tuple[str, TitleDict]], output_file: Path) -> None:
    """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id)."""
    seen: set[tuple[int, str, str, str]] = set()
    queue_lines: list[str] = []
    for term, issue in all_issues:
        for item in issue.values():
            for fanta_page, page_info in item.fanta_pages.items():
                for speech_info in page_info.speech_info_list:
                    # The engine is the constant written on the line below; `SpeechInfo`
                    # does not carry one.
                    engine = OcrTypes.PADDLEOCR.value
                    key = item.fanta_vol, fanta_page, engine, speech_info.group_id
                    if key not in seen:
                        seen.add(key)
                        queue_lines.append(
                            f"{item.fanta_vol}"
                            f" {int(fanta_page)}"
                            f" {engine}"
                            f" {speech_info.group_id}"
                            f" hyphen"
                            f' "{term}"'
                        )

    queue_lines.sort()
    output_file.write_text("\n".join(queue_lines) + ("\n" if queue_lines else ""))
    print(f'\nQueue file: "{output_file}" ({len(queue_lines)} entries).')


app = typer.Typer()


def _tag_volumes(
    comics_database: ComicsDatabase,
    volumes: list[int],
    ocr_index_to_use: OcrTypes,
    entities_dir: Path,
) -> None:
    tagger = EntityTagger()
    all_speech_groups = SpeechGroups(comics_database)

    for vol in volumes:
        print(f"Tagging volume {vol}...")
        volume_entities: dict = {}

        titles = comics_database.get_configured_titles_in_fantagraphics_volumes(
            [vol], exclude_non_comics=True
        )
        for title_str, fanta_info in titles:
            title = fanta_info.comic_book_info.title
            speech_page_groups = all_speech_groups.get_speech_page_groups(title)
            for speech_page in speech_page_groups:
                if speech_page.ocr_index != ocr_index_to_use:
                    continue
                for group_id, speech_text in speech_page.speech_groups.items():
                    entities = tagger.tag(speech_text.ai_text)
                    # Only store non-empty entity lists
                    non_empty = {k: sorted(v) for k, v in entities.items() if v}
                    if non_empty:
                        volume_entities.setdefault(title_str, {}).setdefault(
                            speech_page.fanta_page, {}
                        )[group_id] = non_empty

        save_auto_entities(entities_dir, vol, volume_entities)
        print(f"  Saved {entities_dir / f'entities-vol-{vol:02d}.json'}")


@app.command(help="Build Whoosh index from Gemini AI groups")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    ocr_index: int = 1,
    do_checks: bool = False,
    checks_output: Path | None = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Queue file path (default: auto-named ocr-check-vol-N-DATE.txt in CWD)",
    ),
    tag: bool = typer.Option(
        default=False,
        help="Run spaCy tagging, save entity JSONs, then build index",
    ),
    tag_only: bool = typer.Option(
        default=False,
        help="Run spaCy tagging and save entity JSONs only (no index build)",
    ),
    skip_missing_pages: bool = typer.Option(
        default=False,
        help=(
            "Leave out pages with no prelim OCR file instead of failing the build."
            " Every skipped page is listed first; the titles stay absent from search."
        ),
    ),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "make-whoosh-index-from-gemini-ai-groups.log", log_level_str)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    assert ocr_index in OCR_TYPE_DICT

    volumes_index_dir = get_volumes_index_dir(ocr_index)

    if do_checks:
        check_index_integrity(comics_database, volumes, checks_output, volumes_index_dir)
        return

    if tag or tag_only:
        _tag_volumes(comics_database, volumes, OCR_TYPE_DICT[ocr_index], volumes_index_dir)
        if tag_only:
            return

    if skip_missing_pages:
        _report_missing_prelim_pages(comics_database, volumes)

    entity_provider = get_merged_entity_provider(volumes_index_dir, volumes)
    whoosh_search = SearchEngineCreator(
        comics_database, volumes_index_dir, OCR_TYPE_DICT[ocr_index]
    )
    whoosh_search.index_volumes(
        volumes, entity_provider=entity_provider, skip_missing_pages=skip_missing_pages
    )


def _report_missing_prelim_pages(comics_database: ComicsDatabase, volumes: list[int]) -> None:
    """Print every page the build is about to leave out, so a hole is never silent.

    A build that skips pages must say so up front, title by title: the whole
    reason the default refuses gaps is that an index with a story quietly
    missing looks exactly like a complete one.
    """
    all_speech_groups = SpeechGroups(comics_database)
    titles = comics_database.get_configured_titles_in_fantagraphics_volumes(
        volumes, exclude_non_comics=True
    )
    total = 0
    print("Pages with no prelim OCR file (skipped):")
    for title_str, fanta_info in titles:
        missing = all_speech_groups.get_missing_prelim_pages(fanta_info.comic_book_info.title)
        if not missing:
            continue
        pages = sorted({m.fanta_page for m in missing})
        total += len(missing)
        print(f'    "{title_str}": pages {", ".join(pages)}')
    if not total:
        print("    none")
    else:
        logger.warning(f"Skipping {total} missing prelim page/engine file(s); see the list above.")


def _discover_entities(
    comics_database: ComicsDatabase,
    volumes: list[int],
    ocr_index_to_use: OcrTypes,
    output_path: Path,
) -> None:
    """Run spaCy tagging and output uncurated entity candidates with context."""
    tagger = EntityTagger()
    all_speech_groups = SpeechGroups(comics_database)
    curated_names = _build_curated_set()

    candidates: dict[str, dict] = defaultdict(
        lambda: {"types": Counter(), "count": 0, "examples": []}
    )
    max_examples = 3

    titles = comics_database.get_configured_titles_in_fantagraphics_volumes(
        volumes, exclude_non_comics=True
    )
    for title_str, fanta_info in titles:
        title = fanta_info.comic_book_info.title
        speech_page_groups = all_speech_groups.get_speech_page_groups(title)
        for speech_page in speech_page_groups:
            if speech_page.ocr_index != ocr_index_to_use:
                continue
            for group_id, speech_text in speech_page.speech_groups.items():
                entities = tagger.tag(speech_text.ai_text)
                _collect_uncurated_from_group(
                    entities,
                    curated_names,
                    candidates,
                    title_str,
                    speech_page.fanta_page,
                    group_id,
                    speech_text.ai_text[:200],
                    max_examples,
                )

    _write_discover_output(candidates, output_path)


def _build_curated_set() -> set[str]:
    """Build flat set of all lowercase curated entity names (across all types)."""
    curated: set[str] = set()
    for term_set in BARKSIAN_ENTITY_TYPE_MAP:
        for term in term_set:
            curated.add(term.lower())
    curated.update(k.lower() for k in CAPITALIZATION_MAP)
    return curated


def _collect_uncurated_from_group(  # noqa: PLR0913
    entities: dict[EntityType, set[str]],
    curated_names: set[str],
    candidates: dict[str, dict],
    title_str: str,
    fanta_page: str,
    group_id: str,
    speech_text_snippet: str,
    max_examples: int,
) -> None:
    """Record any entity names not in any curated list as candidates."""
    for entity_type in EntityType:
        for name in entities.get(entity_type, set()):
            if name.lower() not in curated_names:
                info = candidates[name]
                info["types"][entity_type.value] += 1
                info["count"] += 1
                if len(info["examples"]) < max_examples:
                    info["examples"].append(
                        {
                            "title": title_str,
                            "page": fanta_page,
                            "group": group_id,
                            "text": speech_text_snippet,
                        }
                    )


def _write_discover_output(candidates: dict[str, dict], output_path: Path) -> None:
    """Group candidates by type, sort by frequency, and write to JSON."""
    by_type: dict[str, list[dict]] = defaultdict(list)
    for name, info in sorted(candidates.items(), key=lambda x: x[0].lower()):
        primary_type = info["types"].most_common(1)[0][0]
        by_type[primary_type].append(
            {
                "name": name,
                "count": info["count"],
                "spacy_types": dict(info["types"]),
                "examples": info["examples"],
            }
        )

    result = {}
    for entity_type in EntityType:
        type_candidates = by_type.get(entity_type.value, [])
        if type_candidates:
            type_candidates.sort(key=lambda x: x["count"], reverse=True)
            result[entity_type.value] = type_candidates

    output_path.write_text(json.dumps(result, indent=4) + "\n")
    total = sum(len(v) for v in result.values())
    print(f"Discovered {total} uncurated entity candidates.")
    for entity_type, entries in result.items():
        print(f"  {entity_type}: {len(entries)} candidates")
    print(f'\nOutput: "{output_path}"')


@app.command(help="Discover uncurated spaCy entity candidates for review")
def discover(
    volumes_str: VolumesArg = "",
    ocr_index: int = 1,
    output: Path = typer.Option(  # noqa: B008
        "entity-candidates.json",
        "--output",
        "-o",
        help="Output file for discovered candidates",
    ),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "discover-entities.log", log_level_str)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    assert ocr_index in OCR_TYPE_DICT

    _discover_entities(comics_database, volumes, OCR_TYPE_DICT[ocr_index], output)


if __name__ == "__main__":
    app()
