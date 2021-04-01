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
from .exception import MissingDependency
from .shell import run_ssh_cmd, run_shell_cmd, check_bash_version_local
import click
from platform import node
import pathlib
import os


def check_target(target=None):
    if target is None:
        check_bash_version_local()
        clog.info(f"PASS - Bash version is sufficiently new")
        check_conda_installed_local()
        clog.info(f"PASS - Conda is installed locally")
        check_unison_installed_local()
        clog.info(f"PASS - Unison is installed locally")
    else:
        try:
            check_conda_installed_remote(target)
            clog.info(f"PASS - Conda is installed on remote '{target['name']}'")
        except MissingDependency:
            if click.confirm(
                "It seems conda is not available on the remote. "
                "Do you want to install it now?",
                default=True,
            ):
                install_conda_remote(target)
        try:
            check_unison_installed_remote(target)
            clog.info(f"PASS - Unison is installed on remote '{target['name']}'")
        except MissingDependency:
            if click.confirm(
                "It seems unison is not available on the remote. "
                "Do you want to install it now?",
                default=True,
            ):
                install_unison_remote(target)


def check():
    check_target()
    db = read_remote_db()
    for remote_id in list_remote_ids(db):
        clog.info(f"Checking remote '{remote_id}'")
        remote_settings = get_remote(db, remote_id)
        check_target(remote_settings)
        if in_resolos_dir():
            check_unison_connection(remote_settings)


def setup_ssh(remote_settings):
    key_location = os.path.expanduser("~/.ssh/id_rsa_resolos")
    if not pathlib.Path(key_location).exists():
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
    clog.info(
        f"Will set up now remote '{remote_settings['name']}' to accept the new SSH key. "
        f"Please enter your password when prompted"
    )
    ret_val, pub_key = run_shell_cmd("cat ~/.ssh/id_rsa_resolos.pub")
    run_ssh_cmd(
        remote_settings, f"mkdir -p .ssh && echo '{pub_key}' >> .ssh/authorized_keys"
    )
    gdc = get_global_dict_config()
    s = gdc.read()
    s["ssh_key"] = key_location
    gdc.write(s)