import '../barks-comic-building/.justfile'

_default2:
    just --list --unsorted

# Find titles containing words.
[group('OCR')]
find-words words:
    {{uv_run}} "{{source_dir()}}/src/make-whoosh-index-from-gemini-ai-groups.py" --volume 2-14 --unstemmed --words "{{words}}"

# Open Vol/Page OCR files in editor
[group('OCR')]
open-prelim volume page:
    {{uv_run}} "{{source_dir()}}/src/open-prelim-ocr.py" --volume {{volume}} --page {{page}}

# Show Vol/Page OCR annotations
[group('OCR')]
show-annotations volume page:
    {{uv_run}} "{{source_dir()}}/src/show-annotation-page.py" --volume {{volume}} --page {{page}}

# Open editor and show Vol/Page OCR
[group('OCR')]
open-show volume page:
    just open-prelim {{volume}} {{page}}
    just show-annotations {{volume}} {{page}}

# Check OCR files
[group('OCR')]
check-ocr volume:
    {{uv_run}} "{{source_dir()}}/src/gemini-ai-groups-prelim-json-string-replacer.py" --dry-run --volume {{volume}}
