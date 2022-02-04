#!/usr/bin/env python

""" pulls and lists the VOIP services on your account """

#pylint: disable=wrong-import-position

import asyncio
import json
from pathlib import Path
import sys

import aiohttp

filepath = Path(__file__)
sys.path.append(filepath.parent.parent.as_posix())


# pylint: disable=import-error
from aussiebb.asyncio import AussieBB
from config import USERNAME2, PASSWORD2


async def main(mainloop):
    """ cli """
    async with aiohttp.ClientSession(loop=mainloop) as session:
        client = AussieBB(USERNAME2, PASSWORD2, session=session)
        await client.login()

        services = await client.get_services()
        # found_networks = []
        if services is None:
            client.logger.error("No services found")
            return
        for service in services:
            client.logger.info(json.dumps(service, indent=4, ensure_ascii=False))

            usage = await client.get_usage(service["service_id"])
            client.logger.success(json.dumps(usage, indent=4, ensure_ascii=False))



loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
loop.close()
