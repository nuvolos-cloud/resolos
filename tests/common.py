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
    force_password=False,
):
    if "conda --version" in cmd:
        return 0, echo("conda 4.9.2")
    elif "unison -version" in cmd:
        return 0, echo("unison version 2.51.3")
    elif ".ssh/authorized_keys" in cmd:
        return 0, echo("[mock] Successfully set up SSH access on remote")
    elif "mkdir -p" in cmd:
        return 0, echo("[mock] Successfully created new folder structure on the remote")
    elif "rm -rf" in cmd:
        return 0, echo("[mock] Successfully deleted folder on the remote")
    elif "conda install" in cmd:
        return 0, echo("[mock] Successfully installed packages on the remote")
    elif "conda uninstall" in cmd:
        return 0, echo("[mock] Successfully uninstalled packages on the remote")
    elif "sbatch --wrap" in cmd:
        return 0, echo("[mock] Successfully submitted sbatch wrap job on the remote")
    elif "sbatch" in cmd:
        return 0, echo("[mock] Successfully submitted sbatch script on the remote")
    elif "scontrol show jobid" in cmd:
        return 0, echo("[mock] Successfully showed job details on the remote")
    elif "squeue" in cmd:
        return 0, echo("[mock] Successfully listed jobs on the remote")
    elif "scancel" in cmd:
        return 0, echo("[mock] Successfully cancelled job on the remote")
    elif "conda activate" in cmd:
        return 0, echo("[mock] Successfully activated conda environment on the remote")
    else:
        return 1, echo(f"Missing mock implementation for ssh command: '{cmd}'")


def fake_shell_cmd(
    cmd,
    max_wait_secs: int = 3600,
    sleep_secs: int = 1,
    stdout_as_info=False,
    shell_type="bash_interactive_login",
):
    if "unison -version" in cmd:
        return 0, echo("unison version 2.51.3")
    elif "export UNISON=" in cmd:
        return 0, echo("[mock] Successfully ran unison command")
    else:
        return 1, echo(f"Missing mock implementation for shell command: '{cmd}'")
