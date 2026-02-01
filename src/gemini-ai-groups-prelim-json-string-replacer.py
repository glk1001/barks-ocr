# ruff: noqa: T201

import codecs
import json
import re
import textwrap
from pathlib import Path

import typer
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from comic_utils.common_typer_options import VolumesArg
from intspan import intspan

SKIP_PREFIXES = {
    (" - ", 12): [105],
    (" -- ", 7): [135],
}


def replace_string_in_files(
    dir_path: Path,
    target_string: str,
    replacement_string: str,
    file_pattern: str,
    skip_prefixes: list[int],
    dry_run: bool = False,
) -> None:
    """Recursively replaces a target string with a replacement string in a directory.

    Args:
        dir_path (str or Path): The root directory to start searching from.
        target_string (str): The string to find.
        replacement_string (str): The string to use as a replacement.
        file_pattern (str): A glob pattern for files to process (e.g., "*.txt", "*.py", "*").
        skip_prefixes: List of integer file prefixes to skip.
        dry_run: If True, do not change any files.

    """
    if not dir_path.is_dir():
        print(f"Error: Directory not found at '{dir_path}'")
        return

    print(f"Starting replacement process in: {dir_path.resolve()}")
    print(f"Target: '{target_string}', Replacement: '{replacement_string}'\n")

    try:
        target_regex = re.compile(target_string)
    except re.error as e:
        print(f"Error: Invalid regex pattern '{target_string}': {e}")
        return

    files_checked_count = 0
    files_processed_count = 0
    lines_process_count = 0

    # Use rglob to recursively find files matching the pattern
    for file_path in dir_path.rglob(file_pattern):
        if not file_path.is_file():
            continue
        if int(file_path.stem[0:3]) in skip_prefixes:
            print(f'FILE IN SKIP LIST. SKIPPING "{file_path.name}".')
            continue

        files_checked_count += 1
        try:
            # Read the file content
            content = json.loads(file_path.read_text(encoding="utf-8"))

            # Perform the replacement over all the OCR groups.
            dirty_content = False
            for group in content["groups"].values():
                ai_text = group["ai_text"]
                new_ai_text = target_regex.sub(replacement_string, ai_text)
                if new_ai_text != ai_text:
                    dirty_content = True
                    group["ai_text"] = new_ai_text
                    lines_process_count += 1
                    print(
                        f'Modified "{file_path.name}", ai_text:\n'
                        f"{textwrap.indent(ai_text, ' ' * 4)} ->\n"
                        f"====\n"
                        f"{textwrap.indent(group['ai_text'], ' ' * 4)}\n"
                    )

            # Write back if changes were made.
            if dirty_content:
                if dry_run:
                    print(f'DRY RUN: Would have modified "{file_path.name}".\n')
                else:
                    with file_path.open("w", encoding="utf-8") as f:
                        json.dump(content, f, indent=4)
                    print(f'Modified "{file_path.name}", wrote new json to file.')
                files_processed_count += 1
        except Exception as e:  # noqa: BLE001
            print(f"Error processing {file_path}: {e}")

    print(
        f"\nReplacement complete. Total files checked: {files_checked_count};"
        f" files modified: {files_processed_count};"
        f" lines modified: {lines_process_count}.\n"
    )


FILE_GLOB_PATTERN = "*-gemini-prelim-groups.json"
app = typer.Typer()


@app.command(help="Replace string in JSON files")
def main(
    volumes_str: VolumesArg,
    target_str: str,
    replacement_str: str,
    dry_run: bool = False,
) -> None:
    # Decode escape sequences (like \n or \u2014) in the input strings
    target_str = codecs.decode(target_str, "unicode_escape")
    replacement_str = codecs.decode(replacement_str, "unicode_escape")

    volumes = list(intspan(volumes_str))
    assert len(volumes) >= 1

    comics_database = ComicsDatabase()

    for volume in volumes:
        volume_dirname = comics_database.get_fantagraphics_volume_title(volume)
        prelim_dir = OCR_PRELIM_DIR / volume_dirname
        skip_prefixes = SKIP_PREFIXES.get((target_str, volume), [])
        replace_string_in_files(
            prelim_dir, target_str, replacement_str, FILE_GLOB_PATTERN, skip_prefixes, dry_run
        )


if __name__ == "__main__":
    app()
