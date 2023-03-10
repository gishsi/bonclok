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

    parser.add_argument('-f', '--force',
        action='store_true',
        dest='force',
        required=False,
        help='Force the modpack build despite existing builds and download failure.')

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

    # TODO: We can set the "required" property to false and build both client and server when not specified
    parser.add_argument('-t', '--build-target',
        action='store',
        dest='buildTarget',
        required=True,
        help='Specify the build target: CLIENT/SERVER.')

    parser.add_argument('-i', '--install',
        action='store_true',
        dest='install',
        required=False,
        help='Run the default installation process after the build.')

    parser.add_argument('-d', '--dev-install',
        action='store_true',
        dest='devInstall',
        required=False,
        help='Run the development installation process after the build.')

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
            skipChecksum=args.skipChecksum,
            forceBuild=args.force,
            packToZip=args.packToZip,
            buildTarget=args.buildTarget)

        builder = ModpackBuilder(args.modpackFilePath, builderOptions, logger)
        builder.build()
    
        if args.install:
            builder.install(True)
            exit(0)

        if args.devInstall:
            builder.install(False)
            exit(0)

        exit(0)
    except ModpackBuilderException as ex:
        logger.log_error(ex)
        exit(1)
    except Exception as ex:
        logger.log_error(ex)
        exit(1)