from click.testing import CliRunner
from resolos.interface import res_check
import logging

logger = logging.getLogger(__name__)


def test_check():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(res_check, ["--raise-on-error"])
        assert result.exit_code == 0, result.stderr
