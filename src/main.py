import argparse
import logging

from builder import ModpackBuilder

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-m', '--modpack',
        action='store',
        dest='modpackFilePath',
        required=True,
        help='The path to the mod pack configuration JSON file.')

    parser.add_argument('-v', '--verbose',
        action='store_true',
        dest='verboseMode',
        required=False,
        help='Log more details about the modpack building process.')

    return parser

def configure_logging(verboseMode: bool) -> None:
    logLevel = logging.INFO
    if verboseMode: logLevel = logging.DEBUG
    
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(logLevel)
    handler.setFormatter(formatter)

    logging.basicConfig(level=logLevel, force=True, handlers=[ handler ])

if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()
    
    configure_logging(args.verboseMode)
    
    # TODO: Currently the builder is case-sensitive (Json props), this is the price of choosing Python...
    builder = ModpackBuilder(args.modpackFilePath)

    exit(0)