from enum import Enum
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

# Enum class that is representing the modpack build target (client or server)
class ModpackTarget(str, Enum):
    CLIENT = 'client'
    SERVER = 'server'

# Class that is representing a collection of mods for a specific modding-API/game version
class ModpackVersion(BaseModel):
    mods: list[Mod]

# Class that is representig the properties of the mod pack and contains a list of mods for all specified modpack versions
class Modpack(BaseModel):
    name: str
    buildTarget: ModpackTarget
    buildVersions: dict[str, ModpackVersion]

    class Config:
        use_enum_values = True

__all__ = [ 'ConfigFile', 'Mod', 'ModpackTarget', 'ModpackVersion', 'Modpack' ] 