import json
import sys
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from loguru import logger
from loguru_config import LoguruConfig

from utils.gemini_ai import CLIENT

APP_LOGGING_NAME = "gemr"


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
    log_filename = "make-gemini-ai-groups-get-batch-results.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    out_dir = cmd_args.get_work_dir() / "prelim"
    out_dir.mkdir(parents=True, exist_ok=True)

    assert (cmd_args.get_num_volumes() <= 1) or (len(cmd_args.get_titles()) <= 1)
    if cmd_args.one_or_more_volumes():
        batch_suffix = f"{cmd_args.get_volume()}"
    else:
        assert len(cmd_args.get_titles()) == 1
        batch_suffix = f"{cmd_args.get_title()}"

    batch_details_file = Path("/tmp") / f"batch-job-details-{batch_suffix}.json"  # noqa: S108
    logger.info(f'Getting batch details from file: "{batch_details_file}".')

    with Path(batch_details_file).open("r") as f:
        details = json.load(f)
    batch_job_name = details["batch_job_name"]
    gemini_output_files = details["gemini_output_files"]
    logger.info(f'Gemini batch job name: {batch_job_name}".')

    # CLIENT.batches.delete(name=batch_job_name)
    # sys.exit(0)

    batch_job_from_file = CLIENT.batches.get(name=batch_job_name)
    if batch_job_from_file.state.name != "JOB_STATE_SUCCEEDED":
        logger.info(f"Job did not succeed. Final state: {batch_job_from_file.state.name}")
    else:
        logger.info(f"Job status: {batch_job_from_file.state.name}.")
        # The output is in another file.
        result_file_name = batch_job_from_file.dest.file_name
        logger.info(f'Results are in Gemini file: "{result_file_name}".')

        logger.info("Downloading and parsing result file content...")
        file_content_bytes = CLIENT.files.download(file=result_file_name)
        file_content = file_content_bytes.decode("utf-8")

        # The result file is also a JSONL file. Parse and save each line.
        file_index = 0
        for line in file_content.splitlines():
            if line:
                parsed_response = json.loads(line)

                if "error" in parsed_response:
                    logger.error(parsed_response["error"])
                    continue

                for part in parsed_response["response"]["candidates"][0]["content"]["parts"]:
                    if part.get("text"):
                        out_file = out_dir / gemini_output_files[file_index]
                        file_index += 1

                        logger.info(f'Writing line {file_index} to file: "{out_file}"...')
                        with out_file.open("w") as f:
                            f.write(part["text"])
