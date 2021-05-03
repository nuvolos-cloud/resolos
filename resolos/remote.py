from .config import (
    get_global_remotes_dict_config,
)
from .exception import (
    RemoteMissingError,
    RemoteUnspecifiedError,
    NoRemotesError,
    RemoteAlreadyExistsError,
)


def get_remote(db, remote_id):
    if remote_id is None:
        remote_ids = list_remote_ids(db)
        if len(remote_ids) == 0:
            raise NoRemotesError(
                "There are no remotes configured yet, please configure them using 'res remote add ...'"
            )
        elif len(remote_ids) == 1:
            remote_id = remote_ids[0]
            settings = db.get(remote_id)
            settings["name"] = remote_id
            return settings
        else:
            raise RemoteUnspecifiedError(
                "There was no remote name specified, "
                "but there are multiple remotes defined, "
                "cannot determine which one to use"
            )
    else:
        settings = db.get(remote_id)
        if settings is None:
            raise RemoteMissingError(f"Remote with name {remote_id} does no exist yet")
        settings["name"] = remote_id
        return settings


def add_remote(db, remote_id, desc):
    if remote_id in db:
        raise RemoteAlreadyExistsError(f"Remote '{remote_id}' already exists")
    db[remote_id] = desc
    write_dict_to_remote_db(db)
    return


def set_remote(db, remote_id, desc):
    db[remote_id] = desc
    write_dict_to_remote_db(db)
    return


def delete_remote(db, remote_id):
    try:
        db.pop(remote_id)
    except KeyError:
        raise RemoteMissingError(
            f"Remote '{remote_id}' does not exist, cannot delete it"
        )

    write_dict_to_remote_db(db)
    return


def list_remote_ids(db):
    return list(db.keys())


def read_remote_db():
    return get_global_remotes_dict_config().read()


def write_dict_to_remote_db(d):
    return get_global_remotes_dict_config().write(d)


def update_remote_settings(db, remote_id, **kwargs):
    desc = db.get(remote_id)
    if desc is None:
        raise RemoteMissingError(f"Remote with name {remote_id} does no exist yet")
    global_config_keys = [
        "username",
        "hostname",
        "port",
        "scheduler",
        "conda_load_command",
        "unison_path",
        "conda_install_path"
    ]
    for key in global_config_keys:
        new_val = kwargs.get(key)
        if new_val is not None:
            desc[key] = new_val
    return desc
