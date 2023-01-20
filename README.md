# Bonclok
Bonclok (*in the Silesian dialect means a cauldron or a large pot*) is a tool that allows you to automate the process of preparing mods and their configuration files for Minecraft in order to create your dream mod pack. Attention! Remember that the priority is to comply with the rules and licenses of the mods used. If you want to put a mod in your own pack, make sure there is a record that allows it. You can only automate mod downloads from services that allow it. Downloading from your own servers is recommended.

## Installation
Requirements:
- Python 3.10+
- git

```sh
# Clone the repository
git clone https://github.com/gishsi/bonclok.git

# Go the cloned directory
cd bonclok

# Optional: Create a Python virtual environment and activate it
# Install all the dependencies
pip install -r requirements.txt

# You can now use bonclok
python src/main.py --help
```

## Usage
When using bonclok we need to specify two required parameters: path to the modpack config JSON file and information about whether we want to build the modpack for use on the client or server side. Flags and parameters:
- `-m` `--modpack` - The path to the mod pack configuration JSON file.
- `-t` `--build-target` - Specify the build target: CLIENT/SERVER.

- `-f` `--force` - Force the modpack build despite existing builds and download failure.
- `-z` `--zip` - Pack the build folder into a .zip archive.
- `-v` `--verbose` - Log more details about the modpack building process.
- `-s` `--skip-checksum` - Skip the process of checking the mod file hash.
- `-i` `--install` - Run the default installation process after the build.
- `-d` `--dev-install` - Run the development installation process after the build.

An example of the structure of the modpack JSON configuration file:
```json
{
    "name": "Our modpack name",
    "version": "1.16.5",
    "api": {
        "name": "our-modding-api-name-1.16.5-1.0.0",
        "resourceUrl": "https://modding-api.bonclok/compiled",
        "sourceUrl": "https://modding-api.bonclok/source",
        "checksum": "<SHA256 hash>"
    },
    "mods": [
        {
            "name": "Example mod",
            "includeClient": true,
            "includeServer": true,
            "resourceUrl": "https://example-mod.bonclok/compiled",
            "sourceUrl": "https://example-mod.bonclok/source",
            "configFiles": [
                {
                    "sourcePath": "all-my-configs/example-mod/config.yaml",
                    "destinationPath": "config/example-mod-config.yaml"
                }
            ],
            "checksum": "<SHA256 hash>"
        }
    ],
    "installation": [
        {
            "sourcePath": "all-my-configs/my-custom-config.yaml",
            "destinationPath": "~/configs/config.yaml"
        }
    ],
    "devInstallation": [
        {
            "sourcePath": "all-my-configs/my-custom-config.yaml",
            "destinationPath": "~/configs/config.yaml"
        }
    ]
}
```