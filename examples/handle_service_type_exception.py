#!/usr/bin/env python3

""" contrived example checking for invalid services """

from pathlib import Path
import sys


script_path = Path(__file__)
sys.path.append(script_path.parent.parent.as_posix())

# pylint: disable=import-error,wrong-import-position
from aussiebb import AussieBB  # noqa E402
import aussiebb.exceptions  # noqa E402


client = AussieBB("12345", "12345")

services = [
    {"type": "VOIP", "service_id": 223457},
    {"type": "broken", "service_id": 12345},
    {"type": "NBN", "service_id": 22345},
]

print(dir(client))

for service in services:
    try:
        client.validate_service_type(service)
        print(f"Ok service_id={service['service_id']} - service_type={service['type']}")
    except aussiebb.exceptions.UnrecognisedServiceType:
        pass
