import click_logging
import logging


class MyFormatter(click_logging.ColorFormatter):
    def __init__(self, style_kwargs):
        super().__init__(style_kwargs)

    def format(self, record):
        msg = click_logging.ColorFormatter.format(self, record)
        if record.levelname in ("DEBUG", "INFO"):
            new_msg = "> " + msg
        elif record.levelname in ("WARNING"):
            new_msg = ">> " + msg
        elif record.levelname in ("ERROR", "CRITICAL"):
            new_msg = ">>> " + msg
        else:
            new_msg = msg
        return new_msg


normalized_styles = {
    "error": dict(fg="red"),
    "exception": dict(fg="red"),
    "critical": dict(fg="red"),
    "debug": dict(fg="blue"),
    "warning": dict(fg="yellow"),
}
normalized_echo_kwargs = dict()

clog = logging.getLogger(__name__)


def my_basic_config(logger=None, style_kwargs=None, echo_kwargs=None):
    myhandler = click_logging.ClickHandler(echo_kwargs)
    myhandler.formatter = MyFormatter(style_kwargs)
    logger.handlers = [myhandler]
    logger.propagate = False
    return logger


clog = my_basic_config(clog, normalized_styles, normalized_echo_kwargs)
