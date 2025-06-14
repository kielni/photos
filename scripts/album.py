import argparse
import glob
import traceback

from util.photos import rename_exif, to_mp4


def rename():
    # copy *.{jpg,jpeg,JPG} files to current directory
    for idx, fn in enumerate(
        glob.glob("../all/*.jpg")
        + glob.glob("../all/*.jpeg")
        + glob.glob("../all/*.JPG")
    ):
        try:
            rename_exif(fn, "../album", year_prefix=False)
        except Exception:
            print(f"error renaming {fn}")
            traceback.print_exc()


def livephotos():
    # *.{mov,mp4} files in current directory to mp4 without audio
    for idx, fn in enumerate(glob.glob("*.mp4") + glob.glob("*.mov")):
        try:
            mp4_filename = to_mp4(fn)
            print(f"wrote Live Photo to {mp4_filename}")
        except Exception:
            print(f"error renaming {fn}")
            traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("op", type=str, default="rename")
    args = parser.parse_args()
    if args.op == "rename":
        rename()
    elif args.op == "livephotos":
        livephotos()
    else:
        print(f"unknown operation: {args.op}")
        exit(1)
