# ruff: noqa: T201

import json
from collections import Counter, defaultdict
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT, NON_COMIC_TITLES
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.entity_types import EntityType
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT, OcrTypes, SpeechGroups
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
from loguru_config import LoguruConfig

import barks_ocr.log_setup as _log_setup
from barks_ocr.pipeline.entity_store import get_merged_entity_provider, save_auto_entities
from barks_ocr.pipeline.entity_tagger import EntityTagger

_RESOURCES = Path(__file__).parent.parent / "resources"

APP_LOGGING_NAME = "whoi"


def check_index_integrity(
    comics_database: ComicsDatabase, volumes: list[int], checks_output: Path | None
) -> None:
    volumes_index_dir = BARKS_ROOT_DIR / "Compleat Barks Disney Reader/Reader Files/Indexes"
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

    print("Checking lemmatized terms...")
    check_lemmatized_terms(search_engine, checks_output)

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
        found = search_engine.find_words(key, use_unstemmed_terms=True)
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
        found = search_engine.find_words(key, use_unstemmed_terms=True)
        if not found:
            msg = f'Fragment "{key}" not found'
            raise ValueError(msg)


def check_all_caps(search_engine: SearchEngine) -> None:
    for word in ALL_CAPS:
        found = search_engine.find_words(word, use_unstemmed_terms=True)
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
        found = search_engine.find_words(term, use_unstemmed_terms=True)
        if not found:
            logger.error(f'Barksian extra term "{term}" not found')


def check_lemmatized_terms(search_engine: SearchEngine, checks_output: Path | None) -> None:
    # spell = SpellChecker()  # noqa: ERA001
    all_issues: list[tuple[str, TitleDict]] = []
    for term in search_engine.get_cleaned_lemmatized_terms():
        error = False
        if "-" in term:
            term_with_no_hyphen = term.replace("-", "")
            if (
                search_engine.find_words(term_with_no_hyphen, use_unstemmed_terms=True)
                and term not in BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS
            ):
                logger.error(f'Hyphenated term has non-hyphenated term as well: "{term}"')
                error = True

        found = search_engine.find_all_words(term)
        if not found:
            logger.error(f'Could not find any content for term: "{term}"')

        if error:
            all_issues.append((term, found))

    if all_issues and checks_output:
        _write_queue_file(all_issues, checks_output)


def _write_queue_file(all_issues: list[tuple[str, TitleDict]], output_file: Path) -> None:
    """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id)."""
    seen: set[tuple[int, str, str, str]] = set()
    queue_lines: list[str] = []
    for term, issue in all_issues:
        for item in issue.values():
            for fanta_page, page_info in item.fanta_pages.items():
                for speech_info in page_info.speech_info_list:
                    key = item.fanta_vol, fanta_page, speech_info.group_id, speech_info.group_id
                    if key not in seen:
                        seen.add(key)
                        queue_lines.append(
                            f"{item.fanta_vol}"
                            f" {int(fanta_page)}"
                            f" {OcrTypes.PADDLEOCR.value}"
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
        for title_str, _ in titles:
            title = BARKS_TITLE_DICT[title_str]
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
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "make-whoosh-index-from-gemini-ai-groups.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    assert ocr_index in OCR_TYPE_DICT

    indexes_dirname = "Indexes" if ocr_index == 1 else "Indexes-easyocr"
    volumes_index_dir = BARKS_ROOT_DIR / (
        "Compleat Barks Disney Reader/Reader Files/" + indexes_dirname
    )

    if do_checks:
        check_index_integrity(comics_database, volumes, checks_output)
    elif tag or tag_only:
        _tag_volumes(comics_database, volumes, OCR_TYPE_DICT[ocr_index], volumes_index_dir)
        if not tag_only:
            entity_provider = get_merged_entity_provider(volumes_index_dir, volumes)
            whoosh_search = SearchEngineCreator(
                comics_database, volumes_index_dir, OCR_TYPE_DICT[ocr_index]
            )
            whoosh_search.index_volumes(volumes, entity_provider=entity_provider)
    else:
        entity_provider = get_merged_entity_provider(volumes_index_dir, volumes)
        whoosh_search = SearchEngineCreator(
            comics_database, volumes_index_dir, OCR_TYPE_DICT[ocr_index]
        )
        whoosh_search.index_volumes(volumes, entity_provider=entity_provider)


def _build_curated_sets() -> dict[EntityType, set[str]]:
    """Build mapping from EntityType to set of lowercase curated names."""
    curated: dict[EntityType, set[str]] = {t: set() for t in EntityType}
    for term_set, entity_type in BARKSIAN_ENTITY_TYPE_MAP.items():
        for term in term_set:
            curated[entity_type].add(term.lower())
    return curated


def _collect_uncurated_from_group(  # noqa: PLR0913
    entities: dict[EntityType, set[str]],
    curated_sets: dict[EntityType, set[str]],
    candidates: dict[str, dict],
    title_str: str,
    fanta_page: str,
    group_id: str,
    speech_text_snippet: str,
    max_examples: int,
) -> None:
    """Record any entity names not in the curated sets as candidates."""
    for entity_type in EntityType:
        curated = curated_sets.get(entity_type, set())
        for name in entities.get(entity_type, set()):
            if name.lower() not in curated:
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


def _discover_entities(
    comics_database: ComicsDatabase,
    volumes: list[int],
    ocr_index_to_use: OcrTypes,
    output_path: Path,
) -> None:
    """Run spaCy tagging and output uncurated entity candidates with context."""
    tagger = EntityTagger()
    all_speech_groups = SpeechGroups(comics_database)
    curated_sets = _build_curated_sets()

    candidates: dict[str, dict] = defaultdict(
        lambda: {"types": Counter(), "count": 0, "examples": []}
    )
    max_examples = 3

    titles = comics_database.get_configured_titles_in_fantagraphics_volumes(
        volumes, exclude_non_comics=True
    )
    for title_str, _ in titles:
        title = BARKS_TITLE_DICT[title_str]
        speech_page_groups = all_speech_groups.get_speech_page_groups(title)
        for speech_page in speech_page_groups:
            if speech_page.ocr_index != ocr_index_to_use:
                continue
            for group_id, speech_text in speech_page.speech_groups.items():
                entities = tagger.tag(speech_text.ai_text)
                _collect_uncurated_from_group(
                    entities,
                    curated_sets,
                    candidates,
                    title_str,
                    speech_page.fanta_page,
                    group_id,
                    speech_text.ai_text[:200],
                    max_examples,
                )

    _write_discover_output(candidates, output_path)


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
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "discover-entities.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    assert ocr_index in OCR_TYPE_DICT

    _discover_entities(comics_database, volumes, OCR_TYPE_DICT[ocr_index], output)


if __name__ == "__main__":
    app()
