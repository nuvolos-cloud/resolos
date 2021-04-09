from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_init, res_run
import logging

logger = logging.getLogger(__name__)


def test_init_empty():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        logger.info("Creating new project")
        result = runner.invoke(res_init, ["-y"])
        assert result.exit_code == 0, result.stderr
        logger.info("Checking conda version")
        result2 = runner.invoke(res_run, ["conda --version"])
        assert result2.exit_code == 0, result.stderr


def test_download():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        logger.info("Checking conda version")
        result = runner.invoke(
            res_init,
            [
                "-s",
                "https://resolos.s3.eu-central-1.amazonaws.com/examples/data_with_pandas.tar.gz",
            ],
        )
        assert result.exit_code == 0, result.stderr
        assert (Path(fs) / "process_dataset.py").exists(), result.output
