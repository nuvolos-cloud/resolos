import click
from .platform import find_project_dir
from .config import (
    initialize_user_configs,
    get_default_config_path,
    randomString,
    get_project_dict_config,
    get_project_remote_dict_config,
    get_project_env,
    get_project_settings_for_remote,
    info,
)
import click_logging
from .logging import clog
from .remote import (
    get_remote,
    add_remote,
    delete_remote,
    list_remote_ids,
    read_remote_db,
    update_remote_settings,
    set_remote,
)
from .check import check_target, check, setup_ssh
from .unison import sync_files
from .conda import (
    execute_command_in_local_conda_env,
    install_conda_packages,
    uninstall_conda_packages,
    sync_env_and_files,
    check_conda_env_exists_remote,
    create_conda_env_remote,
)
from .archive import make_archive, load_archive
from .job import job_cancel, job_list, job_status, job_submit, job_run
from .exception import NoRemotesError, NotAProjectFolderError
from .init import init_project, teardown
import yaml


@click.group("res")
@click_logging.simple_verbosity_option(clog)
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
    "-s",
    "--source",
    help="The source archive to initialize the project from. "
    "Can be a path on the filesystem, or a download URL of the archive file",
)
@click.option(
    "-y",
    is_flag=True,
    help="If specified, the local/remote conda environment will be created without a confirmation prompt.",
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

    check_target()
    init_project(
        kwargs.get("source"),
        local_env_name=kwargs.get("env_name"),
        remote_env_name=kwargs.get("remote_env_name"),
        remote_files_path=kwargs.get("remote_path"),
        yes_to_all=kwargs.get("y"),
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
@click.pass_context
def res_remote_add(ctx, **kwargs):
    """
    Adds a new remote with name 'name' to the Resolos configuration
    """
    # print(ctx.obj)
    remote_name = kwargs.get("name")
    no_remote_setup = kwargs.get("no_remote_setup", False)
    create_dict = {
        "username": kwargs.get("username"),
        "hostname": kwargs.get("hostname"),
        "port": kwargs.get("port"),
        "scheduler": kwargs.get("scheduler"),
        "conda_load_command": kwargs.get("conda_load_command"),
        "unison_path": kwargs.get("unison_path"),
    }
    add_remote(read_remote_db(), remote_name, create_dict)
    remote_settings = get_remote(read_remote_db(), remote_name)
    if not no_remote_setup:
        if click.confirm(
            f"Do you want resolos to use its own SSH key for accessing the remote?",
            default=True,
        ):
            setup_ssh(remote_settings)
        clog.info(f"Running checks on new remote '{remote_name}'...")
        check_target(remote_settings)
    try:
        project_dir = find_project_dir()
        project_remote_config = get_project_remote_dict_config().read()
        files_path = (
            kwargs.get("remote_path")
            or f"./resolos_projects/{project_dir.name}_{randomString()}"
        )
        remote_env_name = (
            kwargs.get("remote_env_name") or f"resolos_env_{randomString()}"
        )
        project_remote_config[remote_name] = {
            "env_name": remote_env_name,
            "files_path": files_path,
        }
        get_project_remote_dict_config().write(project_remote_config)
        if not no_remote_setup:
            if not check_conda_env_exists_remote(create_dict, remote_env_name):
                if click.confirm(
                    f"Remote conda environment '{remote_env_name}' does not exists yet. "
                    f"Do you want to create it now?",
                    default=True,
                ):
                    create_conda_env_remote(create_dict, remote_env_name)
            else:
                clog.info(
                    f"Remote conda environment '{remote_env_name}' already exists, continuing..."
                )
        else:
            clog.info(f"Skipped setup for remote")
    except NotAProjectFolderError:
        clog.debug(
            f"Command was not executed from a project folder, no project set up was done"
        )
    clog.info(f"Remote {remote_name} added!")
    return


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
@click.pass_context
def res_remote_update(ctx, **kwargs):
    """
    Updates existing remote with name 'name' in the Resolos configuration
    """
    remote_id = kwargs["name"]
    db = read_remote_db()
    update_dict = update_remote_settings(db, remote_id, **kwargs)
    update_dict["name"] = remote_id
    clog.debug(f"The new remote config is:\n\n{update_dict}")
    clog.info(f"Running checks on remote '{remote_id}'...")
    check_target(update_dict)
    try:
        project_dir = find_project_dir()
        project_remote_config = get_project_remote_dict_config().read()
        project_remote_settings = project_remote_config.get(remote_id)
        if project_remote_settings is None:
            files_path = (
                kwargs.get("remote_path")
                or f"./resolos_projects/{project_dir.name}_{randomString()}"
            )
            remote_env_name = (
                kwargs.get("remote_env_name") or f"resolos_env_{randomString()}"
            )
            project_remote_config[remote_id] = {
                "env_name": remote_env_name,
                "files_path": files_path,
            }
        else:
            if kwargs.get("remote_env_name"):
                remote_env_name = kwargs.get("remote_env_name")
                project_remote_settings["env_name"] = remote_env_name
            else:
                remote_env_name = project_remote_settings.get("env_name")
            if kwargs.get("remote_path"):
                project_remote_settings["files_path"] = kwargs.get("remote_path")
        get_project_remote_dict_config().write(project_remote_config)
        if not check_conda_env_exists_remote(update_dict, remote_env_name):
            if click.confirm(
                f"Remote conda environment '{remote_env_name}' does not exists yet. "
                f"Do you want to create it now?",
                default=True,
            ):
                create_conda_env_remote(update_dict, remote_env_name)
        else:
            clog.info(
                f"Remote conda environment '{remote_env_name}' already exists, continuing..."
            )
    except NotAProjectFolderError:
        clog.debug(
            f"Command was not executed from a project folder, no project set up was done"
        )
    set_remote(db, remote_id, update_dict)
    clog.info(f"Remote {remote_id} successfully  modified!")
    return


@res_remote.command("remove")
@click.argument("name")
@click.pass_context
def res_remote_remove(ctx, **kwargs):
    """
    Removes the remote from the Resolos configuration
    """
    delete_remote(read_remote_db(), kwargs.get("name"))
    clog.info(f"Removed remote {kwargs.get('name')}!")


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
@click.argument("output", type=click.Path())
@click.pass_context
def res_archive_create(ctx, output, **kwargs):
    """
    Archives the project to the specified destination.

    Output must be a filesystem path (e.g. ../res_v1.tar.gz) writeable for the the resolos process.
    The path should not be inside the project folder.
    """
    local_env = get_project_env()
    make_archive(local_env, output)


@res_archive.command("load")
@click.argument("source")
@click.pass_context
def res_archive_load(ctx, source, **kwargs):
    """
    Loads the specified archive into the project.

    Source can be a filesystem path or a publicly accessible https download url.
    """

    load_archive(source)


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
