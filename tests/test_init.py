from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_init, res_run
from tests.common import verify_result
import logging

logger = logging.getLogger(__name__)


def test_init_empty():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        verify_result(runner.invoke(res_init, ["-y"]))


def test_init_from_archive():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        project_folder = Path(fs)
        verify_result(
            runner.invoke(
                res_init,
                [
                    "-s",
                    "https://resolos.s3.eu-central-1.amazonaws.com/examples/data_with_pandas.tar.gz",
                ],
            )
        )
        assert (project_folder / "README.md").exists()
        assert (project_folder / "process_dataset.py").exists()
        assert (project_folder / "var_spx_monthly.csv").exists()
        assert not (project_folder / "var_spx_monthly_mean.csv").exists()
        output = verify_result(
            runner.invoke(
                res_run,
                ["python process_dataset.py"],
            )
        )
        assert "Written the mean of the columns to var_spx_monthly_mean.csv" in output
        assert (project_folder / "README.md").exists()
        assert (project_folder / "process_dataset.py").exists()
        assert (project_folder / "var_spx_monthly.csv").exists()
        assert (project_folder / "var_spx_monthly_mean.csv").exists()
