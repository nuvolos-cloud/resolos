import os
import yaml
from .logging import clog
from .platform import (
    get_default_config_path,
    get_default_config_dir,
    get_unison_config_folder,
    get_remotes_config_path,
    find_resolos_dir,
    in_resolos_dir,
    get_project_config_path,
    get_project_remotes_config_path,
)
from .exception import (
    ResolosException,
    MissingRemoteEnv,
    MissingProjectRemoteConfig,
    MissingRemoteLocation,
)
import pathlib
import string
import random
import pkgutil
from .version import __version__
import re
from semver import VersionInfo
from datetime import datetime
from click import BadOptionUsage


ver_re = re.compile(r"\d+.\d+.\d+")
BASH_MIN_VERSION = VersionInfo.parse("5.0.0")
CONDA_MIN_VERSION = VersionInfo.parse("4.8.0")
UNISON_VERSION = VersionInfo.parse("2.51.3")

SSH_SERVERALIVEINTERVAL = 30
CONDA_LINUX_INSTALLER_URL = (
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
)
UNISON_LINUX_INSTALLER_URL = "https://github.com/bcpierce00/unison/releases/download/v2.51.3/unison-v2.51.3+ocaml-4.10.0+x86_64.linux.static.tar.gz"


GLOBAL_CONFIG_TEMPLATE = {"app_name": str, "ssh_key": str}


GLOBAL_REMOTE_TEMPLATE = {
    "conda_load_command": str,
    "hostname": str,
    "port": int,
    "scheduler": str,
    "unison_path": str,
    "username": str,
}


PROJECT_CONFIG_TEMPLATE = {
    "arch": str,
    "env_name": str,
    "env_initialized": bool,
    "platform": str,
    "project_path": str,
    "resolos_version": str,
}


PROJECT_REMOTE_TEMPLATE = {
    "env_name": str,
    "env_initialized": bool,
    "files_path": str,
    "last_files_sync": datetime,
    "last_env_sync": datetime,
}


DEBUG_CONFIG_ACCESS = os.getenv("RESOLOS_DEBUG_CONFIG_ACCESS")


class DictConfig(object):
    def __init__(self, path, default_generator=None):
        self.path = pathlib.Path(path)
        self.default_generator = default_generator

    def read(self):
        if not self.path.exists():
            if self.default_generator:
                self.write(self.default_generator())
        with self.path.open(mode="r") as f:
            d = yaml.safe_load(f)
            if DEBUG_CONFIG_ACCESS:
                clog.debug(f"Read config {self.path}:\n{d}")
            return d

    def write(self, d):
        if not self.path.parent.exists():
            pathlib.Path.mkdir(self.path.parent, parents=True)
        with self.path.open(mode="w") as f:
            if DEBUG_CONFIG_ACCESS:
                clog.debug(f"Writing new config to {self.path}:\n{d}")
            return yaml.dump(d, f)


def get_project_dict_config():
    return DictConfig(get_project_config_path(), generate_default_project_config)


def get_project_remote_dict_config():
    return DictConfig(
        get_project_remotes_config_path(), generate_default_project_remote_config
    )


def read_project_remote_config(remote_id):
    return get_project_remote_dict_config().read().get(remote_id)


def write_project_remote_config(remote_id, remote_config: dict):
    prdc = get_project_remote_dict_config()
    prc = prdc.read()
    if remote_id in prc:
        prc[remote_id].update(remote_config)
    else:
        prc[remote_id] = remote_config
    prdc.write(prc)


def default_global_configs():
    return {"app_name": "resolos", "ssh_key": None}


def get_global_dict_config():
    return DictConfig(get_default_config_path(), default_global_configs)


def get_global_remotes_dict_config():
    return DictConfig(get_remotes_config_path(), generate_default_remote_config)


def generate_default_global_config():
    to_write = {"app_name": "resolos", "ssh_key": None}

    config_path = get_default_config_path()
    if not config_path.exists():
        clog.debug(f"Creating default configuration file at {config_path}")
        pathlib.Path.mkdir(get_default_config_dir(), parents=True, exist_ok=True)
        with config_path.open(mode="w") as f:
            yaml.dump(to_write, f)


def generate_default_project_config():
    return {"project_path": str(find_resolos_dir())}


def generate_default_project_remote_config():
    return {}


def generate_default_remote_config():
    return {}


def generate_unison_folder():
    unison_folder = get_unison_config_folder()
    clog.debug(f"Initializing unison folder in {unison_folder}")
    target_unison_prf = unison_folder / ("default.prf")
    if not target_unison_prf.exists():
        clog.debug(f"Creating default unison preferences file {target_unison_prf}")
        pathlib.Path.mkdir(unison_folder, parents=True, exist_ok=True)
        with open(target_unison_prf, "w") as f:
            f.write(pkgutil.get_data("resolos", "unison/default.prf").decode("UTF-8"))


def initialize_user_configs():
    generate_default_global_config()
    generate_unison_folder()


def randomString(stringLength=8):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


def create_project_folder():
    localdir = pathlib.Path.cwd()
    resolos_hidden = localdir / (".resolos")
    pathlib.Path.mkdir(resolos_hidden)
    pathlib.Path.mkdir(resolos_hidden / ("remotes"))
    pathlib.Path.touch(resolos_hidden / (".resolos_init_complete"))
    return localdir


def get_project_env():
    project_config = get_project_dict_config().read()
    local_env = project_config.get("env_name")
    if local_env is None:
        raise ResolosException(f"Local conda env name is not defined!")
    return local_env


def get_project_settings_for_remote(remote_id, generate_env_if_missing=True):
    local_env = get_project_env()
    project_remote_settings = read_project_remote_config(remote_id)
    if project_remote_settings is None:
        raise MissingProjectRemoteConfig(
            f"Project-level remote settings for remote '{remote_id}' are not defined!"
        )
    remote_env = project_remote_settings.get("env_name")
    if remote_env is None and generate_env_if_missing:
        remote_env = f"resolos_env_{randomString()}"
        clog.debug(
            f"Remote env name was missing for remote '{remote_id}', generated new name {remote_env}"
        )
        project_remote_settings["env_name"] = remote_env
        write_project_remote_config(remote_id, project_remote_settings)
    remote_path = project_remote_settings.get("files_path")
    if remote_path is None:
        raise MissingRemoteLocation(
            f"Remote project location is not defined for remote '{remote_id}'"
        )
    return local_env, remote_env, remote_path


def get_ssh_key():
    return get_global_dict_config().read().get("ssh_key")


def info():
    clog.info(
        """
                     _           
                    | |          
 _ __ ___  ___  ___ | | ___  ___ 
| '__/ _ \/ __|/ _ \| |/ _ \/ __| 
| | |  __/\__ \ (_) | | (_) \__ \ 
|_|  \___||___/\___/|_|\___/|___/ 
"""
    )
    clog.info(f"Version: {__version__}")
    gc = get_global_dict_config().read()
    clog.info(f"The global config ({get_default_config_path()}):\n{yaml.dump(gc)}")
    grc = get_global_remotes_dict_config().read()
    clog.info(
        f"The global remotes config ({get_remotes_config_path()}):\n{yaml.dump(grc)}"
    )
    if in_resolos_dir():
        pc = get_project_dict_config().read()
        prc = get_project_remote_dict_config().read()
        clog.info(f"The project config ({get_project_config_path()}):\n{yaml.dump(pc)}")
        clog.info(
            f"The project remote config ({get_project_remotes_config_path()}):\n{yaml.dump(prc)}"
        )


def get_option(d: dict, key: str, err_msg: str = None, split_list=False, pop=False):
    res = d.pop(key, None) if pop else d.get(key)
    if res is None and err_msg:
        raise BadOptionUsage(key, err_msg)
    else:
        if res and split_list:
            return [c.strip() for c in res.split(",")]
        else:
            return res


def verify_mutually_exclusive_options(keys, options, must_select_one=True, **kwargs):
    count = 0
    for key in keys:
        if kwargs.get(key):
            count += 1
    if must_select_one and count == 0:
        raise BadOptionUsage(
            None, f"One of the following options is mandatory: {options}"
        )
    elif count > 1:
        raise BadOptionUsage(
            None, f"Only one of the following options may be specified: {options}"
        )
