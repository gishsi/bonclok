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
from file import copy_file, copy_file_tree, remove_file_tree, create_directory

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
    def __init__(self, skipChecksum: bool, forceBuild: bool, packToZip: bool, buildTarget: str):
        self.skipChecksum = skipChecksum
        self.forceBuild = forceBuild
        self.packToZip = packToZip
        self.buildTarget = buildTarget

# Helper function used to extract the mod name from the url or alternatively combine it from other known mod properties
def parse_remote_resource_file_name(name: str, version: str, resourceUrl: str) -> str:
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
        
        formatedBuildTarget = options.buildTarget.strip().lower()
        if (formatedBuildTarget == 'client'):
            self.logger.log_verbose('Selected build target is: client.')
            self.buildTarget = ModpackTarget.CLIENT
        elif (formatedBuildTarget == 'server'):
            self.logger.log_verbose('Selected build target is: server.')
            self.buildTarget = ModpackTarget.SERVER
        else:
            self.logger.log_verbose("Invalid build target specified: {}.".format(options.buildTarget))
            raise ModpackBuilderException("Invalid build target specified.")

        with open(modpackFilePath, "r") as modpackFile:
            self.logger.log_verbose("Modpack config file opened.")
            self.modpackFilePath = modpackFilePath

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
        self.logger.log_success("Modpack: {} ({}) build process started.".format(self.modpackData.name.strip(), self.buildTarget))

        buildDirectory = "{}-{}-{}-build".format(self.modpackData.name, self.modpackData.version, self.buildTarget)
        if os.path.isdir(buildDirectory):
            if self.options.forceBuild:
                self.logger.log_verbose("Force build flag is enabled, removing the existing build.")
                
                self.logger.log_verbose("Removing the build directory tree.")
                if not remove_file_tree(buildDirectory):
                    self.logger.log_verbose("Failed to remove the build directory: {}.".format(buildDirectory))
                    raise ModpackBuilderException("Failed to remove the build directory.")
                else:
                    self.logger.log_verbose("Build directory tree removed successful.")

            else:
                self.logger.log_verbose("The build directory: {} already exists. The previous build may be corrupted.".format(buildDirectory))
                raise ModpackBuilderException("The build directory already exists. The previous build may be corrupted.")

        self.logger.log_verbose("Creating build directory.")
        if not create_directory(buildDirectory):
            self.logger.log_verbose("Failed to create build directory: {}.".format(buildDirectory))
            raise ModpackBuilderException("Failed to create build directory.")
        else:
            self.logger.log_verbose("Build directory created.")

        apiLoggingPrefix = "({})".format(self.modpackData.api.name.strip())

        self.logger.log_verbose("{} Starting to download the remote modding api resource.".format(apiLoggingPrefix))
        resourceResult = requests.get(self.modpackData.api.resourceUrl, headers=HTTP_HEADERS)
        if resourceResult.status_code != 200:
            if self.options.forceBuild:
                self.logger.log_verbose("{} Force build flag is enabled, skipping operations on the modding api.".format(apiLoggingPrefix))
            else:
                self.logger.log_verbose("{} The request returned a: {} status code.".format(apiLoggingPrefix, resourceResult.status_code))
                raise ModpackBuilderException("The requested resource returned a non-2** status code.")
                
        self.logger.log_verbose("{} Remote modding api resource downloaded successful.".format(apiLoggingPrefix))
            
        if self.options.skipChecksum:
            self.logger.log_verbose("{} Checksum verification skipped due to the builder options.".format(apiLoggingPrefix))
        else:
            self.logger.log_verbose("{} Starting checksum verification.".format(apiLoggingPrefix))

            calculatedChecksum = calculate_resource_checksum(resourceResult.content)
            if calculatedChecksum != self.modpackData.api.checksum:
                self.logger.log_verbose("{} The expected and calculated checksums are not matching.".format(apiLoggingPrefix))
                raise ModpackBuilderException("The expected and calculated checksums are not matching.")
            else:
                self.logger.log_verbose("{} Checksums are matching. Verification succeed.".format(apiLoggingPrefix))

        self.logger.log_verbose("{} Preparing modding api resource file name and path.".format(apiLoggingPrefix))
        apiFileName = parse_remote_resource_file_name(self.modpackData.api.name, self.modpackData.version, self.modpackData.api.resourceUrl)
        apiFilePath = os.path.join(buildDirectory, apiFileName)
            
        self.logger.log_verbose("{} Preparing modding api resource file.".format(apiLoggingPrefix))
        with open(apiFilePath, 'wb') as apiFile:
            self.logger.log_verbose("{} Writing downloaded modding api resource content to file.".format(apiLoggingPrefix))
            apiFile.write(resourceResult.content)

        self.logger.log_success("Modding api resource: {} downloaded successful.".format(self.modpackData.api.name.strip()))

        self.logger.log_verbose("Creating mods directory.")
        modsDirectory = os.path.join(buildDirectory, "mods")
        if not create_directory(modsDirectory):
            self.logger.log_verbose("Failed to create mods directory: {}.".format(modsDirectory))
            raise ModpackBuilderException("Failed to create mods directory.")
        else:
            self.logger.log_verbose("Mods directory created.")

        for mod in self.modpackData.mods:
            modLoggingPrefix = "({})".format(mod.name.strip())

            if self.buildTarget == ModpackTarget.CLIENT and not mod.includeClient:
                self.logger.log_verbose("{} Skipping the mod. Current build target is CLIENT and the mod has been flagged for exclusion from the CLIENT.".format(modLoggingPrefix))
                continue

            if self.buildTarget == ModpackTarget.SERVER and not mod.includeServer:
                self.logger.log_verbose("{} Skipping the mod. Current build target is SERVER and the mod has been flagged for exclusion from the SERVER.".format(modLoggingPrefix))
                continue

            self.logger.log_verbose("{} Starting to download the remote mod resource.".format(modLoggingPrefix))
            resourceResult = requests.get(mod.resourceUrl, headers=HTTP_HEADERS)
            if resourceResult.status_code != 200:
                if self.options.forceBuild:
                    self.logger.log_verbose("Force build flag is enabled, skipping operations on the current mod.")
                    continue;
                else:
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
            modFileName = parse_remote_resource_file_name(mod.name, self.modpackData.version, mod.resourceUrl)
            modFilePath = os.path.join(modsDirectory, modFileName)
            
            self.logger.log_verbose("{} Preparing mod resource file.".format(modLoggingPrefix))
            with open(modFilePath, 'wb') as modFile:
                self.logger.log_verbose("{} Writing downloaded mod resource content to file.".format(modLoggingPrefix))
                modFile.write(resourceResult.content)

            self.logger.log_success("Mod resource: {} downloaded successful.".format(mod.name.strip()))

            self.logger.log_verbose("{} Starting to copy mod resource config files.".format(modLoggingPrefix))
            for configFile in mod.configFiles:
                self.logger.log_verbose("{} Preparing source config file: {}.".format(modLoggingPrefix, configFile.sourcePath))
                modpackConfigPath = str(Path(self.modpackFilePath).parent)          
                fullSourcePath = Path(os.path.join(modpackConfigPath, configFile.sourcePath))
                if not fullSourcePath.exists() and not fullSourcePath.is_file():
                    if self.options.forceBuild:
                        self.logger.log_verbose("{} The mod config source path does not exists bu the force flag is set. Skipping the config file.")
                    else:
                        raise ModpackBuilderException("The mod config file path does not exist.")

                self.logger.log_verbose("{} Preparing destination config file: {}.".format(modLoggingPrefix, configFile.destinationPath))
                destinationPath = Path(configFile.destinationPath)
                fullDestinationPath = Path(os.path.join(buildDirectory, str(destinationPath.parent)))
                fullDestinationPath.mkdir(parents=True, exist_ok=True)
                fullDestinationFilePath = os.path.join(fullDestinationPath, destinationPath.name)

                self.logger.log_verbose("{} Starting to copy the config file.".format(modLoggingPrefix))
                if not copy_file(fullSourcePath, fullDestinationFilePath):
                    self.logger.log_verbose("{} Failed to copy config file from: {} to: {}.".format(modLoggingPrefix, fullSourcePath, fullDestinationFilePath))
                    raise ModpackBuilderException("Failed to copy config file.")
                else:
                    self.logger.log_verbose("{} Config file copied successfully.".format(modLoggingPrefix))
                
        self.logger.log_success("Modpack: {} ({}) build process finished.".format(self.modpackData.name.strip(), self.buildTarget))

        if self.options.packToZip:
            self.logger.log_verbose("Starting to packing build directory to zip archive.")
            archiveName = "{}.zip".format(buildDirectory)
            put_directory_into_archive(buildDirectory, archiveName)
            self.logger.log_verbose("Packing build directory to zip archive succeed.")

    # Start the interpretation process of the parsed mod pack instruction file
    def install(self, useDevInstructions: bool) -> None:
        self.logger.log_success("Modpack: {} ({}) installation process started.".format(self.modpackData.name.strip(), self.buildTarget))
        
        instructions = None
        if useDevInstructions:
            self.logger.log_verbose("Using the development installation rules.")
            instructions = self.modpackData.devInstallation
        else:
            self.logger.log_verbose("Using the default installation rules.")
            instructions = self.modpackData.installation
        
        if instructions == None:
            raise ModpackBuilderException("The installation rules are not specified.")

        for instruction in instructions:
            sourcePath = Path(instruction.sourcePath)
            if not sourcePath.exists():
                raise ModpackBuilderException("The installation source file/directory path does not exist.")
                        
            # TODO: We can use various strategies for cp.
            #
            # 1. Copy the files only if the dir structure exists
            # 2. Create the directory tree and cp files
            # 3. Create the directory tree and remove old files and paste the new ones
            
            destinationPath = Path(instruction.destinationPath)
            if sourcePath.is_file():
                self.logger.log_verbose("Starting the installation of the file source: {}.".format(instruction.sourcePath))
                if not copy_file(sourcePath, destinationPath):
                    self.logger.log_verbose("Installation of the file source: {} failed.".format(instruction.sourcePath))
                    raise ModpackBuilderException("Installation of the file source failed.")
                else:
                   self.logger.log_verbose("Installation of the file source: {} succeeded.".format(instruction.sourcePath)) 
            elif sourcePath.is_dir():
                self.logger.log_verbose("Starting the installation of the directory tree source: {}.".format(instruction.sourcePath))
                if not copy_file_tree(sourcePath, destinationPath):    
                    self.logger.log_verbose("Installation of the directory tree source: {} failed.".format(instruction.sourcePath))
                    raise ModpackBuilderException("Installation of the directory tree source failed")
                else:
                    self.logger.log_verbose("Installation of the directory tree source: {} succeeded.".format(instruction.sourcePath))
            else:
                raise ModpackBuilderException("Can not determine the source type.")

        self.logger.log_success("Modpack: {} ({}) installation process finished.".format(self.modpackData.name.strip(), self.buildTarget))

__all__ = [ 'ModpackBuilderException', 'ModpackBuilderOptions', 'ModpackBuilder', 'InitializeNewModpack' ]