# Archival

Resolos is capable of archiving projects and loading them on other machines. The archive contains all the data
present in the project folder in a compressed format, plus information on the conda environment needed for 
reproducing it somewhere else.

> Migrating environments between different machines is a difficult task, and the more customization a conda 
> environment has, the harder it is to replicate it on a different machine. For example, if your code relies on a 
> propriatery software that is only available for Windows, then there is no way to exactly replicate that environment on Linux
> or macOS. The rule of thumb is that as long as you install all of your dependencies via conda (and pip), you'll have a good
> change of replicability on different OSes. 
>

## Creating an archive

You can create a new archive with the `r3s archive create` command:

```
r3s archive create ../my_archive_name.tar.gz
```

The archive should not be created inside the project itself, and it can take a couple of minutes until the environment
is scanned and exported. Once finished, you can publish the archive file and then other users will be able to load your 
environment with resolos easily.

## Loading an archive

You can initialize new projects from an archive file directly:

```
r3s init -s ../my_archive_name.tar.gz
```

Resolos also supports downloading archives from publicly accessible HTTPS or SFTP locations:

```
r3s archive create https://my-storage-service.org/my_archive_name.tar.gz
```

Finally, you can also load an archive to an existing project. Note that this'll overwrite the contents of
the project folder and the conda environment!

```
r3s archive load https://my-storage-service.org/my_archive_name.tar.gz
```