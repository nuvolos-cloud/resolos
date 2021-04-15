from click.testing import CliRunner
from resolos.interface import (
    res_remote_add,
    res_remote_remove,
    res_remote_update,
    res_remote_list,
)
from resolos.remote import read_remote_db
from tests.common import verify_result
import logging

logger = logging.getLogger(__name__)


class TestIntegration:
    remote_id = "test_remote"

    def test_remote_add(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(
                runner.invoke(
                    res_remote_add, [self.remote_id, "-h", "localhost", "-u", ]
                )
            )
            remotes_list = read_remote_db()
            assert self.remote_id in remotes_list
            remotes_settings = remotes_list[self.remote_id]
            assert remotes_settings["hostname"] == "hostname"
            assert remotes_settings["username"] == "username"

    def test_remote_remove(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_remote_remove, [self.remote_id]))