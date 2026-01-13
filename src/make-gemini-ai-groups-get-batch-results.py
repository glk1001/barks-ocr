import json
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.ocr_file_paths import (
    BATCH_JOBS_OUTPUT_DIR,
    FINISHED_BATCH_JOBS_DIR,
    get_batch_details_file,
    get_batch_requests_file,
)
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from intspan import intspan
from loguru import logger
from loguru_config import LoguruConfig

from utils.gemini_ai import CLIENT

APP_LOGGING_NAME = "gemr"


def process_batch_jobs(comics_database: ComicsDatabase, titles: list[str]) -> None:
    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        process_batch_job(comics_database, title)


def process_batch_job(comics_database: ComicsDatabase, title: str) -> None:  # noqa: PLR0915
    # noinspection PyBroadException
    num_errors = 0
    # noinspection PyBroadException
    try:
        batch_details_file = get_batch_details_file(title)
        finished_batch_details_file = FINISHED_BATCH_JOBS_DIR / batch_details_file.name

        if not batch_details_file.is_file():
            if not finished_batch_details_file.exists():
                msg = (
                    f"Batch details file not found and"
                    f' no finished batch details file: "{batch_details_file}"'
                )
                raise FileNotFoundError(msg)
            logger.info(
                f'Found finished batch details file: "{finished_batch_details_file}" - skipping.'
            )
            return

        logger.info(f'Getting batch details from file: "{batch_details_file}".')

        with Path(batch_details_file).open("r") as f:
            details = json.load(f)
        batch_job_name = details["batch_job_name"]
        gemini_output_files = details["gemini_output_files"]
        logger.info(f'Gemini batch job name: {batch_job_name}".')

        # CLIENT.batches.delete(name=batch_job_name)  # noqa: ERA001
        # sys.exit(0)  # noqa: ERA001

        batch_job_from_file = CLIENT.batches.get(name=batch_job_name)
        assert batch_details_file
        job_state = batch_job_from_file.state.name  # ty: ignore[possibly-missing-attribute]
        if job_state != "JOB_STATE_SUCCEEDED":
            logger.error(f"Job did not succeed. Final state: {job_state}")
            return

        logger.info(f"Job status: {job_state}.")
        # The output is in another file.
        result_file_name = batch_job_from_file.dest.file_name  # ty: ignore[possibly-missing-attribute]
        logger.info(f'Results are in Gemini file: "{result_file_name}".')

        logger.info("Downloading and parsing result file content...")
        assert result_file_name
        file_content_bytes = CLIENT.files.download(file=result_file_name)
        file_content = file_content_bytes.decode("utf-8")

        volume = comics_database.get_fanta_volume_int(title)
        volume_dirname = comics_database.get_fantagraphics_volume_title(volume)
        out_dir = BATCH_JOBS_OUTPUT_DIR / volume_dirname
        out_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Writing downloaded data to volume directory "{out_dir}"...')

        # The result file is also a JSONL file. Parse and save each line.
        file_index = 0
        for line in file_content.splitlines():
            if line:
                parsed_response = json.loads(line)

                if "error" in parsed_response:
                    logger.error(parsed_response["error"])
                    continue

                # noinspection PyBroadException
                try:
                    for part in parsed_response["response"]["candidates"][0]["content"]["parts"]:
                        if part.get("text"):
                            out_file = out_dir / gemini_output_files[file_index]
                            file_index += 1

                            logger.info(f'Writing line {file_index} to file: "{out_file}"...')
                            with out_file.open("w") as f:
                                f.write(part["text"])
                except Exception:  # noqa: BLE001
                    logger.error(
                        f"Error parsing line {file_index}:"
                        f" {parsed_response['response']['candidates'][0]}"
                    )
                    num_errors += 1
                    logger.exception(f"Error parsing line {file_index} but continuing")

        batch_details_file.rename(finished_batch_details_file)
        logger.info(f'Moved "{batch_details_file}" to finished "{finished_batch_details_file}".')

        batch_requests_file = get_batch_requests_file(title)
        finished_batch_requests_file = FINISHED_BATCH_JOBS_DIR / batch_requests_file.name
        batch_requests_file.rename(finished_batch_requests_file)
        logger.info(f'Moved "{batch_requests_file}" to finished "{finished_batch_requests_file}".')

    except:  # noqa: E722
        logger.exception(f'Could not fully process batch result for title: "{title}".')

    if num_errors > 0:
        logger.error(
            f"There were {num_errors} errors while processing batch results for title: '{title}'."
        )


app = typer.Typer()
log_level = ""
log_filename = "make-gemini-ai-groups-get-batch-results.log"


@app.command(help="Get gemini ai groups results from batch job")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    # Global variable accessed by loguru-config.
    global log_level  # noqa: PLW0603
    log_level = log_level_str
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()

    if volumes:
        batch_job_titles = get_titles(comics_database, volumes, title_str)
    else:
        assert len(volumes) == 0
        batch_job_titles = [title_str]

    process_batch_jobs(comics_database, batch_job_titles)


if __name__ == "__main__":
    app()
