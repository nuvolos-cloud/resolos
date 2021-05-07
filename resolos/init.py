from .logging import clog
import pathlib
from .config import (
    create_project_folder,
    randomString,
    get_project_dict_config,
    get_project_remote_dict_config,
    in_resolos_dir,
    get_project_settings_for_remote,
)
from .platform import get_arch, get_user_platform, in_home_folder, find_resolos_dir
from .remote import list_remote_ids, read_remote_db, get_remote
from .shell import remove_remote_folder
from .conda import (
    check_conda_env_exists_local,
    create_conda_env_local,
    sync_env_and_files,
    execute_local_conda_command,
    execute_remote_conda_command,
)
from .archive import load_archive
import click
from .version import __version__
import shutil
from datetime import datetime


def _init_project(
    base_url=None,
    access_token=None,
    url=None,
    filename=None,
    deposit_id=None,
    local_env_name=None,
    remote_env_name=None,
    remote_files_path=None,
    no_confirm=False,
    no_to_remote_setup=False,
):
    clog.info(f"Creating Resolos project at {pathlib.Path.cwd()}...")
    localdir = create_project_folder()
    pdc = get_project_dict_config()
    if url or filename or deposit_id:
        load_archive(
            base_url=base_url,
            access_token=access_token,
            url=url,
            filename=filename,
            deposit_id=deposit_id,
            confirm_needed=False,
        )
        project_settings = pdc.read()
        env_name = project_settings["env_name"]
        project_settings["resolos_version"] = __version__
        project_settings["platform"] = get_user_platform()
        project_settings["arch"] = get_arch()
        pdc.write(project_settings)
    else:
        if local_env_name is None:
            env_name = f"resolos_env_{randomString()}"
            clog.info(
                f"No conda env name was specified, will use generated name '{env_name}'..."
            )
        else:
            env_name = local_env_name
        project_config = {
            "resolos_version": __version__,
            "platform": get_user_platform(),
            "arch": get_arch(),
            "env_name": local_env_name or env_name,
            "env_initialized": False,
        }
        pdc.write(project_config)
        if not check_conda_env_exists_local(env_name):
            if no_confirm or click.confirm(
                f"Local conda environment '{env_name}' does not exists yet. "
                f"Do you want to create it now?",
                default=True,
            ):
                create_conda_env_local(env_name)
                project_config["env_initialized"] = True
                pdc.write(project_config)
                clog.info(f"Local conda env successfully created")
        else:
            clog.info(
                f"Local conda environment '{env_name}' already exists, continuing..."
            )
    project_remote_config = {}
    remote_db = read_remote_db()
    remote_ids = list_remote_ids(remote_db)
    for remote_id in remote_ids:
        prdc = get_project_remote_dict_config()
        if remote_env_name is None:
            clog.info(
                f"No remote conda env name was specified, "
                f"will use the local env's name '{env_name}' on the remote '{remote_id}' as well"
            )
        else:
            env_name = remote_env_name
        files_path = (
            remote_files_path or f"./resolos_projects/{localdir.name}_{randomString()}"
        )
        project_remote_config[remote_id] = {
            "env_name": env_name,
            "env_initialized": False,
            "files_path": files_path,
            "last_files_sync": None,
            "last_env_sync": None,
        }
        prdc.write(project_remote_config)
        if no_to_remote_setup:
            clog.info(
                f"Skipped environment and project files configuration on remote '{remote_id}'"
            )
        else:
            remote_settings = get_remote(remote_db, remote_id)
            if no_confirm or click.confirm(
                f"Do you want to sync the project files and the conda environment to remote '{remote_id}' now?",
                default=True,
            ):
                now = datetime.utcnow()
                sync_env_and_files(remote_settings)
                project_remote_config[remote_id]["env_initialized"] = True
                project_remote_config[remote_id]["last_files_sync"] = now
                project_remote_config[remote_id]["last_env_sync"] = now
                prdc.write(project_remote_config)
                clog.info(
                    f"Project files and environment successfully synced to remote '{remote_id}'"
                )


def init_project(
    base_url=None,
    access_token=None,
    url=None,
    filename=None,
    deposit_id=None,
    local_env_name=None,
    remote_env_name=None,
    remote_files_path=None,
    no_confirm=False,
    no_to_remote_setup=False,
):
    if in_resolos_dir():
        clog.warning(
            "You are already in a directory contained in a resolos project. Nothing was changed."
        )
    elif in_home_folder():
        clog.warning(
            "You cannot create a resolos project from your home folder, as it contains global resolos configs as well. "
            "Please create a subfolder and init the project there."
        )
    else:
        try:
            _init_project(
                base_url,
                access_token,
                url,
                filename,
                deposit_id,
                local_env_name,
                remote_env_name,
                remote_files_path,
                no_confirm,
                no_to_remote_setup,
            )
        except Exception as ex:
            clog.error(ex, exc_info=True)
            clog.info(f"Running teardown now")
            teardown(skip_local=False, skip_remotes=True)


def teardown(skip_local=True, skip_remotes=True):
    if skip_remotes:
        clog.info("Skipped teardown of remote environment(s)")
    else:
        remote_db = read_remote_db()
        remote_ids = list_remote_ids(remote_db)
        for remote_id in remote_ids:
            remote_settings = get_remote(remote_db, remote_id)
            local_env, remote_env, remote_path = get_project_settings_for_remote(
                remote_id, generate_env_if_missing=False
            )
            if click.confirm(
                f"Do you want to delete synced project files and environment on remote '{remote_id}'?",
                default=True,
            ):
                if remote_env:
                    execute_remote_conda_command(
                        f"env remove --name {remote_env}", remote_settings
                    )
                    clog.info(f"Removed remote env '{remote_env}'")
                else:
                    clog.info(f"Found no configured remote env to remove")
                remove_remote_folder(remote_settings, remote_path)
                clog.info(f"Removed project files folder '{remote_path}'")
    if skip_local:
        clog.info("Skipped teardown of local environment")
    else:
        pc = get_project_dict_config().read()
        env_name = pc.get("env_name")
        if env_name:
            execute_local_conda_command(f"env remove --name {env_name}")
            clog.info(f"Removed local environment {env_name}")
        else:
            clog.info(f"No linked local environment was found to be deleted")
        resolos_dir = find_resolos_dir()
        shutil.rmtree(resolos_dir)
        clog.info(f"Removed folder {resolos_dir}")
