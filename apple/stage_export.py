"""
Run this to rename exported files to a standard format.

Get files in export directory (JPG, jpeg, mov, mp4)
Rename IMG_d+.jpeg to yyyy-mm-dd_105109_2283.jpg
Re-encode mov to mp4
Rename with timestamp
"""

import argparse
import glob
import os

from util.photos import rename_jpg, exif_datetime, to_mp4, rename_mp4, mp4_path


def _main(src_dir: str, dest_dir: str):
    fn = "/Users/kimberly/Pictures/family-share-export/IMG_2461.jpeg"
    r = exif_datetime(fn)
    print(r)


def main(src_dir: str, dest_dir: str):
    filenames = rename_jpg(
        src_dir, dest_dir, year_prefix=False, overwrite=False, dry_run=False
    )
    print(f"\nmoved {len(filenames)} jpg files from {src_dir} to {dest_dir}")

    video_files = glob.glob(f"{src_dir}/*.mov") + glob.glob(f"{src_dir}/*.MOV")
    for idx, mov_path in enumerate(video_files):
        print(f"{idx+1}/{len(video_files)}: {mov_path}")
        to_mp4(mov_path)
        os.remove(mov_path)
    # rename mp4 with creation time
    video_files = glob.glob(f"{src_dir}/*.mp4")
    for idx, input_path in enumerate(video_files):
        output_path = mp4_path(input_path)
        print(f"{idx+1}/{len(video_files)}: rename {input_path} to {output_path}")
        os.rename(input_path, output_path)
    filenames = rename_mp4(
        src_dir, dest_dir, year_prefix=False, overwrite=False, dry_run=False
    )
    print(f"\nmoved {len(filenames)} video files from {src_dir} to {dest_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    root = os.getenv("PHOTOS_ROOT", "")
    parser.add_argument("--src", type=str, default=f"{root}/family-share-export")
    parser.add_argument("--dest", type=str, default=f"{root}/staging")
    args = parser.parse_args()
    main(args.src, args.dest)
