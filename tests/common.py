import logging
from click.testing import Result

logger = logging.getLogger(__name__)


def verify_result(result: Result):
    if result.exit_code != 0:
        logger.info(result.output)
        if result.exception:
            raise result.exception
        else:
            raise Exception(
                f"Exit code was {result.exit_code}, but no exception was caught"
            )
    else:
        return result.output
