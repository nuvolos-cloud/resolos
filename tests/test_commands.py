from pathlib import Path
from click.testing import CliRunner
from resolos.interface import res_init, res_run


def test_init_empty():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(res_init, ["-y"])
        assert result.exit_code == 0
        result2 = runner.invoke(res_run, ["conda --version"])
        assert result2.exit_code == 0
        #assert result2.output.startswith("> conda ")


def test_download():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(res_init, ["-s", "https://resolos.s3.eu-central-1.amazonaws.com/examples/data_with_pandas.tar.gz"])
        assert result.exit_code == 0
        assert (Path(fs) / "process_dataset.py").exists()
