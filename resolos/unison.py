from .logging import clog
from .config import (
    UNISON_LINUX_INSTALLER_URL,
    read_project_remote_config,
    write_project_remote_config,
    randomString,
    get_ssh_key,
    SSH_SERVERALIVEINTERVAL,
    UNISON_VERSION,
)
from .exception import (
    MissingDependency,
    RemoteCommandError,
    LocalCommandError,
    DependencyVersionError,
)
from .shell import run_shell_cmd, run_ssh_cmd
from .platform import find_project_dir, get_unison_config_folder
import click
from semver import VersionInfo
from datetime import datetime
import re


unison_ver_re = re.compile(r"unison version (\d+.\d+.\d+)")


def unison_base_command():
    return f"export PATH=~/bin:$PATH && export UNISON={get_unison_config_folder()} && unison"


def verify_unison_version(output):
    m = unison_ver_re.search(output)
    if m:
        unison_ver = VersionInfo.parse(m.group(1))
        if unison_ver != UNISON_VERSION:
            raise DependencyVersionError(
                f"Resolos requires a fixed unison version {UNISON_VERSION}, "
                f"while it seems you have version {unison_ver} installed. "
                f"Please reinstall the requested version"
            )
    else:
        clog.warning(
            f"Could not determine unison version, resolos might not function correctly. "
            f"Please uinstall the specified unison version"
        )


def check_unison_installed_local():
    ret_val, output = run_shell_cmd("export PATH=~/bin:$PATH && unison -version")
    if ret_val != 0:
        raise MissingDependency(
            f"Unison test command 'unison -version' raised error on local machine:\n\n{output}\n\n"
            f"Please try and reinstall unison"
        )
    verify_unison_version(output)


def check_unison_installed_remote(remote_settings):
    ret_val, output = run_ssh_cmd(
        remote_settings, f"{remote_settings['unison_path']} -version"
    )
    if ret_val != 0:
        raise MissingDependency(
            f"Unison test command 'unison -version' raised error on remote {remote_settings['name']}:\n\n{output}\n\n"
            f"Please try and reinstall unison"
        )
    verify_unison_version(output)


def install_unison_remote(remote_settings):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"mkdir -p ~/bin "
        f"&& wget {UNISON_LINUX_INSTALLER_URL} -O ~/bin/unison.tar.gz "
        f"&& tar -xvf ~/bin/unison.tar.gz bin/unison -C {remote_settings['unison_path']}"
        f"&& rm ~/bin/unison.tar.gz",
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Could not install unison on remote, the error message was:\n\n{output}\n\n"
        )


def main_unison_command(remote_settings, local_folder, remote_folder):
    ssh_key = get_ssh_key()
    if ssh_key is None:
        return (
            f"{unison_base_command()} default "
            f"{local_folder} "
            f"ssh://{remote_settings['username']}@{remote_settings['hostname']}/{remote_folder} "
            f'-sshargs "-p {remote_settings["port"]} -o ServerAliveInterval={SSH_SERVERALIVEINTERVAL}" '
            f"-servercmd {remote_settings['unison_path']}"
        )
    else:
        return (
            f"{unison_base_command()} default "
            f"{local_folder} "
            f"ssh://{remote_settings['username']}@{remote_settings['hostname']}/{remote_folder} "
            f'-sshargs "-p {remote_settings["port"]} -i {ssh_key}" '
            f"-servercmd {remote_settings['unison_path']}"
        )


def check_unison_connection(remote_settings):
    project_dir = find_project_dir()
    remote_path = f"./{project_dir.name}"

    ret_val, output = run_shell_cmd(
        f"{main_unison_command(remote_settings, project_dir.absolute(), remote_path)} -testserver",
        shell_type="bash_login",
    )
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not run sync on remote, the error message was:\n\n{output}\n\n"
        )
    clog.info(f"PASS - Unison test command worked on '{remote_settings['name']}'")


def sync_files(remote_settings):
    project_dir = find_project_dir()
    remote_id = remote_settings["name"]
    project_remote_settings = read_project_remote_config(remote_id)
    if project_remote_settings is None:
        project_remote_settings = {
            "env_name": None,
            "files_path": f"./resolos_projects/{project_dir.name}_{randomString()}",
        }
        write_project_remote_config(remote_id, project_remote_settings)
    remote_path = project_remote_settings["files_path"]
    if remote_path is None:
        remote_path = f"./resolos_projects/{project_dir.name}_{randomString()}"
        project_remote_settings["files_path"] = remote_path
        write_project_remote_config(remote_id, project_remote_settings)
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"mkdir -p {remote_path}",
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Failed to create project folder {remote_path} on remote, "
            f"the error message was:\n{output}"
        )
    ret_val, output = run_shell_cmd(
        main_unison_command(remote_settings, project_dir.absolute(), remote_path),
        shell_type="bash_login",
    )
    if ret_val == 0:
        project_remote_settings["last_files_sync"] = datetime.utcnow()
        write_project_remote_config(remote_id, project_remote_settings)
        clog.info(f"Successfully synced project files")
    else:
        if re.search("Archive .* is MISSING", output):
            clog.debug(
                f"Encountered 'Archive missing' unison error, "
                f"running unison again with the -ignorearchives flag"
            )
            ret_val, output = run_shell_cmd(
                f"{main_unison_command(remote_settings, project_dir.absolute(), remote_path)} -ignorearchives",
                shell_type="bash_login",
            )
            if ret_val != 0:
                raise RemoteCommandError(
                    f"Could not run sync on remote '{remote_settings['name']}', the error message was:\n\n{output}\n\n"
                )
            else:
                project_remote_settings["last_files_sync"] = datetime.utcnow()
                write_project_remote_config(remote_id, project_remote_settings)
                clog.info(f"Successfully synced project files")
        elif re.search("the archives are locked", output):
            clog.info(
                f"The unison archive files are locked for remote '{remote_settings['name']}'. This can happen "
                f"if a previous sync was stopped before completion, "
                f"or if there is another sync already in progress with the remote. "
                f"You can continue now by ignoring the archive locks, which can cause problems in case there "
                f"is another sync in progress."
            )
            if click.confirm(
                "Do you want to continue with the current sync?", default=True
            ):
                ret_val, output = run_shell_cmd(
                    f"{main_unison_command(remote_settings, project_dir.absolute(), remote_path)} -ignorelocks",
                    shell_type="bash_login",
                )
                if ret_val != 0:
                    raise RemoteCommandError(
                        f"Could not run sync on remote '{remote_settings['name']}', the error message was:\n\n{output}\n\n"
                    )
                else:
                    project_remote_settings["last_files_sync"] = datetime.utcnow()
                    write_project_remote_config(remote_id, project_remote_settings)
                    clog.info(f"Successfully synced project files")
        elif re.search(
            "Try running once with the fastcheck option set to 'no'", output
        ):
            clog.debug(
                f"Encountered 'Try running once with the fastcheck option set to 'no'' unison error, "
                f"running unison again with the -fastcheck false flag"
            )
            ret_val, output = run_shell_cmd(
                f"{main_unison_command(remote_settings, project_dir.absolute(), remote_path)} -fastcheck false",
                shell_type="bash_login",
            )
            if ret_val != 0:
                raise RemoteCommandError(
                    f"Could not run sync on remote '{remote_settings['name']}', the error message was:\n\n{output}\n\n"
                )
            else:
                project_remote_settings["last_files_sync"] = datetime.utcnow()
                write_project_remote_config(remote_id, project_remote_settings)
                clog.info(f"Successfully synced project files")
        else:
            raise RemoteCommandError(
                f"Could not run sync on remote '{remote_settings['name']}', the error message was:\n\n{output}\n\n"
            )
