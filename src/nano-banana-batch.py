# ruff: noqa: ERA001,T201,E501

import json
from pathlib import Path

from utils.gemini_ai import AI_IMAGE_MODEL, CLIENT

image_root_dir = Path("~/Books/Carl Barks/Barks Panels Pngs").expanduser()
folder = "Favourites"

prompt = "Remove all speech bubbles from the image."

title_images = {
    "The Persistent Postman": "112-3.png",
    "The Half-Baked Baker": "124-3.png",
}

image_paths = [image_root_dir / folder / title / title_images[title] for title in title_images]

gemini_image_files = []
for image_path in image_paths:
    print(f"Uploading image file: {image_path}")
    image_file = CLIENT.files.upload(file=str(image_path))
    print(f"Uploaded image file: {image_file.name} with MIME type: {image_file.mime_type}")
    gemini_image_files.append(image_file)

image_records = {}
requests_data = []
for i, image_file in enumerate(gemini_image_files):
    # Request: multi-modal prompt with text and an image reference.
    key = f"request_{i}"
    file_data = {
        "file_uri": image_file.uri,
        "mime_type": image_file.mime_type,
    }
    parts = [
        {"text": prompt},
        {"file_data": file_data},
    ]
    requests_data.append(
        {
            "key": key,
            "request": {
                "contents": [{"parts": parts}],
                "generation_config": {"response_modalities": ["TEXT", "IMAGE"], "temperature": 0.0},
            },
        }
    )

    image_records[i] = str(image_paths[i].relative_to(image_root_dir))

json_file_path = Path("/tmp") / "batch_requests_with_image.json"

print(f'\nCreating JSONL file: "{json_file_path}"...')
with json_file_path.open("w") as f:
    f.writelines(json.dumps(req) + "\n" for req in requests_data)

print(f'Uploading JSONL file: "{json_file_path}"...')
batch_input_file = CLIENT.files.upload(file=json_file_path)
print(f'Uploaded JSONL file: "{batch_input_file.name}".')

print("\nCreating batch job...")
batch_job_from_file = CLIENT.batches.create(
    model=AI_IMAGE_MODEL,
    src=batch_input_file.name,
    config={
        "display_name": "speech-bubble-removal-batch-job",
    },
)
print(f"Created batch job from file: {batch_job_from_file.name}")

print("You can now monitor the job status using its name.")

output = {
    "batch_job_name": batch_job_from_file.name,
    "image_records": image_records,
}
json_file_path = Path("/tmp") / "batch_job-details.json"  # noqa: S108

with Path("/tmp/batch-job-details.txt").open("w") as f:  # noqa: S108
    json.dump(output, f)
