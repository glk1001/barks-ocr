#!/usr/bin/env bash
# Run `ocr_check --fix-padding` one volume at a time: write, verify, commit, queue.
#
#     bash scripts/vision/padding_rollout.sh QUEUE_DIR VOLUME [VOLUME ...]
#
# For each volume, in order:
#   1. refuses to start unless the prelim repo is clean (ocr_check's own --fix rule:
#      every fix must be undoable with git);
#   2. runs `barks-ocr-check --volume N --fix-padding`, logging to QUEUE_DIR/logs;
#   3. runs scripts/vision/padding_verify.py, which refuses the write unless only
#      `text_box` changed and both engines still agree as they did at HEAD, and which
#      writes QUEUE_DIR/volN-padded.txt for an editor spot-check;
#   4. stages that volume's files BY PATH and commits them as one prelim commit,
#      naming the barks-ocr commit that wrote them.
# It stops at the first volume that fails any step and leaves it uncommitted.
#
# WHAT IT ASSUMES. The prelim repo is `OCR_PRELIM_DIR` -- set BARKS_OCR_PRELIM_DIR to
# use a worktree -- and is otherwise idle: NO EDITOR SESSION may be open on it. The
# editor holds the page it shows in memory, so a page padded here and then saved
# there loses one of the two writes. (2026-10-11: a reviewer's queue reached Vol. 1
# while this ran on Vol. 7; the path-scoped verify and staging kept the two apart.)
# Run it from the barks-ocr repo root.
#
# Set PADDING_COMMIT_TRAILER to append a trailer line (e.g. Co-Authored-By) to each
# commit, as lanes.sh's LANE_COMMIT_TRAILER does.
#
# Calibration and the measurement are in src/barks_ocr/utils/box_padding.py; dry-run
# a volume first with `barks-ocr-check --volume N --check-padding`.
set -u

if [ $# -lt 2 ]; then
  sed -n '2,28p' "$0"
  exit 2
fi
QUEUE_DIR=$1
shift
mkdir -p "$QUEUE_DIR/logs"

PRELIM=$(uv run --offline python -c \
  'from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR; print(OCR_PRELIM_DIR)' 2>/dev/null)
[ -d "$PRELIM" ] || { echo "No prelim dir: '$PRELIM'"; exit 1; }
WRITER=$(git rev-parse --short HEAD)

for v in "$@"; do
  [ -z "$(git -C "$PRELIM" status --short)" ] || { echo "STOP vol $v: prelim repo not clean"; exit 1; }

  uv run --offline barks-ocr-check --volume "$v" --fix-padding \
    -o "$QUEUE_DIR/logs/vol$v-after.txt" --log-level INFO > "$QUEUE_DIR/logs/vol$v.log" 2>&1 \
    || { echo "STOP vol $v: ocr_check failed (see logs/vol$v.log)"; exit 1; }

  mapfile -t files < <(git -C "$PRELIM" diff --name-only | grep "^Carl Barks Vol. $v - ")
  if [ ${#files[@]} -eq 0 ]; then
    echo "vol $v: nothing to fix"
    continue
  fi

  out=$(uv run --offline python scripts/vision/padding_verify.py "$v" "$QUEUE_DIR/vol$v-padded.txt" 2>&1 \
    | grep -v "| DEBUG\|| INFO\|| WARNING")
  echo "vol $v: $out"
  echo "$out" | grep -q "^CHANGED" || { echo "STOP vol $v: verification failed, left uncommitted"; exit 1; }
  n=$(echo "$out" | awk '/^CHANGED/{print $2}')

  git -C "$PRELIM" add -- "${files[@]}"
  if git -C "$PRELIM" diff --cached --name-only | grep -qv "^Carl Barks Vol. $v - "; then
    echo "STOP vol $v: something outside the volume is staged"
    exit 1
  fi
  msg="fix(boxes): Vol. $v text_boxes padded out to their lettering

ocr_check --fix-padding (barks-ocr $WRITER) padded $n balloon text_box(es),
counted per engine, whose lettering crossed an edge out to the house
padding. Only text_box changed, and both engines' boxes still agree as
they did before."
  trailer=()
  [ -n "${PADDING_COMMIT_TRAILER:-}" ] && trailer=(-m "$PADDING_COMMIT_TRAILER")
  git -C "$PRELIM" commit -q -m "$msg" "${trailer[@]}" > "$QUEUE_DIR/logs/vol$v-commit.log" 2>&1 \
    || { echo "STOP vol $v: commit failed (see logs/vol$v-commit.log)"; exit 1; }
  echo "vol $v: committed $(git -C "$PRELIM" log -1 --format=%h)"
done
echo DONE
