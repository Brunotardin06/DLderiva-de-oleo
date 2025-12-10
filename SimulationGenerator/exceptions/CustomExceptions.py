class DownloadEnvironmentDataError(Exception):
    pass

class DownloadWindError(DownloadEnvironmentDataError):
    pass

class DownloadCurrentError(DownloadEnvironmentDataError):
    pass



class ConfigFileNotFound(Exception):
    pass


class CredentialsConfigFileNotFound(ConfigFileNotFound):
    pass

class EnvironmentConfigFileNotFound(ConfigFileNotFound):
    pass

class GifConfigFileNotFound(ConfigFileNotFound):
    pass

class MainConfigFileNotFound(ConfigFileNotFound):
    pass

class ReferenceSimulationConfigFileNotFound(ConfigFileNotFound):
    pass

class TimestepOverOutputTimestep(Exception):
    pass

class CopernicusDateRangeError(Exception):
    pass