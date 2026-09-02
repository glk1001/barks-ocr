#!/usr/bin/env bash
#
# closeout.sh -- the read-only close-out checks for one vision-pass title.
#
#   bash scripts/closeout.sh [--stage apply|review] "Some Title"
#
# Folds the close-out sequence from the vision-pass skill into one command:
# the missed-text audit, the engine diff, outstanding text/type corrections,
# unreviewed speaker stragglers on BOTH engines, the mirror dry run, and
# `git status` in every repo the pass touches.
#
# It WRITES NOTHING and COMMITS NOTHING. Every command it runs is a report; the
# mirror is invoked without --write. Safe to run at any point.
#
# Two stages, because the same check means different things at each:
#
#   --stage apply   (default) after vision-apply, before handing the title to the
#                   reviewer. Unreviewed speakers and a pending mirror are the
#                   expected state, so they are reported but do not fail.
#   --stage review  after the reviewer says the review is done AND after
#                   `barks-ocr-vision-mirror --write`. Now stragglers and a
#                   non-empty mirror dry run are failures: they mean the title
#                   is not actually finished.
#
# Exits 0 only if every gating check for the stage is clean; 1 otherwise, with
# the per-check log paths printed so the finding can be read in full. Reading
# the output still matters -- an engine diff or near-miss count is advisory, and
# the audit's three classes each need a different response (see the skill).
#
# Offline: export UV_OFFLINE=1. Every barks-ocr-* command otherwise dies with no
# network, because uv revalidates the en-core-web-sm URL dependency.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${TMPDIR:-/tmp}/closeout-$$"
STAGE="apply"
TITLE=""

usage() {
    sed -n '2,/^$/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-2}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --stage)
            STAGE="${2:-}"
            shift 2 || usage
            ;;
        --stage=*)
            STAGE="${1#*=}"
            shift
            ;;
        -h | --help)
            usage 0
            ;;
        -*)
            echo "closeout.sh: unknown flag '$1'" >&2
            usage
            ;;
        *)
            [[ -n "$TITLE" ]] && {
                echo "closeout.sh: more than one title given ('$TITLE', '$1')" >&2
                usage
            }
            TITLE="$1"
            shift
            ;;
    esac
done

[[ -n "$TITLE" ]] || {
    echo "closeout.sh: a title is required." >&2
    usage
}
[[ "$STAGE" == "apply" || "$STAGE" == "review" ]] || {
    echo "closeout.sh: --stage must be 'apply' or 'review', not '$STAGE'." >&2
    exit 2
}

# uv resolves the project from the cwd; running from anywhere else makes every
# barks-ocr-* script "fail to spawn".
cd "$REPO_DIR" || exit 2
mkdir -p "$LOG_DIR"

FAILURES=0
declare -a ROWS=()

# row <verdict> <check> <detail>
row() {
    ROWS+=("$1|$2|$3")
    [[ "$1" == "FAIL" ]] && FAILURES=$((FAILURES + 1))
    return 0
}

# capture <log> <command...> -- run it, keep the output, return its status.
capture() {
    local name="$1"
    shift
    "$@" >"$LOG_DIR/$name.log" 2>&1
}

# num <log> <sed-expression> -- first captured number, or empty.
num() {
    sed -n "$2" "$LOG_DIR/$1.log" | head -1
}

echo "closeout: \"$TITLE\"  (stage: $STAGE)"
echo "logs:     $LOG_DIR"
echo

# --- 1. missed text: lettering no group covers -------------------------------
echo "-> missed-text audit"
if capture missed-text uv run python scripts/vision/audit_missed_text.py --title "$TITLE"; then
    neither=$(num missed-text 's/^=== grouped by NEITHER engine: \([0-9]*\) ===$/\1/p')
    one_only=$(num missed-text 's/^=== grouped by only ONE engine: \([0-9]*\) ===$/\1/p')
    near=$(num missed-text 's/^=== nearly a grouped text.*: \([0-9]*\) ===$/\1/p')
    swept=$(num missed-text 's/^Swept \([0-9]*\) vision-passed page(s).*/\1/p')

    # Every check below is a search for defects, so a title the pass has never
    # read comes back silently all-clean. Refuse to call that a close-out.
    if [[ -n "$swept" ]] && ((swept == 0)); then
        row FAIL "vision pass" "no vision-passed page carries visible_text -- title not read"
    fi

    if [[ -z "$neither" || -z "$one_only" ]]; then
        row FAIL "missed-text audit" "could not parse output -- read the log"
    elif ((neither > 0 || one_only > 0)); then
        row FAIL "missed-text audit" "$neither in neither engine, $one_only in one only"
    else
        row OK "missed-text audit" "no lettering left ungrouped"
    fi
    if [[ -n "$near" ]] && ((near > 0)); then
        row WARN "  near-misses" "$near -- transcription off by a letter, or a truncated group"
    fi
else
    row FAIL "missed-text audit" "command failed -- read the log"
fi

# --- 2. engine diff: text one engine has and the other has nothing like ------
# Advisory by design: the engines legitimately split and merge balloons
# differently, so a count is not a defect. Read the strings.
echo "-> engine diff"
if capture engine-diff uv run python scripts/vision/engine_diff.py "$TITLE"; then
    odd=$(num engine-diff 's/^\([0-9]*\) page(s) where the engines carry text.*/\1/p')
    if [[ -z "$odd" ]]; then
        row FAIL "engine diff" "could not parse output -- read the log"
    elif ((odd > 0)); then
        row WARN "engine diff" "$odd page(s) disagree -- read the strings, not the count"
    else
        row OK "engine diff" "engines carry the same text"
    fi
else
    row FAIL "engine diff" "command failed -- read the log"
fi

# --- 3. outstanding text and type corrections --------------------------------
# A separate review state from speakers: a title can be 125/125 on speakers and
# still have every text correction untouched.
echo "-> outstanding corrections"
if capture corrections uv run barks-ocr-vision-corrections --title "$TITLE"; then
    if grep -q '^Nothing outstanding across' "$LOG_DIR/corrections.log"; then
        row OK "corrections" "nothing outstanding"
    else
        outstanding=$(num corrections 's/^\([0-9]*\) outstanding across.*/\1/p')
        row FAIL "corrections" "${outstanding:-?} text/type correction(s) outstanding"
    fi
    # The stale panel-segments mtime gate makes a title vanish from the scan
    # rather than erroring, so an unchecked title must not read as clean.
    if grep -q 'NOT checked -- stale panel-segments mtime' "$LOG_DIR/corrections.log"; then
        row FAIL "  segmentation" "title(s) skipped for stale panel-segments mtime"
    fi
else
    row FAIL "corrections" "command failed -- read the log"
fi

# --- 4. unreviewed speaker stragglers, on both engines -----------------------
# Both engines, because a "review complete" commit that is really 140/141 on
# either side is bad provenance.
for engine in easyocr paddleocr; do
    echo "-> unreviewed speakers ($engine)"
    capture "stragglers-$engine" uv run barks-ocr-speaker-queue \
        --title "$TITLE" --engine "$engine" --unreviewed \
        -o "$LOG_DIR/queue-$engine.txt"
    status=$?

    # Read the count off stdout: an empty run leaves the PREVIOUS queue file on
    # disk, so the file is not evidence. And "no calls match" exits 1 while
    # meaning the best possible outcome -- nothing left unreviewed -- so the
    # exit status cannot be the verdict either.
    if grep -q '^No calls match those selectors' "$LOG_DIR/stragglers-$engine.log"; then
        queued=0
    elif ((status != 0)); then
        queued=""
    else
        queued=$(num "stragglers-$engine" 's/.*; \([0-9]*\) queued\.$/\1/p')
    fi

    if [[ -z "$queued" ]]; then
        row FAIL "stragglers ($engine)" "command failed -- read the log"
    elif ((queued > 0)); then
        if [[ "$STAGE" == "review" ]]; then
            row FAIL "stragglers ($engine)" "$queued group(s) never speaker_reviewed"
        else
            row INFO "stragglers ($engine)" "$queued awaiting review (expected at this stage)"
        fi
    else
        row OK "stragglers ($engine)" "every group reviewed"
    fi
done

# --- 4b. stored-group integrity: speaker drift, evidence, added-group faults --
# Advisory. All three classes carry a standing backlog that predates the check,
# so this prints and never gates; --fail-on-findings is for once one is cleared.
echo "-> group audit"
if capture group-audit uv run python scripts/vision/audit_groups.py "$TITLE"; then
    lopsided=$(num group-audit 's/^=== hand-added groups present on only one engine: \([0-9]*\) page(s) ===$/\1/p')
    drift=$(num group-audit 's/^=== other: speakers that differ only by case or an article: \([0-9]*\) ===$/\1/p')
    if [[ -z "$lopsided" || -z "$drift" ]]; then
        row FAIL "group audit" "could not parse output -- read the log"
    elif ((lopsided > 0)); then
        row WARN "group audit" "$lopsided page(s) add a group on one engine only"
    elif ((drift > 0)); then
        row WARN "group audit" "$drift other: speaker(s) differ only by an article"
    else
        row OK "group audit" "no speaker drift or one-engine adds"
    fi
else
    row FAIL "group audit" "command failed -- read the log"
fi

# --- 5. mirror dry run -------------------------------------------------------
# At --stage review this runs AFTER `vision-mirror --write`, so a non-zero count
# means the mirror did not take. Never invoked with --write here.
echo "-> mirror dry run"
if capture mirror uv run barks-ocr-vision-mirror --title "$TITLE"; then
    pending=$(num mirror 's/.*DRY RUN -- \([0-9]*\) page(s) would be written.*/\1/p')
    if [[ -z "$pending" ]]; then
        row FAIL "mirror" "could not parse output -- read the log"
    elif ((pending > 0)); then
        if [[ "$STAGE" == "review" ]]; then
            row FAIL "mirror" "$pending page(s) not yet mirrored -- run --write"
        else
            row INFO "mirror" "$pending page(s) would mirror (not due until review is done)"
        fi
    else
        row OK "mirror" "both engines already match"
    fi
else
    row FAIL "mirror" "command failed -- read the log"
fi

# --- 6. git status, every repo the pass touches ------------------------------
# The prelim JSON is its own repo. Ask the package where it is rather than
# hardcoding the path, and keep any symlink in the reported path intact.
PRELIM_DIR=$(uv run python -c \
    'from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR; print(OCR_PRELIM_DIR)' \
    2>"$LOG_DIR/prelim-dir.log")

for repo in "$REPO_DIR" "$PRELIM_DIR"; do
    [[ -n "$repo" ]] || continue
    echo "-> git status ($repo)"
    if ! dirty=$(git -C "$repo" status --porcelain 2>"$LOG_DIR/git-status.log"); then
        row FAIL "git ($(basename "$repo"))" "not a git repo, or git failed"
    elif [[ -n "$dirty" ]]; then
        count=$(printf '%s\n' "$dirty" | wc -l)
        row WARN "git ($(basename "$repo"))" "$count uncommitted path(s) -- may not all be yours"
    else
        row OK "git ($(basename "$repo"))" "clean"
    fi
done
[[ -n "$PRELIM_DIR" ]] || row FAIL "git (prelim)" "could not resolve OCR_PRELIM_DIR"

# --- summary -----------------------------------------------------------------
echo
printf '%-6s  %-24s  %s\n' "RESULT" "CHECK" "DETAIL"
printf '%-6s  %-24s  %s\n' "------" "------------------------" "------"
for r in "${ROWS[@]}"; do
    printf '%-6s  %-24s  %s\n' "${r%%|*}" "$(cut -d'|' -f2 <<<"$r")" "${r##*|}"
done
echo

if ((FAILURES > 0)); then
    echo "closeout: $FAILURES check(s) FAILED for \"$TITLE\" at stage $STAGE."
    echo "          logs in $LOG_DIR"
    exit 1
fi
echo "closeout: all gating checks clean for \"$TITLE\" at stage $STAGE."
echo "          WARN/INFO rows above still want reading."
exit 0
