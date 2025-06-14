import glob
import traceback

from util.photos import rename_exif
from exif import Image


def copy_datetime(fn: str) -> bool:
    with open(fn, "rb") as image_file:
        img = Image(image_file)
    keys = img.list_all()
    if "datetime_original" not in keys:
        return False
    if img.datetime == img.datetime_original:
        return False
    img.datetime = img.datetime_original
    print(f"{fn}\tcopied datetime {img.datetime}")
    with open(fn, "wb") as image_file:
        image_file.write(img.get_file())
    return True


def main():
    for idx, fn in enumerate(
        glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.JPG")
    ):
        try:
            if copy_datetime(fn):
                rename_exif(fn)
        except Exception:
            print(f"error renaming {fn}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
