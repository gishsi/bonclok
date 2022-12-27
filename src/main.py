import argparse

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

if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("Hello world!")
    exit(0)