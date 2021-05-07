from click.testing import CliRunner
from resolos.interface import res
from tests.common import verify_result, fake_ssh_cmd, fake_shell_cmd
from unittest.mock import patch
from pytest import mark
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def create_project_files(project_folders, project_files):
    for f in project_folders:
        f.mkdir()
    for f in project_files:
        f.touch()


def check_project_files_exist(project_folders, project_files):
    for f in project_folders:
        assert f.exists(), f"Folder {f} is missing"
    for f in project_files:
        assert f.exists(), f"File {f} is missing"


def check_project_files_missing(project_folders, project_files):
    for f in project_folders:
        assert not f.exists(), f"Folder {f} exists"
    for f in project_files:
        assert not f.exists(), f"File {f} exists"


def delete_project_files(project_folders, project_files):
    for f in reversed(project_files):
        f.unlink()
    for f in reversed(project_folders):
        f.rmdir()


@patch("resolos.shell.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.conda.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.unison.run_shell_cmd", wraps=fake_shell_cmd)
@patch("resolos.check.run_ssh_cmd", wraps=fake_ssh_cmd)
@patch("resolos.job.run_ssh_cmd", wraps=fake_ssh_cmd)
@mark.usefixtures("class_proj")
class TestArchive:
    # Folders will be created in sequence, and removed in reversed order
    test_folders = [Path("folder1"), Path("folder1/folder2"), Path("empty_folder")]
    test_files = [
        Path("file1.txt"),
        Path("folder1/file2.txt"),
        Path("folder1/folder2/file3.txt"),
    ]
    test_archive = f"{tempfile.mkdtemp()}/test_archive.tar.gz"

    def test_archive_create_load(self, *args):
        create_project_files(self.test_folders, self.test_files)
        runner = CliRunner()
        verify_result(
            runner.invoke(
                res, ["-v", "DEBUG", "archive", "create", "-f", self.test_archive]
            )
        )
        delete_project_files(self.test_folders, self.test_files)
        verify_result(
            runner.invoke(
                res, ["-v", "DEBUG", "archive", "load", "-f", self.test_archive, "-y"]
            )
        )
        check_project_files_exist(self.test_folders, self.test_files)
