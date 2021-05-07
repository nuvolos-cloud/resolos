from .logging import clog
import tarfile
from .conda import (
    pack_conda_env,
    explicit_package_list,
    export_conda_env,
    execute_local_conda_command,
    create_conda_env_local,
    get_requirements,
    get_nondep_packages,
)
from .exception import (
    LocalCommandError,
    ResolosException,
    NotAProjectFolderError,
    NotAResolosArchiveError,
)
from .platform import find_project_dir, get_arch, get_user_platform, find_resolos_dir
from .config import (
    get_project_dict_config,
    randomString,
    DictConfig,
    get_option,
    verify_mutually_exclusive_options,
)
from .shell import run_shell_cmd
from .storage.yareta import deposit_archive, download_archive
import click
import shutil
import tempfile
import urllib.request
import pathlib
import glob
import os
from .version import __version__
from datetime import datetime


PACK_NAME = "env_pack.tar.gz"
ENV_YAML_NAME = "env.yaml"
ENV_FROM_HISTORY_YAML_NAME = "env_history.yaml"
EXPLICIT_PACKAGES_NAME = "explicit_packages.yaml"
REQUIREMENTS_NAME = "requirements.txt"
NONDEP_PACKAGES_NAME = "nondep_packages.txt"
FILES_NAME = "files"
RESOLOS_FOLDER_NAME = ".resolos"
TAR_HEADER_RESOLOS_VERSION = "resolos_version"
TAR_HEADER_CREATED_ON = "created_on"
ARCHIVE_FILENAME = "resolos_archive.tar.gz"

EXCLUDE_FILES = [".DS_Store", ".tmp"]
SUPPORTED_REMOTE_PROTOCOLS = ["http", "https", "ftp", "sftp"]


def filter_files(ti: tarfile.TarInfo):
    if ti.type == tarfile.DIRTYPE:
        for exc_dir in [".resolos", ".env"]:
            if ti.name.endswith(exc_dir):
                return None
    if ti.type in tarfile.REGULAR_TYPES:
        for exc_file in EXCLUDE_FILES:
            if ti.name.endswith(exc_file):
                return None
    return ti


def filter_resolos(ti: tarfile.TarInfo):
    if ti.type == tarfile.DIRTYPE:
        for exc_dir in ["remotes"]:
            if ti.name.endswith(exc_dir):
                return None
    if ti.type in tarfile.REGULAR_TYPES:
        for exc_file in EXCLUDE_FILES:
            if ti.name.endswith(exc_file):
                return None
    return ti


def make_archive(env_name: str, **kwargs):
    verify_mutually_exclusive_options(
        ["filename", "organizational_unit_id"],
        ["--filename", "--organizational-unit-id"],
        **kwargs,
    )
    if kwargs.get("filename"):
        output_filename = kwargs.get("filename")
        make_archive_file(env_name, output_filename=output_filename)
        clog.info(f"Successfully archived resolos project to {output_filename}!")
    elif kwargs.get("organizational_unit_id"):
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_filename = f"{tmpdirname}/{ARCHIVE_FILENAME}"
            base_url = get_option(
                kwargs, "base_url", f"No Yareta base url was found", pop=True
            )
            access_token = get_option(
                kwargs, "access_token", f"No access token was found", pop=True
            )
            org_unit_id = get_option(
                kwargs,
                "organizational_unit_id",
                f"No organizational unit id was found",
                pop=True,
            )
            title = get_option(
                kwargs, "title", f"Missing required option: --title", pop=True
            )
            year = get_option(
                kwargs, "year", f"Missing required option: --year", pop=True
            )
            description = get_option(
                kwargs,
                "description",
                f"Missing required option: --description",
                pop=True,
            )
            make_archive_file(env_name, output_filename=output_filename)
            clog.debug(f"Successfully created archive file {output_filename}!")
            clog.info(f"Depositing resolos project archive to Yareta...")
            deposit_id = deposit_archive(
                output_filename,
                base_url,
                access_token,
                org_unit_id,
                title,
                year,
                description,
                **kwargs,
            )
            clog.info(
                f"Successfully deposited resolos project archive to Yareta, deposit id is '{deposit_id}'!"
            )
    else:
        raise ResolosException(f"Unknown resolos archival destination")


def make_archive_file(env_name: str, output_filename: str):
    resolos_dir = find_resolos_dir()
    project_dir = resolos_dir.parent
    files_path = str(project_dir.absolute())
    resolos_path = str(resolos_dir.absolute())
    with tempfile.TemporaryDirectory() as tmpdirname:
        pack_absolute_path = f"{tmpdirname}/{PACK_NAME}"
        env_yaml_path = f"{tmpdirname}/{ENV_YAML_NAME}"
        env_history_yaml_path = f"{tmpdirname}/{ENV_FROM_HISTORY_YAML_NAME}"
        explicit_packages_path = f"{tmpdirname}/{EXPLICIT_PACKAGES_NAME}"
        requirements_path = f"{tmpdirname}/{REQUIREMENTS_NAME}"
        nondep_path = f"{tmpdirname}/{NONDEP_PACKAGES_NAME}"
        clog.info(f"Packing environment...")
        pack_conda_env(env_name, pack_absolute_path)
        clog.info(f"Exporting environment...")
        export_conda_env(env_name, filename=env_history_yaml_path)
        export_conda_env(
            env_name, filename=env_yaml_path, only_explicitly_installed=False
        )
        clog.info(f"Exporting explicit packages list...")
        explicit_package_list(env_name, filename=explicit_packages_path)
        clog.info(f"Exporting requirements file...")
        get_requirements(env_name, filename=requirements_path)
        clog.info(f"Exporting non-dependent packages...")
        get_nondep_packages(env_name, filename=nondep_path)
        pax_headers = {
            TAR_HEADER_RESOLOS_VERSION: __version__,
            TAR_HEADER_CREATED_ON: datetime.now().isoformat(),
        }
        with tarfile.open(
            output_filename, "w:gz", format=tarfile.PAX_FORMAT, pax_headers=pax_headers
        ) as tar:
            tar.add(files_path, arcname=FILES_NAME, filter=filter_files)
            tar.add(resolos_path, arcname=RESOLOS_FOLDER_NAME, filter=filter_resolos)
            tar.add(pack_absolute_path, arcname=PACK_NAME)
            tar.add(env_yaml_path, arcname=ENV_YAML_NAME)
            tar.add(env_history_yaml_path, arcname=ENV_FROM_HISTORY_YAML_NAME)
            tar.add(explicit_packages_path, arcname=EXPLICIT_PACKAGES_NAME)
            tar.add(requirements_path, arcname=REQUIREMENTS_NAME)
            tar.add(nondep_path, arcname=NONDEP_PACKAGES_NAME)


def members_in_subfolder(tar, folder):
    pattern = f"{folder}/"
    l = len(pattern)
    for member in tar.getmembers():
        if member.path.startswith(pattern):
            member.path = member.path[l:]
            yield member


def extract_subfolder(tar, subfolder: str, path: str = "."):
    tar.extractall(path=path, members=members_in_subfolder(tar, subfolder))


def extract_file(tar, file: str, path: str = ""):
    tar.extract(file, path=path)


def clean_folder(folder_path):
    for path in glob.glob(f"{folder_path}/*"):
        if os.path.isdir(path):
            clog.debug(f"Removing folder {path}")
            shutil.rmtree(path)
        elif os.path.isfile(path):
            clog.debug(f"Removing file {path}")
            os.remove(path)
        else:
            clog.warn(f"Cannot delete object {path}, as it's not a file or folder")


def load_archive_file(input_filename: str, files_path):
    pdc = get_project_dict_config()
    project_settings = pdc.read()
    old_env_name = project_settings.get("env_name")
    new_env_name = f"resolos_env_{randomString()}"
    with tarfile.open(input_filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
        if TAR_HEADER_RESOLOS_VERSION not in tar.pax_headers:
            raise NotAResolosArchiveError(
                f"{input_filename} is not an archive created by resolos."
            )
        clog.info(f"Loading archive...")
        resolos_version = tar.pax_headers[TAR_HEADER_RESOLOS_VERSION]
        created_on = tar.pax_headers[TAR_HEADER_CREATED_ON]
        clog.debug(
            f"Archive created by resolos version {resolos_version} on {created_on}"
        )
        clean_folder(files_path)
        extract_subfolder(tar, "files", path=str(files_path.absolute()))
        with tempfile.TemporaryDirectory() as tmpdirname:
            pack_absolute_path = f"{tmpdirname}/{PACK_NAME}"
            env_yaml_path = f"{tmpdirname}/{ENV_YAML_NAME}"
            env_history_yaml_path = f"{tmpdirname}/{ENV_FROM_HISTORY_YAML_NAME}"
            explicit_packages_path = f"{tmpdirname}/{EXPLICIT_PACKAGES_NAME}"
            requirements_path = f"{tmpdirname}/{REQUIREMENTS_NAME}"
            nondep_path = f"{tmpdirname}/{NONDEP_PACKAGES_NAME}"
            resolos_path = f"{tmpdirname}/{RESOLOS_FOLDER_NAME}"
            extract_file(tar, ENV_YAML_NAME, tmpdirname)
            extract_file(tar, ENV_FROM_HISTORY_YAML_NAME, tmpdirname)
            extract_file(tar, EXPLICIT_PACKAGES_NAME, tmpdirname)
            extract_file(tar, REQUIREMENTS_NAME, tmpdirname)
            extract_file(tar, NONDEP_PACKAGES_NAME, tmpdirname)
            extract_subfolder(tar, RESOLOS_FOLDER_NAME, path=resolos_path)
            apdc = DictConfig(f"{resolos_path}/config.yaml")
            archive_settings = apdc.read()
            create_conda_env_local(new_env_name)
            if (
                archive_settings.get("platform") == get_user_platform()
                and archive_settings.get("arch") == get_arch()
            ):
                try:
                    clog.info(
                        f"Archive was created on the same platform ({get_user_platform()}) "
                        f"and architecture ({get_arch()}) "
                        f"as the current machine, will try to use the explicit packages "
                        f"list to load the environment"
                    )
                    execute_local_conda_command(
                        f"install -y --name {new_env_name} --file {explicit_packages_path}"
                    )
                    project_settings["env_name"] = new_env_name
                    if old_env_name:
                        execute_local_conda_command(
                            f"remove -y --name {old_env_name} --all"
                        )
                    pdc.write(project_settings)
                except Exception as ex:
                    clog.info(
                        f"Failed to load conda env using explicit packages list, "
                        f"will use now conda-pack..."
                    )
                    clog.debug(f"The error was:\n\n{ex}\n\n")
                    extract_file(tar, PACK_NAME, pack_absolute_path)
                    run_shell_cmd(
                        f"mkdir -p ~/.resolos/envs/{new_env_name} && "
                        f"tar -xzf {pack_absolute_path} -C ~/.resolos/envs/{new_env_name} && "
                        f"source ~/.resolos/envs/{new_env_name}/bin/activate && "
                        f"conda-unpack",
                    )
                    project_settings[
                        "env_name"
                    ] = f"source ~/.resolos/envs/{new_env_name}/bin/activate"
                    pdc.write(project_settings)
            else:
                try:
                    clog.info(
                        f"Archive was created on a different platform/architecture "
                        f"({project_settings.get('platform')}/{project_settings.get('arch')}) "
                        f"as the current machine's platform/architecture ({get_user_platform()}/{get_arch()}) "
                        f", will try to use the conda environment file"
                    )
                    execute_local_conda_command(
                        f"env update -n {new_env_name} -f {env_yaml_path}"
                    )
                    project_settings["env_name"] = new_env_name
                    if old_env_name:
                        execute_local_conda_command(
                            f"remove -y --name {old_env_name} --all"
                        )
                    pdc.write(project_settings)
                except Exception as ex:
                    clog.info(
                        f"Failed to load conda env using environment file, "
                        f"will try  to install now only the explicitly installed packages"
                    )
                    try:
                        clog.debug(f"The error was:\n\n{ex}\n\n")
                        execute_local_conda_command(
                            f"env update -n {new_env_name} -f {env_history_yaml_path}"
                        )
                        project_settings["env_name"] = new_env_name
                        if old_env_name:
                            execute_local_conda_command(
                                f"remove -y --name {old_env_name} --all"
                            )
                        pdc.write(project_settings)
                    except LocalCommandError:
                        clog.info(
                            f"Failed to load conda env using only the explicitly installed packages, will try now "
                            f"the requirements file"
                        )
                        try:
                            execute_local_conda_command(
                                f"install -y --name {new_env_name} --file {requirements_path}"
                            )
                            project_settings["env_name"] = new_env_name
                            if old_env_name:
                                execute_local_conda_command(
                                    f"remove -y --name {old_env_name} --all"
                                )
                            pdc.write(project_settings)
                        except LocalCommandError:
                            clog.info(
                                f"Failed to load conda env using only the requirements file, will try now "
                                f"the list of non-dependent packages only"
                            )
                            execute_local_conda_command(
                                f"install -y --name {new_env_name} --file {nondep_path}"
                            )
                            project_settings["env_name"] = new_env_name
                            if old_env_name:
                                execute_local_conda_command(
                                    f"remove -y --name {old_env_name} --all"
                                )
                            pdc.write(project_settings)


def load_archive(**kwargs):
    verify_mutually_exclusive_options(
        ["url", "filename", "deposit_id"],
        ["--url", "--filename", "--deposit-id"],
        **kwargs,
    )
    project_dir = find_project_dir()
    if not kwargs.get("confirm_needed") or click.confirm(
        "This operation will overwrite the contents of your project. Continue?",
        default=True,
    ):
        if kwargs.get("url"):
            url = get_option(kwargs, "url", "Missing required option: --url")
            supported_proto = False
            for proto in SUPPORTED_REMOTE_PROTOCOLS:
                if url.startswith(proto):
                    supported_proto = True
            if not supported_proto:
                raise ResolosException(
                    f"Unsupported protocol in url '{url}', "
                    f"the only supported ones are: {SUPPORTED_REMOTE_PROTOCOLS}"
                )
            clog.info(f"Downloading archive '{url}'...")
            with urllib.request.urlopen(url) as response:
                with tempfile.NamedTemporaryFile(delete=True) as arch_file:
                    shutil.copyfileobj(response, arch_file)
                    load_archive_file(arch_file.name, project_dir)
                    clog.info(
                        f"Successfully loaded archive '{url}' into project '{project_dir.absolute()}'"
                    )
        elif kwargs.get("filename"):
            input_filename = get_option(
                kwargs, "filename", "Missing required option: --filename"
            )
            load_archive_file(input_filename, project_dir)
            clog.info(
                f"Successfully loaded archive '{input_filename}' into project '{project_dir.absolute()}'"
            )
        elif kwargs.get("deposit_id"):
            base_url = get_option(kwargs, "base_url", f"No Yareta base url was found")
            access_token = get_option(
                kwargs, "access_token", f"No access token was found"
            )
            deposit_id = get_option(
                kwargs, "deposit_id", "Missing required option: --deposit-id"
            )
            with tempfile.NamedTemporaryFile(delete=True) as arch_file:
                download_archive(
                    arch_file.name, ARCHIVE_FILENAME, deposit_id, access_token, base_url
                )
                load_archive_file(arch_file.name, project_dir)
                clog.info(
                    f"Successfully loaded archive from Yareta deposit '{deposit_id}' into project '{project_dir.absolute()}'"
                )
        else:
            raise ResolosException(f"Missing source specification")
