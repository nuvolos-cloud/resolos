import subprocess
import os
from shutil import which
from time import sleep
from shlex import quote
from .logging import clog
from .config import get_ssh_key, SSH_SERVERALIVEINTERVAL, BASH_MIN_VERSION, ver_re
from .exception import (
    ShellError,
    MissingDependency,
    DependencyVersionError,
    SSHError,
    RemoteCommandError,
)
from semver import VersionInfo
from pathlib import Path

CMD_BEGIN = "-----------------RESOLOS_BEGIN-----------------"
CMD_END = "-----------------RESOLOS_END-----------------"


def check_bash_version_local():
    ret_val, output = run_shell_cmd("bash --version")
    if ret_val != 0:
        raise MissingDependency(
            f"Bash test command 'bash --version' raised error on local machine:\n\n{output}\n\n"
            f"Please try and reinstall bash"
        )
    m = ver_re.search(output)
    if m:
        bash_ver = VersionInfo.parse(m.group())
        if bash_ver < BASH_MIN_VERSION:
            raise DependencyVersionError(
                f"Resolos requires a minimum bash version {BASH_MIN_VERSION}, "
                f"while it seems you have version {bash_ver} installed. "
                f"Please update your bash"
            )
    else:
        clog.warning(
            f"Could not determine bash version, resolos might not function correctly. "
            f"Please update to the latest available bash version"
        )


def trim_stdout(stdout):
    parts = stdout.split(CMD_BEGIN)
    if len(parts) < 2:
        raise ShellError(
            f"Shell command output should contain string {CMD_BEGIN}, but it was not found. "
            f"The output was:\n\n{stdout}"
        )
    elif len(parts) > 2:
        raise ShellError(
            f"Shell command output should contain string {CMD_BEGIN} only once, "
            f"but it was found more than once! The output was:\n\n{stdout}"
        )
    else:
        output = parts[1]
        parts = output.split(CMD_END)
        if len(parts) < 1:
            # In case an error was thrown, CMD_END will not be appended
            return output
        elif len(parts) > 2:
            raise ShellError(
                f"Shell command output should contain string {CMD_END} only once, "
                f"but it was found more than once! The output was:\n\n{stdout}"
            )
        else:
            return parts[0]


def run_shell_cmd(
    cmd,
    max_wait_secs: int = 3600,
    sleep_secs: int = 1,
    stdout_as_info=False,
    shell_type="bash_interactive_login",
):
    waited = 0
    stdout = ""
    if shell_type == "bash_interactive_login":
        bash_cmd = f"bash -i -l -c {quote(f'cd {Path.cwd()} && echo {CMD_BEGIN} && ' + cmd + f' && echo {CMD_END}; exit 2>/dev/null')}"
    elif shell_type == "bash_login":
        bash_cmd = f"bash -l -c {quote(f'cd {Path.cwd()} && echo {CMD_BEGIN} && ' + cmd + f' && echo {CMD_END}')}"
    elif shell_type == "bash_non_login":
        bash_cmd = f"bash -c {quote(f'cd {Path.cwd()} && echo {CMD_BEGIN} && ' + cmd + f' && echo {CMD_END}')}"
    else:
        bash_cmd = quote(f"echo {CMD_BEGIN} && " + cmd + f" && echo {CMD_END}")
    clog.debug(f"Running command '{bash_cmd}'...")
    proc = subprocess.Popen(
        bash_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        shell=True,
        bufsize=1,
        universal_newlines=True,
    )
    # Wait for the process end and print error in case of failure
    ret_val = proc.poll()
    print_to_info = False
    while ret_val is None:
        if waited >= max_wait_secs:
            proc.kill()
            raise TimeoutError()
        new_stdout = proc.stdout.readline()
        while new_stdout:
            if stdout_as_info:
                if new_stdout.startswith(CMD_END):
                    print_to_info = False
                if print_to_info:
                    clog.info(new_stdout.replace("\n", ""))
                if new_stdout.startswith(CMD_BEGIN):
                    print_to_info = True
            else:
                clog.debug(new_stdout.replace("\n", ""))
            stdout = stdout + new_stdout
            new_stdout = proc.stdout.readline()
        waited = waited + sleep_secs
        sleep(sleep_secs)
        ret_val = proc.poll()
    # Get the last part
    proc.stdout.flush()
    new_stdout = proc.stdout.readline()
    while new_stdout:
        if stdout_as_info:
            if new_stdout.startswith(CMD_END):
                print_to_info = False
            if print_to_info:
                clog.info(new_stdout.trim())
            if new_stdout.startswith(CMD_BEGIN):
                print_to_info = True
        else:
            clog.debug(new_stdout.replace("\n", ""))
        stdout = stdout + new_stdout
        new_stdout = proc.stdout.readline()
    clog.debug(f"Command '{bash_cmd}' finished with exit code {ret_val}")
    return ret_val, trim_stdout(stdout)


def run_ssh_cmd(
    remote_settings,
    cmd,
    max_wait_secs: int = 3600,
    sleep_secs: int = 1,
    stdout_as_info=False,
    shell_type="bash_login",
    login_shell_remote=True,
    force_password=False,
):
    username = remote_settings["username"]
    hostname = remote_settings["hostname"]
    port = remote_settings["port"]
    if login_shell_remote:
        remote_cmd = f"bash -l -c {quote(cmd)}"
    else:
        remote_cmd = cmd
    ssh_key = get_ssh_key()
    if ssh_key is None or force_password:
        if which("sshpass") and "SSHPASS" in os.environ:
            ssh_cmd = f"sshpass -e ssh {username}@{hostname} -p {port} -o ServerAliveInterval={SSH_SERVERALIVEINTERVAL} {quote(remote_cmd)}"
        else:
            ssh_cmd = f"ssh {username}@{hostname} -p {port} -o ServerAliveInterval={SSH_SERVERALIVEINTERVAL} {quote(remote_cmd)}"
    else:
        ssh_cmd = f"ssh {username}@{hostname} -p {port} -o ServerAliveInterval={SSH_SERVERALIVEINTERVAL} -i {ssh_key} {quote(remote_cmd)}"
    ret_val, output = run_shell_cmd(
        ssh_cmd,
        max_wait_secs=max_wait_secs,
        sleep_secs=sleep_secs,
        stdout_as_info=stdout_as_info,
        shell_type=shell_type,
    )
    if ret_val != 0:
        if "Could not resolve hostname" in output:
            raise SSHError(output)
        elif "Connection refused" in output:
            raise SSHError(output)
    return ret_val, output


def remove_remote_folder(remote_settings, folder):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"if [ -d {quote(folder)} ]; then rm -rf {quote(folder)}; fi",
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Could not remove folder '{folder}' on remote, the error message was:\n{output}\n"
        )
