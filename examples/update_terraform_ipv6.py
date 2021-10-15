#!/usr/bin/env python3

""" updates terraform.tfvars based on the current ipv6 subnet assigned to your network

    looks for a variable called "base_ipv6_network" and updates it.
"""

import os
import re
import sys
from ipaddress import ip_network, IPv6Network

from aussiebb import AussieBB
from loguru import logger

TF_FILE = "terraform.tfvars"


def get_network():
    """ grabs an ipv6 network object"""
    client = AussieBB( os.getenv('ABB_USERNAME'), os.getenv('ABB_PASSWORD'))

    logger.debug("Logging in")
    if not client.login():
        logger.error("Failed to log in")
        sys.exit(1)

    services = client.get_services(servicetypes=['NBN'])
    found_network = False

    for service in services:
        if service.get('type') != 'NBN':
            continue
        logger.debug(service)
        if 'ipAddresses' in service:
            logger.info("Found a service: {}", service.get('description'))
            for address in service.get("ipAddresses"):
                logger.debug("address: {}", address)
                try:
                    parsed = ip_network(address)
                except Exception as error_message: # pylint: disable=broad-except
                    logger.error("Not sure what this was, but it's not an address! {} - {}", address, error_message)
                    continue
                if isinstance(parsed, IPv6Network):
                    if not found_network:
                        found_network = parsed
                    elif found_network.prefixlen > parsed.prefixlen:
                        logger.debug("Found bigger network, making it current: {}", parsed)
                        found_network = parsed
                    else:
                        logger.debug("Smaller network found, skipping: {}", parsed)
    if not found_network:
        logger.error("Didn't find an ipv6 network!")

    return found_network



def check_need_to_update_file(updated_address: str) -> bool:
    """ checks terraform.tfvars for the base_ipv6_network variable and sees if we need to update it"""

    with open(TF_FILE, 'r') as file_handle:
        terraform_file = file_handle.readlines()
    regex = re.compile(r'base_ipv6_network\s*\=\s*\"(?P<network>[^"]+)\".*')

    for line in terraform_file:
        matches = regex.match(line)
        if matches:
            logger.debug("Found line: {}", line)
            found_address = matches.groupdict().get('network')
            logger.debug("network: {}", found_address)
            if found_address != updated_address:
                logger.info("Need to update line... was {}, needs to be {}", found_address, updated_address)
                return True
            logger.info("No need to update file!")
            return False
    return False


def update_file(new_address):
    """ updates the file with a new address """
    with open(TF_FILE, 'r') as file_handle:
        file_contents = file_handle.read()
    result = re.sub(
        r'base_ipv6_network\s*\=\s*\"[^"]+\"',
        f"base_ipv6_network = \"{new_address}\"",
        file_contents,
        count=1
        )
    with open(TF_FILE, 'w') as file_handle:
        file_handle.write(result)
    logger.info("Updated file!")


network_address = get_network()
if not network_address:
    sys.exit(1)

ACTUAL_NEW_ADDRESS = str(network_address.network_address)

if check_need_to_update_file(ACTUAL_NEW_ADDRESS):
    update_file(ACTUAL_NEW_ADDRESS)
else:
    logger.info("Didn't need to update file!")
