"""Volumes the vision pass must not read yet, while the reviewer is cleaning them.

The list lives in ``scripts/vision/volume-holds.txt`` beside the missed-text
ignore list, so lifting a hold is a one-line edit with the reason next to it. See
that file's header for why holds exist.
"""

from pathlib import Path

HOLDS_FILE = Path(__file__).resolve().parents[3] / "scripts" / "vision" / "volume-holds.txt"


def held_volumes(holds_file: Path = HOLDS_FILE) -> dict[int, str]:
    """Return the held volumes, each with the reason written beside it.

    A missing file means nothing is held, so a checkout without it behaves as
    before rather than failing.

    Args:
        holds_file: The list to read.

    Returns:
        Volume number to reason (an empty string when none was given).

    Raises:
        ValueError: A non-comment line does not start with a volume number.

    """
    if not holds_file.is_file():
        return {}
    holds: dict[int, str] = {}
    for n, raw in enumerate(holds_file.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, reason = line.partition(" ")
        if not head.isdigit():
            msg = f"{holds_file}:{n}: expected a volume number, got {head!r}"
            raise ValueError(msg)
        holds[int(head)] = reason.strip()
    return holds
