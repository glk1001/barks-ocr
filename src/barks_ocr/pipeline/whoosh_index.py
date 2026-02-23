# ruff: noqa: T201
from collections import defaultdict
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import NON_COMIC_TITLES
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT
from barks_fantagraphics.whoosh_barks_terms import (
    ALL_CAPS,
    BARKSIAN_EXTRA_TERMS,
    BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS,
    NAME_MAP,
)
from barks_fantagraphics.whoosh_search_engine import SearchEngine, SearchEngineCreator
from comic_utils.common_typer_options import LogLevelArg, VolumesArg
from intspan import intspan
from loguru import logger
from loguru_config import LoguruConfig

import barks_ocr.log_setup as _log_setup
from barks_ocr.utils.paragraph_wrap import ParagraphWrapper

_RESOURCES = Path(__file__).parent.parent / "resources"

APP_LOGGING_NAME = "gemi"


def print_index(search_eng: SearchEngine, _title: str) -> None:
    # noinspection PyProtectedMember
    with search_eng._index.reader() as reader:  # noqa: SLF001
        all_terms = list(reader.all_terms())

    print("All terms in the index:")
    for field_name, text in all_terms:
        print(f"Field: {field_name}, Term: {text}")


def print_unstemmed_terms(search_eng: SearchEngine) -> None:
    # noinspection PyProtectedMember
    with search_eng._index.reader() as reader:  # noqa: SLF001
        all_terms = list(reader.terms_from("unstemmed", ""))

    print("All terms in the index:")
    for _field_name, text in all_terms:
        print(f"{text}")


def print_unstemmed_terms_summary(search_eng: SearchEngine) -> None:
    unstemmed_terms = search_eng.get_cleaned_unstemmed_terms()

    counts = defaultdict(int)
    for term in unstemmed_terms:
        first_letter = term[0].lower()
        counts[first_letter] += 1

    for letter, num in counts.items():
        print(f"{letter}: {num}")

    print(f"Total: {len(unstemmed_terms)}")


def check_index_integrity(comics_database: ComicsDatabase, volumes: list[int]) -> None:
    volumes_index_dir = BARKS_ROOT_DIR / "Compleat Barks Disney Reader/Reader Files/Indexes"
    search_engine = SearchEngine(volumes_index_dir)

    print("Checking NAME_MAP...")
    check_name_map(search_engine)

    print("Checking ALL_CAPS...")
    check_all_caps(search_engine)

    print("Checking BARKSIAN_EXTRA_TERMS...")
    check_barksian_terms(search_engine)

    print("Checking all titles included in index...")
    check_all_titles_included(comics_database, search_engine, volumes)

    print("Checking lemmatized terms...")
    check_lemmatized_terms(search_engine)

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


def check_name_map(search_engine: SearchEngine) -> None:
    assert "ele-phant" in NAME_MAP

    for key, value in NAME_MAP.items():
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
                    if value.lower() not in speech_lower:
                        msg = f'"{value.lower()}":\n{speech_lower}\n\n{speech_info.speech_text}'
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


def check_lemmatized_terms(search_engine: SearchEngine) -> None:
    # spell = SpellChecker()  # noqa: ERA001
    for term in search_engine.get_cleaned_lemmatized_terms():
        if "-" in term:
            term_with_no_hyphen = term.replace("-", "")
            if (
                search_engine.find_words(term_with_no_hyphen, use_unstemmed_terms=True)
                and term not in BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS
            ):
                logger.error(f'Hyphenated term has non-hyphenated term as well: "{term}"')

        if not search_engine.find_all_words(term):
            logger.error(f'Could not find any content for term: "{term}"')


app = typer.Typer()


@app.command(help="Make whoosh index from gemini ai groups")
def main(
    volumes_str: VolumesArg = "",
    words: str = "",
    create_index: bool = False,
    ocr_index: int = 1,  # paddleocr
    unstemmed: bool = False,
    do_checks: bool = False,
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
    if not create_index:
        whoosh_search = SearchEngine(volumes_index_dir)
    else:
        whoosh_search = SearchEngineCreator(
            comics_database, volumes_index_dir, OCR_TYPE_DICT[ocr_index]
        )
        whoosh_search.index_volumes(volumes)

    # print_index(search_engine, "")  # noqa: ERA001
    # print_unstemmed_terms(search_engine)  # noqa: ERA001
    # print_unstemmed_terms_summary(search_engine)  # noqa: ERA001

    if do_checks:
        check_index_integrity(comics_database, volumes)

    text_indenter = ParagraphWrapper(initial_indent="       ", subsequent_indent="            ")
    found_text = whoosh_search.find_words(words, unstemmed)
    for comic_title, title_info in found_text.items():
        print(f'"{comic_title}"')

        for fanta_page, page_info in title_info.fanta_pages.items():
            print(
                f"     Fanta vol {title_info.fanta_vol}, page {fanta_page},"
                f" Comic page {page_info.comic_page}"
            )
            for speech_info in page_info.speech_info_list:
                sp_id = speech_info.group_id
                panel = speech_info.panel_num
                text_lines = speech_info.speech_text.replace("\u00ad", "-")
                indented_text = text_indenter.fill(f'"{sp_id} ({panel})": {text_lines}')
                print(indented_text)
                print()
            print()


if __name__ == "__main__":
    app()
