# The comic-building recipes, when that repo is cloned beside this one. `mod?` keeps
# this repo's own recipes working without it.

# The barks-comic-building recipes: `just comics` lists them, `just comics build 9`
mod? comics '../barks-comic-building'

# `uv run` re-syncs the project before every command and revalidates over the network
# any dependency it cannot resolve from disk or its cache. This repo is the one that
# really needs the switch: the `en-core-web-sm` dev dependency is a direct URL
# (github.com), so uv revalidates it on every sync, and every recipe below then fails
# with no connection whether or not it touches spacy. The wheel is already cached.
# UV_OFFLINE=1 runs from the installed venv; after adding or changing a dependency:
#
#     UV_OFFLINE=0 just check-ocr 9 /tmp/queue.txt
export UV_OFFLINE := env("UV_OFFLINE", "1")

uv_run := "uv run --project " + source_dir()

_default:
    @just --list --unsorted

# Create whoosh index.
[group('OCR')]
create-index ocr_index *extras:
    {{uv_run}} "barks-ocr-whoosh-index" main --volume 1-27 --ocr-index {{ocr_index}} {{extras}}

# Find titles containing words.
[group('OCR')]
find-words words *extras:
    {{uv_run}} "barks-ocr-whoosh-find" --words "{{words}}" {{extras}}

# Open Vol/Page OCR files in editor
[group('OCR')]
open-prelim volume page:
    {{uv_run}} "barks-ocr-open-prelim" --volume {{volume}} --page {{page}}

# Show OCR annotations for a volume or volumes
[group('OCR')]
annotate-ocr volume:
    {{uv_run}} "barks-ocr-annotate" --volume {{volume}}

# Show OCR annotations for a title
[group('OCR')]
annotate-ocr-title title:
    {{uv_run}} "barks-ocr-annotate" --title "{{title}}"

# Show Vol/Page OCR annotations
[group('OCR')]
show-annotations volume page:
    {{uv_run}} "barks-ocr-show-annotated" --volume {{volume}} --page {{page}}

# Open editor and show Vol/Page OCR
[group('OCR')]
open-show volume page:
    just open-prelim {{volume}} {{page}}
    just show-annotations {{volume}} {{page}}

# Check OCR files for issues and write a kivy-editor queue file
[group('OCR')]
check-ocr volume queue_file *extras:
    {{uv_run}} "barks-ocr-check" --log-level WARNING --volume {{volume}} -o {{queue_file}} {{extras}}

# Invoke the kivy editor for one page only
[group('OCR')]
kivy-editor volume fanta_page easy_id='0' paddle_id='0':
    KIVY_NO_ARGS=1 {{uv_run}} "barks-ocr-kivy-editor" --volume {{volume}} --fanta-page {{fanta_page}} --easyocr-group-id {{easy_id}} --paddleocr-group-id {{paddle_id}}

# Invoke the kivy editor for a queue
[group('OCR')]
kivy-editor-queue qfile:
    KIVY_NO_ARGS=1 {{uv_run}} "barks-ocr-kivy-editor" --queue-file {{qfile}}

# The two checks run in this order on purpose. The second reads the Image column at face
# value, so a row whose image has drifted from the story it names would send it looking
# at the wrong page and report a fix as undocumented when it is not.

# Check the censorship fixes CSV against its own stories, then against the images
[group('censorship')]
check-censorship:
    {{uv_run}} barks-ocr-censorship-csv --check
    just comics check-censorship-csv
