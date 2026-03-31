# ruff: noqa: T201
import contextlib
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT
from barks_fantagraphics.whoosh_search_engine import ENTITY_TYPES, SearchEngine
from comic_utils.common_typer_options import LogLevelArg

from barks_ocr.cli_setup import init_logging
from barks_ocr.utils.paragraph_wrap import ParagraphWrapper

APP_LOGGING_NAME = "whof"

app = typer.Typer()


@app.command(help="Find words in the Whoosh index")
def main(
    words: str = "",
    ocr_index: int = 1,
    entity_type: str | None = typer.Option(
        None,
        "--entity-type",
        help=f"Search by entity type ({', '.join(ENTITY_TYPES)})",
    ),
    add_to_queue: Path | None = typer.Option(  # noqa: B008
        None,
        "--add-to-queue",
        help="Append found items to queue file (format: volume fanta_page engine group_id)",
    ),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "whoosh-find.log", log_level_str)

    assert ocr_index in OCR_TYPE_DICT

    indexes_dirname = "Indexes" if ocr_index == 1 else "Indexes-easyocr"
    volumes_index_dir = BARKS_ROOT_DIR / (
        "Compleat Barks Disney Reader/Reader Files/" + indexes_dirname
    )
    whoosh_search = SearchEngine(volumes_index_dir)

    if entity_type is not None and entity_type not in ENTITY_TYPES:
        print(f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(ENTITY_TYPES)}")
        raise typer.Exit(code=1)

    engine = OCR_TYPE_DICT[ocr_index]
    text_indenter = ParagraphWrapper(initial_indent="       ", subsequent_indent="            ")
    if entity_type is not None:
        found_text = whoosh_search.find_entities(entity_type, words)
    else:
        found_text = whoosh_search.find_words(words)
    with add_to_queue.open("a") if add_to_queue else contextlib.nullcontext() as queue_file:
        for comic_title, title_info in found_text.items():
            print(f'"{comic_title}"')
            title = BARKS_TITLE_DICT[comic_title]

            for fanta_page, page_info in title_info.fanta_pages.items():
                print(
                    f"     Fanta vol {title_info.fanta_vol}, page {fanta_page},"
                    f" Comic page {page_info.comic_page}"
                )
                for speech_info in page_info.speech_info_list:
                    sp_id = speech_info.group_id
                    panel = speech_info.panel_num
                    text_lines = speech_info.speech_text.replace("\u00ad", "-")
                    entity_suffix = (
                        f" [{','.join(speech_info.entity_types)}]"
                        if speech_info.entity_types
                        else ""
                    )
                    indented_text = text_indenter.fill(
                        f'"{sp_id} ({panel}){entity_suffix}": {text_lines}'
                    )
                    print(indented_text)
                    print()
                    if queue_file is not None:
                        queue_file.write(
                            f'"{words}" {title.name} {page_info.comic_page}'
                            f"  {title_info.fanta_vol} {fanta_page} {engine} {sp_id}\n"
                        )
                print()


if __name__ == "__main__":
    app()
