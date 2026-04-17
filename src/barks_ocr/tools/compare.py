# ruff: noqa: T201

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

import typer
from barks_fantagraphics.comic_book_info import BARKS_TITLE_DICT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup, SpeechText
from comic_utils.common_typer_options import TitleArg, VolumesArg
from future.moves.itertools import zip_longest
from intspan import intspan

app = typer.Typer()


# ── Mismatch data ───────────────────────────────────────────────────────────


@dataclass
class MismatchFound:
    volume: int
    fanta_page: str
    engine: str
    group_id: str
    issue_type: str


# ── Comparison logic ────────────────────────────────────────────────────────


def _compare_title(
    comics_database: ComicsDatabase,
    title_str: str,
    verbose: bool,
) -> tuple[list[MismatchFound], int, int, int]:
    """Compare EasyOCR vs PaddleOCR for one title. Return mismatches and counts."""
    title = BARKS_TITLE_DICT[title_str]
    volume = comics_database.get_fanta_volume_int(title_str)
    speech_groups = SpeechGroups(comics_database)
    speech_page_groups = speech_groups.get_speech_page_groups(title)

    pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
    for g in speech_page_groups:
        pages[g.fanta_page][g.ocr_index] = g

    all_mismatches: list[MismatchFound] = []
    total_panels = 0
    total_perfect_matches = 0
    total_mismatches = 0

    for page_name in sorted(pages.keys()):
        ocr_variants = pages[page_name]
        if OcrTypes.EASYOCR not in ocr_variants or OcrTypes.PADDLEOCR not in ocr_variants:
            print(f"\nPage: {page_name} — skipping (missing OCR variant)")
            continue

        easy = ocr_variants[OcrTypes.EASYOCR]
        paddle = ocr_variants[OcrTypes.PADDLEOCR]

        if easy.renumber_groups():
            easy.save_json()
        if paddle.renumber_groups():
            paddle.save_json()

        easy_panel_groups = easy.get_panel_groups()
        paddle_panel_groups = paddle.get_panel_groups()

        all_panel_nums = set(easy_panel_groups.keys()) | set(paddle_panel_groups.keys())
        if not all_panel_nums:
            print(f"\nPage: {page_name} (Comic Page: {easy.comic_page}) — no speech groups")
            continue

        sorted_panel_nums = sorted(all_panel_nums)

        print(f"\nPage: {page_name} (Comic Page: {easy.comic_page})")
        print("-" * 80)

        sorted_panel_nums = list(range(1, sorted_panel_nums[-1] + 1))
        for panel_num in sorted_panel_nums:
            skip, panel_mismatches, panel_perfect_matches, panel_mismatch_records = _check_panel(
                easy_panel_groups,
                paddle_panel_groups,
                panel_num,
                volume,
                page_name,
                verbose,
            )

            if skip:
                continue

            total_mismatches += panel_mismatches
            total_perfect_matches += panel_perfect_matches
            total_panels += 1
            all_mismatches.extend(panel_mismatch_records)

    return all_mismatches, total_panels, total_mismatches, total_perfect_matches


def _check_panel(  # noqa: C901, PLR0913
    easy_panel_groups: dict[int, list[SpeechText]],
    paddle_panel_groups: dict[int, list[SpeechText]],
    panel_num: int,
    volume: int,
    fanta_page: str,
    verbose: bool,
) -> tuple[bool, int, int, list[MismatchFound]]:
    """Check one panel. Return (skip, mismatches, perfect_matches, mismatch_records)."""
    if (panel_num not in easy_panel_groups) and (panel_num not in paddle_panel_groups):
        if verbose:
            print(f"Panel {panel_num:<2} NOT IN EASYOCR OR PADDLEOCR")
    elif panel_num not in easy_panel_groups:
        print(f"Panel {panel_num:<2} NOT IN EASYOCR")
    elif panel_num not in paddle_panel_groups:
        print(f"Panel {panel_num:<2} NOT IN PADDLEOCR")
    if panel_num not in easy_panel_groups or panel_num not in paddle_panel_groups:
        return True, 0, 0, []

    pt_easy_speech_list = easy_panel_groups[panel_num]
    pt_paddle_speech_list = paddle_panel_groups[panel_num]

    panel_mismatches = 0
    panel_perfect_matches = 0
    records: list[MismatchFound] = []

    for txt_easy, txt_paddle in zip_longest(pt_easy_speech_list, pt_paddle_speech_list):
        if not txt_easy:
            print(
                f"Panel {panel_num:<2}, group {txt_paddle.group_id}:"
                f' ONLY IN PADDLE: "{txt_paddle.raw_ai_text!r}".'
            )
            panel_mismatches += 1
            records.append(
                MismatchFound(
                    volume, fanta_page, "paddleocr", txt_paddle.group_id, "only_in_paddle"
                )
            )
            continue

        if not txt_paddle:
            print(
                f"Panel {panel_num:<2}, group {txt_easy.group_id}:"
                f' ONLY IN EASY: "{txt_easy.raw_ai_text!r}".'
            )
            panel_mismatches += 1
            records.append(
                MismatchFound(volume, fanta_page, "easyocr", txt_easy.group_id, "only_in_easy")
            )
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
            records.append(
                MismatchFound(volume, fanta_page, "easyocr", txt_easy.group_id, "text_mismatch")
            )

    return False, panel_mismatches, panel_perfect_matches, records


# ── Output helpers ──────────────────────────────────────────────────────────


def _write_queue_file(all_mismatches: list[MismatchFound], output_file: Path) -> None:
    """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id)."""
    seen: set[tuple[int, str, str, str]] = set()
    queue_lines: list[str] = []
    for m in all_mismatches:
        key = (m.volume, m.fanta_page, m.engine, m.group_id)
        if key not in seen:
            seen.add(key)
            queue_lines.append(
                f"{m.volume} {int(m.fanta_page)} {m.engine} {m.group_id} {m.issue_type}"
            )
    output_file.write_text("\n".join(queue_lines) + ("\n" if queue_lines else ""))
    print(f'\nQueue file: "{output_file}" ({len(queue_lines)} entries).')


def _default_output_file(volumes_str: str) -> Path:
    today = datetime.now(tz=UTC).date().isoformat()
    if volumes_str:
        safe = volumes_str.replace(",", "_").replace(" ", "")
        return Path(f"ocr-compare-vol-{safe}-{today}.txt")
    return Path(f"ocr-compare-{today}.txt")


# ── CLI ─────────────────────────────────────────────────────────────────────


@app.command(help="Compare EasyOCR and PaddleOCR text; optionally write a kivy-editor queue file.")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    output: Path = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Queue file path (default: auto-named ocr-compare-vol-N-DATE.txt in CWD)",
    ),
    verbose: bool = False,
) -> None:
    """Compare EasyOCR and PaddleOCR text for given volumes/titles."""
    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    all_mismatches: list[MismatchFound] = []
    grand_total_panels = 0
    grand_total_mismatches = 0
    grand_total_perfect_matches = 0

    for title_name in title_list:
        print("=" * 80)
        print(f"Loading groups for {title_name}...")
        mismatches, panels, mis, perfect = _compare_title(comics_database, title_name, verbose)
        all_mismatches.extend(mismatches)
        grand_total_panels += panels
        grand_total_mismatches += mis
        grand_total_perfect_matches += perfect

    print("\n" + "=" * 80)
    print(f"Total Panels Compared: {grand_total_panels}")
    print(f"Mismatches:            {grand_total_mismatches}")
    print(f"Perfect Matches:       {grand_total_perfect_matches}")

    output_file = output or _default_output_file(volumes_str)
    _write_queue_file(all_mismatches, output_file)


if __name__ == "__main__":
    app()
