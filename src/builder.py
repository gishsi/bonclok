from collections import OrderedDict
import hashlib
import json
import logging
import os
from urllib.parse import urlparse
import requests
from pathlib import Path

from models import ModPack, ModpackTarget

HTTP_HEADERS: OrderedDict = OrderedDict({
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
})

# Exception base class implementation used to raise builder related exceptions
class ModpackBuilderException(Exception):
    def __init__(self, message: str = "Unexpected modpack builder failure."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

# Class used to store builder options
class ModpackBuilderOptions():
    def __init__(self, buildVersion: str, skipChecksum: bool):
        self.buildVersion = buildVersion
        self.skipChecksum = skipChecksum

# Helper function used to extract the mod name from the url or alternatively combine it from other known mod properties
def parse_mod_file_name(name: str, version:str, resourceUrl: str) -> str:
    urlPath = Path(urlparse(resourceUrl).path)
    fileNamePart = urlPath.name

    if fileNamePart.lower().endswith('.jar'):
        return fileNamePart

    escapedVersion = version.lower().replace('.', '-')
    return "%s-%s.jar".format(name.lower(), escapedVersion)

# Helper function used to calculate the SHA-256 checksum from the remote resource and return the haxadecimal representation of the hash
def calculate_resource_checksum(resource: bytes) -> str:
    sha256 = hashlib.sha256(resource)
    return sha256.hexdigest()

# Class used to parse and perform all the modpack build instructions required to obtain a read-to-use pack of mods
class ModpackBuilder:
    def __init__(self, modpackFilePath: str, options: ModpackBuilderOptions):
        if modpackFilePath == None or len(modpackFilePath) == 0:
            logging.debug("Invalid modpack file path provided.")
            raise ModpackBuilderException("Invalid modpack file path provided.")

        if options == None:
            logging.debug("Invalid modpack builder options provided.")
            raise ModpackBuilderException("Invalid modpack builder options provided.")
        
        self.options = options

        with open(modpackFilePath, "r") as modpackFile:
            modpackFileContent = modpackFile.read()
            if len(modpackFileContent) == 0:
                logging.debug("The modpack file can not be accessed or is corrupted.")
                raise ModpackBuilderException("The modpack file can not be accessed or is corrupted.")

            modpackContentDictionary = json.loads(modpackFileContent)
            self.modpackData = ModPack(**modpackContentDictionary)
        
        logging.info("Parsing of the modpack file succeeded.")
        
    # Start the interpretation process of the parsed mod pack instruction file    
    def build(self) -> None:
        if not self.options.buildVersion in self.modpackData.buildVersions:
            logging.debug("The provided build version is not described in the parsed modpack file.")
            raise ModpackBuilderException("The provided build version is not described in the parsed modpack file.")
        
        buildDirectory = "%s-%s-build".format(self.modpackData.buildName, self.options.buildVersion)
        if os.path.isdir(buildDirectory):
            logging.debug("The build directory already exists. The previous build may be corrupted.")
            raise ModpackBuilderException("The build directory already exists. The previous build may be corrupted.")

        logging.debug("Build directory created.")
        os.mkdir(buildDirectory)

        buildVersion = self.modpackData.buildVersions[self.options.buildVersion]
        for mod in buildVersion.mods:
            if self.modpackData.buildTarget == ModpackTarget.CLIENT and not mod.includeClient:
                logging.debug("Mod skipped due to the modpack specification.")
                continue

            if self.modpackData.buildTarget == ModpackTarget.SERVER and not mod.includeServer:
                logging.debug("Mod skipped due to the modpack specification.")
                continue

            logging.info("Preparing resource: %s".format(mod.name))

            logging.info("Starting to download remote resource.")
            resourceResult = requests.get(mod.resourceUrl, headers=HTTP_HEADERS)
            if resourceResult.status_code != 200:
                logging.debug("The requested resource returned a non-2** status code.")
                raise ModpackBuilderException("The requested resource returned a non-2** status code.")

            logging.info("Remote resource downloaded successful.")

            if not self.options.skipChecksum:
                calculatedChecksum = calculate_resource_checksum(resourceResult.content)
                if calculatedChecksum != mod.checksum:
                    logging.debug("The expected and calculated checksums are not matching.")
                    raise ModpackBuilderException("The expected and calculated checksums are not matching.")

            modFileName = parse_mod_file_name(mod.name, self.options.buildVersion, mod.resourceUrl)
            modFilePath = os.path.join(buildDirectory, modFileName)
            
            logging.info("Creating local mod file.")
            with open(modFilePath, 'wb') as modFile:
                modFile.write(resourceResult.content)

            logging.info("Local mod file created successful.")

        
        # TODO: Implement .zip support 
        logging.info("Modpack build process finished.")

__all__ = [ 'ModpackBuilderException', 'ModpackBuilderOptions', 'ModpackBuilder', 'InitializeNewModpack' ]