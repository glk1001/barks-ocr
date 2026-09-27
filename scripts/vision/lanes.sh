#!/usr/bin/env bash
# Prelim worktrees for concurrent vision-pass lanes: create, inspect, merge back.
#
#     bash scripts/vision/lanes.sh setup     # one worktree per planned lane, at main
#     bash scripts/vision/lanes.sh status    # each lane's commits, dirt and volumes
#     bash scripts/vision/lanes.sh merge     # merge every lane into main, reset lanes
#
# WHAT IT ASSUMES. A plan from `scripts/vision/lane_plan.py` in ~/barks-vision/lanes.
# Lane N works in the worktree `Prelim-laneN` beside the main prelim checkout, on
# branch `laneN`, with its session started as
#     BARKS_OCR_PRELIM_DIR=<worktree> claude
# so every barks-ocr-* command it runs reads and writes that worktree. The main
# checkout is `OCR_PRELIM_DIR` with that variable UNSET, and it must be clean.
#
# WHY merge IS STRICT. Lanes are only safe because they share no volume. `merge`
# refuses a lane whose commits touch a volume that is not in its plan, and a lane
# with uncommitted files, before anything is merged -- so a round either merges
# whole or not at all. After merging it fast-forwards every lane branch to main, so
# the next `setup` starts from the merged tree.
#
# WHY setup ARCHIVES THE CLOSE-OUTS. A lane session writes its findings to
# ~/barks-vision/lanes/lane-<N>-closeout.md, and the coordinator folds them into the
# docs AFTER `merge` -- so `merge` must leave them alone. Nothing else removed them,
# and a new round's lane session writes to the same path, where a stale file gets
# appended to or folded twice. So once every lane has passed its checks, `setup`
# moves the last round's close-outs to ~/barks-vision/lanes/done/<date-time>/.
#
# Set LANE_COMMIT_TRAILER to append a trailer line (e.g. Co-Authored-By) to the
# merge commits.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LANES_DIR="$HOME/barks-vision/lanes"

cd "$REPO_DIR"
PRELIM=$(env -u BARKS_OCR_PRELIM_DIR uv run --offline python -c \
    'from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR; print(OCR_PRELIM_DIR)' \
    2>/dev/null | tail -1)
[[ -d "$PRELIM/.git" || -f "$PRELIM/.git" ]] || { echo "no prelim repo at $PRELIM" >&2; exit 1; }

shopt -s nullglob
PLANS=("$LANES_DIR"/lane-*.json)
((${#PLANS[@]})) || { echo "no lane plan in $LANES_DIR -- run lane_plan.py" >&2; exit 1; }

field() {  # field <plan.json> <key>
    python3 -c 'import json,sys; v=json.load(open(sys.argv[1]))[sys.argv[2]]; print(" ".join(map(str,v)) if isinstance(v,list) and not (v and isinstance(v[0],dict)) else v)' "$1" "$2"
}

main_clean() {
    [[ -z "$(git -C "$PRELIM" status --porcelain)" ]] || {
        echo "main prelim checkout $PRELIM has uncommitted changes" >&2; exit 1; }
    [[ "$(git -C "$PRELIM" branch --show-current)" == main ]] || {
        echo "main prelim checkout is not on main" >&2; exit 1; }
}

cmd_setup() {
    main_clean
    for plan in "${PLANS[@]}"; do
        local branch wt
        branch=$(field "$plan" branch); wt=$(field "$plan" worktree)
        if [[ -e "$wt" ]]; then
            [[ -z "$(git -C "$wt" status --porcelain)" ]] || {
                echo "$wt has uncommitted changes -- finish or merge that lane first" >&2; exit 1; }
            git -C "$PRELIM" merge-base --is-ancestor "$branch" main || {
                echo "$branch has commits not merged into main -- run merge first" >&2; exit 1; }
            git -C "$wt" merge --ff-only --quiet main
            echo "reset   $wt ($branch) to main"
        else
            git -C "$PRELIM" worktree add --quiet -B "$branch" "$wt" main
            echo "created $wt ($branch) at main"
        fi
    done
    archive_closeouts
}

archive_closeouts() {  # the last round's close-outs, now folded into the docs
    local files=("$LANES_DIR"/lane-*-closeout.md) dest
    ((${#files[@]})) || return 0
    dest="$LANES_DIR/done/$(date -r "${files[0]}" +%F-%H%M%S)"
    mkdir -p "$dest"
    mv -n -- "${files[@]}" "$dest"/
    local left=("$LANES_DIR"/lane-*-closeout.md)
    ((${#left[@]} == 0)) || { echo "could not archive ${left[*]} -- $dest already has it" >&2; exit 1; }
    echo "archived ${#files[@]} close-out(s) to $dest"
}

cmd_status() {
    for plan in "${PLANS[@]}"; do
        local branch wt ahead dirty
        branch=$(field "$plan" branch); wt=$(field "$plan" worktree)
        if [[ ! -e "$wt" ]]; then echo "$branch: no worktree yet"; continue; fi
        ahead=$(git -C "$PRELIM" rev-list --count "main..$branch")
        dirty=$(git -C "$wt" status --porcelain | wc -l)
        echo "$branch: $ahead commit(s) ahead of main, $dirty uncommitted; planned volumes $(field "$plan" volumes)"
        git -C "$PRELIM" diff --name-only "main...$branch" | sed 's/ - .*//' | sort | uniq -c | sed 's/^/    /'
    done
}

cmd_merge() {
    main_clean
    # Check every lane before merging any.
    for plan in "${PLANS[@]}"; do
        local branch wt vols
        branch=$(field "$plan" branch); wt=$(field "$plan" worktree); vols=$(field "$plan" volumes)
        [[ -e "$wt" ]] || { echo "$branch: no worktree" >&2; exit 1; }
        [[ -z "$(git -C "$wt" status --porcelain)" ]] || {
            echo "$branch: uncommitted changes in $wt" >&2; exit 1; }
        while IFS= read -r vol; do
            [[ -z "$vol" ]] && continue
            [[ " $vols " == *" $vol "* ]] || {
                echo "$branch touches Vol. $vol, which is not in its plan ($vols)" >&2; exit 1; }
        done < <(git -C "$PRELIM" diff --name-only "main...$branch" \
                 | sed -n 's/^Carl Barks Vol\. \([0-9]*\) .*/\1/p' | sort -u)
    done
    for plan in "${PLANS[@]}"; do
        local branch ahead titles msg
        branch=$(field "$plan" branch)
        ahead=$(git -C "$PRELIM" rev-list --count "main..$branch")
        if [[ "$ahead" == 0 ]]; then echo "$branch: nothing to merge"; continue; fi
        titles=$(python3 -c 'import json,sys; print(", ".join(t["title"] for t in json.load(open(sys.argv[1]))["titles"]))' "$plan")
        msg="Merge $branch: vision pass -- $titles"
        if [[ -n "${LANE_COMMIT_TRAILER:-}" ]]; then
            git -C "$PRELIM" merge --no-ff --quiet "$branch" -m "$msg" -m "$LANE_COMMIT_TRAILER"
        else
            git -C "$PRELIM" merge --no-ff --quiet "$branch" -m "$msg"
        fi
        echo "merged  $branch ($ahead commit(s))"
    done
    for plan in "${PLANS[@]}"; do
        git -C "$(field "$plan" worktree)" merge --ff-only --quiet main
    done
    echo "every lane branch now at main: $(git -C "$PRELIM" rev-parse --short main)"
}

case "${1:-}" in
    setup) cmd_setup ;;
    status) cmd_status ;;
    merge) cmd_merge ;;
    *) sed -n '2,8p' "$0" >&2; exit 2 ;;
esac
