from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_info
from tests.common import verify_result
import logging

logger = logging.getLogger(__name__)


def test_info():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        verify_result(runner.invoke(res_info))
