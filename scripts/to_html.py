import argparse
from typing import List


def main(filenames: List[str]):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", type=str, nargs="+", help="Write HTML")
    args = parser.parse_args()
    main(args.filenames)
