[![PyPI version](https://img.shields.io/pypi/v/resolos)](https://pypi.org/project/resolos/) 
[![GitHub version](https://img.shields.io/github/v/release/nuvolos-cloud/resolos)](https://github.com/nuvolos-cloud/resolos)
[![Integration tests](https://github.com/nuvolos-cloud/resolos/actions/workflows/integration-test.yaml/badge.svg)](https://github.com/nuvolos-cloud/resolos/actions/workflows/integration-test.yaml)

# Introduction

Resolos is a toolkit written in Python for maintaining reproducible environments for scientific computations.
It's main goal is to enable researchers to easily replicate environments through space (running code on HPC environment)
and time (environment preservation for long term archival).

## How does it work?

The core resolos concept is a project, which is nothing else than a folder on the filesystem associated
with a conda environment. The project folder contains the source code, while the conda environment is 
used as an execution environment. With the two combined, resolos is capable of the following:

- archive resolos projects into a single compressed file
- load resolos archive files on different operating systems. Resolos will replicate the original environment
as accurately as possible
- sync project files and environments between a local development machine and a remote HPC cluster
- submit and monitor jobs on remote HPC clusters

The following section details the installation of resolos and its dependencies.

