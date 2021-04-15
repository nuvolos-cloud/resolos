from click.testing import CliRunner
from resolos.interface import res_init, res_install, res_uninstall, res_run
from tests.common import verify_result, fake_ssh_cmd
from unittest.mock import patch
from pytest import raises
from resolos.exception import LocalCommandError
import logging

logger = logging.getLogger(__name__)


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
class TestInstall:
    test_command = "python -c 'import dateutil; import xlrd'"

    def test_install_uninstall_packages(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_init))
            with raises(LocalCommandError):
                verify_result(runner.invoke(res_run, [self.test_command]))
            verify_result(runner.invoke(res_install, ["xlrd", "python-dateutil"]))
            verify_result(runner.invoke(res_run, [self.test_command]))
            verify_result(runner.invoke(res_uninstall, ["xlrd", "python-dateutil"]))
            with raises(LocalCommandError):
                verify_result(runner.invoke(res_run, [self.test_command]))
