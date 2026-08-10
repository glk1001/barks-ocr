# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it rewrote is the whole point of running it.
"""Sort a review queue into volume, page, group, engine order, in place.

    python3 scripts/vision/sort_queue.py <queue.txt> [<queue.txt> ...]

The queue tools group their output by speaker category and print a
`# --- <category> ---` separator between the blocks, which is not the order a
reviewer works in: they work down a volume, page by page, and want both engines
for a group together. This rewrites the body into that order and drops the
category separators, keeping the summary header line at the top.

Each body line is `<volume> <page> <engine> <group> <kind>`, so the sort key is
fields 1, 2, 4 (numeric) and 3 -- group is field 4 and engine field 3, which is
why this is not a plain `sort -n`.
"""

import sys
from pathlib import Path

BODY_FIELDS = 5
USAGE = __doc__.strip().splitlines()[2].strip()
MIN_ARGV = 2  # argv[0] plus at least one queue file.


def key(line: str) -> tuple[int, int, int, str]:
    volume, page, engine, group = line.split()[:4]
    return (int(volume), int(page), int(group), engine)


def main() -> None:
    if len(sys.argv) < MIN_ARGV:
        msg = f"usage: {USAGE}"
        raise SystemExit(msg)

    for name in sys.argv[1:]:
        path = Path(name).expanduser()
        lines = path.read_text().splitlines()
        header = [line for line in lines if line.startswith("#") and "---" not in line]
        body = [line for line in lines if line and not line.startswith("#")]
        bad = [line for line in body if len(line.split()) != BODY_FIELDS]
        if bad:
            msg = f"{path}: unexpected line {bad[0]!r}"
            raise SystemExit(msg)
        body.sort(key=key)
        path.write_text("\n".join([*header, *body]) + "\n")
        print(f"{path}  {len(body)} entr{'y' if len(body) == 1 else 'ies'}, sorted")


if __name__ == "__main__":
    main()
