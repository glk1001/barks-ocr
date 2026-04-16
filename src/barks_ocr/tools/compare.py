# ruff: noqa: T201

from collections import defaultdict
from difflib import SequenceMatcher

import typer
from barks_fantagraphics.barks_titles import Titles
from barks_fantagraphics.comic_book_info import BARKS_TITLE_DICT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup, SpeechText
from future.moves.itertools import zip_longest

app = typer.Typer()


@app.command()
def main(title_name: str, verbose: bool = False) -> None:
    """Compare EasyOCR and PaddleOCR text for a given title."""
    try:
        title = BARKS_TITLE_DICT[title_name]
    except KeyError:
        print(f"Error: '{title_name}' is not a valid Title.")
        print("Available titles:")
        for t in Titles:
            print(f"  {t.name}")
        return

    print(f"Loading groups for {title.name}...")
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    speech_page_groups = speech_groups.get_speech_page_groups(title)

    # Organize by page: page_name -> {OcrType -> PanelPageGroup}
    pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
    for g in speech_page_groups:
        pages[g.fanta_page][g.ocr_index] = g

    total_panels = 0
    total_perfect_matches = 0
    total_mismatches = 0

    # Sort pages by filename.
    sorted_page_names = sorted(pages.keys())

    for page_name in sorted_page_names:
        ocr_variants = pages[page_name]
        easy = ocr_variants[OcrTypes.EASYOCR]
        paddle = ocr_variants[OcrTypes.PADDLEOCR]

        easy_panel_groups = easy.get_panel_groups()
        paddle_panel_groups = paddle.get_panel_groups()

        # Collect all panel numbers present in either
        all_panel_nums = set(easy_panel_groups.keys()) | set(paddle_panel_groups.keys())

        sorted_panel_nums = sorted(all_panel_nums)

        print(f"\nPage: {page_name} (Comic Page: {easy.comic_page})")
        print("-" * 80)

        sorted_panel_nums = list(range(1, sorted_panel_nums[-1] + 1))
        for panel_num in sorted_panel_nums:
            skip, panel_mismatches, panel_perfect_matches = _check_panel(
                easy_panel_groups,
                paddle_panel_groups,
                panel_num,
                verbose,
            )

            if skip:
                continue

            total_mismatches += panel_mismatches
            total_perfect_matches += panel_perfect_matches
            total_panels += 1

    print("\n" + "=" * 80)
    print(f"Total Panels Compared: {total_panels}")
    print(f"Mismatches:            {total_mismatches}")
    print(f"Perfect Matches:       {total_perfect_matches}")


def _check_panel(  # noqa: C901
    easy_panel_groups: dict[int, list[SpeechText]],
    paddle_panel_groups: dict[int, list[SpeechText]],
    panel_num: int,
    verbose: bool,
) -> tuple[bool, int, int]:
    if (panel_num not in easy_panel_groups) and (panel_num not in paddle_panel_groups):
        if verbose:
            print(f"Panel {panel_num:<2} NOT IN EASYOCR OR PADDLEOCR")
    elif panel_num not in easy_panel_groups:
        print(f"Panel {panel_num:<2} NOT IN EASYOCR")
    elif panel_num not in paddle_panel_groups:
        print(f"Panel {panel_num:<2} NOT IN PADDLEOCR")
    if panel_num not in easy_panel_groups or panel_num not in paddle_panel_groups:
        return True, 0, 0  # skip this panel

    pt_easy_speech_list = easy_panel_groups[panel_num]
    pt_paddle_speech_list = paddle_panel_groups[panel_num]

    panel_mismatches = 0
    panel_perfect_matches = 0
    for txt_easy, txt_paddle in zip_longest(pt_easy_speech_list, pt_paddle_speech_list):
        if not txt_easy:
            print(
                f"Panel {panel_num:<2}, group {txt_paddle.group_id}:"
                f' ONLY IN PADDLE: "{txt_paddle.raw_ai_text!r}".'
            )
            panel_mismatches += 1
            continue

        if not txt_paddle:
            print(
                f"Panel {panel_num:<2}, group {txt_easy.group_id}:"
                f' ONLY IN EASY: "{txt_easy.raw_ai_text!r}".'
            )
            panel_mismatches += 1
            continue

        matcher = SequenceMatcher(None, txt_easy.raw_ai_text, txt_paddle.raw_ai_text)
        ratio = matcher.ratio()

        if ratio == 1.0:
            panel_perfect_matches += 1
            if verbose:
                print(
                    f"Panel {panel_num:<2},"
                    f" groups {txt_easy.group_id}, {txt_paddle.group_id}"
                    f"  | MATCH: {txt_easy.raw_ai_text!r}"
                )
                print()
        else:
            panel_mismatches += 1
            print(f"Panel {panel_num:<2} | SIM: {ratio:.2f}")
            print(f"  Easy,   group {txt_easy.group_id}:   {txt_easy.raw_ai_text!r}")
            print(f"  Paddle, group {txt_paddle.group_id}: {txt_paddle.raw_ai_text!r}")
            print()

    return False, panel_mismatches, panel_perfect_matches


if __name__ == "__main__":
    app()
