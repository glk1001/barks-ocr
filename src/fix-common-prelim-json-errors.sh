VOLUMES=1-16

DRY_RUN=""
#DRY_RUN="--dry-run"

export UV_ENV_FILE=.env

uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " - " " \u2014 "
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " -\n" " \u2014\n"
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " -$" " \u2014"
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} "^- " "\u2014 "
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " -- " " \u2014 "
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " --\n" " \u2014\n"
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} " --$" " \u2014"
uv run src/gemini-ai-groups-prelim-json-string-replacer.py ${DRY_RUN} --volume ${VOLUMES} "^-- " "\u2014 "
