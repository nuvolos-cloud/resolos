# Quickstart

As explained later in the [archival](archive.md) section, resolos is capable of archiving your project files together
with the execution environment, so that is can be reproduced elsewhere. This makes it possible to easily
transport projects between different machines.

After installing resolos and its dependencies, below are a few examples to get you started.

## Working with data

```
mkdir data_with_pandas
cd data_with_pandas
r3s init -s https://resolos.s3.eu-central-1.amazonaws.com/examples/v0.3.0/data_with_pandas.tar.gz
```

This example contains a small script, an input data and an environment with pandas already installed.
Check `README.md` in the project folder for further instructions.


## Running parallelized code

```
mkdir hpc_python
cd hpc_python
r3s init -s https://resolos.s3.eu-central-1.amazonaws.com/examples/v0.3.0/hpc_python.tar.gz
```

This example contains a small script that can leverage multiple CPUs.
Check `README.md` in the project folder for further instructions.
