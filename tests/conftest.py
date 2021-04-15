from click.testing import CliRunner
from resolos.interface import res_init, res_teardown, res_remote_add, res_remote_remove
from tests.common import verify_result
from pytest import fixture
import os
import tempfile
import shutil


@fixture(scope="class")
def class_proj(request):
    # Creates a new empty resolos project for the test class
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    runner = CliRunner()
    verify_result(runner.invoke(res_init, ["--no-remote-setup"]))
    request.cls.t = t
    yield
    try:
        verify_result(runner.invoke(res_teardown, ["--skip-remotes"]))
        os.chdir(cwd)
        shutil.rmtree(t)
    except (OSError, IOError):  # noqa: B014
        pass


@fixture(scope="class")
def test_remote(request):
    # Creates a test remote for the class
    runner = CliRunner()
    verify_result(
        runner.invoke(
            res_remote_add, ["test_remote_id", "-h", "hostname", "-u", "username"]
        )
    )
    yield
    verify_result(runner.invoke(res_remote_remove, ["test_remote_id"]))
