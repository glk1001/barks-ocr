# ruff: noqa: T201

import sys
import textwrap
from collections import defaultdict
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.whoosh_barks_terms import BARKSIAN_EXTRA_TERMS
from barks_fantagraphics.whoosh_search_engine import SearchEngine, SearchEngineCreator, NAME_MAP
from loguru import logger
from loguru_config import LoguruConfig

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


def check_all_barksian_terms() -> None:
    volumes_index_dir = BARKS_ROOT_DIR / "Compleat Barks Disney Reader/Reader Files/Indexes"
    search_engine = SearchEngine(volumes_index_dir)

    for key, value in NAME_MAP.items():
        found = search_engine.find_words(key, use_unstemmed_terms=True)
        if not found:
            raise ValueError(f'"{key}" not found')

        for comic_title, title_info in found.items():
            print(f'"{comic_title}"')
            for page in title_info.pages:
                text = page[2].lower().replace("\n", " ")
                if f"{value.lower()}" not in text:
                    raise ValueError(f"{value.lower()}:\n{text}")

    for term in BARKSIAN_EXTRA_TERMS:
        found = search_engine.find_words(term, use_unstemmed_terms=True)
        if not found:
            logger.error(f'Barksian extra term "{term}" not found')
#            raise ValueError(f'Barksian extra term "{term}" not found')

    for term in BARKSIAN_EXTRA_TERMS:
        found = search_engine.find_words(term, use_unstemmed_terms=True)
        if not found:
            logger.error(f'Barksian term to capitalize "{term}" not found')
#            raise ValueError(f'Barksian term to capitalize "{term}" not found')

if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--create-index", action="store_true", type=bool, default=False),
        ExtraArg("--unstemmed", action="store_true", type=bool, default=False),
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
        check_all_barksian_terms()
        search_engine = SearchEngine(volumes_index_dir)
    else:
        search_engine = SearchEngineCreator(comics_database, volumes_index_dir)
        search_engine.index_volumes(cmd_args.get_volumes())

    # print_index(search_engine, "")
    # print_unstemmed_terms(search_engine)
    print_unstemmed_terms_summary(search_engine)

    unstemmed = cmd_args.get_extra_arg("--unstemmed")
    words = cmd_args.get_extra_arg("--words")
    found = search_engine.find_words(words, unstemmed)
    for comic_title, title_info in found.items():
        print(f'"{comic_title}"')
        for page in title_info.pages:
            print(f"   Fanta vol {title_info.fanta_vol}, Fanta page: {page[0]}, Page: {page[1]}")
            indented_text = textwrap.indent(page[2], "        ")
            print(indented_text)
            print()
