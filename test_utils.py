""" test utils """

import json
import os
from pathlib import Path

import pytest

# from aussiebb import AussieBB
from aussiebb.types import AussieBBConfigFile

def configloader() -> AussieBBConfigFile:
    """ loads config """
    for filename in [ os.path.expanduser("~/.config/aussiebb.json"), "aussiebb.json" ]:
        filepath = Path(filename).resolve()
        if filepath.exists():
            try:
                configfile = AussieBBConfigFile.parse_file(filepath)
                return configfile
            except json.JSONDecodeError as json_error:
                pytest.exit(f"Failed to parse config file: {json_error}")
    return AussieBBConfigFile()

    # TODO: add a validator that checks that either a user or a list of them is supplied
