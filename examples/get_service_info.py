#!/usr/bin/env python

""" pulls and lists the VOIP services on your account """

# pylint: disable=wrong-import-position

import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Optional

import aiohttp

script_path = Path(__file__)
sys.path.append(script_path.parent.parent.as_posix())


# pylint: disable=import-error
from aussiebb.asyncio import AussieBB  # noqa E402
from aussiebb.types import AussieBBConfigFile  # noqa E402


def configloader() -> Optional[AussieBBConfigFile]:
    """loads config"""
    for filename in [os.path.expanduser("~/.config/aussiebb.json"), "aussiebb.json"]:
        filepath = Path(filename).resolve()
        if filepath.exists():
            try:
                return AussieBBConfigFile.parse_file(filepath)
            except json.JSONDecodeError as json_error:
                sys.exit(f"Failed to parse config file: {json_error}")
    return None


async def main(mainloop: asyncio.AbstractEventLoop) -> None:
    """cli"""

    config = configloader()
    if config is None:
        sys.exit("Couldn't load config")
    if len(config.users) == 0:
        print("no users in config, bailing")
        sys.exit(1)
    user = config.users[0]
    async with aiohttp.ClientSession(loop=mainloop) as session:
        client = AussieBB(user.username, user.password, session=session)
        await client.login()

        services = await client.get_services()
        # found_networks = []
        if services is None:
            client.logger.error("No services found")
            return
        for service in services:
            client.logger.error(json.dumps(service, indent=4, ensure_ascii=False))
            usage = await client.get_usage(service["service_id"])
            client.logger.error(json.dumps(usage, indent=4, ensure_ascii=False))


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
loop.close()
