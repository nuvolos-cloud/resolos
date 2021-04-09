from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_info
import logging

logger = logging.getLogger(__name__)


def test_info():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(res_info)
        assert result.exit_code == 0, result.stderr
