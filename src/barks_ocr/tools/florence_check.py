# ruff: noqa: T201
"""Spot-check cleaned OCR text against speech-bubble images using Florence-2.

For each speech bubble in a title, crops the bubble from the restored page PNG,
runs Florence-2 OCR on the crop, and prints a fuzzy-string similarity score
against the cleaned ``raw_ai_text``.  Intended as a quick final-stage validator
on top of the EasyOCR/PaddleOCR + Gemini cleanup pipeline.

Florence-2 is loaded on demand and is NOT a hard dependency.  Install with:

    uv pip install transformers torch einops timm
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2 as cv
import typer
from barks_fantagraphics.comic_book import ComicBook
from barks_fantagraphics.comic_book_info import BARKS_TITLE_DICT
from barks_fantagraphics.comics_consts import PNG_FILE_EXT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from comic_utils.common_typer_options import TitleArg, VolumesArg
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from intspan import intspan
from PIL import Image
from thefuzz import fuzz

app = typer.Typer()

DEFAULT_MODEL = "microsoft/Florence-2-large"
_OCR_TASK = "<OCR>"
_DEFAULT_PAD_PX = 10
_MIN_CROP_PX = 5


@dataclass(frozen=True, slots=True)
class _Result:
    fanta_page: str
    panel_num: int
    group_id: str
    cleaned: str
    florence: str
    score: int


def _load_florence(model_id: str) -> tuple[Any, Any, str, Any]:
    """Load a Florence-2 model + processor.

    Args:
        model_id: HuggingFace model id, e.g. ``microsoft/Florence-2-large``.

    Returns:
        ``(model, processor, device, dtype)``.

    """
    try:
        import torch  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415  # ty: ignore[unresolved-import]
            AutoModelForCausalLM,
            AutoProcessor,
        )
    except ImportError as exc:
        msg = (
            "Florence-2 needs transformers/torch/einops/timm.\n"
            "  Install: uv pip install transformers torch einops timm"
        )
        raise typer.BadParameter(msg) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f'Loading "{model_id}" on {device}...')
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype=dtype
    ).to(device)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    return model, processor, device, dtype


def _florence_ocr(
    image: Image.Image,
    model: Any,  # noqa: ANN401
    processor: Any,  # noqa: ANN401
    device: str,
    dtype: Any,  # noqa: ANN401
) -> str:
    """Run Florence-2 OCR on a single PIL image and return the recognized text."""
    inputs = processor(text=_OCR_TASK, images=image, return_tensors="pt").to(device, dtype)
    ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        num_beams=3,
    )
    raw = processor.batch_decode(ids, skip_special_tokens=False)[0]
    parsed = processor.post_process_generation(raw, task=_OCR_TASK, image_size=image.size)
    return parsed[_OCR_TASK]


def _bbox_from_polygon(
    polygon: list[tuple[int | float, int | float]],
    pad: int,
    image_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Axis-aligned bbox of ``polygon``, padded by ``pad`` and clipped to ``image_size``."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    x0 = max(0, int(min(xs)) - pad)
    y0 = max(0, int(min(ys)) - pad)
    x1 = min(image_size[0], int(max(xs)) + pad)
    y1 = min(image_size[1], int(max(ys)) + pad)
    return x0, y0, x1, y1


def _normalize(s: str) -> str:
    """Uppercase and collapse whitespace runs so single-line/multi-line both compare fairly."""
    return " ".join(s.upper().split())


def _load_page_image(comic: ComicBook, fanta_page: str) -> Image.Image:
    """Load the restored-page PNG that the OCR engines saw (RGB PIL image)."""
    svg_file = comic.get_srce_restored_svg_story_file(fanta_page)
    png_file = Path(str(svg_file) + PNG_FILE_EXT)
    if not png_file.is_file():
        msg = f'Page PNG not found: "{png_file}".'
        raise FileNotFoundError(msg)
    bw = get_bw_image_from_alpha(png_file)
    return Image.fromarray(cv.merge([bw, bw, bw])).convert("RGB")


def _print_result(r: _Result, threshold: int) -> None:
    flag = "  " if r.score >= threshold else "!!"
    print(
        f"{flag} page {r.fanta_page:>4}  panel {r.panel_num:>2}  group {r.group_id:>3}"
        f"  sim={r.score:>3}"
    )
    if r.score < threshold:
        print(f"     cleaned : {r.cleaned!r}")
        print(f"     florence: {r.florence!r}")


def _process_title(  # noqa: C901, PLR0913
    comics_database: ComicsDatabase,
    title_str: str,
    engine: OcrTypes,
    florence: tuple[Any, Any, str, Any],
    threshold: int,
    limit: int,
    pad: int,
    save_crops_dir: Path | None,
) -> tuple[int, int]:
    """Validate all bubbles for one title.  Returns (checked, flagged)."""
    title = BARKS_TITLE_DICT[title_str]
    speech_groups = SpeechGroups(comics_database)
    speech_page_groups = speech_groups.get_speech_page_groups(title)
    comic = comics_database.get_comic_book(title_str)

    model, processor, device, dtype = florence

    checked = 0
    flagged = 0

    for page_group in speech_page_groups:
        if page_group.ocr_index != engine:
            continue

        try:
            page_image = _load_page_image(comic, page_group.fanta_page)
        except FileNotFoundError as exc:
            print(f"  Skip page {page_group.fanta_page}: {exc}")
            continue

        for speech_text in page_group.speech_groups.values():
            if speech_text.panel_num == -1:
                continue
            if not speech_text.raw_ai_text.strip():
                continue
            if not speech_text.text_box:
                continue

            bbox = _bbox_from_polygon(speech_text.text_box, pad, page_image.size)
            crop = page_image.crop(bbox)
            if crop.width < _MIN_CROP_PX or crop.height < _MIN_CROP_PX:
                continue

            if save_crops_dir is not None:
                save_crops_dir.mkdir(parents=True, exist_ok=True)
                safe_title = title_str.replace("/", "_")
                crop_path = save_crops_dir / (
                    f"{safe_title}_p{page_group.fanta_page}"
                    f"_panel{speech_text.panel_num}_g{speech_text.group_id}.png"
                )
                crop.save(crop_path)

            florence_text = _florence_ocr(crop, model, processor, device, dtype)
            score = fuzz.ratio(_normalize(speech_text.raw_ai_text), _normalize(florence_text))

            result = _Result(
                fanta_page=page_group.fanta_page,
                panel_num=speech_text.panel_num,
                group_id=speech_text.group_id,
                cleaned=speech_text.raw_ai_text,
                florence=florence_text,
                score=score,
            )
            _print_result(result, threshold)

            checked += 1
            if score < threshold:
                flagged += 1
            if limit and checked >= limit:
                return checked, flagged

    return checked, flagged


@app.command(help="Spot-check cleaned OCR text against bubble images using Florence-2.")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    engine: OcrTypes = typer.Option(  # noqa: B008
        OcrTypes.EASYOCR, "--engine", "-e", help="Which cleaned OCR pass to validate."
    ),
    model_id: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        "-m",
        help="Florence-2 model id (use microsoft/Florence-2-base for a faster smaller run).",
    ),
    threshold: int = typer.Option(
        85, "--threshold", "-t", help="Flag bubbles below this similarity score (0-100)."
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Stop after this many bubbles per title (0 = no limit)."
    ),
    pad: int = typer.Option(
        _DEFAULT_PAD_PX, "--pad", help="Padding (px) around each bubble bbox before cropping."
    ),
    save_crops_dir: Path | None = typer.Option(  # noqa: B008
        None,
        "--save-crops",
        help="If set, save each cropped bubble PNG here (for manual inspection).",
    ),
) -> None:
    """Run Florence-2 validation across one or more titles."""
    if volumes_str and title_str:
        msg = "Options --volumes and --title are mutually exclusive."
        raise typer.BadParameter(msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    florence = _load_florence(model_id)

    grand_checked = 0
    grand_flagged = 0
    for title_name in title_list:
        print("=" * 80)
        print(f"Validating {title_name} ({engine.value})...")
        checked, flagged = _process_title(
            comics_database,
            title_name,
            engine,
            florence,
            threshold,
            limit,
            pad,
            save_crops_dir,
        )
        grand_checked += checked
        grand_flagged += flagged
        print(f"  {checked} bubbles checked, {flagged} below threshold {threshold}.")

    print("\n" + "=" * 80)
    print(f"Total: {grand_checked} bubbles, {grand_flagged} flagged below {threshold}.")


if __name__ == "__main__":
    app()
