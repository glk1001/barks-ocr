#VOLUMES=1-16
VOLUMES=28

DRY_RUN=""
DRY_RUN="--dry-run"

export UV_ENV_FILE=.env

uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " - "   --replace " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -\n"  --replace " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -$"   --replace " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "^- "   --replace "\u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -- "  --replace " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " --\n" --replace " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " --$"  --replace " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "^-- "  --replace "\u2014 "
