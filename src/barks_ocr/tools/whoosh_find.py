# ruff: noqa: T201
from pathlib import Path

import typer
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT
from barks_fantagraphics.whoosh_search_engine import SearchEngine
from comic_utils.common_typer_options import LogLevelArg
from loguru_config import LoguruConfig

import barks_ocr.log_setup as _log_setup
from barks_ocr.utils.paragraph_wrap import ParagraphWrapper

_RESOURCES = Path(__file__).parent.parent / "resources"

APP_LOGGING_NAME = "whof"

app = typer.Typer()


@app.command(help="Find words in the Whoosh index")
def main(
    words: str = "",
    ocr_index: int = 1,
    unstemmed: bool = False,
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "whoosh-find.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    assert ocr_index in OCR_TYPE_DICT

    indexes_dirname = "Indexes" if ocr_index == 1 else "Indexes-easyocr"
    volumes_index_dir = BARKS_ROOT_DIR / (
        "Compleat Barks Disney Reader/Reader Files/" + indexes_dirname
    )
    whoosh_search = SearchEngine(volumes_index_dir)

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
