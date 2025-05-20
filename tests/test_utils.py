"""test utils"""

import json
import os
from pathlib import Path


import pytest

# from aussiebb import AussieBB
from aussiebb.types import AussieBBConfigFile

CONFIG_FILES = [os.path.expanduser("~/.config/aussiebb.json"), "aussiebb.json"]


def configloader() -> AussieBBConfigFile:
    """loads config"""
    for filename in CONFIG_FILES:
        filepath = Path(filename).resolve()
        if filepath.exists():
            try:
                with Path(filename).open(encoding="utf-8") as file_handle:
                    filedata = json.load(file_handle)
                configfile = AussieBBConfigFile.model_validate(filedata)
                if len(configfile.users) == 0:
                    pytest.exit("You need some users in config.json")
                return configfile
            except json.JSONDecodeError as json_error:
                pytest.exit(reason=f"Failed to parse config file: {json_error}")
    print(f"No config file found... tried looking in {','.join(CONFIG_FILES)}")
    return AussieBBConfigFile.model_validate({})
