from click.testing import CliRunner
from resolos.interface import (
    res_remote_add,
    res_remote_remove,
    res_init,
    res_sync,
    res
)
from resolos.remote import read_remote_db, list_remote_ids, delete_remote   
from tests.common import verify_result
import logging
from pathlib import Path
import os


logger = logging.getLogger(__name__)
USER = os.environ["TEST_USER"]
PWD = os.environ["SSHPASS"]
HOST = os.environ["TEST_HOST"]

class TestIntegration:
    remote_id = "test_remote"

    def test_job(self, *args):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            # Initialize a new local project
            logger.info(f"Initializing new project in {fs}")
            verify_result(runner.invoke(res, ["-v", "DEBUG", "info"]))
            verify_result(runner.invoke(res_init, ["-y"]))
            # Add remote
            logger.info(f"### Adding remote in {fs}")
            verify_result(
                runner.invoke(
                    res_remote_add,
                    [self.remote_id, "-y", "-h", HOST, "-p", "3144", "-u", USER, "--remote-path", "/data/integration_test", "--conda-install-path", "/data", "--conda-load-command", "source /data/miniconda/bin/activate"]
                )
            )
            remotes_list = read_remote_db()
            assert self.remote_id in remotes_list
            remotes_settings = remotes_list[self.remote_id]
            assert remotes_settings["hostname"] == HOST
            assert remotes_settings["username"] == USER
            # Run job
            with (Path(fs) / "test_script.py").open("w") as py:
                py.write("""with open('test_output.txt', 'w') as txtf:
    txtf.write('Hello, world!')""")
            logger.info(f"### Syncing with remote {self.remote_id}")
            verify_result(runner.invoke(res_sync, ["-r", self.remote_id]))
            logger.info(f"### Running test job on {self.remote_id}")
            verify_result(runner.invoke(res, ["-v", "DEBUG", "job", "-r", self.remote_id, "run", "-p", "normal", "python test_script.py"]))
            # Sync back job results
            logger.info(f"### Syncing results from remote {self.remote_id}")
            verify_result(runner.invoke(res_sync, ["-r", self.remote_id]))
            assert (Path(fs) / "test_output.txt").exists()
            # Remove remote
            logger.info(f"### Removing remote {self.remote_id}")
            verify_result(runner.invoke(res_remote_remove, [self.remote_id]))