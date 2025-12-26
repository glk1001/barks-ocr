import '../barks-comic-building/.justfile'

_default2:
    just --list --unsorted

# Firnf titles containing words
find-words words:
    {{uv_run}} "{{source_dir()}}/src/make-whoosh-index-from-gemini-ai-groups.py" --volume 2-14 --unstemmed --words "{{words}}"
