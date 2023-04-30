""" downloads invoices and receipts and stuff """

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
import sys

from aiohttp import ClientSession

from aussiebb.asyncio import AussieBB
from aussiebb.types import AussieBBConfigFile

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
    parser = argparse.ArgumentParser(
        prog="download_invoices",
        description="Download invoices and receipts from AussieBB",
        epilog="Buyer beware",
    )
    parser.add_argument(
        "--earliest",
        help="Earliest date to download from, in YYYY-MM-DD format",
        action="store",
        type=str,
    )
    args = parser.parse_args()

    if args.earliest:
        earliest_date = datetime.strptime(args.earliest, "%Y-%m-%d")
    else:
        earliest_date = datetime.strptime("1970-01-01", "%Y-%m-%d")
    print(f"Earliest date: {earliest_date.strftime('%Y-%m-%d')}")

    async with ClientSession() as session:
        aussiebb = AussieBB(
            username=configfile.users[0].username,
            password=configfile.users[0].password,
            session=session,
        )
        print("Logging in...")
        await aussiebb.login()
        print("Pulling transactions...")
        transactions = await aussiebb.account_transactions()
        for _transaction_date, transaction in transactions.items():
            timestamp = datetime.strptime(transaction["time"], "%Y-%m-%d")
            download_path = Path(
                f"{transaction['time']}-{transaction['id']}-{transaction['type']}.pdf"
            )
            if download_path.exists():
                print(f"Already have {download_path}, skipping")
                continue
            if timestamp < earliest_date:
                print(f"Skipping {download_path} due to timestamp")
                continue
            if transaction["type"] == "receipt":
                invoice = await aussiebb.billing_receipt(transaction["id"])
            elif transaction["type"] == "invoice":
                invoice = await aussiebb.billing_invoice(transaction["id"])
            elif transaction["type"] == "credit":
                invoice = await aussiebb.billing_download(
                    transaction["type"], transaction["id"]
                )
            else:
                print(
                    "Unhandled event type: %s for id=%s",
                    transaction["type"],
                    transaction["id"],
                )
                return
            download_path.write_bytes(await invoice.content.read())
            print(f"{download_path} Done!")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
