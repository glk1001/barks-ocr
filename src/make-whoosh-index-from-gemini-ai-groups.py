# ruff: noqa: T201

import sys
import textwrap
from collections import defaultdict
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.whoosh_search_engine import SearchEngine, SearchEngineCreator
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

    volumes_index_dir = Path("/tmp/index_dir2")
    create_index = cmd_args.get_extra_arg("--create_index")
    if not create_index:
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
        print(f'"{comic_title}" [Fanta volume {title_info.fanta_vol}]')
        for page in title_info.pages:
            print(f"   Page: {page[1]}, Fanta page: {page[0]}")
            indented_text = textwrap.indent(page[2], "        ")
            print(indented_text)
            print()
