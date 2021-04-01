# Resolos

This is the documentation of the [resolos](https://github.com/nuvolos-cloud/resolos) python package.

Resolos is a toolkit for maintaining reproducible environments for scientific computations.
The main resolos object is a project, which is nothing else than a folder on the filesystem associated
with a conda environment. The project folder contains the source code, while the conda environment is 
used as an execution environment. With the two combined, resolos is capable of the following:

- archive resolos projects into a single compressed file
- load resolos archive files on different operating systems. Resolos will replicate the original environment
as accurately as possible
- sync project files and environments between a local development machine and a remote HPC cluster
- submit and monitor jobs on remote HPC clusters

The following section details the installation of resolos and its dependencies.

