from click.testing import CliRunner
from resolos.interface import res_check
from tests.common import verify_result
import logging

logger = logging.getLogger(__name__)


def test_check():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        verify_result(runner.invoke(res_check, ["--raise-on-error"]))
