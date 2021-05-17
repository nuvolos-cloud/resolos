import click
from .config import (
    initialize_user_configs,
    get_project_env,
    get_project_settings_for_remote,
    info,
    verify_mutually_exclusive_options,
)
import click_log
from .logging import clog
from .remote import (
    get_remote,
    list_remote_ids,
    read_remote_db,
)
from .remote_configuration import (
    add_remote_configuration,
    update_remote_configuration,
    teardown_remote_configuration,
)
from .check import check_target, check, setup_ssh
from .unison import sync_files
from .conda import (
    execute_command_in_local_conda_env,
    install_conda_packages,
    uninstall_conda_packages,
    sync_env_and_files,
)
from .archive import make_archive, load_archive
from .job import job_cancel, job_list, job_status, job_submit, job_run
from .exception import NoRemotesError
from .init import init_project, teardown
import yaml


@click.group("res")
@click_log.simple_verbosity_option(clog)
@click.pass_context
def res(ctx):
    """
    Resolos is a toolkit for managing and archiving scientific projects
    both on local development machines and remote HPC cluster.

    """
    if ctx.obj is None:
        ctx.obj = dict()
    initialize_user_configs()


@res.command("init")
@click.option(
    "--env-name",
    type=str,
    help="The name of the local conda environment for software dependencies. Will be created if not exists",
)
@click.option(
    "--remote-env-name",
    type=str,
    help="The name of the conda environment for software dependencies to be used on remotes. "
    "Will be created if not exists",
)
@click.option(
    "--remote-path",
    type=str,
    help="The path of the project folder on the remote. Will be created if not exists",
)
@click.option(
    "--base-url",
    type=str,
    envvar="YARETA_BASE_URL",
    default="https://access.yareta.unige.ch",
    help="The base url of the Yareta API",
)
@click.option(
    "-a",
    "--access-token",
    type=str,
    envvar="YARETA_ACCESS_TOKEN",
    help="The personal DLCM access token",
)
@click.option(
    "-d",
    "--deposit-id",
    type=str,
    help="The deposit id of the Yareta deposit",
)
@click.option(
    "-f",
    "--filename",
    type=click.Path(),
    help="The filename of the archive to load",
)
@click.option(
    "-u",
    "--url",
    type=str,
    help="The publicly accessible url to load the archive from",
)
@click.option(
    "-y",
    is_flag=True,
    help="If specified, no prompts will be displayed to install conda/unison.",
    required=False,
)
@click.option(
    "--no-remote-setup",
    is_flag=True,
    help="If specified, remote configuration will be skipped (syncing of project files and environment)",
    required=False,
)
@click.pass_context
def res_init(ctx, **kwargs):
    """
    Initializes a new resolos project in the current working directory. The following steps are executed:

    - Creates the project configuration folder .resolos

    - Initializes a new conda environment or link and existing one for the project

    """

    verify_mutually_exclusive_options(
        ["url", "filename", "deposit_id"],
        ["--url", "--filename", "--deposit-id"],
        must_select_one=False,
        **kwargs,
    )
    check_target(no_confirm=kwargs.get("y", False))
    init_project(
        base_url=kwargs.get("base_url"),
        access_token=kwargs.get("access_token"),
        url=kwargs.get("url"),
        filename=kwargs.get("filename"),
        deposit_id=kwargs.get("deposit_id"),
        local_env_name=kwargs.get("env_name"),
        remote_env_name=kwargs.get("remote_env_name"),
        remote_files_path=kwargs.get("remote_path"),
        no_confirm=kwargs.get("y", False),
        no_to_remote_setup=kwargs.get("no_remote_setup"),
    )


@res.command("teardown")
@click.option(
    "--skip-local",
    is_flag=True,
    help="If specified, the local environment and the .resolos folder will not be deleted",
    required=False,
)
@click.option(
    "--skip-remotes",
    is_flag=True,
    help="If specified, the remote environment and the synced files will not be deleted",
    required=False,
)
@click.pass_context
def res_teardown(ctx, **kwargs):
    """
    Reverses the steps of resolos init:

    - Clears the project configuration folder .resolos

    - Removes the linked conda environment

    """
    teardown(kwargs.get("skip_local", False), kwargs.get("skip_remotes", False))


@res.command("check")
@click.option(
    "--raise-on-error",
    is_flag=True,
    help="Do not offer installing missing dependencies on remotes, raise exception instead",
    required=False,
)
@click.pass_context
def res_check(ctx, **kwargs):
    """
    Runs some checks for the configured remotes and the local environment.
    Must be called from a resolos project

    """
    check(kwargs.get("raise_on_error", False))


@res.command("info")
@click.pass_context
def res_info(ctx, **kwargs):
    """
    Returns resolos global configuration.
    When called from a resolos project, it displays configuration for the project itself as well.

    """
    info()


@res.command("setup-ssh")
@click.option(
    "-r",
    "--remote",
    help="The name of the remote running the jobs. Can be omitted if there is only one remote configured",
    required=False,
)
@click.pass_context
def res_setup_ssh(ctx, **kwargs):
    """
    Configures passwordless SSH access via SSH keys.
    Only needs to be run once per remote.

    """
    remote_settings = get_remote(read_remote_db(), kwargs.get("remote"))
    setup_ssh(remote_settings)


@res.group("remote")
@click.pass_context
def res_remote(ctx):
    """
    Remotes are machines with SSH access supporting job execution with some job scheduler.
    Currently only Slurm running on Linux machines is supported.
    """
    pass


@res_remote.command("add")
@click.argument("name")
@click.option(
    "-h",
    "--hostname",
    type=str,
    help="The host name of the remote server for the SSH connection.",
    required=True,
)
@click.option(
    "-u",
    "--username",
    type=str,
    help="Username on the remote server for the SSH connection",
    required=True,
)
@click.option(
    "-p", "--port", type=int, default=22, help="Port for using the SSH connection"
)
@click.option(
    "--scheduler",
    type=str,
    default="slurm",
    help="The type of the scheduler on the remote",
)
@click.option(
    "--conda-load-command",
    type=str,
    default="source ~/miniconda/bin/activate",
    help="The command that makes the 'conda' command available for the shell",
)
@click.option(
    "--conda-install-path",
    type=str,
    default="~",
    help="The path to install miniconda on the remote, if required",
)
@click.option(
    "--unison-path",
    type=str,
    default="./bin/unison",
    help="The path of the unison executable on the remote",
)
@click.option(
    "--remote-env-name",
    type=str,
    help="The name of the conda environment for software dependencies to be used on remotes. "
    "Will be created if not exists",
)
@click.option(
    "--remote-path",
    type=str,
    help="The path of the project folder on the remote. Will be created if not exists",
)
@click.option(
    "--no-remote-setup",
    is_flag=True,
    help="If specified, remote configuration will be skipped (ssh key setup, syncing of project files and environment)",
    required=False,
)
@click.option(
    "-y",
    is_flag=True,
    help="If specified, SSH key setup, conda and unison install will happen without confirmation.",
    required=False,
)
@click.pass_context
def res_remote_add(ctx, **kwargs):
    """
    Adds a new remote with name 'name' to the Resolos configuration
    """
    add_remote_configuration(**kwargs)


@res_remote.command("update")
@click.argument("name")
@click.option(
    "-h",
    "--hostname",
    type=str,
    help="The host name of the remote server for the SSH connection.",
)
@click.option(
    "-u",
    "--username",
    type=str,
    help="Username on the remote server for the SSH connection",
)
@click.option("-p", "--port", type=int, help="Port for using the SSH connection")
@click.option(
    "--scheduler",
    type=str,
    help="The type of the scheduler on the remote",
)
@click.option(
    "--conda-load-command",
    type=str,
    help="The command that makes the 'conda' command available for the shell",
)
@click.option(
    "--conda-install-path",
    type=str,
    default="~",
    help="The path to install miniconda on the remote, if required",
)
@click.option(
    "--unison-path",
    type=str,
    help="The path of the unison executable on the remote",
)
@click.option(
    "--remote-env-name",
    type=str,
    help="The name of the conda environment for software dependencies to be used on remotes. "
    "Will be created if not exists",
)
@click.option(
    "--remote-path",
    type=str,
    help="The path of the project folder on the remote. Will be created if not exists",
)
@click.option(
    "-y",
    is_flag=True,
    help="If specified, SSH key setup, conda and unison install will happen without confirmation.",
    required=False,
)
@click.pass_context
def res_remote_update(ctx, **kwargs):
    """
    Updates existing remote with name 'name' in the Resolos configuration
    """
    update_remote_configuration(**kwargs)


@res_remote.command("remove")
@click.argument("name")
@click.option(
    "--purge",
    is_flag=True,
    help="Removes all synced project files and environments from the remote",
    required=False,
)
@click.pass_context
def res_remote_remove(ctx, **kwargs):
    """
    Removes the remote from the Resolos configuration
    """
    teardown_remote_configuration(**kwargs)


@res_remote.command("list")
@click.pass_context
def res_remote_list(ctx):
    """
    Lists the configured remotes
    """
    remote_list = read_remote_db()
    clog.info(f"The remotes are:\n{yaml.dump(remote_list)}")


@res.command("sync")
@click.option(
    "-r",
    "--remote",
    help="The name of the remote to sync with. Can be omitted if there is only one remote configured",
    required=False,
)
@click.option(
    "--env",
    is_flag=True,
    help="Also update the conda environment on remote with the packages installed on the local machine",
    required=False,
)
@click.pass_context
def res_sync(ctx, **kwargs):
    """
    Performs a 2-way sync on the project files and environment with the selected remote.
    In case only one remote is configured, the remote does not need to be specified.
    """
    remote_settings = get_remote(read_remote_db(), kwargs.get("remote"))

    if kwargs.get("env"):
        sync_env_and_files(remote_settings)
    else:
        sync_files(remote_settings)
    clog.info(f"Sync ran with {remote_settings['name']}!")


@res.command("run")
@click.argument("command", type=str)
@click.pass_context
def res_run(ctx, **kwargs):
    cmd = kwargs.get("command")
    local_env = get_project_env()
    execute_command_in_local_conda_env(cmd, local_env)


@res.group("job")
@click.option(
    "-r",
    "--remote",
    help="The name of the remote running the jobs. Can be omitted if there is only one remote configured",
    required=False,
)
@click.pass_context
def res_job(ctx, **kwargs):
    ctx.obj["remote_settings"] = get_remote(read_remote_db(), kwargs.get("remote"))
    ctx.obj["remote"] = ctx.obj["remote_settings"]["name"]
    pass


@res_job.command("run")
@click.argument("command", type=str)
@click.option(
    "-p",
    "--partition",
    type=str,
    default="debug-cpu",
    help="The name of the partition to submit to",
)
@click.option(
    "-n",
    "--ntasks",
    type=str,
    default="1",
    help="The number of tasks that will be run by the script",
)
@click.option(
    "-c",
    "--cpus-per-task",
    type=str,
    default="1",
    help="The number of CPUs to reserve per task",
)
@click.option(
    "--nodes",
    type=str,
    help="The number of nodes to reserve for the job",
)
@click.pass_context
def res_job_run(ctx, command, **kwargs):
    """
    Submits the given command on the remote
    """
    local_env, remote_env, remote_path = get_project_settings_for_remote(
        ctx.obj["remote"]
    )
    job_run(ctx.obj["remote_settings"], remote_env, remote_path, command, **kwargs)


@res_job.command("submit")
@click.argument("submission_script", type=click.Path(exists=True))
@click.pass_context
def res_job_submit(ctx, submission_script, **kwargs):
    """
    Submits the given script on the remote
    """
    local_env, remote_env, remote_path = get_project_settings_for_remote(
        ctx.obj["remote"]
    )
    job_submit(ctx.obj["remote_settings"], remote_path, submission_script)


@res_job.command("cancel")
@click.argument("job_id")
@click.pass_context
def res_job_cancel(ctx, job_id, **kwargs):
    """
    Cancels the job on the remote identified by the supplied job_id
    """
    job_cancel(ctx.obj["remote_settings"], job_id)
    clog.info(f"Cancelled job {job_id}")


@res_job.command("status")
@click.argument("job_id")
@click.pass_context
def res_job_status(ctx, job_id, **kwargs):
    """
    Displays the job details on the remote identified by the supplied job_id
    """
    job_status(ctx.obj["remote_settings"], job_id)


@res_job.command("list")
@click.option(
    "--all-users",
    is_flag=True,
    help="Show jobs for all users, not just the user configured for the remote",
    required=False,
)
@click.pass_context
def res_job_list(ctx, **kwargs):
    """
    Lists the job(s) on the remote
    """
    job_list(ctx.obj["remote_settings"], kwargs.get("all_users", False))


@res.group("archive")
@click.pass_context
def res_archive(ctx):
    """
    Archives contain all project files plus recepies for rebuilding the conda environment on another machine.
    """
    pass


@res_archive.command("create")
@click.option(
    "--base-url",
    type=str,
    envvar="YARETA_BASE_URL",
    default="https://access.yareta.unige.ch",
    help="The base url of the Yareta API",
)
@click.option(
    "-a",
    "--access-token",
    type=str,
    envvar="YARETA_ACCESS_TOKEN",
    help="The personal DLCM access token",
)
@click.option(
    "-o",
    "--organizational-unit-id",
    type=str,
    envvar="YARETA_ORG_UNIT_ID",
    help="The resource id of the organizational unit",
)
@click.option(
    "-f",
    "--filename",
    type=click.Path(),
    default=None,
    help="The filename of the archive",
)
@click.option(
    "-t",
    "--title",
    type=str,
    help="The title of the Yareta deposit to create for the archive",
)
@click.option(
    "-y",
    "--year",
    type=str,
    help="The year of the Yareta deposit",
)
@click.option(
    "-desc",
    "--description",
    type=str,
    help="The description of the Yareta deposit",
)
@click.option(
    "--deposit-access",
    type=str,
    default="PUBLIC",
    help="The access level of the Yareta deposit",
)
@click.option(
    "--license-id",
    type=str,
    default="CC-BY-4-0",
    help="The license id of the Yareta deposit",
)
@click.option(
    "--keywords",
    type=str,
    help="Comma-separated list of the Yareta deposit keywords",
)
@click.pass_context
def res_archive_create(ctx, **kwargs):
    """
    Archives the project to the specified destination. The currently supported destinations are local file (-f, --filename)
    and Yareta archive (-o, --organizational-unit-id).

    Notes for the local file destination:

        --filename:
        Filename must be a filesystem path (e.g. ../res_v1.tar.gz) writeable for the the resolos process.
        The path should not be inside the project folder.
    """
    local_env = get_project_env()
    make_archive(local_env, **kwargs)


@res_archive.command("load")
@click.option(
    "--base-url",
    type=str,
    envvar="YARETA_BASE_URL",
    default="https://access.yareta.unige.ch",
    help="The base url of the Yareta API",
)
@click.option(
    "-a",
    "--access-token",
    type=str,
    envvar="YARETA_ACCESS_TOKEN",
    help="The personal DLCM access token",
)
@click.option(
    "-d",
    "--deposit-id",
    type=str,
    help="The deposit id of the Yareta deposit",
)
@click.option(
    "-f",
    "--filename",
    type=click.Path(),
    help="The filename of the archive to load",
)
@click.option(
    "-u",
    "--url",
    type=str,
    help="The url to load the archive from",
)
@click.option(
    "-y",
    is_flag=True,
    help="If specified, the archive will be loaded without a confirmation prompt.",
    required=False,
)
@click.pass_context
def res_archive_load(ctx, **kwargs):
    """
    Loads the specified archive into the project.

    Source can be a filesystem path or a publicly accessible https download url.
    """

    load_archive(confirm_needed=not kwargs.get("y"), **kwargs)


@res.command("install")
@click.argument("packages", nargs=-1)
@click.option(
    "-r",
    "--remote",
    help="The name of the remote to also install the package to. Can be omitted if there is only one remote configured",
    required=False,
)
@click.option(
    "--all-remotes",
    is_flag=True,
    help="Also install the package to all configured remotes",
    required=False,
)
@click.pass_context
def res_install(ctx, packages, **kwargs):
    """
    Installs conda package(s) into the linked local and remote conda environments

    """
    all_remotes = kwargs.get("all_remotes")
    if all_remotes:
        install_conda_packages(packages)
        db = read_remote_db()
        remote_ids = list_remote_ids(db)
        for remote_id in remote_ids:
            remote_settings = get_remote(db, remote_id)
            install_conda_packages(packages, remote_settings)
    else:
        try:
            remote_settings = get_remote(read_remote_db(), kwargs.get("remote"))
            install_conda_packages(packages)
            install_conda_packages(packages, remote_settings)
        except NoRemotesError as ex:
            clog.info(
                "No remotes were specified, will only install the package locally"
            )
            install_conda_packages(packages)

    clog.info(f"Successfully installed packages {packages}")


@res.command("uninstall")
@click.argument("packages", nargs=-1)
@click.option(
    "-r",
    "--remote",
    help="The name of the remote to also uninstall the package from. "
    "Can be omitted if there is only one remote configured",
    required=False,
)
@click.option(
    "--all-remotes",
    is_flag=True,
    help="Uninstall the package from all configured remotes",
    required=False,
)
@click.pass_context
def res_uninstall(ctx, packages, **kwargs):
    """
    Uninstall conda package(s) from the linked local and remote conda environments

    """
    all_remotes = kwargs.get("all_remotes")
    if all_remotes:
        uninstall_conda_packages(packages)
        db = read_remote_db()
        remote_ids = list_remote_ids(db)
        for remote_id in remote_ids:
            remote_settings = get_remote(db, remote_id)
            uninstall_conda_packages(packages, remote_settings)
    else:
        try:
            remote_settings = get_remote(read_remote_db(), kwargs.get("remote"))
            uninstall_conda_packages(packages)
            uninstall_conda_packages(packages, remote_settings)
        except NoRemotesError as ex:
            clog.info(
                "No remotes were specified, will only uninstall the package(s) locally"
            )
            uninstall_conda_packages(packages)

    clog.info(f"Successfully uninstalled packages {packages}")
