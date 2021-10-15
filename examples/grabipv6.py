#!/usr/bin/env python3

""" pulls and lists the IPv6 addresess for your services """

from ipaddress import ip_network,  IPv4Network, IPv6Network

from aussiebb import AussieBB
from loguru import logger


from config import USERNAME, PASSWORD

client = AussieBB(USERNAME, PASSWORD)

logger.debug("Logging in")
client.login()


services = client.get_services()
found_networks = []
for service in services:
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

            if isinstance(parsed, IPv4Network):
                logger.debug("Found IPv4, nobody cares about this old stuff!")
            elif isinstance(parsed, IPv6Network):
                logger.debug("Found IPv6, woo! {}", parsed)
                found_networks.append(parsed)
logger.info("Found the following IPv6 networks:")
for network in found_networks:
    logger.info(" - {}", network)
