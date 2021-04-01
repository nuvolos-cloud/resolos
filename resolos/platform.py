import sys
import pathlib
import os
from platform import machine, python_version
from .logging import clog
from .exception import NotAProjectFolderError


def get_user_platform():
    platforms = {"linux": "linux", "linux1": "linux", "darwin": "macos", "win32": "win"}

    if sys.platform not in platforms:
        raise OSError(f"OS {sys.platform} is not supported")

    return platforms[sys.platform]


def get_arch():
    archs = {"x86": "x86", "x86_64": "x86_64"}
    m = machine()
    if m in archs:
        return archs[m]
    else:
        return m


def is_linux_64():
    return get_user_platform() == "linux" and get_arch() == "x86_64"


def get_python_version():
    return python_version()


def get_home():
    platform = get_user_platform()

    if platform == "linux":
        return pathlib.Path(os.getenv("HOME"))
    elif platform == "macos":
        return pathlib.Path(os.getenv("HOME"))
    elif platform == "win":
        return pathlib.Path(os.getenv("LocalAppData"))
    else:
        pass

    return


def get_default_config_dir():
    platform = get_user_platform()

    if platform == "linux":
        default_config_path = pathlib.Path(get_home()) / (".resolos")
    elif platform == "macos":
        default_config_path = pathlib.Path(get_home()) / (".resolos")
    elif platform == "win":
        default_config_path = pathlib.Path(get_home()) / ("resolos")
    else:
        raise OSError(f"OS {platform} is not supported")

    return default_config_path


def create_default_config_folder():
    config_path = get_default_config_dir()
    if not config_path.exists():
        clog.debug(f"Creating global configuration folder {config_path}")
        pathlib.Path.mkdir(config_path, parents=True)


def get_default_config_path():
    return get_default_config_dir() / ("config.yaml")


def get_remotes_config_dir():
    return get_default_config_dir() / ("remotes")


def get_remotes_config_path():
    return get_remotes_config_dir() / ("remotes.yaml")


def get_unison_config_folder():
    return get_default_config_dir() / ("unison")


def get_local_remotes_dir():
    return find_resolos_dir() / ("remotes")


def get_project_remotes_config_path():
    return get_local_remotes_dir() / ("remotes.yaml")


def get_envs_path():
    return get_local_remotes_dir() / ("envs.yaml")


def get_project_config_path():
    return find_resolos_dir() / ("config.yaml")


def find_resolos_dir():
    localdir = pathlib.Path.cwd()
    px = localdir
    i = 1
    while True and i < 256:
        resolos_dir = px / (".resolos")
        if pathlib.Path.exists(resolos_dir) and pathlib.Path.exists(
            resolos_dir / (".resolos_init_complete")
        ):
            return resolos_dir
        px_old = px
        px = px.parent
        i += 1
        if px_old == px:
            break
    raise NotAProjectFolderError(
        f"Folder '{localdir}' is not in a resolos project folder. Please execute the command from a "
        f"resolos project folder instead"
    )


def find_project_dir():
    return find_resolos_dir().parent


def in_resolos_dir():
    try:
        find_resolos_dir()
        return True
    except NotAProjectFolderError:
        return False


def in_home_folder():
    return pathlib.Path.cwd().absolute() == get_home().absolute()


def resolos_relative_path(path=None):
    if path is None:
        path = pathlib.Path.cwd()

    project_dir = find_project_dir()
    relative_path = path.absolute().relative_to(project_dir)
    return relative_path
