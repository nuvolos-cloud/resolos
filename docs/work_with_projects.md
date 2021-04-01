# Working with projects

## Installing/uninstalling conda packages

You can use the commands

```
r3s install <packages>
```

and 

```
r3s uninstall <packages>
```

To install/uninstall conda packages in you resolos project's linked conda environment. You need to be inside
a resolos project to be able to call the above commands.

If there is only one remote defined, the above command will also try to install/uninstall the packes on the remote.
In case you have more than one remote defined, you can specify the remote with the `--remote <remote_id>` option or
use the `--all-remotes` flag to install to all remotes in sequence.
Please check the [command reference](commands.md) for detailed usage.


## Syncing environments

In an ideal setup, you perform the following steps in order:

1. Configure remote(s)
2. Create new project(s)
3. Install/uninstall packages with `res install ...`

If you have initialized your resolos project with an external conda environment, or if you have installed 
packages externally into your resolos conda environment, you'll need to do a full sync of the environments with the
command

```
r3s sync -r <remote_id> --env
```

Note that the above command will perform a two-way sync for the project files but a one way sync for the environments
(packages installed on the local env will get installed on the remote environment as well).

## Running remote jobs

If your remote has a Slurm job scheduler, you can manage Slurm jobs directly with rsesolos. In all the examples below,
remote_id can be omitted in case there is only one remote defined.

### Running jobs

You can run simple jobs with `r3s job run`:

```
r3s job -r <remote_id> run "python my_script.py"
```

If you want to fine-tune the submission details, you may create a Slurm submission script first, and use

```
r3s job -r <remote_id> submit my_submission_script.sbatch
```

### Listing jobs

Use the `r3s job list` command to list your jobs running on the remote.

```
r3s job -r <remote_id> list
```

### Getting job details

The `r3s job status` command will get you more details about your job.

```
r3s job -r <remote_id> status <job_id>
```

### Cancelling a job

You can use the `r3s job cancel` command to cancel a job:

```
r3s job -r <remote_id> cancel <job_id>
```