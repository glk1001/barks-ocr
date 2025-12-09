import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from loguru import logger
from loguru_config import LoguruConfig
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from barks_fantagraphics.pages import get_sorted_srce_and_dest_pages
from ocr_json_files import JsonFiles

APP_LOGGING_NAME = "gemi"

STOP_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "doing",
    "don",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "s",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "t",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}
UNIMPORTANT_WORDS = {
    "even",
    "get",
    "go",
    "goes",
    "got",
    "haven't",
    "he'll",
    "he's",
    "here's",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "isn't",
    "it's",
    "let",
    "wasn't",
    "we'll",
    "we're",
    "what'll",
    "what's",
    "won't",
    "you'll",
}

ALL_WORDS_TO_IGNORE = STOP_WORDS.union(UNIMPORTANT_WORDS)


class SearchEngine:
    def __init__(self) -> None:
        # self._volumes = list[int]
        schema = Schema(title=TEXT(stored=True), page=ID(stored=True), content=TEXT)
        #        self.index = create_in("/tmp/indexdir", schema)
        self.index = open_dir("/tmp/indexdir")

    def add_page_content(self, title: str, content: dict[str, str]) -> None:
        writer = self.index.writer()

        for page, ai_text in content.items():
            writer.add_document(title=title, page=page, content=ai_text)

        writer.commit()


def make_word_index_from_gemini_ai_groups_for_titles(titles: list[str]) -> None:
    search_engine = SearchEngine()

    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        make_word_index_from_gemini_ai_groups_for_title(search_engine, title)


def make_word_index_from_gemini_ai_groups_for_title(
    search_engine: SearchEngine, title: str
) -> None:
    title_content = get_content(title)

    search_engine.add_page_content(title, title_content)


def print_index(search_engine: SearchEngine, title: str) -> None:
    with search_engine.index.reader() as reader:
        all_terms = list(reader.all_terms())

    print("All terms in the index:")
    for fieldname, text in all_terms:
        print(f"Field: {fieldname}, Term: {text}")


def find_words(search_engine: SearchEngine, words: str) -> dict[str, list[str]]:
    prelim_results = defaultdict(list)
    with search_engine.index.searcher() as searcher:
        query = QueryParser("content", search_engine.index.schema).parse(words)
        results = searcher.search(query)
        for hit in results:
            prelim_results[hit["title"]].append(hit["page"])

    title_results = {}
    for title in sorted(prelim_results.keys()):
        title_results[title] = sorted(prelim_results[title])

    return title_results


def map_to_tite_pages(title: str, fanta_pages: list[str]) -> list[str]:
    comic = comics_database.get_comic_book(title)
    srce_and_dest_pages = get_sorted_srce_and_dest_pages(comic, get_full_paths=True)
    for srce, dest in zip(srce_and_dest_pages.srce_pages, srce_and_dest_pages.dest_pages):
        print(srce.page_num, srce.page_filename, dest.page_num, dest.page_filename)

    return fanta_pages


def get_content(title: str) -> dict[str, str]:
    json_files = JsonFiles(comics_database, title)

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_raw_ocr_story_files(RESTORABLE_PAGE_TYPES)

    content = {}
    for ocr_file in ocr_files:
        json_files.set_ocr_file(ocr_file)

        ocr_prelim_group2 = json.loads(json_files.ocr_prelim_groups_json_file[1].read_text())

        all_ai_text = ""
        for group in ocr_prelim_group2["groups"].values():
            all_ai_text += "\n" + group["ai_text"]

        content[json_files.page] = all_ai_text

    return content


def normalize_string(text: str) -> list[str]:
    lower_string = text.lower()

    no_number_string = lower_string
    # no_number_string = re.sub(r"\d[^5]+", "", lower_string)

    no_punc_string = re.sub(r"—|\.\.\.", " ", no_number_string)
    no_punc_string = re.sub(r"[\"!=?,:;.<>/()*&%$#]", "", no_punc_string)

    no_whitespace_string = no_punc_string.strip()

    prelim_word_list = [no_whitespace_string][0].split()

    # Remove not useful words.
    return [w for w in prelim_word_list if w not in ALL_WORDS_TO_IGNORE]


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--words", action="store", type=str, default=""),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title", CmdArgNames.VOLUME | CmdArgNames.TITLE, extra_args
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "make-gemini-ai-groups-batch-job.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    # make_word_index_from_gemini_ai_groups_for_titles(cmd_args.get_titles())

    search_engine = SearchEngine()
    # print_index(search_engine, "")
    words = cmd_args.get_extra_arg("--words")
    found = find_words(search_engine, words)
    for title, fanta_pages in found.items():
        pages = map_to_tite_pages(title, fanta_pages)
        print(f"Title: {title}, Page: {', '.join(pages)}")
