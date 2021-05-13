from .logging import clog
from .config import (
    CONDA_LINUX_INSTALLER_URL,
    get_project_remote_dict_config,
    get_project_settings_for_remote,
    get_project_env,
    randomString,
    CONDA_MIN_VERSION,
    read_project_remote_config,
    write_project_remote_config,
)
from .exception import MissingDependency, RemoteCommandError, LocalCommandError
from .shell import run_shell_cmd, run_ssh_cmd
from .platform import find_project_dir, is_linux_64
from .exception import ResolosException, DependencyVersionError, SSHError
from .unison import sync_files
import pathlib
import json
import ast
from semver import VersionInfo
from datetime import datetime
import re


conda_ver_re = re.compile(r"conda (\d+.\d+.\d+)")


def verify_conda_version(output):
    m = conda_ver_re.search(output)
    if m:
        conda_ver = VersionInfo.parse(m.group(1))
        if conda_ver < CONDA_MIN_VERSION:
            raise DependencyVersionError(
                f"Resolos requires a minimum conda version {CONDA_MIN_VERSION}, "
                f"while it seems you have version {conda_ver} installed. "
                f"Please run 'conda update conda' or your preferred update method"
            )
    else:
        clog.warning(
            f"Could not determine conda version, resolos might not function correctly. "
            f"Please reinstall conda"
        )


def check_conda_installed_local():
    ret_val, output = run_shell_cmd("conda --version")
    if ret_val != 0:
        raise MissingDependency(
            f"Conda test command 'conda --version' raised error on local machine:\n\n{output}\n\n"
            f"Please try and reinstall conda"
        )
    verify_conda_version(output)


def check_conda_env_exists_local(env_name: str):
    if env_name.startswith("source "):
        ret_val, output = run_shell_cmd(env_name)
        if ret_val == 0:
            return True
        elif "Could not find conda environment" in output:
            return False
        else:
            raise ResolosException(
                f"Unexpected conda error for command '{env_name}':\n\n{output}\n\n"
            )
    else:
        cmd = f"conda activate {env_name}"
        ret_val, output = run_shell_cmd(cmd)
        if ret_val == 0:
            return True
        elif "Could not find conda environment" in output:
            return False
        else:
            raise ResolosException(
                f"Unexpected conda error for command '{cmd}':\n\n{output}\n\n"
            )


def create_conda_env_local(env_name: str):
    # Python < 3.9 is required by conda-tree
    # https://stackoverflow.com/questions/66174862/import-error-cant-import-name-gcd-from-fractions
    ret_val, output = run_shell_cmd(
        f'conda create -y -n {env_name} "python<3.9"',
    )
    if ret_val != 0:
        raise ResolosException(
            f"Unexpected conda error for command 'conda create -n {env_name}':\n\n{output}\n\n"
        )


def check_conda_installed_remote(remote_settings):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"{remote_settings['conda_load_command']} && conda --version",
    )
    if ret_val != 0:
        raise MissingDependency(
            f"Conda test command 'conda --version' raised error on remote {remote_settings['name']}:\n\n{output}\n\n"
            f"Please run 'res check'"
        )
    verify_conda_version(output)


def check_conda_env_exists_remote(remote_settings, env_name):
    if env_name.startswith("source "):
        ret_val, output = run_ssh_cmd(
            remote_settings,
            env_name,
        )
        if ret_val == 0:
            return True
        elif "Could not find conda environment" in output:
            return False
        else:
            raise ResolosException(
                f"Unexpected conda error for command '{env_name}':\n\n{output}\n\n"
            )
    else:
        cmd = f"{remote_settings['conda_load_command']} && conda activate {env_name}"
        ret_val, output = run_ssh_cmd(
            remote_settings,
            cmd,
        )
        if ret_val == 0:
            return True
        elif "Could not find conda environment" in output:
            return False
        else:
            raise ResolosException(
                f"Unexpected conda error for command '{cmd}':\n\n{output}\n\n"
            )


def create_conda_env_remote(remote_settings, env_name: str):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"{remote_settings['conda_load_command']} && conda create -y -n {env_name}",
    )
    if ret_val != 0:
        raise ResolosException(
            f"Unexpected conda error for command 'conda create -n {env_name}':\n\n{output}\n\n"
        )


def install_conda_remote(remote_settings):
    ret_val, output = run_ssh_cmd(
        remote_settings,
        f"wget -q {CONDA_LINUX_INSTALLER_URL} -O {remote_settings['conda_install_path']}/miniconda.sh "
        f"&& bash {remote_settings['conda_install_path']}/miniconda.sh -b -p {remote_settings['conda_install_path']}/miniconda"
        f"&& rm {remote_settings['conda_install_path']}/miniconda.sh",
        stdout_as_info=True,
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Could not install conda on remote, the error message was:\n\n{output}\n\n"
        )


def execute_command_in_local_conda_env(cmd, env, stdout_as_info=True):
    if env.startswith("source "):
        conda_cmd = f"{env} && {cmd}"
    else:
        # Multiple conda installations can cause problems with environment activation when running
        # in a subshell
        # https://github.com/conda/conda/issues/9392
        # Workaround: do a deactivate first
        conda_cmd = f"conda deactivate && conda activate {env} && {cmd}"
    ret_val, output = run_shell_cmd(conda_cmd, stdout_as_info=stdout_as_info)
    if ret_val != 0:
        raise LocalCommandError(
            f"Command '{cmd}' executed in local conda env {env} raised error:\n\n{output}\n\n"
        )
    return ret_val, output


def execute_command_in_remote_conda_env(cmd, remote_settings, env, stdout_as_info=True):
    if env.startswith("source "):
        conda_cmd = f"{env} && {cmd}"
    else:
        conda_cmd = (
            f"{remote_settings['conda_load_command']} && conda activate {env} && {cmd}"
        )
    ret_val, output = run_ssh_cmd(
        remote_settings,
        conda_cmd,
        stdout_as_info=stdout_as_info,
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Remote command '{cmd}' raised error on remote machine:\n\n{output}\n\n"
        )
    return ret_val, output


def execute_local_conda_command(cmd, env=None, stdout_as_info=False):
    if env:
        if env.startswith("source "):
            conda_cmd = f"{env} && conda {cmd}"
        else:
            # Multiple conda installations can cause problems with environment activation when running
            # in a subshell
            # https://github.com/conda/conda/issues/9392
            # Workaround: do a deactivate first
            conda_cmd = f"conda deactivate && conda activate {env} && conda {cmd}"
    else:
        conda_cmd = f"conda {cmd}"
    ret_val, output = run_shell_cmd(conda_cmd, stdout_as_info=stdout_as_info)
    if ret_val != 0:
        raise LocalCommandError(
            f"Command '{conda_cmd}' raised error on local machine:\n\n{output}\n\n"
        )
    return ret_val, output


def execute_remote_conda_command(cmd, remote_settings, env=None, stdout_as_info=True):
    if env:
        if env.startswith("source "):
            conda_cmd = f"{env} && conda {cmd}"
        else:
            conda_cmd = f"{remote_settings['conda_load_command']} && conda activate {env} && conda {cmd}"
    else:
        conda_cmd = f"{remote_settings['conda_load_command']} && conda {cmd}"
    ret_val, output = run_ssh_cmd(
        remote_settings,
        conda_cmd,
        stdout_as_info=stdout_as_info,
    )
    if ret_val != 0:
        raise RemoteCommandError(
            f"Remote command 'conda {cmd}' raised error on remote machine:\n\n{output}\n\n"
        )
    return ret_val, output


def execute_conda_command(
    cmd, target=None, env=None, stdout_as_info=False, info_msg=None
):
    if target:
        if info_msg:
            clog.info(f"{info_msg} on remote {target['name']}...")
        return execute_remote_conda_command(
            cmd, target, env=env, stdout_as_info=stdout_as_info
        )
    else:
        if info_msg:
            clog.info(f"{info_msg} on local machine...")
        return execute_local_conda_command(cmd, env=env, stdout_as_info=stdout_as_info)


def execute_conda_command_local_and_remote(
    cmd: str,
    remote: str,
    env=None,
    stdout_as_info=True,
    local_msg: str = None,
    remote_msg: str = None,
    success_message: str = None,
):
    if local_msg:
        clog.info(local_msg)
    execute_local_conda_command(cmd, env=env, stdout_as_info=stdout_as_info)
    if remote_msg:
        clog.info(remote_msg)
    execute_remote_conda_command(cmd, remote, env=env, stdout_as_info=stdout_as_info)
    if success_message:
        clog.info(success_message)


def install_conda_packages(package_list, target=None):
    packages = " ".join(package_list)
    install_command = f"install -y {packages}"
    if target:
        remote_id = target["name"]
        local_env, remote_env, remote_path = get_project_settings_for_remote(remote_id)
        clog.info(f"Installing packages {packages} in remote environment {remote_env}")
        if not check_conda_env_exists_remote(target, remote_env):
            create_conda_env_remote(target, remote_env)
        execute_remote_conda_command(
            install_command,
            target,
            env=remote_env,
        )
    else:
        clog.info(f"Installing packages {packages} in local environment")
        local_env = get_project_env()
        if not check_conda_env_exists_local(local_env):
            create_conda_env_local(local_env)
        execute_local_conda_command(
            install_command,
            env=local_env,
            stdout_as_info=True,
        )


def uninstall_conda_packages(package_list, target=None):
    packages = " ".join(package_list)
    uninstall_command = f"uninstall -y {packages}"
    if target:
        remote_id = target["name"]
        local_env, remote_env, remote_path = get_project_settings_for_remote(remote_id)
        if not check_conda_env_exists_remote(target, remote_env):
            create_conda_env_remote(target, remote_env)
        execute_remote_conda_command(
            uninstall_command,
            target,
            env=remote_env,
        )
    else:
        local_env = get_project_env()
        if not check_conda_env_exists_local(local_env):
            create_conda_env_local(local_env)
        execute_local_conda_command(
            uninstall_command,
            env=local_env,
            stdout_as_info=True,
        )


def pack_conda_env(env_name: str, pack_name: str, target=None):
    clog.debug(f"Installing conda-pack...")
    ret_val, output = execute_local_conda_command(f"install -y conda-pack")
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not install conda-pack "
            f"with command 'conda install -y conda-pack', "
            f"the error was:\n\n{output}\n\n"
        )
    return execute_conda_command(f"pack -n {env_name} -o {pack_name}", target=target)


def export_conda_env(
    env_name: str, only_explicitly_installed=True, target=None, filename=None
):
    flags = "--from-history" if only_explicitly_installed else ""
    if filename is None:
        return execute_conda_command(
            f"env export {flags}", target=target, env=env_name, stdout_as_info=False
        )
    else:
        ret_val, output = execute_conda_command(
            f"env export {flags}", target=target, env=env_name, stdout_as_info=False
        )
        if ret_val != 0:
            raise LocalCommandError(
                f"Could not export conda env, the error message was:\n\n{output}\n\n"
            )
        else:
            with open(filename, "w") as f:
                f.write(output)


def explicit_package_list(env_name: str, target=None, filename=None):
    if filename is None:
        return execute_conda_command(
            f"list --explicit", target=target, env=env_name, stdout_as_info=False
        )
    else:
        ret_val, output = execute_conda_command(
            f"list --explicit", target=target, env=env_name, stdout_as_info=False
        )
        if ret_val != 0:
            raise LocalCommandError(
                f"Could not list explicit packages, the error message was:\n\n{output}\n\n"
            )
        else:
            with open(filename, "w") as f:
                f.write(output)


def get_requirements(env_name, filename=None):
    ret_val, output = execute_local_conda_command(f"list --json", env=env_name)
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not get list of installed packages in json format "
            f"with command 'conda list --json', "
            f"the error was:\n\n{output}\n\n"
        )
    packages_data = json.loads(output)
    res = []
    for pkg in packages_data:
        skip = False
        name = pkg.get("name")
        if name is None:
            clog.warning(f"Could not get name of package {pkg}, will skip it")
            skip = True
        version = pkg.get("version")
        if version is None:
            clog.warning(f"Could not get version of package {pkg}, will skip it")
            skip = True
        if not skip:
            res.append(f"{name}=={version}")
    requirements = "\n".join(res)
    clog.debug(f"The requirements file is:\n{requirements}\n")
    if filename is None:
        return requirements
    else:
        with open(filename, "w") as f:
            f.write(requirements)


def get_nondep_packages(env_name, filename=None):
    clog.debug(f"Installing conda-tree...")
    ret_val, output = execute_local_conda_command(
        f"install -y -c conda-forge conda-tree", env=env_name
    )
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not install conda-tree to get the list of non-dependency packages "
            f"with command 'conda install -y -c conda-forge conda-tree', "
            f"the error was:\n\n{output}\n\n"
        )
    clog.debug(f"Getting list of packages...")
    ret_val, output = execute_local_conda_command(f"list --json", env=env_name)
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not get list of installed packages in json format "
            f"with command 'conda list --json', "
            f"the error was:\n\n{output}\n\n"
        )
    packages_data = json.loads(output)
    ret_val, output = execute_command_in_local_conda_env(
        "conda-tree leaves", env_name, stdout_as_info=False
    )
    if ret_val != 0:
        raise LocalCommandError(
            f"Could not get list of non-dependency packages "
            f"with command 'conda-tree leaves', "
            f"the error was:\n\n{output}\n\n"
        )
    leaves = ast.literal_eval(output)
    res = []
    for pkg in leaves:
        if pkg not in ["conda-tree", "pip", "conda"]:
            pgk_data = [i for i in packages_data if i.get("name") == pkg]
            if len(pgk_data) == 0:
                res.append(pkg)
            else:
                ver = pgk_data[0].get("version")
                if ver:
                    res.append(f"{pkg}=={ver}")
                else:
                    res.append(pkg)
    clog.debug(f"Found non-dependent packages: {res}")
    if filename is None:
        return res
    else:
        requirements = "\n".join(res)
        with open(filename, "w") as f:
            f.write(requirements)


def sync_env_and_files(remote_settings):
    project_dir = find_project_dir()
    remote_id = remote_settings["name"]
    local_env, remote_env, remote_path = get_project_settings_for_remote(remote_id)
    env_folder = project_dir / ".env"
    pathlib.Path.mkdir(env_folder, exist_ok=True)
    if is_linux_64():
        clog.info(
            f"The local machine has the same platform and OS as the remote (linux, x86_64), will use the "
            f"explicit packages list to sync the environment"
        )
        explicit_packages_file = env_folder / "spec-file.txt"
        explicit_package_list(local_env, filename=explicit_packages_file)
        clog.info(f"Syncing project files...")
        sync_files(remote_settings)
        if not check_conda_env_exists_remote(remote_settings, remote_env):
            create_conda_env_remote(remote_settings, remote_env)
        try:
            execute_remote_conda_command(
                f"install --name {remote_env} --file {remote_path}/.env/spec-file.txt",
                remote_settings,
            )
            project_remote_settings = read_project_remote_config(remote_id)
            project_remote_settings["last_env_sync"] = datetime.utcnow()
            write_project_remote_config(remote_id, project_remote_settings)
        except RemoteCommandError as ex:
            clog.info(
                f"Failed to sync conda env to remote '{remote_id}' using explicit packages list, "
                f"will use now conda-pack..."
            )
            pack_file = env_folder / "conda_pack.tar.gz"
            pack_conda_env(local_env, pack_file)
            sync_files(remote_settings)
            remote_env_name = f"resolos_env_{randomString()}"
            ret_val, output = run_ssh_cmd(
                remote_settings,
                f"mkdir -p ./.resolos/envs/{remote_env_name} && "
                f"tar -xzf {remote_path}/.env/conda_pack.tar.gz -C ./.resolos/envs/{remote_env_name} && "
                f"source ./.resolos/envs/{remote_env_name}/bin/activate && "
                f"conda-unpack",
            )
            if ret_val != 0:
                raise RemoteCommandError(
                    f"Could not use conda-pack to sync the environment to the remote, "
                    f"the error message was:\n{output}\n"
                )
            project_remote_settings = read_project_remote_config(remote_id)
            project_remote_settings[
                "env_name"
            ] = f"source ./.resolos/envs/{remote_env_name}/bin/activate"
            project_remote_settings["last_env_sync"] = datetime.utcnow()
            write_project_remote_config(remote_id, project_remote_settings)
    else:
        clog.info(
            f"The local machine has a different platform or OS as the remote (linux, x86_64), will use the environment "
            f"yaml file to sync the environment"
        )
        env_file = env_folder / "env.yaml"
        env_history_file = env_folder / "env_from_history.yaml"
        export_conda_env(local_env, filename=env_file, only_explicitly_installed=False)
        export_conda_env(local_env, filename=env_history_file)
        clog.info("Syncing project files...")
        sync_files(remote_settings)
        try:
            execute_remote_conda_command(
                f"env update -n {remote_env} -f {remote_path}/.env/env.yaml",
                remote_settings,
            )
            project_remote_settings = read_project_remote_config(remote_id)
            project_remote_settings["last_env_sync"] = datetime.utcnow()
            write_project_remote_config(remote_id, project_remote_settings)
        except RemoteCommandError as ex:
            clog.info(
                f"Failed to sync conda env to remote '{remote_id}' using complete environment description, "
                f"will try  to replay conda install history on remote instead..."
            )
            try:
                execute_remote_conda_command(
                    f"env update -n {remote_env} -f {remote_path}/.env/env_from_history.yaml",
                    remote_settings,
                )
                project_remote_settings = read_project_remote_config(remote_id)
                project_remote_settings["last_env_sync"] = datetime.utcnow()
                write_project_remote_config(remote_id, project_remote_settings)
            except RemoteCommandError:
                clog.info(
                    f"Failed to sync conda env to remote '{remote_id}' using conda env --from-history, "
                    f"will try to install now the non-dependent packages"
                )
                nondep_packages = get_nondep_packages(local_env)
                install_conda_packages(nondep_packages, target=remote_settings)
                project_remote_settings = read_project_remote_config(remote_id)
                project_remote_settings["last_env_sync"] = datetime.utcnow()
                write_project_remote_config(remote_id, project_remote_settings)
