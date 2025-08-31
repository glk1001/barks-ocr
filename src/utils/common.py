from enum import Enum, auto


class ProcessResult(Enum):
    SUCCESS = auto()
    SKIPPED = auto()
    FAILURE = auto()
