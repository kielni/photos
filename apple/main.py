import argparse
import glob
import os
import re
from datetime import datetime, timedelta
from typing import List, Iterable, Optional

import osxphotos
from osxphotos import QueryOptions, ExifTool, PhotoInfo

from util.photos import to_mp4, sync_to_s3

"""
usage:
set in environment
    S3_PHOTOS_BUCKET = S3 bucket for photos and videos

setup: python apple/main.py
  - copy favorited photos and live photos from the last 45 days to staging directory
  - re-encode mov to mp4

sync: python apple/main.py --sync
  - copy photos to S3 and ente sync folder
"""


def filename_from_date(pi: PhotoInfo, ext: Optional[str] = None) -> str:
    # 2024-07-20_093327_01636776
    filename = pi.date.strftime("%Y-%m-%d_%H%M%S")
    if match := re.search(r"(\d+)", pi.original_filename):
        filename += "_" + match.group(1)
    return f"{filename}.{ext}" if ext else filename


def export_live_photos(output_dir: str, results: Iterable[PhotoInfo]):
    print(f"Found {len(results)} live photos")
    for photo in results:
        base_filename = filename_from_date(photo)
        filename = f"{base_filename}.mov"
        mov_path = f"{output_dir}/{filename}"
        photo.export(output_dir, filename=filename, overwrite=True, live_photo=True)
        photo.export(
            output_dir,
            filename=filename.replace(".mov", ".jpg"),
            overwrite=True,
            live_photo=False,
        )
        mp4_filename = to_mp4(mov_path)
        print(f"wrote Live Photo to {mp4_filename}")
        os.remove(mov_path)


def export_photos_with_metadata(output_dir: str, results: Iterable[PhotoInfo]):
    print(f"Found {len(results)} photos")
    for photo in results:
        filename = filename_from_date(photo, "jpg")
        full_filename = f"{output_dir}/{filename}"
        print(f"\nexport {photo.original_filename} to {output_dir}/{filename}")
        photo.export(
            output_dir, filename=filename, overwrite=True, edited=photo.hasadjustments
        )
        # copy metadata from library and write to EXIF
        with ExifTool(f"{full_filename}", flags=["-m"]) as exif_tool:
            keywords: List[str] = []
            persons = [p for p in photo.persons if p != "_UNKNOWN_"]
            if persons:
                print(f"\tpersons={persons}")
                exif_tool.setvalue("XMP:PersonInImage", "; ".join(persons))
                keywords += persons
            albums = [a for a in photo.albums if a]
            if albums:
                print(f"\talbums={albums}")
                keywords += albums
            if photo.labels_normalized:
                keywords += photo.labels_normalized
            if keywords:
                keywords_str = "; ".join(keywords)
                print("\twriting keywords: ", keywords)
                exif_tool.setvalue("IPTC:Keywords", keywords_str)
            exif_tool.setvalue("IPTC:ObjectName", photo.original_filename)
            if photo.description:
                exif_tool.setvalue("EXIF:ImageDescription", photo.description)
                print("writing description: ", photo.description)


def export(output_dir: str, days: int):
    from_dt = datetime.now() - timedelta(days=days)
    print(f"Export photos since {from_dt.strftime('%m/%d/%Y')} to {output_dir}")
    print("Loading PhotosDB..")
    photosdb = osxphotos.PhotosDB()
    export_photos_with_metadata(
        output_dir, photosdb.query(QueryOptions(favorite=True, from_date=from_dt))
    )
    print("\n\n")
    export_live_photos(
        output_dir,
        photosdb.query(QueryOptions(favorite=True, from_date=from_dt, live=True)),
    )
    print(f"\nreview photos in {output_dir}, then\npython apple/main.py --sync")


def sync(root: str, bucket: str):
    """Sync contents of output_dir to S3."""
    # move *.mp4 and *.jpg from root/staging to root/keep
    keep_dir = f"{root}/keep"
    staging_dir = f"{root}/staging"
    filenames: List[str] = []
    for full_filename in glob.glob(f"{staging_dir}/*.mp4") + glob.glob(
        f"{staging_dir}/*.jpg"
    ):
        filename = os.path.basename(full_filename)
        year = filename[:4]
        year_filename = f"{year}/{filename}"
        filenames.append(year_filename)
        # if keep_dir/year directory does not exist, create the directory
        print(f"rename from {full_filename} to {keep_dir}/{year_filename}")
        os.rename(f"{full_filename}", f"{keep_dir}/{year_filename}")

    sync_to_s3(keep_dir, bucket, filenames)


"""
remove these
  "ExifTool:ExifToolVersion": 10.15,
  "ExifTool:Warning": "[minor] Bad format (16) for MakerNotes entry 13",
  "Directory": "/Users/kimberly/Downloads/apple",
  "SourceFile": "/Users/kimberly/Downloads/apple/20240901_103304_1887.jpg",
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # export to staging, sync to keep
    parser.add_argument("--root", type=str)
    parser.add_argument("--days", type=int, default=45)
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--bucket", type=str)
    args = parser.parse_args()
    _output = args.root or f"/Users/{os.environ.get('USER')}/Pictures"
    if args.sync:
        sync(_output, args.bucket or os.environ.get("S3_PHOTOS_BUCKET"))
    else:
        export(f"{_output}/staging", args.days)
