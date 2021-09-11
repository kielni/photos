import argparse
import glob
from datetime import datetime, timedelta
import os
import subprocess

from util.photos import rename_jpg, rename_mp4, remove_old, process_live_photos


"""
set in environment
    PHOTOS_ROOT = root of photos tree (~/Pictures)
    ICLOUD_USERNAME = username for downloading LivePhotos
    S3_PHOTOS_BUCKET = s3 bucket for photos and videos

assumes directory structure under PHOTOS_ROOT
    amazon-keep = synced to Amazon Photos album
    amazon-phone = synced to phone
    icloud-live-photos = download directory for Live Photos
    staging = selected photos and videos to keep

source local.env
python monthly.py --prep - download LivePhotos to icloud-live-photos
python monthly.py
"""

ROOT = os.environ["PHOTOS_ROOT"]


def monthly_prep():
    """Download Live Photos, re-encode to mp4 without audio, and write to icloud-live-photos/review.

    Use icloudpd to download Live Photos.
    Use process_live_photos to convert photos from previous months to mp4 in icloud-photos/review
    """
    if not os.environ.get("ICLOUD_USERNAME"):
        raise RuntimeError("ICLOUD_USERNAME must be set in environment")
    live_photos = f"{ROOT}/icloud-live-photos"
    # download LivePhotos
    command = [
        "icloudpd",
        "--directory",
        live_photos,
        "--username",
        os.environ["ICLOUD_USERNAME"],
        "-a",
        "Live",
        "--until-found",
        "3",
    ]
    print(f"downloading LivePhotos\n{' '.join(command)}")
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    print(process.stdout)
    # process LivePhotos from this month and last month
    for dt in [datetime.now() - timedelta(days=30), datetime.now()]:
        process_live_photos(
            f"{live_photos}/{dt.strftime('%Y/%m')}", f"{live_photos}/review"
        )
    photos = glob.glob(f"{live_photos}/review/*.mp4")
    print(f"\nreview {len(photos)} LivePhotos in {live_photos}/review")


def monthly(dry_run: bool):
    """Put files to keep in `staging`, then call this to rename and sync to Amazon photos and S3.

    Rename jpg files in `staging` to yyyy-mm-dd_hhmmss_index.jpg
    Rename mp4 files in `staging` to yyyy-mm-dd_index.mp4
    Move files to `amazon-keep` to sync to Amazon Photos album
    Sync files from `amazon-keep` to s3
    Remove files under `amazon-phone` that are older than 730 days
    """
    staging_dir = f"{ROOT}/staging"
    keep_dir = f"{ROOT}/amazon-keep"
    phone_dir = f"{ROOT}/amazon-phone"

    os.chdir(staging_dir)
    div = "\n" + ("-" * 80) + "\n"
    print(f"{div}renaming and moving files from {staging_dir} to {keep_dir}{div}")
    filenames = rename_jpg(f"{keep_dir}", True, dry_run)
    print(f"moved {len(filenames)} jpg files")
    video_filenames = rename_mp4(f"{keep_dir}", True, dry_run)
    print(f"moved {len(video_filenames)} mp4 files")
    filenames += video_filenames

    os.chdir(phone_dir)
    since_dt = datetime.now() - timedelta(days=730)
    print(
        f"{div}remove files in {phone_dir} older than {since_dt.strftime('%Y-%m-%d')}{div}"
    )
    remove_old(since_dt, datetime(2000, 1, 1), dry_run)

    os.chdir(keep_dir)
    s3_bucket = os.environ.get("S3_PHOTOS_BUCKET")
    print(f"{div}sync files in {keep_dir} to S3{div}")
    for idx, fn in enumerate(filenames):
        print(f"{idx+1}/{len(filenames)}")
        # convert to relative path
        fn = fn.replace(keep_dir + "/", "")
        command = ["aws", "s3", "cp", fn, f"s3://{s3_bucket}/{fn}", "--no-progress"]
        print(" ".join(command))
        if not dry_run:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            print(process.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry_run", help="print actions but do not apply", action="store_true"
    )
    parser.add_argument(
        "--prep",
        help="prepare: download and re-encode Live Photos",
        action="store_true",
    )
    args = parser.parse_args()
    if args.prep:
        monthly_prep()
    else:
        monthly(args.dry_run)
