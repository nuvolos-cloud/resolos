from click.testing import CliRunner
from resolos.interface import (
    res_remote_add,
    res_remote_remove,
    res_init,
    res_sync,
    res_job_run
)
from resolos.remote import read_remote_db
from tests.common import verify_result
import logging
from pathlib import Path
import os


logger = logging.getLogger(__name__)
USER = os.environ["TEST_USER"]
PWD = os.environ["TEST_PASSWORD"]


class TestIntegration:
    remote_id = "test_remote"

    def test_remote_add(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(
                runner.invoke(
                    res_remote_add,
                    [self.remote_id, "-h", "localhost", "-u", USER],
                    input=f"{PWD}\n{PWD}\n{PWD}\n{PWD}\n{PWD}\n"
                )
            )
            remotes_list = read_remote_db()
            assert self.remote_id in remotes_list
            remotes_settings = remotes_list[self.remote_id]
            assert remotes_settings["hostname"] == "hostname"
            assert remotes_settings["username"] == "username"

    def test_job(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            # Initialize a new local project
            verify_result(runner.invoke(res_init, ["-y"]))
            with (Path(fs) / "test_script.py").open("w") as py:
                py.write("""with open('test_output.txt') as txtf:
    txtf.write('Hello, world!')""")
            verify_result(runner.invoke(res_sync, ["-r", self.remote_id]))
            verify_result(runner.invoke(res_job_run, ["-r", self.remote_id, "run", "'python test_script.py'"]))
            verify_result(runner.invoke(res_sync, ["-r", self.remote_id]))
            assert (Path(fs) / "test_output.txt").exists()

    def test_remote_remove(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            verify_result(runner.invoke(res_remote_remove, [self.remote_id]))