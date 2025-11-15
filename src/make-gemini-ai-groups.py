import json
import os.path
import sys
from pathlib import Path
from typing import List, Dict, Tuple

from PIL import Image
from loguru import logger
from loguru_config import LoguruConfig

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_no_json_suffix
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from utils.common import ProcessResult
from utils.gemini_ai import get_ai_predicted_groups
from utils.geometry import Rect
from utils.ocr_box import OcrBox, PointList, save_groups_as_json, load_groups_from_json, get_box_str
from utils.preprocessing import preprocess_image

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

APP_LOGGING_NAME = "gocr"


def make_gemini_ai_groups_for_titles(title_list: List[str], out_dir: Path) -> None:
    for title in title_list:
        make_gemini_ai_groups_for_title(title, out_dir)


def make_gemini_ai_groups_for_title(title: str, out_dir: Path) -> None:
    out_dir /= title

    logger.info(f'Making OCR groups for all pages in "{title}". To directory "{out_dir}"...')

    os.makedirs(out_dir, exist_ok=True)
    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)
    panel_segments_files = comic.get_srce_panel_segments_files(RESTORABLE_PAGE_TYPES)

    num_files_processed = 0
    for svg_file, ocr_file, panel_segments_file in zip(svg_files, ocr_files, panel_segments_files):
        svg_stem = Path(svg_file).stem

        for ocr_type_file in ocr_file:
            ocr_suffix = get_ocr_no_json_suffix(ocr_type_file)

            ocr_final_groups_json_file = get_ocr_final_groups_json_filename(
                svg_stem, ocr_suffix, out_dir
            )
            ocr_groups_json_file = get_ocr_groups_json_filename(svg_stem, ocr_suffix, out_dir)
            ocr_groups_txt_file = get_ocr_groups_txt_filename(svg_stem, ocr_suffix, out_dir)

            result = make_gemini_ai_groups(
                svg_file,
                ocr_type_file,
                panel_segments_file,
                ocr_final_groups_json_file,
                ocr_groups_json_file,
                ocr_groups_txt_file,
            )

            if result == ProcessResult.FAILURE:
                raise Exception("There were process errors.")
                # pass
            if result == ProcessResult.SUCCESS:
                num_files_processed += 1

        #break  # Break early for testing


def get_ocr_data(ocr_file: Path) -> List[Dict[str, any]]:
    with ocr_file.open("r") as f:
        ocr_raw_results = json.load(f)

    ocr_data = []
    for result in ocr_raw_results:
        box = result[0]
        ocr_text = result[1]
        accepted_text = result[2]
        ocr_prob = result[3]

        assert len(box) == 8
        text_box = [(box[0], box[1]), (box[2], box[3]), (box[4], box[5]), (box[6], box[7])]

        ocr_data.append({"text_box": text_box, "text": accepted_text, "prob": ocr_prob})

    return ocr_data


def assign_ids_to_ocr_boxes(bounds: List[Dict[str, any]]) -> List[Dict[str, any]]:
    return [{**bound, "text_id": str(i)} for i, bound in enumerate(bounds)]


def get_ocr_groups_txt_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-gemini-groups{ocr_suffix}.txt")


def get_ocr_groups_json_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-gemini-groups{ocr_suffix}.json")


def get_ocr_final_groups_json_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-gemini-final-groups{ocr_suffix}.json")


def make_gemini_ai_groups(
    svg_file: Path,
    ocr_file: Path,
    panel_segments_file: Path,
    ocr_final_data_groups_json_file,
    ocr_groups_json_file: Path,
    ocr_groups_txt_file: Path,
) -> ProcessResult:
    image_name = Path(svg_file).stem
    png_file = Path(str(svg_file) + ".png")

    if not os.path.isfile(png_file):
        logger.error(f'Could not find png file "{png_file}".')
        return ProcessResult.FAILURE
    if not os.path.isfile(ocr_file):
        logger.error(f'Could not find ocr file "{ocr_file}".')
        return ProcessResult.FAILURE

    if os.path.isfile(ocr_groups_json_file):
        logger.info(f'Found groups file - skipping: "{ocr_groups_json_file}".')
        return ProcessResult.SKIPPED

    logger.info(f'Making Gemini AI OCR groups for file "{get_abbrev_path(png_file)}"...')
    logger.info(f'Using OCR file "{get_abbrev_path(ocr_file)}"...')

    ocr_data = get_ocr_data(ocr_file)
    ocr_bound_ids = assign_ids_to_ocr_boxes(ocr_data)

    bw_image = get_bw_image_from_alpha(png_file)
    bw_image = preprocess_image(bw_image)

    ai_predicted_groups = get_ai_predicted_groups(
        Image.fromarray(bw_image), ocr_bound_ids, GEMINI_API_KEY
    )
    with (Path("/tmp") / f"{image_name}-ocr-ai-groups-prelim.json").open("w") as f:
        json.dump(ai_predicted_groups, f, indent=4)

    # Merge boxes into text bubbles
    ai_final_data = get_final_ai_data(ai_predicted_groups, ocr_bound_ids, panel_segments_file)
    with ocr_final_data_groups_json_file.open("w") as f:
        json.dump(ai_final_data, f, indent=4)

    groups = get_text_groups(ai_final_data, ocr_bound_ids)

    save_groups_as_json(groups, ocr_groups_json_file)
    groups = load_groups_from_json(ocr_groups_json_file)

    write_groups_to_text_file(ocr_groups_txt_file, groups)

    return ProcessResult.SUCCESS


def get_final_ai_data(
    groups: Dict[str, any], ocr_boxes_with_ids: List[Dict[str, any]], panel_segments_file: Path
) -> Dict[int, any]:
    id_to_bound: Dict[str, PointList] = {bound["text_id"]: bound for bound in ocr_boxes_with_ids}

    logger.info(f'Loading panel segments file "{get_abbrev_path(panel_segments_file)}".')
    with panel_segments_file.open("r") as f:
        panel_segment_info = json.load(f)

    group_id = 0  # TODO: start from 1
    merged_groups = {}
    for group in groups["groups"]:
        box_ids = group["box_ids"]
        cleaned_box_texts = group["split_cleaned_box_texts"]

        box_bounds: List[PointList] = []
        box_texts = {}
        for box_id in box_ids:
            box = id_to_bound[box_id]["text_box"]
            box_bounds.append(box)

            cleaned_box_text = cleaned_box_texts[box_id]
            box_texts[box_id] = {"text_frag": cleaned_box_text, "text_box": box}

        assert box_bounds
        # print(f"{group_id}: box - {box_bounds}")

        enclosing_box = get_enclosing_box(box_bounds)
        panel_num = get_enclosing_panel_num(enclosing_box, panel_segment_info)

        merged_groups[group_id] = {
            "panel_id": group["panel_id"],
            "panel_num": panel_num,
            "text_box": enclosing_box,
            "ocr_text": group["original_text"],
            "ai_text": group["cleaned_text"],
            "type": group["type"],
            "style": group["style"],
            "notes": group["notes"],
            "cleaned_box_texts": box_texts,
        }

        group_id += 1

    return merged_groups


def get_enclosing_box(boxes: List[PointList]) -> PointList:
    x_min = min(box[0][0] for box in boxes)
    y_min = min(box[1][1] for box in boxes)
    x_max = max(box[2][0] for box in boxes)
    y_max = max(box[3][1] for box in boxes)

    return [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]


def get_enclosing_panel_num(box: PointList, panel_segment_info) -> int:
    ocr_box = OcrBox(box, "", 0, "")
    box = ocr_box.min_rotated_rectangle
    bottom_left = box[0]
    top_right = box[1]
    box_rect = Rect(
        bottom_left[0], bottom_left[1], top_right[0] - bottom_left[0], top_right[1] - bottom_left[1]
    )

    for i, panel_box in enumerate(panel_segment_info["panels"]):
        top_left_x = panel_box[0]
        top_left_y = panel_box[1]
        w = panel_box[2]
        h = panel_box[3]
        print(panel_box, top_left_x, top_left_y, w, h)
        panel_rect = Rect(top_left_x, top_left_y, w, h)
        if panel_rect.is_rect_inside_rect(box_rect):
            return i + 1

    return -1


def get_text_groups(
    ocr_merged_data: Dict[int, any], ocr_bound_ids: List[Dict[str, any]]
) -> Dict[int, List[Tuple[any, float]]]:
    groups = {}

    for group_id in ocr_merged_data:
        dist = 0.0

        group_id = int(group_id)
        ocr_data = ocr_merged_data[group_id]
        group = []
        for text_id in ocr_data["cleaned_box_texts"]:
            cleaned_text_data = ocr_data["cleaned_box_texts"][text_id]
            text_data = {
                "box_id": text_id,
                "box_points": cleaned_text_data["text_box"],
                "ocr_text": ocr_bound_ids[int(text_id)]["text"],
                "ocr_prob": ocr_bound_ids[int(text_id)]["prob"],
                "accepted_text": cleaned_text_data["text_frag"].upper(),
            }
            group.append((text_data, dist))

        groups[group_id] = group

    return groups


def write_groups_to_text_file(file: Path, groups: Dict[int, any]) -> None:
    max_text_len = 0
    max_acc_text_len = 0
    for group in groups:
        for ocr_box, dist in groups[group]:
            max_text_len = max(max_text_len, len(ocr_box.ocr_text))
            max_acc_text_len = max(max_acc_text_len, len(ocr_box.accepted_text))

    with file.open("w") as f:
        for group in groups:
            for ocr_box, dist in groups[group]:
                f.write(
                    f"Group: {group:03d}, "
                    f"text: '{ocr_box.ocr_text:<{max_text_len}}', "
                    f"acc: '{ocr_box.accepted_text:<{max_acc_text_len}}', "
                    f"P: {ocr_box.ocr_prob:4.2f}, "
                    f"box: {get_box_str(ocr_box._box_points)}, rect: {ocr_box.is_approx_rect}\n"
                )


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title",
        CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR,
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "batch-ocr.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    make_gemini_ai_groups_for_titles(cmd_args.get_titles(), cmd_args.get_work_dir())
