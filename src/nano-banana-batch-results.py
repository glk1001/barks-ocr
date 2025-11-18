# ruff: noqa: ERA001,T201,E501

import base64
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from utils.gemini_ai import CLIENT

with Path("/tmp/batch-job-details.txt").open("r") as f:  # noqa: S108
    details = json.load(f)
batch_job_name = details["batch_job_name"]
image_records = details["image_records"]

print(f"Checking batch job from file: {batch_job_name}")

batch_job_from_file = CLIENT.batches.get(name=batch_job_name)
if batch_job_from_file.state.name != "JOB_STATE_SUCCEEDED":
    print(f"Job did not succeed. Final state: {batch_job_from_file.state.name}")
else:
    # The output is in another file.
    result_file_name = batch_job_from_file.dest.file_name
    print(f"Results are in file: {result_file_name}")

    print("\nDownloading and parsing result file content...")
    file_content_bytes = CLIENT.files.download(file=result_file_name)
    file_content = file_content_bytes.decode("utf-8")

    # The result file is also a JSONL file. Parse and print each line.
    image_index = 0
    for line in file_content.splitlines():
        if line:
            parsed_response = json.loads(line)

            dest_image = Path(f"/tmp/{image_records[str(image_index)]}")  # noqa: S108
            dest_image.parent.mkdir(parents=True, exist_ok=True)
            image_index += 1

            for part in parsed_response["response"]["candidates"][0]["content"]["parts"]:
                if part.get("text"):
                    print(part["text"])
                elif part.get("inlineData"):
                    mime = part["inlineData"]["mimeType"]
                    data = base64.b64decode(part["inlineData"]["data"])
                    srce_image1 = Image.open(BytesIO(data))
                    srce_image1.save(dest_image)
