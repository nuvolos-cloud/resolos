from .logging import clog
from .conda import (
    check_conda_installed_remote,
    check_conda_installed_local,
    install_conda_remote,
)
from .unison import (
    check_unison_installed_remote,
    check_unison_installed_local,
    check_unison_connection,
    install_unison_remote,
)
from .config import get_global_dict_config
from .platform import in_resolos_dir
from .remote import read_remote_db, list_remote_ids, get_remote
from .exception import MissingDependency, ShellError
from .shell import run_ssh_cmd, run_shell_cmd, check_bash_version_local
import click
from platform import node
import pathlib
import os

RESOLOS_PRIVATE_SSH_KEY_LOCATION = "~/.ssh/id_rsa_resolos"


def check_target(target=None, raise_on_error=False, no_confirm=False):
    if target is None:
        check_conda_installed_local()
        clog.info(f"PASS - Conda is installed locally")
        check_unison_installed_local()
        clog.info(f"PASS - Unison is installed locally")
    else:
        try:
            check_conda_installed_remote(target)
            clog.info(f"PASS - Conda is installed on remote '{target['name']}'")
        except MissingDependency as ex:
            if raise_on_error:
                raise ex
            elif no_confirm or click.confirm(
                "It seems conda is not available on the remote. "
                "Do you want to install it now?",
                default=True,
            ):
                install_conda_remote(target)
        try:
            check_unison_installed_remote(target)
            clog.info(f"PASS - Unison is installed on remote '{target['name']}'")
        except MissingDependency as ex:
            if raise_on_error:
                raise ex
            elif no_confirm or click.confirm(
                "It seems unison is not available on the remote. "
                "Do you want to install it now?",
                default=True,
            ):
                install_unison_remote(target)


def check(raise_on_error=False):
    check_target(raise_on_error=raise_on_error)
    db = read_remote_db()
    for remote_id in list_remote_ids(db):
        clog.info(f"Checking remote '{remote_id}'")
        remote_settings = get_remote(db, remote_id)
        check_target(remote_settings, raise_on_error=raise_on_error)
        if in_resolos_dir():
            check_unison_connection(remote_settings)


def setup_ssh(remote_settings):
    key_location = os.path.expanduser(RESOLOS_PRIVATE_SSH_KEY_LOCATION)
    if not pathlib.Path(key_location).exists():
        clog.info(f"Generating new SSH key {key_location}")
        ret_val, output = run_shell_cmd(
            f"ssh-keygen -t rsa -N '' -C resolos@{node()} -f ~/.ssh/id_rsa_resolos"
        )
        if ret_val != 0:
            if "command not found" in output:
                raise MissingDependency(
                    f"Looks like ssh-keygen is not installed, "
                    f"please install it to generate new key pair"
                )
            else:
                raise MissingDependency(
                    f"Unexpected error with ssh-keygen:\n\n{output}\n\n"
                )
    else:
        clog.info(f"Using SSH key {key_location}")
    clog.info(
        f"Will set up now remote '{remote_settings['name']}' to accept the SSH key {key_location}. "
        f"Please enter your password when prompted"
    )
    ret_val, pub_key = run_shell_cmd(f"cat {RESOLOS_PRIVATE_SSH_KEY_LOCATION}.pub")
    if ret_val != 0:
        raise ShellError(
            f"Could not find SSH public key {RESOLOS_PRIVATE_SSH_KEY_LOCATION}.pub"
        )
    ret_val, output = run_ssh_cmd(
        remote_settings, f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys", force_password=True
    )
    if ret_val != 0:
        raise ShellError(
            f"Could not add resolos ssh key to authorized_keys on remote, "
            f"the error message was: {output}"
        )
    gdc = get_global_dict_config()
    s = gdc.read()
    if s.get("ssh_key") != key_location:
        s["ssh_key"] = key_location
        gdc.write(s)
