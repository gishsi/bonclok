import argparse
import sys

from builder import ModpackBuilder, ModpackBuilderException, ModpackBuilderOptions
from logger import Logger, LoggerException

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

    # TODO: We can use a flag to specify how to handle unavailable resources (crashing the build or skiping a given resource) 

    parser.add_argument('-z', '--zip',
        action='store_true',
        dest="packToZip",
        required=False,
        help='Pack the build folder into a .zip archive.')

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

if __name__ == "__main__":
    logger = None

    try:
        parser = create_argument_parser()
        args = parser.parse_args()

        try:
            logger = Logger(sys.stdout, args.verboseMode)
        except LoggerException:
            exit(2)

        # TODO: Currently the builder is case-sensitive (Json props), this is the price of choosing Python...
        builderOptions = ModpackBuilderOptions(
            buildVersion=args.buildVersion,
            skipChecksum=args.skipChecksum,
            packToZip=args.packToZip)

        builder = ModpackBuilder(args.modpackFilePath, builderOptions, logger)
        builder.build()
    
        exit(0)
    except ModpackBuilderException as ex:
        logger.log_error(ex)
        exit(1)
    except Exception as ex:
        logger.log_error(ex)
        exit(1)