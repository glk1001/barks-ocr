import json
import os
from pathlib import Path

from google import genai
from loguru import logger

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

out_dir = Path("/tmp")

# batch_job_name = "batches/6uebhj4gmlr7ruedit2sinbzba7x9e312a0m"
# client.batches.delete(name=batch_job_name)

with Path("/tmp/batch-job-details.json").open("r") as f:
    details = json.load(f)
batch_job_name = details["batch_job_name"]
gemini_output_files = details["gemini_output_files"]

logger.info(f"Checking batch job from file: {batch_job_name}")

batch_job_from_file = client.batches.get(name=batch_job_name)
if batch_job_from_file.state.name != "JOB_STATE_SUCCEEDED":
    logger.info(f"Job did not succeed. Final state: {batch_job_from_file.state.name}")
else:
    logger.info(f"Job status: {batch_job_from_file.state.name}.")
    # The output is in another file.
    result_file_name = batch_job_from_file.dest.file_name
    logger.info(f'Results are in file: "{result_file_name}".')

    logger.info("Downloading and parsing result file content...")
    file_content_bytes = client.files.download(file=result_file_name)
    file_content = file_content_bytes.decode("utf-8")

    # The result file is also a JSONL file. Parse and print each line.
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
                    logger.info(f'Writing to file: "{out_file}"...')
                    with out_file.open("w") as f:
                        f.write(part["text"])
                    file_index += 1
