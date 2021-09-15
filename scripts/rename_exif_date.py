import argparse

import glob
import os
import re
from exif import Image

"""
    rename jpg files with prefix from Exif datetime field; keep the numbers at the end
      IMG_123.jpg -> 20200301_1200_123.jpg
      2021-07-09_12-57-27_471.jpeg -> 2021-07-09_125727_471.jpg
      dscn0519.jpg -> 20200301_1200_0519.jpg
    also change jpeg to jpg

    python ~/work/home/photos/scripts/rename_exif_date.py --dest ~/Pictures/amazon-keep --year
"""


def rename_exif(orig: str, dest: str, year_prefix: str, dry_run: bool):
    with open(orig, "rb") as image_file:
        img = Image(image_file)
    # 2020:02:23 14:12:03
    dt = img.datetime.replace(" ", "_").replace(":", "")
    # get the trailing digits of the filename
    match = re.search(r"(\d+)\.", orig)
    suffix = f"_{match.group(1)}" if match else ""
    ext = orig.split(".")[-1].lower().replace("jpeg", "jpg")
    fn = f"{dt}{suffix}.{ext}"
    if fn == orig:
        return
    prefix = ""
    if dest:
        filename = fn.split("/")[-1]
        if year_prefix:
            prefix = f"{dest}/{fn[:4]}/"
            if not os.path.exists(dest):
                print(f"creating {dest}")
                if not dry_run:
                    os.mkdir(dest)
            if not os.path.exists(prefix):
                print(f"creating {prefix}")
                if not dry_run:
                    os.mkdir(prefix)
        else:
            prefix = f"{dest}/"
    print("rename", orig, f"{prefix}{fn}")
    if not dry_run:
        os.rename(orig, f"{prefix}{fn}")


def main(dest: str, year_prefix: bool, dry_run: bool):
    for idx, fn in enumerate(glob.glob("*.jpg") + glob.glob("*.jpeg")):
        rename_exif(fn, dest, year_prefix, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest", help="move files to this path; if not specified, rename in place"
    )
    parser.add_argument("--year", help="add year to end of dest path", action="store_true")
    parser.add_argument("--dry_run", help="don't actually rename", action="store_true")
    args = parser.parse_args()
    main(args.dest, args.year, args.dry_run)
