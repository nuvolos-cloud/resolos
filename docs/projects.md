# Resolos projects

In resolos, execution environments are called projects. A resolos project consist of the following parts:

- a folder containing source code, input and/or output data, documentation, etc.
- a linked conda environment on the local machine

Projects have the following capabilites:

- run code in the linked environment locally
- archive to and load from project archive files
- sync the project folder and the linked environment to defined remote(s)
- manage HPC jobs on defined remote(s)

## Initializing a new project

To initalize a new resolos project, cd in a terminal to the desired project folder, and execute

```
r3s init
```

Initialization will generate the initial configuration for the project, and runs some checks. For a complete reference of 
options, check the [command refence](commands.md)

At this point, it's already possible to run code locally in the created environment with

```
r3s run "echo Hello world!"
```

## Projects and remotes

In Resolos, there is a following hierarchy between projects and remotes:

- Resolos stores its configuration in the home folder of the user account. Therefore, multiple resolos installations on the same user account are not recommended!
- a Resolos configuration can have multiple remotes defined
- arbitrary number of projects can be initalized in file system folders, but nested projects are not allowed
- each project can be synced to any of the remotes defined for the user

When you create a new project with a remote already defined, the following steps happen:

- the local conda environment is created if needed and is stored in the configuration
- the remote conda environment is created if needed and is stored in the configuration
- the remote location for the project files is created and is stored in the configuration

## Syncing your project files

Resolos provides a two-way sync between your remote and your local machine using the command

```
r3s sync -r <remote_id>
```

You may omit the remote_id if there is only one remote defined. In case you want to sync the conda environment
from your local machine onto the remove env, you can use the `--env` flag as described in [Working with projects](work_with_projects.md).