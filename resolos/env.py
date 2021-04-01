import yaml
from .platform import in_resolos_dir, get_envs_path
from .exception import (
    EnvCommandError,
    EnvMissingError,
    NotAProjectFolderError,
)
from .remote import read_remote_db, list_remote_ids
from .logging import clog

# Env map would look like:

# Env_id:
#    remote_name: ~ Name of the remote
#    remote_env_name: Name of the environment on the remote.


def read_env_map():
    if in_resolos_dir():
        env_map = get_envs_path()
        with env_map.open(mode="r") as f:
            try:
                env_dict = yaml.safe_load(f)

                if env_dict is None:
                    env_dict = {}

                return env_dict
            except yaml.YAMLError as exc:
                raise exc
    else:
        raise NotAProjectFolderError(
            "Cannot read environment mapping: not in a resolos project directory."
        )


def write_env_map(dict):
    if in_resolos_dir():
        env_map = get_envs_path()
        with env_map.open(mode="w") as f:
            try:
                yaml.dump(dict, f)
            except yaml.YAMLError as exc:
                raise exc
    else:
        raise NotAProjectFolderError(
            "Cannot write environment mapping: not in a resolos project directory."
        )


def modify_env_map(key, value):
    env_dict = read_env_map()
    try:
        env_dict[key] = value
    except KeyError:
        raise EnvMissingError(
            "The environment setup you are trying to modify does not exist."
        )


def add_env(db, env_id, desc):
    if env_id in db:
        raise EnvCommandError(
            "The environment already exists, you can modify it with env modify."
        )
    db[env_id] = desc
    write_env_map(db)
    return


def set_env(db, env_id, desc):
    db[env_id] = desc
    write_env_map(db)
    return


def delete_env(db, env_id):
    try:
        db.pop(env_id)
    except KeyError:
        raise EnvMissingError(f"Cannot delete remote '{env_id}', it does not exist.")

    write_env_map(db)
    return


def validate_env_setting(dict):
    remote_db = read_remote_db()
    remote_name = dict["remote_name"]
    if remote_name in list_remote_ids(remote_db):
        clog.info(
            f"PASS: {remote_name} is available in both environment mappings and remote mappings."
        )
    else:
        clog.info(
            f"FAIL: The environment mapping refers to {remote_name}, however the remote does not exist."
        )
