import json
import logging
import os.path
import sys
from pathlib import Path
from typing import List, Dict, Tuple

from PIL import Image

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_image_io import get_bw_image_from_alpha
from barks_fantagraphics.comics_utils import get_abbrev_path, setup_logging
from ocr.utils.gemini_ai import get_ai_predicted_groups
from ocr.utils.ocr_box import OcrBox, save_groups_as_json, load_groups_from_json, get_box_str
from ocr.utils.preprocessing import preprocess_image

# TODO - Hide this
GEMINI_API_KEY = "AIzaSyARdJ8qA8bVPNtahIe72rh3u_O5_sKm-PE"


def make_gemini_ai_groups_for_titles(titles: List[str], out_dir: str) -> None:
    for title in titles:
        make_gemini_ai_groups_for_title(title, out_dir)


def make_gemini_ai_groups_for_title(title: str, out_dir: str) -> None:
    out_dir = os.path.join(out_dir, title)

    logging.info(f'Making OCR groups for all pages in "{title}". To directory "{out_dir}"...')

    os.makedirs(out_dir, exist_ok=True)
    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

    for svg_file, ocr_file in zip(svg_files, ocr_files):
        text_box_groups_file = os.path.join(
            out_dir, Path(svg_file).stem + "-ocr-text-box-groups.txt"
        )
        text_box_groups_json_file = os.path.join(
            out_dir, Path(svg_file).stem + "-ocr-text-box-groups.json"
        )
        if not make_gemini_ai_groups(
            svg_file, ocr_file, text_box_groups_file, text_box_groups_json_file
        ):
            raise Exception("There were process errors.")

        break  # for testing


def make_gemini_ai_groups(
    svg_file: str,
    ocr_file: str,
    text_box_groups_file: str,
    text_box_groups_json_file: str,
) -> bool:
    png_file = svg_file + ".png"
    logging.info(f'Making Gemini AI OCR groups for file "{get_abbrev_path(png_file)}"...')

    if not os.path.isfile(png_file):
        logging.error(f'Could not find png file "{png_file}".')
        return False
    if not os.path.isfile(ocr_file):
        logging.error(f'Could not find ocr file "{ocr_file}".')
        return False

    if os.path.isfile(text_box_groups_json_file):
        logging.info(f'Found groups file - skipping: "{text_box_groups_json_file}".')
        return False

    ocr_data = get_ocr_data(ocr_file)
    ocr_bound_ids = assign_ids_to_ocr_boxes(ocr_data)

    bw_image = get_bw_image_from_alpha(png_file)
    bw_image = preprocess_image(bw_image)

    ai_predicted_groups = get_ai_predicted_groups(
        Image.fromarray(bw_image), ocr_bound_ids, GEMINI_API_KEY
    )
    with open(os.path.join("/tmp", f"ocr-ai-groups-prelim.json"), "w") as f:
        json.dump(ai_predicted_groups, f, indent=4)

    # Merge boxes into text bubbles
    ai_final_data = get_ai_final_data(ai_predicted_groups, ocr_bound_ids)
    with open(os.path.join("/tmp", f"ocr-ai-final-data.json"), "w") as f:
        json.dump(ai_final_data, f, indent=4)

    groups = get_text_groups(ai_final_data, ocr_bound_ids)

    save_groups_as_json(groups, text_box_groups_json_file)
    groups = load_groups_from_json(text_box_groups_json_file)

    write_groups_to_text_file(text_box_groups_file, groups)

    return True


def get_ai_final_data(groups, ocr_boxes_with_ids: List[Dict[str, any]]):
    """Merges Bounds into Text Bubbles, Based on AI Response"""
    id_to_bound = {bound["text_id"]: bound for bound in ocr_boxes_with_ids}

    group_id = 0  # TODO: start from 1
    merged_groups = {}
    for group in groups["groups"]:
        box_ids = group["box_ids"]
        cleaned_box_texts = group["split_cleaned_box_texts"]

        box_bounds = []
        box_texts = {}
        for box_id in box_ids:
            box = id_to_bound[box_id]["text_box"]
            box_bounds.append(box)

            cleaned_box_text = cleaned_box_texts[box_id]
            box_texts[box_id] = {"text_frag": cleaned_box_text, "text_box": box}

        assert box_bounds
        x_min = min(box[0] for box in box_bounds)
        y_min = min(box[1] for box in box_bounds)
        x_max = max(box[2] for box in box_bounds)
        y_max = max(box[3] for box in box_bounds)

        merged_groups[group_id] = {
            "panel_id": group["panel_id"],
            "text_box": [x_min, y_min, x_max, y_max],
            "ocr_text": group["original_text"],
            "ai_text": group["cleaned_text"],
            "type": group["type"],
            "style": group["style"],
            "notes": group["notes"],
            "cleaned_box_texts": box_texts,
        }

        group_id += 1

    return merged_groups


def get_text_groups(
    ocr_merged_data, ocr_bound_ids: List[Dict[str, any]]
) -> Dict[int, List[Tuple[OcrBox, float]]]:
    groups = {}

    for group_id in ocr_merged_data:
        dist = 0

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


def write_groups_to_text_file(file: str, groups) -> None:
    max_text_len = 0
    max_acc_text_len = 0
    for group in groups:
        for ocr_box, dist in groups[group]:
            max_text_len = max(max_text_len, len(ocr_box.ocr_text))
            max_acc_text_len = max(max_acc_text_len, len(ocr_box.accepted_text))

    with open(file, "w") as f:
        for group in groups:
            for ocr_box, dist in groups[group]:
                f.write(
                    f"Group: {group:03d}, "
                    f"text: '{ocr_box.ocr_text:<{max_text_len}}', "
                    f"acc: '{ocr_box.accepted_text:<{max_acc_text_len}}', "
                    f"P: {ocr_box.ocr_prob:4.2f}, "
                    f"box: {get_box_str(ocr_box._box_points)}, rect: {ocr_box.is_approx_rect}\n"
                )


def get_ocr_data(ocr_file: str) -> List[Dict[str, any]]:
    with open(ocr_file, "r") as f:
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


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title",
        CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR,
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    make_gemini_ai_groups_for_titles(cmd_args.get_titles(), cmd_args.get_work_dir())
