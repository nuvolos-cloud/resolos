from click.testing import CliRunner
from resolos.interface import (
    res,
    res_job,
    res_job_run,
    res_job_list,
    res_job_cancel,
    res_job_status,
)
from tests.common import verify_result, fake_ssh_cmd, fake_shell_cmd
from unittest.mock import patch
from pytest import mark
from resolos.exception import LocalCommandError
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_shell_cmd", wraps=fake_shell_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.job.run_ssh_cmd", wraps=fake_ssh_cmd)
@mark.usefixtures("class_proj")
@mark.usefixtures("test_remote")
class TestJob:
    def test_job_run(self, *args):
        runner = CliRunner()
        verify_result(
            runner.invoke(res, ["-v", "DEBUG", "job", "run", "dummy_command"])
        )

    def test_job_submit(self, *args):
        runner = CliRunner()
        script_name = "dummy_script_name"
        Path(script_name).touch()
        verify_result(runner.invoke(res, ["-v", "DEBUG", "job", "submit", script_name]))

    def test_job_cancel(self, *args):
        runner = CliRunner()
        verify_result(
            runner.invoke(res, ["-v", "DEBUG", "job", "cancel", "dummy_jobid"])
        )

    def test_job_list(self, *args):
        runner = CliRunner()
        verify_result(runner.invoke(res, ["-v", "DEBUG", "job", "list"]))

    def test_job_status(self, *args):
        runner = CliRunner()
        verify_result(
            runner.invoke(res, ["-v", "DEBUG", "job", "status", "dummy_jobid"])
        )
