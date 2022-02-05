#!/usr/bin/env python3

""" contrived example checking for invalid services """

from pathlib import Path
import sys


filepath = Path(__file__)
sys.path.append(filepath.parent.parent.as_posix())

# pylint: disable=import-error,wrong-import-position
from aussiebb import AussieBB
import aussiebb.exceptions


client = AussieBB( "12345", "12345" )

services = [
    {"type" : "VOIP", "service_id" : 223457},
    {"type" : "broken", "service_id" : 12345},
    {"type" : "NBN", "service_id" : 22345}
]

print(dir(client))

for service in services:
    try:
        client.validate_service_type(service)
        print(f"Ok {service['service_id']} - {service['type']}")
    except aussiebb.exceptions.UnrecognisedServiceType:
        pass
