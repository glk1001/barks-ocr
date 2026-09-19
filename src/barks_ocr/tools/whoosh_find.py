# ruff: noqa: T201
import contextlib
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.speech_groupers import OCR_TYPE_DICT
from barks_fantagraphics.speech_speakers import speaker_display_name
from barks_fantagraphics.whoosh_search_engine import ENTITY_TYPES, SearchEngine
from comic_utils.common_typer_options import LogLevelArg

from barks_ocr.cli_setup import init_logging
from barks_ocr.pipeline.whoosh_index import get_volumes_index_dir
from barks_ocr.utils.paragraph_wrap import ParagraphWrapper

APP_LOGGING_NAME = "whof"

app = typer.Typer()


@app.command(help="Find words in the Whoosh index")
def main(  # noqa: PLR0913
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
    speaker: str | None = typer.Option(
        None,
        "--speaker",
        help='Only lines by this stored speaker value ("Scrooge", "nephews", "other:Witch Hazel")',
    ),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "whoosh-find.log", log_level_str)

    assert ocr_index in OCR_TYPE_DICT

    whoosh_search = SearchEngine(get_volumes_index_dir(ocr_index))

    if entity_type is not None and entity_type not in ENTITY_TYPES:
        print(f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(ENTITY_TYPES)}")
        raise typer.Exit(code=1)
    if entity_type is not None and speaker is not None:
        print("--speaker filters a word search; it cannot be combined with --entity-type.")
        raise typer.Exit(code=1)

    engine = OCR_TYPE_DICT[ocr_index]
    text_indenter = ParagraphWrapper(initial_indent="       ", subsequent_indent="            ")
    if entity_type is not None:
        found_text = whoosh_search.find_entities(entity_type, words)
    else:
        found_text = whoosh_search.find_words(words, speaker=speaker)
    with add_to_queue.open("a") if add_to_queue else contextlib.nullcontext() as queue_file:
        for comic_title, title_info in found_text.items():
            print(f'"{comic_title}"')
            title = STR_TITLE_TO_ENUM[comic_title]

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
                    # Absent from an index built before speakers existed, and for
                    # a `none` speaker (a sound effect, a sign); shown otherwise.
                    who = speaker_display_name(speech_info.speaker) if speech_info.speaker else None
                    speaker_prefix = f" {who}" if who else ""
                    indented_text = text_indenter.fill(
                        f'"{sp_id} ({panel}){speaker_prefix}{entity_suffix}": {text_lines}'
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
