""" WARNING THIS REALLY DOESN'T WORK BECAUSE ... SOMETHING SOMETHING PROBABLY BOT BLOCKING FROM CLOUDFLARE

downloads invoices and receipts and stuff """

import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys

from aiohttp import ClientSession

from aussiebb.asyncio import AussieBB
from aussiebb.types import AccountTransaction, AussieBBConfigFile


config_files = [
    "~/.config/aussiebb.json",
]

async def handle_transaction(aussiebb: AussieBB, transaction: AccountTransaction, earliest_date: datetime ) -> None:
    """ handle an individual transaction... """
    # because python is drunk sometimes
    transaction = AccountTransaction.parse_obj(transaction)

    timestamp = datetime.strptime(transaction.time, "%Y-%m-%d")
    download_path = Path(
        f"{transaction.time}-{transaction.id}-{transaction.type}.pdf"
    )
    if download_path.exists():
        print(f"Already have {download_path}, skipping")
        return
    if timestamp < earliest_date:
        print(f"Skipping {download_path} due to timestamp")
        return
    if transaction.type == "receipt":
        invoice = await aussiebb.billing_receipt(transaction.id)
    elif transaction.type == "invoice":
        invoice = await aussiebb.billing_invoice(transaction.id)
    elif transaction.type == "credit":
        invoice = await aussiebb.billing_download(
            transaction.type, transaction.id
        )
    else:
        print(
            "Unhandled event type: %s for id=%s",
            transaction.type,
            transaction.id,
        )
        return
    with download_path.open(mode = "wb") as file_handle:
        total_content = 0
        read_retry = 3
        content = await invoice.content.read(1024)
        while read_retry > 0:
            if len(content) == 0:
                print("trying another read...")
                read_retry -= 1
            else:
                print(f"content length is {len(content)}")
            total_content += len(content)
            file_handle.write(content)
            content = await invoice.content.read(1024)
    if total_content == 0:
        download_path.unlink()
        print(f"Failed to download {download_path} - 0 byte content!")
    else:
        print(f"{download_path} Done! Wrote {total_content} bytes.")
    sys.exit(1)

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
        help="Earliest date to download from, in YYYY-MM-DD format, defaults to last 30 days.",
        action="store",
        type=str,
    )
    args = parser.parse_args()

    if args.earliest:
        earliest_date = datetime.strptime(args.earliest, "%Y-%m-%d")
    else:
        earliest_date = datetime.now() - timedelta(days=30)
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
            if isinstance(transaction, list):
                for individual_transaction in transaction:
                    await handle_transaction(aussiebb, individual_transaction, earliest_date)
            else:
                await handle_transaction(aussiebb, transaction, earliest_date)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
