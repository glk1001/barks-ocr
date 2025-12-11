import json
import sys
from pathlib import Path
from typing import Any

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_type, get_timestamp_str
from barks_fantagraphics.ocr_file_paths import (
    BATCH_JOBS_OUTPUT_DIR,
    UNPROCESSED_BATCH_JOBS_DIR,
    get_batch_details_file,
    get_batch_requests_file,
    get_ocr_predicted_groups_filename,
    get_ocr_prelim_groups_json_filename,
)
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image

from utils.gemini_ai import AI_PRO_MODEL, CLIENT
from utils.gemini_ai_comic_prompts import comic_prompt
from utils.gemini_ai_for_grouping import norm2ai
from utils.preprocessing import preprocess_image

APP_LOGGING_NAME = "gemb"


def make_gemini_ai_groups_for_titles_batch_job(title_list: list[str]) -> None:
    for title in title_list:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        make_gemini_ai_groups_for_title(title)


def make_gemini_ai_groups_for_title(title: str) -> None:  # noqa: PLR0915
    out_title_dir = UNPROCESSED_BATCH_JOBS_DIR / title
    volume_dirname = comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    title_prev_results_dir = BATCH_JOBS_OUTPUT_DIR / volume_dirname

    logger.info(f'Making OCR groups for all pages in "{title}". To directory "{out_title_dir}"...')

    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_raw_ocr_story_files(RESTORABLE_PAGE_TYPES)

    gemini_requests_data = []
    gemini_output_files = []
    num_files_processed = 0
    for svg_file, ocr_file in zip(svg_files, ocr_files, strict=True):
        svg_stem = Path(svg_file).stem

        for ocr_type_file in ocr_file:
            ocr_type = get_ocr_type(ocr_type_file)
            ocr_batch_results_filename = get_ocr_predicted_groups_filename(svg_stem, ocr_type)

            ocr_predicted_groups_json_file = title_prev_results_dir / ocr_batch_results_filename
            if ocr_predicted_groups_json_file.is_file():
                logger.info(
                    f'Found predicted groups file "{ocr_predicted_groups_json_file}" - skipping.'
                )
                continue

            ocr_prelim_groups_json_file = out_title_dir / get_ocr_prelim_groups_json_filename(
                svg_stem, ocr_type
            )
            if ocr_prelim_groups_json_file.is_file():
                logger.error(
                    f'Found prelim groups file - skipping: "{ocr_prelim_groups_json_file}".'
                )
                return

            result = get_gemini_ai_groups_request(svg_file, ocr_type_file)
            if result is not None:
                gemini_requests_data.append(result)
                gemini_output_files.append(ocr_batch_results_filename)
                num_files_processed += 1

    if num_files_processed == 0:
        logger.warning(f'No request to process for title "{title}".')
        return

    json_file_path = get_batch_requests_file(title)
    if json_file_path.is_file():
        json_backup_file_path = Path(str(json_file_path) + "_" + get_timestamp_str(json_file_path))
        logger.warning(
            f'Found JSONL file "{json_file_path}" - backing up to "{json_backup_file_path}".'
        )
        json_file_path.rename(json_backup_file_path)
    logger.info(f'Creating JSONL file: "{json_file_path}"...')
    with json_file_path.open("w") as f:
        f.writelines(json.dumps(req) + "\n" for req in gemini_requests_data)

    logger.info(f'Uploading JSONL file: "{json_file_path}"...')
    batch_input_file = CLIENT.files.upload(file=json_file_path)
    assert batch_input_file.name
    logger.info(f'Uploaded JSONL file: "{batch_input_file.name}".')

    logger.info("\nCreating batch job...")
    batch_job_from_file = CLIENT.batches.create(
        model=AI_PRO_MODEL,
        src=batch_input_file.name,
        config={
            "display_name": "ocr-grouping-batch-job",
        },
    )
    logger.info(f"Created batch job from file: {batch_job_from_file.name}")

    batch_details = {
        "batch_job_name": batch_job_from_file.name,
        "gemini_output_files": gemini_output_files,
    }
    batch_details_file = get_batch_details_file(title)
    if batch_details_file.is_file():
        batch_details_backup_file = Path(
            str(batch_details_file) + "_" + get_timestamp_str(batch_details_file)
        )
        logger.warning(
            f'Found existing details file "{batch_details_file}"'
            f' - backing up to "{batch_details_backup_file}".'
        )
        batch_details_file.rename(batch_details_backup_file)
    with batch_details_file.open("w") as f:
        json.dump(batch_details, f, indent=4)
    logger.info(
        f"You can download the results using the batch job details file: {batch_details_file.name}"
    )


def get_gemini_ai_groups_request(svg_file: Path, ocr_file: Path) -> dict | None:
    ocr_name = (Path(ocr_file).stem + Path(ocr_file.suffix).stem).replace(".", "-")
    png_file = Path(str(svg_file) + ".png")

    # noinspection PyBroadException
    try:
        if not png_file.is_file():
            logger.error(f'Could not find png file "{png_file}".')
            return None
        if not ocr_file.is_file():
            logger.error(f'Could not find ocr file "{ocr_file}".')
            return None

        logger.info(f'Making Gemini AI OCR groups for file "{get_abbrev_path(png_file)}"...')
        logger.info(f'Using OCR file "{get_abbrev_path(ocr_file)}"...')

        ocr_data = get_ocr_data(ocr_file)
        ocr_bound_ids = assign_ids_to_ocr_boxes(ocr_data)

        bw_image = get_bw_image_from_alpha(png_file)
        bw_image = preprocess_image(bw_image)
        bw_image_file = Path("/tmp/bw_image.png")  # noqa: S108
        bw_image = Image.fromarray(bw_image)
        width, height = bw_image.size
        Image.Image.save(bw_image, bw_image_file)

        return get_ai_predicted_groups_request(
            ocr_name, bw_image_file, width, height, ocr_bound_ids
        )

    except:  # noqa: E722
        logger.exception(f'Could not process file "{png_file}":')
        sys.exit(1)


def get_ai_predicted_groups_request(
    ocr_name: str, image_path: Path, width: int, height: int, ocr_results: list[dict[str, Any]]
) -> dict:
    # Make the data AI-friendly.
    norm_ocr_results = json.dumps(norm2ai(ocr_results, height, width))
    prompt = comic_prompt.format(norm_ocr_results)

    image_file = CLIENT.files.upload(file=str(image_path))

    key = f"request_{ocr_name}"
    image_file_data = {
        "file_uri": image_file.uri,
        "mime_type": image_file.mime_type,
    }
    parts = [
        {"text": prompt},
        {"file_data": image_file_data},
    ]
    generation_config = {"response_mime_type": "application/json"}

    return {
        "key": key,
        "request": {
            "contents": [{"parts": parts}],
            "generation_config": generation_config,
        },
    }


def get_ocr_data(ocr_file: Path) -> list[dict[str, Any]]:
    with ocr_file.open("r") as f:
        ocr_raw_results = json.load(f)

    ocr_data = []
    for result in ocr_raw_results:
        box = result[0]
        # noinspection PyUnusedLocal
        ocr_text = result[1]  # noqa: F841
        accepted_text = result[2]
        ocr_prob = result[3]

        assert len(box) == 8  # noqa: PLR2004
        text_box = [(box[0], box[1]), (box[2], box[3]), (box[4], box[5]), (box[6], box[7])]

        ocr_data.append({"text_box": text_box, "text": accepted_text, "prob": ocr_prob})

    return ocr_data


def assign_ids_to_ocr_boxes(bounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**bound, "text_id": str(i)} for i, bound in enumerate(bounds)]


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title",
        CmdArgNames.VOLUME | CmdArgNames.TITLE,
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

    make_gemini_ai_groups_for_titles_batch_job(cmd_args.get_titles())
