from enum import Enum
from pydantic import BaseModel

# Class that is representing the the source and desinations paths of a mod configuration file
class ConfigFile(BaseModel):
    sourcePath: str
    destinationPath: str

# Class that is representing the properties and build instructions for a single mod
class Mod(BaseModel):
    name: str
    checksum: str
    resourceUrl: str
    sourceUrl: str
    configFiles: list[ConfigFile]

# Enum class that is representing the modpack build target (client or server)
class ModPackTarget(str, Enum):
    CLIENT = 'client'
    SERVER = 'server'

# Class that is representing a collection of mods for a specific modding-API/game version
class ModPackVersion(BaseModel):
    mods: list[Mod]

# Class that is representig the properties of the mod pack and is containing a list of mods for all specified modpack versions
class ModPack(BaseModel):
    name: str
    buildName: str
    buildTarget: ModPackTarget
    buildVersions: dict[str, ModPackVersion]

    class Config:
        use_enum_values = True

__all__ = [ 'ConfigFile', 'Mod', 'ModPackTarget', 'ModPackVersion', 'ModPack' ] 