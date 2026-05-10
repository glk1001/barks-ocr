#VOLUMES=1-16
VOLUMES=7

DRY_RUN=""
#DRY_RUN="--dry-run"

export UV_ENV_FILE=.env

uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " - "   --replace " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -\n"  --replace " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -$"   --replace " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "^- "   --replace "\u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " -- "  --replace " \u2014 "
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " --\n" --replace " \u2014\n"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target " --$"  --replace " \u2014"
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "^-- "  --replace "\u2014 "

uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "(\w) ([!?])" --replace '\\1\\2'
uv run barks-ocr-string-replacer ${DRY_RUN} --volume ${VOLUMES} --target "(\w)\u2014(\w)" --replace '\\1 \u2014 \\2'
