from click.testing import CliRunner
from resolos.interface import (
    res,
    res_job,
    res_job_run,
    res_job_list,
    res_job_cancel,
    res_job_status,
)
from tests.common import verify_result, fake_ssh_cmd
from unittest.mock import patch
from pytest import mark
from resolos.exception import LocalCommandError
import logging
import os

logger = logging.getLogger(__name__)


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.job.run_ssh_cmd", wraps=fake_ssh_cmd)
@mark.usefixtures("class_proj")
class TestJob:
    def test_job_run(self, *args):
        runner = CliRunner()
        verify_result(runner.invoke(res, ["job", "run", "dummy_command"]))
