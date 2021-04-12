from click.testing import CliRunner
from resolos.interface import (
    res_remote_add,
    res_remote_remove,
    res_remote_update,
    res_remote_list,
)
from resolos.remote import read_remote_db
from tests.common import verify_result, fake_ssh_cmd
from unittest.mock import patch
from pytest import raises
from resolos.exception import RemoteMissingError
import logging

logger = logging.getLogger(__name__)


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
class TestRemote:
    remote_id = "test_remote"

    def test_list_empty(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_remote_list))

    def test_remove_nonexistent(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            with raises(RemoteMissingError):
                verify_result(runner.invoke(res_remote_remove, [self.remote_id]))

    def test_remote_add(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(
                runner.invoke(
                    res_remote_add, [self.remote_id, "-h", "hostname", "-u", "username"]
                )
            )
            remotes_list = read_remote_db()
            assert self.remote_id in remotes_list
            remotes_settings = remotes_list[self.remote_id]
            assert remotes_settings["hostname"] == "hostname"
            assert remotes_settings["username"] == "username"

    def test_remote_update(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(
                runner.invoke(
                    res_remote_update,
                    [self.remote_id, "-h", "hostname2", "-u", "username2"],
                )
            )
            remotes_list = read_remote_db()
            assert self.remote_id in remotes_list
            remotes_settings = remotes_list[self.remote_id]
            assert remotes_settings["hostname"] == "hostname2"
            assert remotes_settings["username"] == "username2"

    def test_remote_remove(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_remote_remove, [self.remote_id]))
