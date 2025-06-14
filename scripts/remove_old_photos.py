import argparse
from typing import Optional

import glob
import os
import re
from exif import Image

from dateutil import parser as date_parser


def main(since_str: str, skip_before_str: Optional[str], dry_run: bool):
    since = date_parser.parse(since_str)
    skip_before = date_parser.parse(skip_before_str) if skip_before_str else None
    remove = 0
    for idx, fn in enumerate(glob.glob("*.jpg") + glob.glob("*.jpeg")):
        # if the filename starts with a date, use that
        match = re.match(r"(\d\d\d\d-\d\d-\d\d).*", fn)
        dt = None
        if match:
            dt = date_parser.parse(match.group(1))
        else:
            with open(fn, "rb") as image_file:
                img = Image(image_file)
                try:
                    # fix weird date format: 2021:08:06 16:07:56
                    d, t = img.datetime.split(" ")
                    dt = date_parser.parse(f"{d.replace(':', '-')} {t}")
                except Exception as exc:
                    print(f"{fn}\terror parsing: {exc}")
        if not dt:
            print(f"{fn}\tskip: can't get date")
            continue
        dt_str = dt.strftime("%Y-%m-%d")
        if dt > since:
            # print(f"{fn}\tskip too new: {dt} > {since}")
            continue
        if skip_before and dt < skip_before:
            print(f"{fn}\tskip too old: {dt_str} < {skip_before.strftime('%Y-%m-%d')}")
            continue
        print(f"{fn}\tremove; {dt_str} <= {since.strftime('%Y-%m-%d')}")
        remove += 1
        if not dry_run:
            os.remove(fn)
    print(f"remove {remove}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "since",
        help="remove photos with exif date older than this date (default 2 years ago)",
    )
    parser.add_argument(
        "--skip_before", help="skip files with exif date before this date"
    )
    parser.add_argument(
        "--dry_run", help="print actions but do not delete", action="store_true"
    )
    args = parser.parse_args()
    main(args.since, args.skip_before, args.dry_run)
