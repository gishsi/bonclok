import json
import logging

from models import ModPack

class ModpackBuilderException(Exception):
    def __init__(self, message: str = "Unexpected modpack builder failure."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class ModpackBuilder:
    def __init__(self, modpackFilePath: str):
        if modpackFilePath == None or len(modpackFilePath) == 0:
            logging.debug("Invliad modpack file path provided.")
            raise ModpackBuilderException("Invliad modpack file path provided.")

        with open(modpackFilePath, "r") as modpackFile:
            modpackFileContent = modpackFile.read()
            if len(modpackFileContent) == 0:
                logging.debug("The modpack file can not be accessed or is corrupted.")
                raise ModpackBuilderException("The modpack file can not be accessed or is corrupted.")

            modpackContentDictionary = json.loads(modpackFileContent)
            self.modpackData = ModPack(**modpackContentDictionary)
        
        logging.info("Parsing of the modpack file succeeded.")
        
    # TODO: Implement
    def build() -> None:
        return

__all__ = [ 'ModpackBuilderException', 'ModpackBuilder', 'InitializeNewModpack' ]