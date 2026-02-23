#VOLUMES=1-16
VOLUMES=1

DRY_RUN=""
DRY_RUN="--dry-run"

export UV_ENV_FILE=.env

uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " - " " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " -\n" " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " -$" " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} "^- " "\u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " -- " " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " --\n" " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} " --$" " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} "^-- " "\u2014 "
