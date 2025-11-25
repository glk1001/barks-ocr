import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_type
from loguru import logger

from ocr_file_paths import BATCH_JOBS_OUTPUT_DIR, OCR_RESULTS_DIR, get_ocr_predicted_groups_filename
from utils.common import ProcessResult
from utils.geometry import Rect
from utils.ocr_box import (
    OcrBox,
    PointList,
    get_box_str,
    load_groups_from_json,
    save_groups_as_json,
)


class GeminiAiGrouper:
    def __init__(
        self,
        comics_database: ComicsDatabase,
        get_ai_predicted_groups_func: Callable[[str, str, Path, list[dict[str, Any]], Path], Any],
    ) -> None:
        self._comics_database = comics_database
        self._get_ai_predicted_groups = get_ai_predicted_groups_func

    def make_groups_for_titles(self, title_list: list[str]) -> None:
        for title in title_list:
            if is_non_comic_title(title):
                logger.warning(f'Not a comic title "{title}" - skipping.')
                continue

            self._make_groups_for_title(title)

    def _make_groups_for_title(self, title: str) -> None:
        volume = self._comics_database.get_fanta_volume_int(title)
        volume_dirname = self._comics_database.get_fantagraphics_volume_title(volume)

        prelim_results_dir = BATCH_JOBS_OUTPUT_DIR / volume_dirname
        logger.info(
            f'Looking for preliminary predicted group data in directory "{prelim_results_dir}"...'
        )
        assert prelim_results_dir.is_dir()

        out_dir = OCR_RESULTS_DIR / volume_dirname
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f'Making OCR groups for all pages in "{title}". To directory "{out_dir}"...')

        comic = self._comics_database.get_comic_book(title)
        svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
        ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)
        panel_segments_files = comic.get_srce_panel_segments_files(RESTORABLE_PAGE_TYPES)

        num_files_processed = 0
        for svg_file, ocr_file, panel_segments_file in zip(
            svg_files, ocr_files, panel_segments_files, strict=True
        ):
            svg_stem = svg_file.stem

            for ocr_type_file in ocr_file:
                ocr_type = get_ocr_type(ocr_type_file)

                ocr_final_groups_json_file = out_dir / self._get_ocr_final_groups_json_filename(
                    svg_stem, ocr_type
                )
                ocr_groups_json_file = out_dir / self._get_ocr_groups_json_filename(
                    svg_stem, ocr_type
                )
                ocr_groups_txt_file = out_dir / self._get_ocr_groups_txt_filename(
                    svg_stem, ocr_type
                )

                result = self._make_groups(
                    svg_file,
                    ocr_type_file,
                    ocr_type,
                    prelim_results_dir,
                    panel_segments_file,
                    ocr_final_groups_json_file,
                    ocr_groups_json_file,
                    ocr_groups_txt_file,
                )

                if result == ProcessResult.FAILURE:
                    msg = "There were process errors."
                    logger.error(msg)
                if result == ProcessResult.SUCCESS:
                    num_files_processed += 1

            # break  # Break early for testing  # noqa: ERA001

    def _make_groups(
        self,
        svg_file: Path,
        ocr_file: Path,
        ocr_type: str,
        prelim_dir: Path,
        panel_segments_file: Path,
        ocr_final_data_groups_json_file: Path,
        ocr_groups_json_file: Path,
        ocr_groups_txt_file: Path,
    ) -> ProcessResult:
        svg_stem = svg_file.stem
        png_file = Path(str(svg_file) + ".png")

        # noinspection PyBroadException
        try:
            if not png_file.is_file():
                logger.error(f'Could not find png file "{png_file}".')
                return ProcessResult.FAILURE
            if not ocr_file.is_file():
                logger.error(f'Could not find ocr file "{ocr_file}".')
                return ProcessResult.FAILURE

            ai_predicted_groups_file = prelim_dir / get_ocr_predicted_groups_filename(
                svg_stem, ocr_type
            )
            if ocr_groups_json_file.is_file() and (
                ocr_groups_json_file.stat().st_mtime > ai_predicted_groups_file.stat().st_mtime
            ):
                logger.info(f'Found groups file - skipping: "{ocr_groups_json_file}".')
                return ProcessResult.SKIPPED

            logger.info(f'Making Gemini AI OCR groups for file "{get_abbrev_path(png_file)}"...')
            logger.info(f'Using OCR file "{get_abbrev_path(ocr_file)}"...')

            ocr_data = self._get_ocr_data(ocr_file)
            ocr_bound_ids = self._assign_ids_to_ocr_boxes(ocr_data)

            ai_predicted_groups = self._get_ai_predicted_groups(
                svg_stem, ocr_type, prelim_dir, ocr_bound_ids, png_file
            )

            # Merge boxes into text bubbles
            ai_final_data = self._get_final_ai_data(
                ai_predicted_groups, ocr_bound_ids, panel_segments_file
            )
            with ocr_final_data_groups_json_file.open("w") as f:
                json.dump(ai_final_data, f, indent=4)
            logger.info(f'Wrote final ai group data to "{ocr_final_data_groups_json_file}"...')

            groups = self._get_text_groups(ai_final_data, ocr_bound_ids)

            save_groups_as_json(groups, ocr_groups_json_file)
            groups = load_groups_from_json(ocr_groups_json_file)

            self._write_groups_to_text_file(ocr_groups_txt_file, groups)

        except:  # noqa: E722
            logger.exception(f'Could not process file "{png_file}":')
            sys.exit(1)
        else:
            return ProcessResult.SUCCESS

    def _get_final_ai_data(
        self,
        groups: list[Any],
        ocr_boxes_with_ids: list[dict[str, Any]],
        panel_segments_file: Path,
    ) -> dict[int, Any]:
        id_to_bound: dict[Any, dict[str, Any]] = {
            bound["text_id"]: bound for bound in ocr_boxes_with_ids
        }

        logger.info(f'Loading panel segments file "{get_abbrev_path(panel_segments_file)}".')
        with panel_segments_file.open("r") as f:
            panel_segment_info = json.load(f)

        merged_groups = {}
        # TODO: group_id start from 1
        for group_id, group in enumerate(groups):
            box_ids = group["box_ids"]
            cleaned_box_texts = group["split_cleaned_box_texts"]
            if not cleaned_box_texts:
                logger.warning(f"Ignoring group {group_id}: empty 'split_cleaned_box_texts'.")
                continue

            box_bounds: list[PointList] = []
            box_texts = {}
            for box_id in box_ids:
                if box_id not in cleaned_box_texts:
                    logger.warning(
                        f'For group {group_id}, could not find box_id "{box_id}"'
                        f" in cleaned_box_texts: {cleaned_box_texts.keys()}."
                    )
                    continue

                cleaned_box_text = cleaned_box_texts[box_id]
                if not cleaned_box_text:
                    logger.warning(f'Ignoring empty text fragment for box "{box_id}".')
                elif box_id not in id_to_bound:
                    logger.warning(
                        f'For group {group_id}, could not find box_id "{box_id}"'
                        f" in id_to_bound: {id_to_bound.keys()}."
                    )
                else:
                    box = id_to_bound[box_id]["text_box"]
                    box_texts[box_id] = {"text_frag": cleaned_box_text, "text_box": box}
                    box_bounds.append(box)

            if not box_bounds:
                logger.warning(f"Ignoring group {group_id}: 'box_bounds is None'.")
                continue

            enclosing_box = self._get_enclosing_box(box_bounds)
            # noinspection PyBroadException
            try:
                panel_num = self._get_enclosing_panel_num(enclosing_box, panel_segment_info)
            except:  # noqa: E722
                logger.exception(f"Could not get enclosing panel number for group '{group_id}':")
                continue

            ai_text = group["cleaned_text"]

            try:
                merged_groups[group_id] = {
                    "panel_id": group["panel_id"],
                    "panel_num": panel_num,
                    "text_box": enclosing_box,
                    "ocr_text": group["original_text"],
                    "ai_text": ai_text,
                    "type": group["type"],
                    "style": group["style"],
                    "notes": group["notes"],
                    "cleaned_box_texts": box_texts,
                }
            except Exception as e:
                logger.error(f"Could not set merged_group '{group_id}': {group}")
                raise e from e

        return merged_groups

    @staticmethod
    def _get_ocr_data(ocr_file: Path) -> list[dict[str, Any]]:
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

    @staticmethod
    def _assign_ids_to_ocr_boxes(bounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{**bound, "text_id": str(i)} for i, bound in enumerate(bounds)]

    @staticmethod
    def _get_ocr_groups_txt_filename(svg_stem: str, ocr_type: str) -> str:
        return svg_stem + f"-{ocr_type}-gemini-groups.txt"

    @staticmethod
    def _get_ocr_groups_json_filename(svg_stem: str, ocr_type: str) -> str:
        return svg_stem + f"-{ocr_type}-gemini-groups.json"

    @staticmethod
    def _get_ocr_final_groups_json_filename(svg_stem: str, ocr_type: str) -> str:
        return svg_stem + f"-{ocr_type}-gemini-final-groups.json"

    @staticmethod
    def _get_enclosing_box(boxes: list[PointList]) -> PointList:
        x_min = min(box[0][0] for box in boxes)
        y_min = min(box[1][1] for box in boxes)
        x_max = max(box[2][0] for box in boxes)
        y_max = max(box[3][1] for box in boxes)

        return [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]

    @staticmethod
    def _get_enclosing_panel_num(box: PointList, panel_segment_info) -> int:  # noqa: ANN001
        ocr_box = OcrBox(box, "", 0, "")
        box = ocr_box.min_rotated_rectangle
        bottom_left = box[0]
        top_right = box[1]
        box_rect = Rect(
            bottom_left[0],
            bottom_left[1],
            top_right[0] - bottom_left[0],
            top_right[1] - bottom_left[1],
        )

        for i, panel_box in enumerate(panel_segment_info["panels"]):
            top_left_x = panel_box[0]
            top_left_y = panel_box[1]
            w = panel_box[2]
            h = panel_box[3]
            panel_rect = Rect(top_left_x, top_left_y, w, h)
            if panel_rect.is_rect_inside_rect(box_rect):
                return i + 1

        return -1

    @staticmethod
    def _get_text_groups(
        ocr_merged_data: dict[int, Any], ocr_bound_ids: list[dict[str, Any]]
    ) -> dict[int, list[tuple[Any, float]]]:
        groups = {}

        for group_id, ocr_data in ocr_merged_data.items():
            dist = 0.0

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

    @staticmethod
    def _write_groups_to_text_file(file: Path, groups: dict[int, Any]) -> None:
        max_text_len = 0
        max_acc_text_len = 0
        for group in groups.values():
            for ocr_box, _dist in group:
                max_text_len = max(max_text_len, len(ocr_box.ocr_text))
                max_acc_text_len = max(max_acc_text_len, len(ocr_box.accepted_text))

        with file.open("w") as f:
            for group_id, group in groups.items():
                for ocr_box, _dist in group:
                    # noinspection PyProtectedMember
                    f.write(
                        f"Group: {group_id:03d}, "
                        f"text: '{ocr_box.ocr_text:<{max_text_len}}', "
                        f"acc: '{ocr_box.accepted_text:<{max_acc_text_len}}', "
                        f"P: {ocr_box.ocr_prob:4.2f}, "
                        f"box: {get_box_str(ocr_box._box_points)},"  # noqa: SLF001
                        f" rect: {ocr_box.is_approx_rect}\n"
                    )
