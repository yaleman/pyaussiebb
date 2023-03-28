""" test utils """

import json
import os
from pathlib import Path
import sys

import pytest

# from aussiebb import AussieBB
from aussiebb.types import AussieBBConfigFile
CONFIG_FILES = [ os.path.expanduser("~/.config/aussiebb.json"), "aussiebb.json" ]

def configloader() -> AussieBBConfigFile:
    """ loads config """
    for filename in CONFIG_FILES:
        filepath = Path(filename).resolve()
        if filepath.exists():
            try:
                configfile = AussieBBConfigFile.parse_file(filepath)
                if len(configfile.users) == 0:
                    pytest.exit("You need some users in config.json")
                return configfile
            except json.JSONDecodeError as json_error:
                pytest.exit(f"Failed to parse config file: {json_error}")
    print(f"No config file found... tried looking in {','.join(CONFIG_FILES)}")
    sys.exit(1)

    # TODO: add a validator that checks that either a user or a list of them is supplied
