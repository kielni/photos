import argparse

import glob
import traceback

from util.photos import rename_exif

"""
    rename jpg files with prefix from Exif datetime field; keep the numbers at the end
      IMG_123.jpg -> 20200301_1200_123.jpg
      2021-07-09_12-57-27_471.jpeg -> 2021-07-09_125727_471.jpg
      dscn0519.jpg -> 20200301_1200_0519.jpg
    also change jpeg to jpg

    python ~/home/photos/scripts/rename_exif_date.py --dest ~/Pictures/amazon-keep --year
"""

"""
from util.photos import rename_exif
rename_exif(filename, year_prefix=False)
"""


def main(dest: str, year_prefix: bool, dry_run: bool):
    for idx, fn in enumerate(
        glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.JPG")
    ):
        try:
            rename_exif(fn, dest, year_prefix, dry_run)
        except Exception:
            print(f"error renaming {fn}")
            traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest", help="move files to this path; if not specified, rename in place"
    )
    parser.add_argument(
        "--year", help="add year to end of dest path", action="store_true"
    )
    parser.add_argument("--dry_run", help="don't actually rename", action="store_true")
    args = parser.parse_args()
    main(args.dest, args.year, args.dry_run)
