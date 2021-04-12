import logging
from click.testing import Result
from time import sleep

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


def mock_shell_cmd(
            cmd,
            max_wait_secs: int = 3600,
            sleep_secs: int = 1,
            stdout_as_info=False,
            shell_type="bash_interactive_login",
    ):
    logger.info(f"""Running mock shell command: [{cmd}]
    max_wait_secs: [{max_wait_secs}]
    sleep_secs: [{sleep_secs}]
    stdout_as_info: [{stdout_as_info}]
    shell_type: [{shell_type}]""")
    sleep(5)
    logger.info("Returning 0, 'Mock output'")
    return 0, "Mock output"


# def fake_ssh_command(
#     remote_settings,
#     cmd,
#     max_wait_secs: int = 3600,
#     sleep_secs: int = 1,
#     stdout_as_info=False,
#     shell_type="bash_login",
#     login_shell_remote=True,
# ):
#     logger.info(f"""Running fake SSH command: [{cmd}]
#     stdout_as_info: [{stdout_as_info}]
#     shell_type: [{shell_type}]
#     login_shell_remote: [{login_shell_remote}]""")
#     sleep(3)
#     return fake_shell_cmd(
#         ssh_cmd,
#         max_wait_secs=max_wait_secs,
#         sleep_secs=sleep_secs,
#         stdout_as_info=stdout_as_info,
#         shell_type=shell_type,
#     )