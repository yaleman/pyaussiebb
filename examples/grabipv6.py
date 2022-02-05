#!/usr/bin/env python

""" pulls and lists the IPv6 addresess for your services """

from ipaddress import ip_network,  IPv4Network, IPv6Network
from pathlib import Path
import sys

filepath = Path(__file__)
sys.path.append(filepath.parent.parent.as_posix())


# pylint: disable=import-error,wrong-import-position
from aussiebb.asyncio import AussieBB
from config import USERNAME, PASSWORD

def main():
    """ Example of getting ipv6 services """
    client = AussieBB(USERNAME, PASSWORD)

    client.logger.debug("Logging in")
    client.login()


    services = client.get_services()
    found_networks = []
    if services is None:
        return
    for service in services:
        client.logger.debug(service)
        if 'ipAddresses' not in service:
            continue
        client.logger.info(f"Found a service: {service.get('description')}")
        for address in service["ipAddresses"]:
            client.logger.debug(f"address: {address}")
            try:
                parsed = ip_network(address)
            except Exception as error_message: # pylint: disable=broad-except
                client.logger.error(f"Not sure what this was, but it's not an address! {address} - {error_message}")
                continue

            if isinstance(parsed, IPv4Network):
                client.logger.debug("Found IPv4, nobody cares about this old stuff!")
            elif isinstance(parsed, IPv6Network):
                client.logger.debug(f"Found IPv6, woo! {parsed}")
                found_networks.append(parsed)
    client.logger.info("Found the following IPv6 networks:")
    for network in found_networks:
        client.logger.info(f" - {network}")

if __name__ == '__main__':
    main()
