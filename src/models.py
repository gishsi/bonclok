from enum import Enum
from typing import Optional
from pydantic import BaseModel

# Class that is representing the source and destination paths of a mod configuration file
class ModConfigFile(BaseModel):
    sourcePath: str
    destinationPath: str

# Class that is representing the properties and build instructions for a single mod
class Mod(BaseModel):
    name: str
    checksum: str
    resourceUrl: str
    sourceUrl: str
    includeClient: bool
    includeServer: bool
    configFiles: list[ModConfigFile]

# Class that is representing the properties of the target modding API
class ModdingApi(BaseModel):
    name: str
    checksum: str
    resourceUrl: str
    sourceUrl: str

# Enum class that is representing the modpack build target (client or server)
class ModpackTarget(str, Enum):
    CLIENT = 'client'
    SERVER = 'server'

# Class that is representing the source and destination paths of a build resource to install
class InstallationResource(BaseModel):
    sourcePath: str
    destinationPath: str

# Class that is representig the properties of the mod pack and contains a list of mods for all specified modpack versions
class Modpack(BaseModel):
    name: str
    version: str
    api: ModdingApi
    mods: list[Mod]
    installation: Optional[list[InstallationResource]]
    devInstallation: Optional[list[InstallationResource]]

    class Config:
        use_enum_values = True

__all__ = [ 'ConfigFile', 'Mod', 'ModdingApi', 'ModpackTarget', 'InstallationResource', 'Modpack' ] 