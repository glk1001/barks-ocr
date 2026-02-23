import '../barks-comic-building/.justfile'

_default2:
    just --list --unsorted

# Find titles containing words.
[group('OCR')]
find-words words:
    {{uv_run}} "barks-ocr-whoosh-index" --volume 1-27 --unstemmed --words "{{words}}"

# Open Vol/Page OCR files in editor
[group('OCR')]
open-prelim volume page:
    {{uv_run}} "barks-ocr-open-prelim" --volume {{volume}} --page {{page}}

# Show Vol/Page OCR annotations
[group('OCR')]
annotate-ocr volume:
    {{uv_run}} "barks-ocr-annotate" --volume {{volume}}

# Show Vol/Page OCR annotations
[group('OCR')]
show-annotations volume page:
    {{uv_run}} "barks-ocr-show-annotated" --volume {{volume}} --page {{page}}

# Open editor and show Vol/Page OCR
[group('OCR')]
open-show volume page:
    just open-prelim {{volume}} {{page}}
    just show-annotations {{volume}} {{page}}

# Check OCR files
[group('OCR')]
check-ocr volume:
    {{uv_run}} "barks-ocr-string-replacer" --dry-run --volume {{volume}}
