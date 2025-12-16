
import sys
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.whoosh_search_engine import SearchEngine
from loguru import logger
from loguru_config import LoguruConfig

APP_LOGGING_NAME = "clni"


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
            ExtraArg("--create-index", action="store_true", type=bool, default=False),
            ExtraArg("--unstemmed", action="store_true", type=bool, default=False),
            ExtraArg("--words", action="store", type=str, default=""),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
            "Clean unstemmed words in Whoosh index", CmdArgNames.VOLUME, extra_args
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = Path(__file__).stem + ".log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    search_engine = SearchEngine(
            Path("/home/greg/Books/Carl Barks/Compleat Barks Disney Reader/Reader Files/Indexes"))
    unstemmed_words = search_engine.get_unstemmed_terms()
