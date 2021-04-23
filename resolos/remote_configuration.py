from .remote import (
    add_remote,
    get_remote,
    read_remote_db,
    delete_remote,
    update_remote_settings,
    set_remote,
)
from .logging import clog
from .check import setup_ssh, check_target
from .config import (
    get_project_remote_dict_config,
    randomString,
)
from .conda import check_conda_env_exists_remote, create_conda_env_remote
from .shell import remove_remote_folder
from .platform import find_project_dir
from .exception import NotAProjectFolderError, ResolosException
import click


def add_remote_configuration(**kwargs):
    remote_name = kwargs.get("name")
    no_remote_setup = kwargs.get("no_remote_setup", False)
    no_confirm = kwargs.get("y", False)
    create_dict = {
        "username": kwargs.get("username"),
        "hostname": kwargs.get("hostname"),
        "port": kwargs.get("port"),
        "scheduler": kwargs.get("scheduler"),
        "conda_load_command": kwargs.get("conda_load_command"),
        "conda_install_path": kwargs.get("conda_install_path"),
        "unison_path": kwargs.get("unison_path"),
    }
    add_remote(read_remote_db(), remote_name, create_dict)
    remote_settings = get_remote(read_remote_db(), remote_name)
    if not no_remote_setup:
        if no_confirm or click.confirm(
            f"Do you want resolos to use its own SSH key for accessing the remote?",
            default=True,
        ):
            setup_ssh(remote_settings)
        clog.info(f"Running checks on new remote '{remote_name}'...")
        try:
            check_target(remote_settings)
            clog.info(f"Remote {remote_name} added!")
        except ResolosException as ex:
            clog.error(ex)
            if no_confirm or not click.confirm(
                f"Some of the remote checks have failed. "
                f"Do you still want to keep the new remote configuration '{remote_name}'?",
                default=False,
            ):
                delete_remote(read_remote_db(), remote_name)
            else:
                clog.info(f"Remote {remote_name} added!")
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
                if no_confirm or click.confirm(
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
    except Exception as ex:
        clog.info(f"Failed to initialize project on remote, the error was:\n{ex}\n")


def update_remote_configuration(**kwargs):
    remote_id = kwargs["name"]
    db = read_remote_db()
    update_dict = update_remote_settings(db, remote_id, **kwargs)
    update_dict["name"] = remote_id
    clog.debug(f"The new remote config is:\n\n{update_dict}")
    clog.info(f"Running checks on updated remote '{remote_id}'...")
    no_confirm = kwargs.get("y", False)
    check_target(update_dict, no_confirm=no_confirm)
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
            if no_confirm or click.confirm(
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


def teardown_remote_configuration(**kwargs):
    remote_id = kwargs.get("name")
    purge = kwargs.get("purge")
    remote_settings = get_remote(read_remote_db(), remote_id)
    if purge:
        remove_remote_folder(remote_settings, "~/resolos_projects")
        remove_remote_folder(remote_settings, "~/miniconda")
    try:
        remove_remote_folder(remote_settings, "~/.unison")
    except Exception as ex:
        clog.warning(
            f"Could not remove ~/.unison folder, the error message was:\n{ex}\n"
        )
    delete_remote(read_remote_db(), remote_id)
    clog.info(f"Removed remote '{remote_id}'!")
