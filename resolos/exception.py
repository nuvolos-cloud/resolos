class ResolosException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.msg}"


class MissingDependency(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class DependencyVersionError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class ShellError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class SSHError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class LocalCommandError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class RemoteCommandError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class RemoteSpecificationError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class NoRemotesError(RemoteSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class RemoteMissingError(RemoteSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class RemoteAlreadyExistsError(RemoteSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class RemoteUnspecifiedError(RemoteSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class EnvSpecificationError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class EnvCommandError(EnvSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class EnvMissingError(EnvSpecificationError):
    def __init__(self, msg):
        super().__init__(msg)


class ResolosPathException(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class NotAProjectFolderError(ResolosPathException):
    def __init__(self, msg):
        super().__init__(msg)


class LocalConfigAlreadyExistsError(ResolosPathException):
    def __init__(self, msg):
        super().__init__(msg)


class MissingProjectRemoteConfig(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class MissingRemoteEnv(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class MissingRemoteLocation(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class NotAResolosArchiveError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)


class YaretaError(ResolosException):
    def __init__(self, msg):
        super().__init__(msg)
