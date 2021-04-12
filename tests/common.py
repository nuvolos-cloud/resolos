import logging
from click.testing import Result
from resolos.logging import clog

logger = logging.getLogger(__name__)


def verify_result(result: Result):
    logger.debug(result.output)
    if result.exit_code != 0:
        if result.exception:
            raise result.exception
        else:
            raise Exception(
                f"Exit code was {result.exit_code}, but no exception was caught"
            )
    else:
        return result.output


def echo(msg):
    clog.debug(msg)
    return msg


def fake_ssh_cmd(
    remote_settings,
    cmd,
    max_wait_secs: int = 3600,
    sleep_secs: int = 1,
    stdout_as_info=False,
    shell_type="bash_login",
    login_shell_remote=True,
):
    if "conda --version" in cmd:
        return 0, echo("conda 4.9.2")
    elif "unison -version" in cmd:
        return 0, echo("unison version 2.51.3")
    elif ".ssh/authorized_keys" in cmd:
        return 0, echo("Successfully set up SSH access on remote")
    else:
        return 1, echo(f"Missing mock implementation for command: '{cmd}'")
