#!/usr/bin/env python3

""" updates terraform.tfvars based on the current ipv6 subnet assigned to your network

    looks for a variable called "base_ipv6_network" and updates it.
"""


from ipaddress import ip_network, IPv6Network
import os
from pathlib import Path
import re
import sys
from typing import Optional

filepath = Path(__file__)
sys.path.append(filepath.parent.parent.as_posix())

# pylint: disable=import-error,wrong-import-position
from aussiebb import AussieBB  # noqa E402

TF_FILE = "terraform.tfvars"


# pylint: disable=too-many-branches
def get_network(api: AussieBB) -> Optional[IPv6Network]:
    """grabs an ipv6 network object"""

    api.logger.debug("Logging in")
    if not api.login():
        api.logger.error("Failed to log in")
        sys.exit(1)

    services = api.get_services(servicetypes=["NBN"])
    found_network = None

    if services is None:
        return None
    for service in services:
        if service.get("type") != "NBN":
            continue
        api.logger.debug(service)
        if "ipAddresses" in service:
            api.logger.info("Found a service: {}", service.get("description"))
            if "ipAddresses" not in service:
                continue
            for address in service["ipAddresses"]:
                api.logger.debug("address: {}", address)
                try:
                    parsed = ip_network(address)
                except Exception as error_message:  # pylint: disable=broad-except
                    api.logger.error(
                        "Not sure what this was, but it's not an address! {} - {}",
                        address,
                        error_message,
                    )
                    continue
                if isinstance(parsed, IPv6Network):
                    if found_network is None:
                        found_network = parsed
                    if found_network.prefixlen > parsed.prefixlen:
                        api.logger.debug(
                            "Found bigger network, making it current: {}", parsed
                        )
                        found_network = parsed
                    else:
                        api.logger.debug("Smaller network found, skipping: {}", parsed)
    if not found_network:
        api.logger.error("Didn't find an ipv6 network!")

    return found_network


def check_need_to_update_file(api: AussieBB, updated_address: str) -> bool:
    """checks terraform.tfvars for the base_ipv6_network variable and sees if we need to update it"""

    with open(TF_FILE, "r", encoding="utf8") as file_handle:
        terraform_file = file_handle.readlines()
    regex = re.compile(r'base_ipv6_network\s*\=\s*\"(?P<network>[^"]+)\".*')

    for line in terraform_file:
        matches = regex.match(line)
        if matches:
            api.logger.debug("Found line: {}", line)
            found_address = matches.groupdict().get("network")
            api.logger.debug("network: {}", found_address)
            if found_address != updated_address:
                api.logger.info(
                    "Need to update line... was {}, needs to be {}",
                    found_address,
                    updated_address,
                )
                return True
            api.logger.info("No need to update file!")
            return False
    return False


def update_file(new_address: str) -> None:
    """updates the file with a new address"""
    with open(TF_FILE, encoding="utf8") as file_handle:
        file_contents = file_handle.read()
    result = re.sub(
        r'base_ipv6_network\s*\=\s*\"[^"]+\"',
        f'base_ipv6_network = "{new_address}"',
        file_contents,
        count=1,
    )
    with open(TF_FILE, "w", encoding="utf8") as file_handle:
        file_handle.write(result)
    client.logger.info("Updated file!")


client = AussieBB(os.getenv("ABB_USERNAME", ""), os.getenv("ABB_PASSWORD", ""))
network_address = get_network(client)
if not network_address:
    sys.exit(1)

ACTUAL_NEW_ADDRESS = str(network_address.network_address)

if check_need_to_update_file(client, ACTUAL_NEW_ADDRESS):
    update_file(ACTUAL_NEW_ADDRESS)
else:
    client.logger.info("Didn't need to update file!")
