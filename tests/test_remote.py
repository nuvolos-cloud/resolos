from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_remote_add, res_remote_update, res_remote_list, res_remote_remove
from tests.common import verify_result, mock_shell_cmd
import logging
import pytest
from unittest.mock import patch


logger = logging.getLogger(__name__)


def test_list_empty():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        verify_result(runner.invoke(res_remote_list))


@pytest.mark.xfail
def test_remove_nonexistent():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        verify_result(runner.invoke(res_remote_remove, ["test_remote"]))


def test_add_then_list():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        with patch("resolos.shell.run_shell_cmd", mock_shell_cmd):
            verify_result(runner.invoke(res_remote_add, ["test_remote", "-u", "test_user", "-h", "remote.host.name"]))
            verify_result(runner.invoke(res_remote_list))