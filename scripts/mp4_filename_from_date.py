import argparse
import os

from util.photos import mp4_path


def main(filename: str, rename: bool):
    new_filename = mp4_path(filename)
    print(new_filename)
    if rename:
        print(f"renaming {filename} to {new_filename}")
        os.rename(filename, new_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dest", type=str)
    parser.add_argument("--rename", action="store_true")
    args = parser.parse_args()
    main(args.dest, args.rename)
