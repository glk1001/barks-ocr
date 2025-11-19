from pathlib import Path

OCR_ROOT = Path.home() / "Books" / "Carl Barks" / "Projects" / "OCR"

OCR_RESULTS_DIR = OCR_ROOT / "Results"

BATCH_JOBS_DIR = OCR_ROOT/ "batch-jobs"
UNPROCESSED_BATCH_JOBS_DIR = BATCH_JOBS_DIR / "unprocessed"
FINISHED_BATCH_JOBS_DIR = BATCH_JOBS_DIR / "finished"
BATCH_JOBS_OUTPUT_DIR = BATCH_JOBS_DIR / "output"
