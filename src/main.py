import argparse
import logging

from builder import ModpackBuilder, ModpackBuilderOptions

# Helper function used to define all supported CLI flags and --help docs
def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-m', '--modpack',
        action='store',
        dest='modpackFilePath',
        required=True,
        help='The path to the mod pack configuration JSON file.')

    # TODO: We can use the latest version when this flag is not specified
    parser.add_argument('-b', '--build-version',
        action='store',
        dest='buildVersion',
        required=True,
        help='The target modding API version.')

    # TODO: We can use a flag to specify if we want to build to a directory or .zip file
    # TODO: We can use a flag to specify how to handle unavailable resources (crashing the build or skiping a given resource) 

    parser.add_argument('-v', '--verbose',
        action='store_true',
        dest='verboseMode',
        required=False,
        help='Log more details about the modpack building process.')

    parser.add_argument('-s', '--skip-checksum',
        action='store_true',
        dest='skipChecksum',
        required=False,
        help='Skip the process of checking the mod file hash.')

    return parser

# Helper function used to configure the behavior of the logging system
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
    
    try:
        # TODO: Currently the builder is case-sensitive (Json props), this is the price of choosing Python...
        builderOptions = ModpackBuilderOptions(skipChecksum=args.skipChecksum)
        builder = ModpackBuilder(args.modpackFilePath, builderOptions)
        builder.build()
        
        exit(0)
    except Exception as ex:
        if hasattr(ex, 'message'):
            logging.error(ex.message)
        else:
            logging.error(ex)
        
        exit(1)
