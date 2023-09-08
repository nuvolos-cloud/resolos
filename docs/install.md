# Installing dependencies

## I. Bash

Resolos uses [bash](https://www.gnu.org/software/bash/) to interact with the various tools (conda, unison) for project management and data sychronization.
Bash need not be the default shell on your machine, but it should be possible to execute commands like `bash ...` from the default shell.
Also, bash should be relatively up-to-date (>5.0.0).

### Linux

Your OS should already have an up-to-date bash, if not consult its package manager to update to a newer version.

### macOS

macOS ships with a highly outdated bash version. The simplest solution is to install a newer version via [homebrew](https://brew.sh/).
Follow the instructions to install homebrew itself, then execute:

```
brew install bash
bash --version
```

### Windows

On Windows, using WSL is recommended. 

## II. SSH

In order to use Resolos with a remote HPC cluster, the `ssh` command needs to be available in your shell. Linux and MacOS machines
generally have this tool already installed or can be installed with a few commands. If you have a Windows-based machine,
it's possible to install the openSSH client as well, but it is usually easier to use the Windows Subsystem for Linux (WSL) directly.

## III. conda

### Linux, macOS and Windows

Follow the [official documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation) to install Miniconda which provides the `conda` command.


## IV. unison

Resolos uses [unison](https://github.com/bcpierce00/unison) for file synchronization between local and remote machines.
Since version `2.52`, Unison has a degree of backward and forward compatibility.
Currently it's recommended to use version`2.52` or newer for compatibility:, as it can be easily installed for 
both macOS and Linux.

### Linux

If you have wget and tar, you can execute the following command to install version `2.53.3`:

```
wget https://github.com/bcpierce00/unison/releases/download/v2.53.3/unison-2.53.3-ubuntu-x86_64-static.tar.gz && mkdir -p ~/bin && tar -xf unison-2.53.3-ubuntu-x86_64-static.tar.gz -C ~ bin/unison && hash -r 
```


### macOS

First install [homebrew](https://brew.sh/), then use 

```
brew install unison
```

This should install version `unison version 2.53.3` (or newer). To check, use the command 

```
unsion -version
```

### Windows

You can install both conda and unison natively on Windows, but unison also needs ssh, which has to be installed and configured.
For this reason, using WSL on windows is recommended. Once installed, you can follow the instructions for Linux in WSL.


# Installing resolos

Since resolos needs conda, it is recommended to install resolos into the base conda environment:

```
conda activate
pip install resolos
```

The following section hosts two quickstart examples.