import '../barks-comic-building/.justfile'

_ocr_uv_run := "uv run --project " + justfile_directory()

_default2:
    just --list --unsorted

# Create whoosh index.
[group('OCR')]
create-index ocr_index *extras:
    {{_ocr_uv_run}} "barks-ocr-whoosh-index" main --volume 1-27 --ocr-index {{ocr_index}} {{extras}}

# Find titles containing words.
[group('OCR')]
find-words words *extras:
    {{_ocr_uv_run}} "barks-ocr-whoosh-find" --unstemmed --words "{{words}}" {{extras}}

# Open Vol/Page OCR files in editor
[group('OCR')]
open-prelim volume page:
    {{_ocr_uv_run}} "barks-ocr-open-prelim" --volume {{volume}} --page {{page}}

# Show Vol/Page OCR annotations
[group('OCR')]
annotate-ocr volume:
    {{_ocr_uv_run}} "barks-ocr-annotate" --volume {{volume}}

# Show Vol/Page OCR annotations
[group('OCR')]
show-annotations volume page:
    {{_ocr_uv_run}} "barks-ocr-show-annotated" --volume {{volume}} --page {{page}}

# Open editor and show Vol/Page OCR
[group('OCR')]
open-show volume page:
    just open-prelim {{volume}} {{page}}
    just show-annotations {{volume}} {{page}}

# Check OCR files for issues and write a kivy-editor queue file
[group('OCR')]
check-ocr volume queue_file:
    {{_ocr_uv_run}} "barks-ocr-check" --volume {{volume}} -o {{queue_file}}

# Invoke the kivy editor for one page only
[group('OCR')]
kivy_editor volume fanta_page easy_id='0' paddle_id='0':
    KIVY_NO_ARGS=1 {{_ocr_uv_run}} "barks-ocr-kivy-editor" --volume {{volume}} --fanta-page {{fanta_page}} --easyocr-group-id {{easy_id}} --paddleocr-group-id {{paddle_id}}
