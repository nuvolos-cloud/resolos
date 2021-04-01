from .logging import clog
from .platform import (
    resolos_relative_path,
    find_project_dir,
)
from .shell import run_ssh_cmd
from .exception import RemoteCommandError, NotAProjectFolderError
from .conda import sync_env_and_files, sync_files, check_conda_env_exists_remote
import pathlib


def run_slurm_command(remote_settings, cmd):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        cmd,
        stdout_as_info=True,
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Remote command '{cmd}' raised error on remote '{remote_settings['name']}':\n\n{output}\n\n"
        )
    return output


def job_cancel(remote_settings, job_id):
    return run_slurm_command(remote_settings, f"scancel {job_id}")


def job_status(remote_settings, job_id):
    return run_slurm_command(remote_settings, f"scontrol show jobid {job_id}")


def job_list(remote_settings, all_users=False):
    if all_users:
        return run_slurm_command(remote_settings, f"squeue")
    else:
        return run_slurm_command(
            remote_settings, f"squeue -u {remote_settings['username']}"
        )


def job_submit(remote_settings, remote_path, submission_script):
    script_rel_path = resolos_relative_path(pathlib.Path(submission_script))
    return run_slurm_command(
        remote_settings, f"cd {remote_path} && sbatch {script_rel_path}"
    )


def job_run(
    remote_settings,
    remote_env,
    remote_path,
    cmd,
    partition=None,
    ntasks=None,
    cpus_per_task=None,
    nodes=None,
):
    full_cmd = (
        f"cd {remote_path} && "
        f'sbatch --wrap "{remote_settings["conda_load_command"]} && conda activate {remote_env} && {cmd}"'
    )
    if partition:
        full_cmd = full_cmd + f" -p {partition}"
    if ntasks:
        full_cmd = full_cmd + f" -n {ntasks}"
    if cpus_per_task:
        full_cmd = full_cmd + f" -c {cpus_per_task}"
    if nodes:
        full_cmd = full_cmd + f" -N {nodes}"

    if not check_conda_env_exists_remote(remote_settings, remote_env):
        clog.info("Syncing remote files and conda environment...")
        sync_env_and_files(remote_settings)
    else:
        clog.info("Syncing remote files...")
        sync_files(remote_settings)
    clog.info("Submitting job")
    return run_slurm_command(
        remote_settings,
        full_cmd,
    )
