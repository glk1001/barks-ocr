# ruff: noqa: T201
"""Spot-check cleaned OCR text against speech-bubble images using Florence-2.

For each speech bubble in a title, crops the bubble from the restored page PNG,
runs Florence-2 OCR on the crop, and prints a fuzzy-string similarity score
against the cleaned ``raw_ai_text``.  Intended as a quick final-stage validator
on top of the EasyOCR/PaddleOCR + Gemini cleanup pipeline.

Florence-2 is loaded on demand and is NOT a hard dependency.  Install with:

    uv pip install transformers torch einops timm
"""

import math
import multiprocessing as mp
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
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
from comic_utils.cv_image_utils import get_bw_image_from_alpha, validate_page_bw_image
from intspan import intspan
from PIL import Image
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from thefuzz import fuzz

from barks_ocr.utils.group_checks import is_acknowledged

app = typer.Typer()
_console = Console()

DEFAULT_MODEL = "microsoft/Florence-2-large"
_OCR_TASK = "<OCR>"
_OCR_REGION_TASK = "<OCR_WITH_REGION>"
_DEFAULT_PAD_PX = 10
_MIN_CROP_PX = 5
_FLORENCE_CHECK_ISSUE = "florence-check"
_FLORENCE_PASSED_KEY = "florence_passed"
_SCORE_SKIPPED = -1
_DEFAULT_CACHE_THRESHOLD = 100
_SOUND_EFFECT_TYPE = "sound_effect"
# Florence-2 reads horizontal text fine but fails on rotated text. Sound effects
# are routinely drawn vertically, upside-down, etc. — try each axis-aligned
# rotation and keep whichever gives the best match.
_SFX_ROTATIONS = (0, 90, 180, 270)
# Don't bother deskewing for tiny angles — the original orientation already
# covers it via the rot=0 candidate, and a few degrees rarely changes Florence's
# output enough to matter.
_DESKEW_MIN_ANGLE = 5.0
# Fill colour for the rotated crop's corners when deskewing at arbitrary angles.
# Pages are loaded as black-on-white BW; white avoids a black triangle that would
# confuse Florence's text detector.
_DESKEW_FILL = (255, 255, 255)


@dataclass(frozen=True, slots=True)
class _Result:
    fanta_page: str
    panel_num: int
    group_id: str
    cleaned: str
    florence: str
    score: int
    cached: bool = False
    rotation: int = 0


def _load_florence(model_id: str, *, quantize: bool = True) -> tuple[Any, Any, str, Any]:
    """Load a Florence-2 model + processor.

    Args:
        model_id: HuggingFace model id, e.g. ``microsoft/Florence-2-large``.
        quantize: If True and running on CPU, apply int8 dynamic quantization to
            ``nn.Linear`` layers — typically ~2x faster with small accuracy loss.

    Returns:
        ``(model, processor, device, dtype)``.

    """
    try:
        import torch  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
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
    # `.to(device)` is the documented HF pattern; ty picks the wrong overload from
    # `from_pretrained`'s union return type and complains the str isn't a model.
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=dtype,
        attn_implementation="eager",
    ).to(device)  # ty: ignore[invalid-argument-type]
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

    if device == "cpu" and quantize:
        # Dynamic int8 quantization of all nn.Linear layers — typically ~2x faster
        # on CPU at the cost of small accuracy loss.  Acceptable here because this
        # script is a sanity-check validator, not the source-of-truth OCR.  Disable
        # with --no-quantize when you need maximum recognition quality.  The
        # torch.ao.quantization API is deprecated in favour of torchao; migration
        # is tracked separately and not blocking here.
        from torch.ao.quantization import (  # noqa: PLC0415
            quantize_dynamic,  # ty: ignore[deprecated]
        )

        print("Applying int8 dynamic quantization (CPU)...")
        model = quantize_dynamic(  # ty: ignore[deprecated]
            model, {torch.nn.Linear}, dtype=torch.qint8
        )

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
        max_new_tokens=128,
        num_beams=1,
        # Florence-2's shipped generation_config sets early_stopping=True (for its
        # default num_beams=3); override here so transformers doesn't warn that it's
        # being ignored under greedy decode.
        early_stopping=False,
        # Must stay False: Florence-2's custom prepare_inputs_for_generation indexes
        # past_key_values as a tuple-of-tuples (past_key_values[0][0].shape[2]), but
        # newer transformers pass a DynamicCache object, so use_cache=True raises
        # AttributeError: 'NoneType' object has no attribute 'shape'. Re-enable only
        # if Microsoft updates the Florence-2 modeling code on HF Hub.
        use_cache=False,
    )
    raw = processor.batch_decode(ids, skip_special_tokens=False)[0]
    parsed = processor.post_process_generation(raw, task=_OCR_TASK, image_size=image.size)
    return parsed[_OCR_TASK]


def _longest_edge_angle(quad: list[float]) -> tuple[float, float]:
    """Return ``(angle_deg, length_px)`` of the longest edge of an 8-float quad.

    The angle is computed via ``atan2(dy, dx)`` in PIL image coordinates (y-down),
    which is also the convention PIL.Image.rotate uses (positive = CCW as viewed).
    Normalized to ``[-90, 90]`` so that a 180°-flipped edge collapses onto its
    twin — the axis-aligned rotation sweep already handles the 180° case.
    """
    pts = [(quad[i], quad[i + 1]) for i in range(0, 8, 2)]
    best_len = -1.0
    best_angle = 0.0
    for i in range(4):
        p1 = pts[i]
        p2 = pts[(i + 1) % 4]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length > best_len:
            best_len = length
            best_angle = math.degrees(math.atan2(dy, dx))
    while best_angle > 90:  # noqa: PLR2004
        best_angle -= 180
    while best_angle < -90:  # noqa: PLR2004
        best_angle += 180
    return best_angle, best_len


def _florence_ocr_with_region(
    image: Image.Image,
    model: Any,  # noqa: ANN401
    processor: Any,  # noqa: ANN401
    device: str,
    dtype: Any,  # noqa: ANN401
) -> tuple[str, float | None]:
    """Run Florence's ``<OCR_WITH_REGION>`` task on ``image``.

    Returns ``(joined_label_text, dominant_angle_deg_or_None)``.  The angle is
    derived from the longest edge of the largest detected text quad — for
    rotated sound-effect text that's the text baseline.  Returns ``None`` for
    the angle if Florence failed to localize any text.
    """
    inputs = processor(text=_OCR_REGION_TASK, images=image, return_tensors="pt").to(device, dtype)
    ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=256,
        num_beams=1,
        early_stopping=False,
        use_cache=False,
    )
    raw = processor.batch_decode(ids, skip_special_tokens=False)[0]
    parsed = processor.post_process_generation(raw, task=_OCR_REGION_TASK, image_size=image.size)
    result = parsed.get(_OCR_REGION_TASK, {}) or {}
    quad_boxes = result.get("quad_boxes") or []
    labels = result.get("labels") or []
    joined = " ".join(str(label) for label in labels)
    if not quad_boxes:
        return joined, None
    best_angle = 0.0
    best_length = -1.0
    for quad in quad_boxes:
        quad_list = list(quad)
        if len(quad_list) < 8:  # noqa: PLR2004
            continue
        angle, length = _longest_edge_angle(quad_list)
        if length > best_length:
            best_length = length
            best_angle = angle
    return joined, best_angle if best_length > 0 else None


def _florence_ocr_best_rotation(  # noqa: PLR0913
    image: Image.Image,
    cleaned_normalized: str,
    model: Any,  # noqa: ANN401
    processor: Any,  # noqa: ANN401
    device: str,
    dtype: Any,  # noqa: ANN401
) -> tuple[str, int, int]:
    """Run Florence-2 OCR across multiple orientations, return the best match.

    Tries: each of ``_SFX_ROTATIONS`` (axis-aligned), the joined text from
    ``<OCR_WITH_REGION>`` on the original crop, and — if region detection finds
    a tilted text baseline — a deskewed re-OCR at that angle.

    Returns ``(best_text, best_score, best_rotation_deg)``; ``best_rotation_deg``
    is an int (rounded) — 0 means the unrotated candidate (or region-task text)
    won.  ``cleaned_normalized`` is the pre-normalized cleaned text to score
    against (avoids re-normalizing on each candidate).
    """
    candidates: list[tuple[str, int, int]] = []

    for rot in _SFX_ROTATIONS:
        rotated = image if rot == 0 else image.rotate(rot, expand=True)
        text = _florence_ocr(rotated, model, processor, device, dtype)
        score = fuzz.ratio(cleaned_normalized, _normalize(text))
        candidates.append((text, score, rot))

    region_text, angle = _florence_ocr_with_region(image, model, processor, device, dtype)
    if region_text:
        region_score = fuzz.ratio(cleaned_normalized, _normalize(region_text))
        candidates.append((region_text, region_score, 0))

    if angle is not None and abs(angle) >= _DESKEW_MIN_ANGLE:
        deskewed = image.rotate(angle, expand=True, fillcolor=_DESKEW_FILL)
        deskew_text = _florence_ocr(deskewed, model, processor, device, dtype)
        deskew_score = fuzz.ratio(cleaned_normalized, _normalize(deskew_text))
        candidates.append((deskew_text, deskew_score, round(angle)))

    return max(candidates, key=lambda c: c[1])


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
    """Uppercase and strip all whitespace.

    Florence-2 frequently drops newlines without inserting a space and occasionally adds
    stray spaces before punctuation, so any whitespace-preserving compare understates
    agreement.  Stripping whitespace on both sides isolates true character-level errors.
    """
    return "".join(s.upper().split())


def _load_page_image(comic: ComicBook, fanta_page: str) -> Image.Image:
    """Load the restored-page PNG that the OCR engines saw (RGB PIL image)."""
    svg_file = comic.get_srce_restored_svg_story_file(fanta_page)
    png_file = Path(str(svg_file) + PNG_FILE_EXT)
    if not png_file.is_file():
        msg = f'Page PNG not found: "{png_file}".'
        raise FileNotFoundError(msg)
    bw = get_bw_image_from_alpha(png_file)
    validate_page_bw_image(bw, png_file)
    return Image.fromarray(cv.merge([bw, bw, bw])).convert("RGB")


def _row_style(result: "_Result", threshold: int) -> tuple[str, str]:
    """Return ``(flag glyph, rich style)`` for a result row.

    ``score < 0`` means the bubble was skipped (florence-check acknowledged on
    the group); render dim with a distinct glyph so the row is clearly noise.
    Cached rows (florence_passed hit) get their own glyph so the user can tell
    "florence said 100" apart from "we trusted the cache from a prior run".
    """
    score = result.score
    if score < 0:
        return "-", "dim"
    if result.cached:
        return "=", "cyan"
    if score >= 95:  # noqa: PLR2004
        return "✓", "green"
    if score >= threshold:
        return "·", "yellow"
    return "✗", "bold red"


def _diff_pair(cleaned_stripped: str, florence_stripped: str) -> tuple[Text, Text]:
    """Build (cleaned, florence) ``Text`` objects with mismatching ranges highlighted.

    Matching is case-insensitive so case-only differences (e.g. ``of`` vs ``OF``) are
    not highlighted; the score uses the same comparison.  Both sides are still
    rendered in their original case so case mismatches remain visible to the eye.
    """
    matcher = SequenceMatcher(
        None, cleaned_stripped.upper(), florence_stripped.upper(), autojunk=False
    )
    c_text = Text()
    f_text = Text()
    diff_style = "white on red"
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        c_chunk = cleaned_stripped[i1:i2]
        f_chunk = florence_stripped[j1:j2]
        if tag == "equal":
            c_text.append(c_chunk)
            f_text.append(f_chunk)
        else:
            if c_chunk:
                c_text.append(c_chunk, style=diff_style)
            if f_chunk:
                f_text.append(f_chunk, style=diff_style)
    return c_text, f_text


def _new_results_table(title: str) -> Table:
    """Build an empty results table sized to content (no width truncation)."""
    table = Table(
        title=title,
        title_justify="left",
        title_style="bold cyan",
        box=box.SIMPLE_HEAD,
        header_style="bold",
        expand=False,
        pad_edge=False,
    )
    table.add_column("", width=1, no_wrap=True)
    table.add_column("Page", justify="right", style="dim", no_wrap=True)
    table.add_column("Pn", justify="right", style="dim", no_wrap=True)
    table.add_column("Grp", justify="right", style="dim", no_wrap=True)
    table.add_column("Sim", justify="right", no_wrap=True)
    table.add_column("Cleaned", overflow="fold")
    table.add_column("Compare (whitespace stripped)", overflow="fold")
    return table


def _add_result_row(table: Table, r: _Result, threshold: int) -> None:
    """Add one bubble result to ``table`` with a diff-highlighted compare cell."""
    flag, style = _row_style(r, threshold)

    c_stripped = "".join(r.cleaned.split())
    score_text = "skip" if r.score < 0 else str(r.score)

    if r.score < 0:
        compare = Text("(florence-check acknowledged)", style="dim")
    elif r.cached:
        compare = Text(f"(cached pass, prior score={r.score})", style="dim")
    else:
        f_stripped = "".join(r.florence.split())
        c_marked, f_marked = _diff_pair(c_stripped, f_stripped)
        f_label = f"F (rot={r.rotation}°): " if r.rotation else "F: "
        compare = Text()
        compare.append("C: ", style="dim")
        compare.append(c_marked)
        compare.append(f"\n{f_label}", style="dim")
        compare.append(f_marked)

    table.add_row(
        Text(flag, style=style),
        r.fanta_page,
        str(r.panel_num),
        r.group_id,
        Text(score_text, style=style),
        Text(r.cleaned),
        compare,
    )


def _print_progress(r: _Result, threshold: int, elapsed: float) -> None:
    """Print a one-line status as each bubble finishes so the user sees progress."""
    flag, style = _row_style(r, threshold)
    sim_text = "skip" if r.score < 0 else f"{r.score:>3}"
    rot_text = f"  [dim]rot={r.rotation}°[/]" if r.rotation else ""
    _console.print(
        f"  [{style}]{flag}[/] page {r.fanta_page}  "
        f"panel {r.panel_num:>2}  group {r.group_id:>3}  "
        f"[{style}]sim={sim_text}[/]{rot_text}  [dim]{elapsed:.1f}s[/]"
    )


# Worker-process globals: each worker loads its own model + DB once via the pool
# initializer, then reuses them across every title that worker processes.  These
# are intentionally module-level so they survive across imap_unordered calls.
_WORKER_FLORENCE: tuple[Any, Any, str, Any] | None = None
_WORKER_DB: ComicsDatabase | None = None


def _worker_init(model_id: str, quantize: bool) -> None:
    """Pool initializer — load the model and DB once per worker process."""
    global _WORKER_FLORENCE, _WORKER_DB  # noqa: PLW0603
    _WORKER_FLORENCE = _load_florence(model_id, quantize=quantize)
    _WORKER_DB = ComicsDatabase()


def _worker_run(
    args: tuple[str, OcrTypes, int, int, int, Path | None, int, bool],
) -> tuple[int, int, float, list[str]]:
    """Process one title in a worker using the worker-local model and DB."""
    (
        title_name,
        engine,
        threshold,
        limit,
        pad,
        save_crops_dir,
        cache_threshold,
        ignore_cache,
    ) = args
    assert _WORKER_FLORENCE is not None
    assert _WORKER_DB is not None
    _console.rule(f"Validating {title_name} ({engine.value})", style="bold cyan")
    checked, flagged, florence_seconds, queue_lines = _process_title(
        _WORKER_DB,
        title_name,
        engine,
        _WORKER_FLORENCE,
        threshold,
        limit,
        pad,
        save_crops_dir,
        cache_threshold,
        ignore_cache,
    )
    _console.print(
        f"  {checked} bubbles checked, [bold red]{flagged}[/] below threshold {threshold}.\n"
    )
    return checked, flagged, florence_seconds, queue_lines


def _process_title(  # noqa: C901, PLR0913, PLR0912, PLR0915
    comics_database: ComicsDatabase,
    title_str: str,
    engine: OcrTypes,
    florence: tuple[Any, Any, str, Any],
    threshold: int,
    limit: int,
    pad: int,
    save_crops_dir: Path | None,
    cache_threshold: int,
    ignore_cache: bool,
) -> tuple[int, int, float, list[str]]:
    """Validate all bubbles for one title.

    Returns ``(checked, flagged, florence_seconds, queue_lines)`` where
    ``florence_seconds`` is the total time spent inside ``_florence_ocr`` for
    this title and ``queue_lines`` are kivy-editor queue entries for bubbles
    flagged below ``threshold`` (each: ``volume page engine group_id florence-check``).
    """
    title = BARKS_TITLE_DICT[title_str]
    speech_groups = SpeechGroups(comics_database)
    speech_page_groups = speech_groups.get_speech_page_groups(title)
    comic = comics_database.get_comic_book(title_str)

    model, processor, device, dtype = florence

    checked = 0
    flagged = 0
    florence_seconds = 0.0
    results: list[_Result] = []
    queue_lines: list[str] = []

    try:
        for page_group in speech_page_groups:
            if page_group.ocr_index != engine:
                continue

            try:
                page_image = _load_page_image(comic, page_group.fanta_page)
            except FileNotFoundError as exc:
                _console.print(f"  [yellow]Skip page {page_group.fanta_page}: {exc}[/]")
                continue

            json_groups = page_group.speech_page_json.get("groups", {})
            page_dirty = False

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

                group_dict = json_groups.get(speech_text.group_id) or {}
                if is_acknowledged(group_dict, _FLORENCE_CHECK_ISSUE):
                    skipped_result = _Result(
                        fanta_page=page_group.fanta_page,
                        panel_num=speech_text.panel_num,
                        group_id=speech_text.group_id,
                        cleaned=speech_text.raw_ai_text,
                        florence="",
                        score=_SCORE_SKIPPED,
                    )
                    results.append(skipped_result)
                    _print_progress(skipped_result, threshold, 0.0)
                    continue

                if not ignore_cache and _is_cache_hit(
                    group_dict, speech_text.raw_ai_text, threshold
                ):
                    cached_score = int(group_dict[_FLORENCE_PASSED_KEY]["score"])
                    cached_result = _Result(
                        fanta_page=page_group.fanta_page,
                        panel_num=speech_text.panel_num,
                        group_id=speech_text.group_id,
                        cleaned=speech_text.raw_ai_text,
                        florence="",
                        score=cached_score,
                        cached=True,
                    )
                    results.append(cached_result)
                    _print_progress(cached_result, threshold, 0.0)
                    continue

                if save_crops_dir is not None:
                    save_crops_dir.mkdir(parents=True, exist_ok=True)
                    safe_title = title_str.replace("/", "_")
                    crop_path = save_crops_dir / (
                        f"{safe_title}_p{page_group.fanta_page}"
                        f"_panel{speech_text.panel_num}_g{speech_text.group_id}.png"
                    )
                    crop.save(crop_path)

                cleaned_normalized = _normalize(speech_text.raw_ai_text)
                t0 = time.perf_counter()
                if speech_text.type == _SOUND_EFFECT_TYPE:
                    florence_text, score, rotation = _florence_ocr_best_rotation(
                        crop, cleaned_normalized, model, processor, device, dtype
                    )
                else:
                    florence_text = _florence_ocr(crop, model, processor, device, dtype)
                    score = fuzz.ratio(cleaned_normalized, _normalize(florence_text))
                    rotation = 0
                elapsed = time.perf_counter() - t0
                florence_seconds += elapsed

                result = _Result(
                    fanta_page=page_group.fanta_page,
                    panel_num=speech_text.panel_num,
                    group_id=speech_text.group_id,
                    cleaned=speech_text.raw_ai_text,
                    florence=florence_text,
                    score=score,
                    rotation=rotation,
                )
                results.append(result)
                _print_progress(result, threshold, elapsed)

                checked += 1
                if score < threshold:
                    flagged += 1
                    line = _build_queue_line(page_group, engine, speech_text.group_id)
                    if line is not None:
                        queue_lines.append(line)

                if score >= cache_threshold and group_dict:
                    group_dict[_FLORENCE_PASSED_KEY] = {
                        "text": speech_text.raw_ai_text,
                        "score": score,
                    }
                    page_dirty = True

                if limit and checked >= limit:
                    if page_dirty:
                        page_group.save_json()
                    return checked, flagged, florence_seconds, queue_lines

            if page_dirty:
                page_group.save_json()
    finally:
        if results:
            table = _new_results_table(f"{title_str} ({engine.value})")
            for r in results:
                _add_result_row(table, r, threshold)
            _console.print()
            _console.print(table)

    return checked, flagged, florence_seconds, queue_lines


def _is_cache_hit(group_dict: dict, current_text: str, current_threshold: int) -> bool:
    """Return True if the group has a cached florence_passed entry valid for this run.

    Valid means the cached text matches the bubble's current ai_text AND the
    cached score meets the current run's flagging threshold.
    """
    cached = group_dict.get(_FLORENCE_PASSED_KEY)
    if not isinstance(cached, dict):
        return False
    try:
        return (
            cached.get("text") == current_text and int(cached.get("score", -1)) >= current_threshold
        )
    except (TypeError, ValueError):
        return False


def _write_queue_file(
    queue_out: Path, queue_lines: list[str], threshold: int, engine: OcrTypes
) -> None:
    """Write kivy-editor queue lines to ``queue_out`` (deduped, sorted)."""
    queue_out.parent.mkdir(parents=True, exist_ok=True)
    unique_lines = sorted(set(queue_lines))
    header = (
        f"# florence_check flagged bubbles (engine={engine.value}, threshold={threshold})\n"
        "# Format: volume page engine group_id florence-check\n"
    )
    queue_out.write_text(header + "\n".join(unique_lines) + ("\n" if unique_lines else ""))
    _console.print(
        f"[bold]Queue file:[/] {queue_out} ({len(unique_lines)} entr"
        f"{'y' if len(unique_lines) == 1 else 'ies'})."
    )


def _build_queue_line(
    page_group: Any,  # noqa: ANN401
    engine: OcrTypes,
    group_id: str,
) -> str | None:
    """Build a kivy-editor queue line, or None if the page/group can't be int-parsed."""
    try:
        page_int = int(page_group.fanta_page)
        gid_int = int(group_id)
    except (TypeError, ValueError):
        _console.print(
            f"  [yellow]Skip queue line for non-numeric page/group "
            f"{page_group.fanta_page!r}/{group_id!r}[/]"
        )
        return None
    return f"{page_group.fanta_vol} {page_int} {engine.value} {gid_int} {_FLORENCE_CHECK_ISSUE}"


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
    queue_out: Path | None = typer.Option(  # noqa: B008
        None,
        "--queue-out",
        help=(
            "If set, write a kivy-editor queue file here listing every bubble "
            "flagged below --threshold (format: 'volume page engine group_id "
            "florence-check'). Overwrites any existing file."
        ),
    ),
    cache_threshold: int = typer.Option(
        _DEFAULT_CACHE_THRESHOLD,
        "--cache-threshold",
        help=(
            "Minimum score to write a `florence_passed` cache entry on the group. "
            "Cached bubbles whose ai_text is unchanged and cached score >= --threshold "
            "are skipped on subsequent runs. Set to 101 to disable cache writes."
        ),
    ),
    ignore_cache: bool = typer.Option(
        False,  # noqa: FBT003
        "--ignore-cache",
        help="Bypass cached `florence_passed` entries and re-run florence on every bubble.",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help=(
            "Parallel worker processes (1 = no multiprocessing). "
            "Each worker loads its own model copy, so watch memory. "
            "Cap OMP_NUM_THREADS=physical_cores/workers to avoid BLAS contention."
        ),
    ),
    no_quantize: bool = typer.Option(
        False,  # noqa: FBT003
        "--no-quantize",
        help="Skip int8 dynamic quantization (slower but higher OCR quality).",
    ),
) -> None:
    """Run Florence-2 validation across one or more titles."""
    if volumes_str and title_str:
        msg = "Options --volumes and --title are mutually exclusive."
        raise typer.BadParameter(msg)
    if workers < 1:
        msg = "--workers must be >= 1."
        raise typer.BadParameter(msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    # No point spawning more workers than titles.
    effective_workers = min(workers, len(title_list)) if title_list else 1

    wall_start = time.perf_counter()
    grand_checked = 0
    grand_flagged = 0
    grand_florence_seconds = 0.0
    all_queue_lines: list[str] = []

    if effective_workers > 1:
        # Spawn (not fork) to avoid known torch+fork hazards.  Each worker loads
        # its own model via _worker_init, so total RAM is roughly N x model size.
        # Per-bubble progress lines from different workers will interleave on
        # the terminal — acceptable trade for the parallelism.
        ctx = mp.get_context("spawn")
        args_list = [
            (t, engine, threshold, limit, pad, save_crops_dir, cache_threshold, ignore_cache)
            for t in title_list
        ]
        with ctx.Pool(
            processes=effective_workers,
            initializer=_worker_init,
            initargs=(model_id, not no_quantize),
        ) as pool:
            for checked, flagged, florence_seconds, queue_lines in pool.imap_unordered(
                _worker_run, args_list
            ):
                grand_checked += checked
                grand_flagged += flagged
                grand_florence_seconds += florence_seconds
                all_queue_lines.extend(queue_lines)
    else:
        florence = _load_florence(model_id, quantize=not no_quantize)
        for title_name in title_list:
            _console.rule(f"Validating {title_name} ({engine.value})", style="bold cyan")
            checked, flagged, florence_seconds, queue_lines = _process_title(
                comics_database,
                title_name,
                engine,
                florence,
                threshold,
                limit,
                pad,
                save_crops_dir,
                cache_threshold,
                ignore_cache,
            )
            grand_checked += checked
            grand_flagged += flagged
            grand_florence_seconds += florence_seconds
            all_queue_lines.extend(queue_lines)
            _console.print(
                f"  {checked} bubbles checked, "
                f"[bold red]{flagged}[/] below threshold {threshold}.\n"
            )

    if queue_out is not None:
        _write_queue_file(queue_out, all_queue_lines, threshold, engine)

    wall_elapsed = time.perf_counter() - wall_start
    per_bubble = grand_florence_seconds / grand_checked if grand_checked else 0.0
    _console.rule(style="bold")
    _console.print(
        f"[bold]Total:[/] {grand_checked} bubbles, "
        f"[bold red]{grand_flagged}[/] flagged below {threshold}."
    )
    _console.print(
        f"[bold]Florence inference:[/] {grand_florence_seconds:.1f}s "
        f"(avg {per_bubble:.2f}s/bubble)."
    )
    parallelism = grand_florence_seconds / wall_elapsed if wall_elapsed else 0.0
    _console.print(
        f"[bold]Wall time:[/] {wall_elapsed:.1f}s  "
        f"[dim](parallelism {parallelism:.2f}x across {effective_workers} worker(s))[/]"
    )


if __name__ == "__main__":
    app()
