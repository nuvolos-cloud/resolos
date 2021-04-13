from click.testing import CliRunner
from resolos.interface import res_init, res_install, res_uninstall
from tests.common import verify_result, fake_ssh_cmd
from unittest.mock import patch
import logging

logger = logging.getLogger(__name__)


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
class TestInstall:
    remote_id = "test_remote"

    def test_install_uninstall_packages(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_init))
            verify_result(runner.invoke(res_install, ["xlrd", "python-dateutil"]))
            verify_result(runner.invoke(res_uninstall, ["xlrd", "python-dateutil"]))
