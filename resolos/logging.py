import click_log
import logging


class MyFormatter(click_log.ColorFormatter):
    def format(self, record):
        msg = click_log.ColorFormatter.format(self, record)
        if record.levelname in ("DEBUG", "INFO"):
            new_msg = "> " + msg
        elif record.levelname in ("WARNING"):
            new_msg = ">> " + msg
        elif record.levelname in ("ERROR", "CRITICAL"):
            new_msg = ">>> " + msg
        else:
            new_msg = msg
        return new_msg


clog = logging.getLogger(__name__)
myhandler = click_log.ClickHandler()
myhandler.formatter = MyFormatter()
clog.handlers = [myhandler]
clog.propagate = False
