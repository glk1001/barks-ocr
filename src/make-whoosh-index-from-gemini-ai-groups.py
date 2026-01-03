# ruff: noqa: T201
import sys
from collections import defaultdict
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.whoosh_barks_terms import (
    BARKSIAN_EXTRA_TERMS,
    BARKSIAN_WORDS_WITH_OPTIONAL_HYPHENS,
)
from barks_fantagraphics.whoosh_search_engine import NAME_MAP, SearchEngine, SearchEngineCreator
from loguru import logger
from loguru_config import LoguruConfig

from utils.paragraph_wrap import ParagraphWrapper

APP_LOGGING_NAME = "gemi"


def print_index(search_eng: SearchEngine, title: str) -> None:
    with search_eng._index.reader() as reader:
        all_terms = list(reader.all_terms())

    print("All terms in the index:")
    for field_name, text in all_terms:
        print(f"Field: {field_name}, Term: {text}")


def print_unstemmed_terms(search_eng: SearchEngine) -> None:
    with search_eng._index.reader() as reader:
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


def check_index_integrity(volumes: list[int]) -> None:
    volumes_index_dir = BARKS_ROOT_DIR / "Compleat Barks Disney Reader/Reader Files/Indexes"
    search_engine = SearchEngine(volumes_index_dir)

    print("Checking NAME_MAP...")
    check_name_map(search_engine)

    print("Checking BARKSIAN_EXTRA_TERMS...")
    check_barksian_terms(search_engine)

    print("Checking all titles included in index...")
    check_all_titles_included(search_engine, volumes)

    print("Checking lemmatized terms...")
    check_lemmatized_terms(search_engine)

    print()


def check_all_titles_included(search_engine: SearchEngine, volumes: list[int]) -> None:
    all_indexed_titles = search_engine.get_all_titles()
    all_volume_titles = {
        t[0] for t in comics_database.get_all_titles_in_fantagraphics_volumes(volumes)
    }

    not_indexed = all_volume_titles - all_indexed_titles
    if not_indexed:
        print("Titles not indexed:")
        for title in not_indexed:
            print(f'    "{title}"')


def check_name_map(search_engine: SearchEngine) -> None:
    for key, value in NAME_MAP.items():
        found = search_engine.find_words(key, use_unstemmed_terms=True)
        if not found:
            msg = f'"{key}" not found'
            raise ValueError(msg)

        for ttl_info in found.values():
            for pg_info in ttl_info.fanta_pages.values():
                for speech_text in pg_info.speech_bubbles:
                    speech_lower = speech_text[1].lower()
                    speech_lower = speech_lower.replace("-\n", "-")
                    speech_lower = speech_lower.replace("\n", " ")
                    if f"{value.lower()}" not in speech_lower:
                        msg = f'"{value.lower()}":\n{speech_lower}\n\n{speech_text[1]}'
                        raise ValueError(msg)


def check_barksian_terms(search_engine: SearchEngine) -> None:
    for term in BARKSIAN_EXTRA_TERMS:
        found = search_engine.find_words(term, use_unstemmed_terms=True)
        if not found:
            logger.error(f'Barksian extra term "{term}" not found')
    #            raise ValueError(f'Barksian extra term "{term}" not found')


def check_lemmatized_terms(search_engine: SearchEngine) -> None:
    # spell = SpellChecker()
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


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--create-index", action="store_true", type=bool, default=False),
        ExtraArg("--unstemmed", action="store_true", type=bool, default=False),
        ExtraArg("--do-checks", action="store_true", type=bool, default=False),
        ExtraArg("--words", action="store", type=str, default=""),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Whoosh index from Gemini AI OCR groups", CmdArgNames.VOLUME, extra_args
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "make-whoosh-index-from-gemini-ai-groups.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    volumes_index_dir = BARKS_ROOT_DIR / "Compleat Barks Disney Reader/Reader Files/Indexes"
    create_index = cmd_args.get_extra_arg("--create_index")
    if not create_index:
        whoosh_search = SearchEngine(volumes_index_dir)
    else:
        whoosh_search = SearchEngineCreator(comics_database, volumes_index_dir)
        whoosh_search.index_volumes(cmd_args.get_volumes())

    # print_index(search_engine, "")
    # print_unstemmed_terms(search_engine)
    # print_unstemmed_terms_summary(search_engine)

    unstemmed = cmd_args.get_extra_arg("--unstemmed")
    do_checks = cmd_args.get_extra_arg("--do_checks")
    words = cmd_args.get_extra_arg("--words")

    if do_checks:
        check_index_integrity(cmd_args.get_volumes())

    text_indenter = ParagraphWrapper(initial_indent="       ", subsequent_indent="            ")
    found_text = whoosh_search.find_words(words, unstemmed)
    for comic_title, title_info in found_text.items():
        print(f'"{comic_title}"')

        for fanta_page, page_info in title_info.fanta_pages.items():
            print(
                f"     Fanta vol {title_info.fanta_vol}, page {fanta_page},"
                f" Comic page {page_info.comic_page}"
            )
            for speech_bubble in page_info.speech_bubbles:
                sp_id = speech_bubble[0]
                text_lines = speech_bubble[1]
                indented_text = text_indenter.fill(f'"{sp_id}": {text_lines}')
                print(indented_text)
                print()
            print()
