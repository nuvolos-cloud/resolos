from click.testing import CliRunner
from resolos.interface import res_init, res_teardown
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
