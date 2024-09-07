import argparse
import glob
from datetime import datetime, timedelta
import os
import subprocess
from typing import List

from util.photos import rename_jpg, rename_mp4, process_live_photos, sync_to_s3
from util.apple import setup_last_month

"""
set in environment
    PHOTOS_ROOT = root of photos tree (~/Pictures)
    ICLOUD_USERNAME = username for downloading LivePhotos
    S3_PHOTOS_BUCKET = S3 bucket for photos and videos

assumes directory structure under PHOTOS_ROOT
    icloud-live-photos = download directory for Live Photos
    review = copy from Photos library to here
    staging = selected photos and videos to keep
    keep = files to keep and sync to external storage

source local.env
python monthly.py --prep - download LivePhotos to icloud-live-photos
python monthly.py - copy photos from staging to Ente and S3
"""

ROOT = os.environ["PHOTOS_ROOT"]
REVIEW = f"{ROOT}/review"
STAGING = f"{ROOT}/staging"
KEEP = f"{ROOT}/keep"


def monthly_prep():
    """Copy photos from last month from Photos library to staging.

    Download Live Photos, re-encode to mp4 without audio, and write to icloud-live-photos/review.

    Use icloudpd to download Live Photos.
    Use process_live_photos to convert photos from previous months to mp4 in icloud-photos/review
    icloudpd --directory $PHOTOS_ROOT/icloud-live-photos --username $ICLOUD_USERNAME -a Live --until-found 3
    """
    print("start monthly_prep")
    setup_last_month(REVIEW)

    print("download LivePhotos: ")
    username = os.environ.get("ICLOUD_USERNAME", "ICLOUD_USERNAME")
    # this doesn't work well with 2FA
    print(
        f"\ticloudpd --directory ~/Pictures/icloud-live-photos --username {username} -a Live --until-found 3"
    )
    live_photos = f"{ROOT}/icloud-live-photos"
    # process LivePhotos from this month and last month
    for dt in [datetime.now() - timedelta(days=30), datetime.now()]:
        process_live_photos(
            f"{live_photos}/{dt.strftime('%Y/%m')}", f"{live_photos}/review"
        )
    photos = glob.glob(f"{live_photos}/review/*.mp4")
    print(f"\nreview {len(photos)} LivePhotos in {live_photos}/review")




def monthly(dry_run: bool):
    """Put files to keep in `staging`, then call this to rename and sync to Ente and S3.

    Rename jpg files in `staging` to yyyy-mm-dd_hhmmss_index.jpg
    Rename mp4 files in `staging` to yyyy-mm-dd_index.mp4
    Move files to `keep` to sync to external storage
    Sync files from `keep` to S3
    """
    os.chdir(STAGING)
    div = "\n" + ("-" * 80) + "\n"
    print(f"{div}renaming and moving files from {STAGING} to {KEEP}{div}")
    filenames = rename_jpg(f"{KEEP}", True, dry_run)
    print(f"moved {len(filenames)} jpg files")
    video_filenames = rename_mp4(f"{KEEP}", True, dry_run)
    print(f"moved {len(video_filenames)} mp4 files")
    filenames += video_filenames
    sync_to_s3(KEEP, os.environ.get("S3_PHOTOS_BUCKET"), filenames, dry_run)


if __name__ == "__main__":
    print("monthly")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry_run", help="print actions but do not apply", action="store_true"
    )
    parser.add_argument(
        "--prep",
        help="prepare: download and re-encode Live Photos",
        action="store_true",
    )
    parser.add_argument("--s3", help="sync to S3", action="store_true")
    args = parser.parse_args()
    print(args)
    if args.prep:
        monthly_prep()
    elif args.prep:
        s3_sync()
    else:
        monthly(args.dry_run)
