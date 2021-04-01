# Remotes

In resolos, a remote is a remote execution environment - usually an HPC cluster - for your project, usually
equipped with more abundant resources than your local development environment.

Currently resolos supports remotes accepting SSH connections and using Slurm as the job scheduler.

Remotes are identified by a `remote_id`, and they contain information about the following details:

- username on the cluster
- hostname of the login node
- port to use for the SSH connection
- command to activate conda on the login node
- ...

## Passwordless SSH access

You'll see that Resolos issues multiple SSH commands for operations like sync, job submission, etc. While it's possible
to enter your password all the time when prompted, a more convenient way is to set up SSH key based access on the remote.
You can use the command

```
r3s setup-ssh -r <remote_id>
```

to perform the SSH key generation and remote configuration automatically 

> Resolos assumes a standard SSH configuration on both
your local machine and the remote. If you have a nonstandard setting, please configure the SSH client accordingly.

## Defining a new remote

If your remote follows the standard HPC setup, the following minimal example will probably work for you to define a 
new remote:

```
r3s remote add my_remote_id -u my_username -h login.host.name
```

For the list of settings, please check the [command reference](commands.md).

When adding a new remote, Resolos will run a number of checks to make sure all dependencies are installed on the remote
as well.

## Updating a remote

You can update an existing remote definition with the command

```
r3s remote update <remote_id> <settings>
```

The same settings can be configured as at definition time. Before committing the changes, resolos will run again
the tests for the remote definition.

## Deleting a remote

You can delete an existing remote definition with the command

```
r3s remote remove <remote_id>
```

This will only remove the local configuration, no data is removed on the remote itself.