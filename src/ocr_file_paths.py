from pathlib import Path

OCR_ROOT = Path.home() / "Books" / "Carl Barks" / "Projects" / "OCR"

OCR_RESULTS_DIR = OCR_ROOT / "Results"

OCR_FIXES_DIR = OCR_RESULTS_DIR / "Fixes"

BATCH_JOBS_DIR = OCR_ROOT / "batch-jobs"
UNPROCESSED_BATCH_JOBS_DIR = BATCH_JOBS_DIR / "unprocessed"
FINISHED_BATCH_JOBS_DIR = BATCH_JOBS_DIR / "finished"
BATCH_JOBS_OUTPUT_DIR = BATCH_JOBS_DIR / "output"


def get_batch_details_file(title: str) -> Path:
    return UNPROCESSED_BATCH_JOBS_DIR / f"{title}-batch-job-details.json"


def get_batch_requests_file(title: str) -> Path:
    return UNPROCESSED_BATCH_JOBS_DIR / f"{title}-batch-requests-with-image.json"


# TODO: Remove json from inside name
def get_ocr_predicted_groups_filename(svg_stem: str, ocr_type: str) -> str:
    return f"{svg_stem}-{ocr_type}-json-ocr-ai-predicted-groups.json"


def get_ocr_final_groups_json_filename(svg_stem: str, ocr_type: str) -> str:
    return svg_stem + f"-{ocr_type}-gemini-final-groups.json"


def get_ocr_final_text_annotated_filename(svg_stem: str, ocr_type: str) -> str:
    return svg_stem + f"-{ocr_type}-ocr-gemini-final-text-annotated.png"
    # return out_dir / (svg_stem + f"-{ocr_type}-ocr-calculated-annotated.png")


def get_ocr_boxes_annotated_filename(svg_stem: str, ocr_type: str) -> str:
    return svg_stem + f"-{ocr_type}-ocr-gemini-boxes-annotated.png"
    # return out_dir / (svg_stem + f"-{ocr_type}-ocr-calculated-boxes-annotated.png")


def get_ocr_group_filename(svg_stem: str, ocr_type: str) -> str:
    return svg_stem + f"-{ocr_type}-gemini-final-groups.json"
    # return out_dir / (svg_stem + f"-{ocr_type}-calculated-groups.json")
