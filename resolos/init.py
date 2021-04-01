from .logging import clog
import pathlib
from .config import (
    create_project_folder,
    randomString,
    get_project_dict_config,
    get_project_remote_dict_config,
    in_resolos_dir,
)
from .platform import get_arch, get_user_platform, in_home_folder
from .remote import list_remote_ids, read_remote_db, get_remote
from .conda import (
    check_conda_env_exists_local,
    check_conda_env_exists_remote,
    create_conda_env_local,
    create_conda_env_remote,
    sync_env_and_files,
)
from .archive import load_archive
import click
from .version import __version__


def init_project(
    source=None, local_env_name=None, remote_env_name=None, remote_files_path=None
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
        clog.info(f"Creating Resolos project at {pathlib.Path.cwd()}...")
        localdir = create_project_folder()
        if source:
            load_archive(source, confirm_needed=False)
            pdc = get_project_dict_config()
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
            }
            get_project_dict_config().write(project_config)
            if not check_conda_env_exists_local(env_name):
                if click.confirm(
                    f"Local conda environment '{env_name}' does not exists yet. "
                    f"Do you want to create it now?",
                    default=True,
                ):
                    create_conda_env_local(env_name)
                    clog.info(f"Local conda env successfully created")
            else:
                clog.info(
                    f"Local conda environment '{env_name}' already exists, continuing..."
                )
        project_remote_config = {}
        remote_db = read_remote_db()
        remote_ids = list_remote_ids(remote_db)
        num_remote_ids = len(remote_ids)
        for remote_id in remote_ids:
            if remote_env_name is None:
                clog.info(
                    f"No remote conda env name was specified, "
                    f"will use the local env's name '{env_name}' on the remote as well"
                )
            else:
                env_name = remote_env_name
            files_path = (
                remote_files_path
                or f"./resolos_projects/{localdir.name}_{randomString()}"
            )
            project_remote_config[remote_id] = {
                "env_name": env_name,
                "files_path": files_path,
            }
            get_project_remote_dict_config().write(project_remote_config)
            if num_remote_ids == 1:
                clog.info(
                    f"Detected only one configured remote '{remote_id}', "
                    f"checking the existence of the remote conda environment '{env_name}'..."
                )
                remote_settings = get_remote(remote_db, remote_id)
                if not check_conda_env_exists_remote(remote_settings, env_name):
                    if click.confirm(
                        f"Remote conda environment '{env_name}' does not exists yet. "
                        f"Do you want to create it now?",
                        default=True,
                    ):
                        create_conda_env_remote(remote_settings, env_name)
                        clog.info(f"Remote conda env successfully created")
                    if click.confirm(
                        f"Do you want to sync the project to the remote now?",
                        default=True,
                    ):
                        sync_env_and_files(remote_settings)
                else:
                    clog.info(
                        f"Remote conda environment '{env_name}' already exists, continuing..."
                    )
