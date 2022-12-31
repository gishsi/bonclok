from collections import OrderedDict
import hashlib
import json
import os
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile
import requests
from pathlib import Path
from logger import Logger

from models import Modpack, ModpackTarget

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
    def __init__(self, buildVersion: str, skipChecksum: bool, packToZip: bool):
        self.buildVersion = buildVersion
        self.skipChecksum = skipChecksum
        self.packToZip = packToZip

# Helper function used to extract the mod name from the url or alternatively combine it from other known mod properties
def parse_mod_file_name(name: str, version:str, resourceUrl: str) -> str:
    urlPath = Path(urlparse(resourceUrl).path)
    fileNamePart = urlPath.name

    if fileNamePart.lower().endswith('.jar'):
        return fileNamePart

    escapedVersion = version.lower().replace('.', '-')

    return "{}-{}.jar".format(name.lower(), escapedVersion)

# Helper function used to calculate the SHA-256 checksum from the remote resource and return the haxadecimal representation of the hash
def calculate_resource_checksum(resource: bytes) -> str:
    sha256 = hashlib.sha256(resource)
    return sha256.hexdigest()

# Helper function used to create a .zip archive out of a specified directory
def put_directory_into_archive(buildDirectoryPath: str, zipFileName: str) -> None:
    zipArchive = ZipFile(zipFileName, 'w', ZIP_DEFLATED) 
    for dirName, _, files in os.walk(buildDirectoryPath):
        zipArchive.write(dirName)
        for fileName in files:
            zipArchive.write(os.path.join(dirName, fileName))

    zipArchive.close()

# Class used to parse and perform all the modpack build instructions required to obtain a read-to-use pack of mods
class ModpackBuilder:
    def __init__(self, modpackFilePath: str, options: ModpackBuilderOptions, logger: Logger):
        if logger == None:
            raise ModpackBuilderException("The provided logger instance is not initialzied.")
        
        self.logger = logger

        if modpackFilePath == None or len(modpackFilePath) == 0:
            raise ModpackBuilderException("Invalid modpack file path provided.")

        if options == None:
            raise ModpackBuilderException("Invalid modpack builder options provided.")
        
        self.options = options

        with open(modpackFilePath, "r") as modpackFile:
            self.logger.log_verbose("Modpack config file opened.")

            modpackFileContent = modpackFile.read()
            if len(modpackFileContent) == 0:
                self.logger.log_verbose("The length of the modpack file content is zero.")
                raise ModpackBuilderException("The modpack file can not be accessed or is corrupted.")

            modpackContentDictionary = json.loads(modpackFileContent)
            self.logger.log_verbose("Modpack config file content JSON parsed successful.")

            self.modpackData = Modpack(**modpackContentDictionary)
            self.logger.log_verbose("Modpack config file content deserialzied successful.")
        
        self.logger.log_success("Parsing of the modpack file succeeded.")
        
    # Start the interpretation process of the parsed mod pack instruction file    
    def build(self) -> None:
        if not self.options.buildVersion in self.modpackData.buildVersions:
            self.logger.log_verbose("The provided build version: {} is not described in the parsed modpack file.".format(self.options.buildVersion))
            raise ModpackBuilderException("The provided build version is not described in the parsed modpack file.")
        
        buildDirectory = "{}-{}-build".format(self.modpackData.buildName, self.options.buildVersion)
        if os.path.isdir(buildDirectory):
            self.logger.log_verbose("The build directory: {} already exists. The previous build may be corrupted.".format(buildDirectory))
            raise ModpackBuilderException("The build directory already exists. The previous build may be corrupted.")

        self.logger.log_verbose("Creating build directory.")
        os.mkdir(buildDirectory)
        self.logger.log_verbose("Build directory created.")

        buildVersion = self.modpackData.buildVersions[self.options.buildVersion]
        for mod in buildVersion.mods:
            modLoggingPrefix = "({})".format(mod.name.strip())

            if self.modpackData.buildTarget == ModpackTarget.CLIENT and not mod.includeClient:
                self.logger.log_verbose("{} Skipping the mod. Current build target is CLIENT and the mod has been flagged for exclusion from the CLIENT.".format(modLoggingPrefix))
                continue

            if self.modpackData.buildTarget == ModpackTarget.SERVER and not mod.includeServer:
                self.logger.log_verbose("{} Skipping the mod. Current build target is SERVER and the mod has been flagged for exclusion from the SERVER.".format(modLoggingPrefix))
                continue

            self.logger.log_verbose("{} Starting to download the remote mod resource.".format(modLoggingPrefix))
            resourceResult = requests.get(mod.resourceUrl, headers=HTTP_HEADERS)
            if resourceResult.status_code != 200:
                self.logger.log_verbose("{} The request returned a: {} status code.".format(modLoggingPrefix, resourceResult.status_code))
                raise ModpackBuilderException("The requested resource returned a non-2** status code.")

            self.logger.log_verbose("{} Remote mod resource downloaded successful.".format(modLoggingPrefix))
            
            if self.options.skipChecksum:
                self.logger.log_verbose("{} Checksum verification skipped due to the builder options.".format(modLoggingPrefix))
            else:
                self.logger.log_verbose("{} Starting checksum verification.".format(modLoggingPrefix))

                calculatedChecksum = calculate_resource_checksum(resourceResult.content)
                if calculatedChecksum != mod.checksum:
                    self.logger.log_verbose("{} The expected and calculated checksums are not matching.".format(modLoggingPrefix))
                    raise ModpackBuilderException("The expected and calculated checksums are not matching.")
                else:
                    self.logger.log_verbose("{} Checksums are matching. Verification succeed.".format(modLoggingPrefix))

            self.logger.log_verbose("{} Preparing mod resource file name and path.".format(modLoggingPrefix))
            modFileName = parse_mod_file_name(mod.name, self.options.buildVersion, mod.resourceUrl)
            modFilePath = os.path.join(buildDirectory, modFileName)
            
            self.logger.log_verbose("{} Preparing mod resource file.".format(modLoggingPrefix))
            with open(modFilePath, 'wb') as modFile:
                self.logger.log_verbose("{} Writing downloaded mod resource content to file.".format(modLoggingPrefix))
                modFile.write(resourceResult.content)

            self.logger.log_success("Mod resource: {} downloaded successful.".format(mod.name.strip()))

        self.logger.log_success("Modpack: {} ({}) build process finished.".format(self.modpackData.name.strip(), self.modpackData.buildTarget))

        if self.options.packToZip:
            self.logger.log_verbose("Starting to packing build directory to zip archive.")
            archiveName = "{}.zip".format(buildDirectory)
            put_directory_into_archive(buildDirectory, archiveName)
            self.logger.log_verbose("Packing build directory to zip archive succeed.")

__all__ = [ 'ModpackBuilderException', 'ModpackBuilderOptions', 'ModpackBuilder', 'InitializeNewModpack' ]