from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_init, res_run
from tests.common import verify_result
import logging

logger = logging.getLogger(__name__)


def test_init_empty():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        logger.info("Creating new project")
        verify_result(runner.invoke(res_init, ["-y"]))
        logger.info("Checking conda version")
        verify_result(runner.invoke(res_run, ["conda --version"]))


def test_download():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        logger.info("Checking conda version")
        verify_result(
            runner.invoke(
                res_init,
                [
                    "-s",
                    "https://resolos.s3.eu-central-1.amazonaws.com/examples/data_with_pandas.tar.gz",
                ],
            )
        )
        assert (Path(fs) / "process_dataset.py").exists()
