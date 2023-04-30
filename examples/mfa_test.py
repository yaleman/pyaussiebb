""" tests the MFA functionality """


import asyncio
from pathlib import Path
import sys

from aiohttp import ClientSession

from aussiebb.asyncio import AussieBB
from aussiebb.types import AussieBBConfigFile, MFAMethod

config_files = [
    "~/.config/aussiebb.json",
]


async def main() -> None:
    """main"""
    configfile = None
    for filepath in config_files:
        if Path(filepath).expanduser().exists():
            configfile = AussieBBConfigFile.parse_file(
                Path(filepath).expanduser().resolve()
            )
            break
    if configfile is None:
        print("Couldn't find any config files, quitting!")
        sys.exit(1)

    # use argparse to check if --earliest is passed and parse that as a date
    # parser = argparse.ArgumentParser(
    #                 prog='mfa_test',
    #                 description='Test authenticating with MFA and checking service info',
    #                 epilog='')
    # parser.add_argument("--earliest", help="Earliest date to download from, in YYYY-MM-DD format", action='store', type=str)
    # args = parser.parse_args()

    async with ClientSession() as session:
        aussiebb = AussieBB(
            username=configfile.users[0].username,
            password=configfile.users[0].password,
            session=session,
        )
        print("Logging in...")
        await aussiebb.login()
        mfa_method = MFAMethod(method="sms")
        print(f"Sending MFA via {mfa_method.method}")

        await aussiebb.mfa_send(mfa_method)

        # ask the user for the MFA token
        token = input("Enter MFA token: ")

        if token.strip() == "":
            print("No token entered, quitting!")
            sys.exit(1)
        print("Verifying MFA...")
        await aussiebb.mfa_verify(token.strip())

        print("Getting services...")
        services = await aussiebb.get_services()
        print(f"Getting the plan for {services[0]['service_id']}, which requires MFA!")
        print(await aussiebb.service_plans(services[0]["service_id"]))
        print("Done!")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
