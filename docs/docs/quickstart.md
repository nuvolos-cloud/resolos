# Quickstart

As explained in the [archival](archive.md) section, resolos is capable of archiving your project files together
with the execution environment, so that is can be reproduced elsewhere. 

After installing resolos and its dependencies, below are a few examples to get you started.

## Working with data

```
r3s init -s https://resolos.s3.eu-central-1.amazonaws.com/examples/data_with_pandas.tar.gz
```

This example contains a small script, an input data and an environment with pandas already installed.
Check `README.md` in the project folder for further instructions.


## Running parallelized code

```
r3s init -s https://resolos.s3.eu-central-1.amazonaws.com/examples/hpc_python.tar.gz
```

This example contains a small script that can leverage multiple CPUs.
Check `README.md` in the project folder for further instructions.
