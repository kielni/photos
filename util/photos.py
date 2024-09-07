from datetime import datetime

import glob
import os
import re
import subprocess
from typing import Optional, List

from exif import Image

from dateutil import parser as date_parser


def to_mp4(input_path: str, output_path: str, size: Optional[str] = None) -> str:
    """Use ffmpeg to convert a .mov to .mp4.

    -i input file
    -an drop audio track
    -vcodec h264 use H.264 encoding
    -s target image size
    -y overwrite destination file
    """
    size_params = ["-s", size] if size else []
    command = (
            ["ffmpeg", "-i", input_path, "-an"]
            + size_params
            + [output_path, "-y", "-loglevel", "error"]
    )
    print(" ".join(command))
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    print(process.stdout)
    return output_path


def process_live_photos(root: str, dest: str, size: Optional[str] = None):
    """Find MOV files under root, and use ffmpeg to resize, drop audio, and rename.

    :param root: look for .MOV files under this directory
    :param dest: write output to this directory
    :param size: if provided, resize with -s size (ie 768x576)

    Download Live Photos with https://github.com/icloud-photos-downloader/icloud_photos_downloader
    icloudpd --directory ~/Pictures/icloud-live-photos --username username -a Live  --until-found 3

    This creates .MOV in a file tree by date: 2021/06/29/IMG_3397.MOV
    For each .MOV under the root directory,
      - use ffmpeg to resize, drop audio track, and convert to mp4
      - write to dest/yyyy-mm-dd-index.mp4

    See https://medium.com/@kielnicholls/embedding-livephotos-on-a-web-page-5dfa9b8b83e3
    """
    print(f"processing Live Photos from {root} to {dest}")
    files = sorted(glob.glob(f"{root}/**/*.MOV", recursive=True))
    for idx, file_path in enumerate(files):
        print(f"{idx+1}/{len(files)} {file_path}")
        # 2021/07/04/IMG_3417.MOV -> 2021-07-04
        dt_str = "-".join(re.search(r"(\d+)/(\d+)/(\d+)", file_path).groups())
        fn = file_path.split("/")[-1]  # IMG_3417.MOV
        match = re.search(r"_(\d+)\.", fn)
        index = match.group(1) if match else str(idx)
        # dest/2021-07-07_3417.mp4
        out_fn = f"{dest}/{dt_str}_{index}.mp4"
        to_mp4(file_path, out_fn, size)
        print(f"wrote {out_fn}")


def filename_datetime(filename: str) -> datetime:
    """Try to get a datetime from a filename.

    :param filename: filename
    :return: datetime if filename matches a known format
    """
    # Amazon photos filename format is 2020-07-04_21-00-11.jpg
    match = re.search(r"(\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d)", filename)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d_%H-%M-%S")
    # IMG_20140629_103425.jpg
    match = re.search(r"(\d\d\d\d\d\d\d\d_\d\d\d\d\d\d)", filename)
    if match:
        return date_parser.parse(match.group(1))
    raise ValueError(f"no date from {filename}")


def exif_datetime(fn: str) -> datetime:
    """Try to get datetime from Exif metadata. If that doesn't work, try filename.

    :param fn: filename
    :return: datetime form Exif or filename.
    """
    with open(fn, "rb") as image_file:
        img = Image(image_file)
        try:
            # fix weird date format: 2021:08:06 16:07:56
            keys = img.list_all()
            d = t = None
            for key in ["datetime", "datetime_original"]:
                if key in keys:
                    d, t = img[key].split(" ")
                    break
            if not d:
                raise ValueError(f"no exif date")
            return date_parser.parse(f"{d.replace(':', '-')} {t}")
        except Exception as exc:
            # print(f"{fn}\terror parsing: {exc}")
            pass
    return filename_datetime(fn)


def rename_exif(
    orig: str,
    dest: Optional[str] = None,
    year_prefix: bool = True,
    dry_run: bool = False,
) -> str:
    """Rename JPG files with a datetime prefix; keep numbers at the end.

    Change .jpeg to .jpg
    Examples:
        IMG_123.jpg -> 2020-03-01_1200_123.jpg
        2021-07-09_12-57-27_471.jpeg -> 2021-07-09_125727_471.jpg
        dscn0519.jpg -> 2020-03-01_1200_0519.jpg
        IMG_20130828_071618(1).jpg -> 20130828_071618.jpg

    :param orig: filename
    :param dest: destination path prefix
    :param year_prefix: if true, add the year as a path segment
    :param dry_run: if true, do not actually rename files
    :return: new filename
    """
    dt = exif_datetime(orig)
    if not dt:
        raise ValueError(f"cannot extract datetime from {orig}")
    # get the trailing digits of the filename
    match = re.search(r"(\d+)\.", orig)
    suffix = f"_{match.group(1)}" if match else ""
    ext = orig.split(".")[-1].lower().replace("jpeg", "jpg")
    fn = f"{dt.strftime('%Y-%m-%d_%H%M%S')}{suffix}.{ext}"
    if fn == orig:
        return
    prefix = ""
    if dest:
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
    final_filename = f"{prefix}{fn}"
    print("rename", orig, final_filename)
    if not dry_run:
        os.rename(orig, final_filename)
    return final_filename


def rename_jpg(dest: str, year_prefix: bool, dry_run: bool) -> List[str]:
    """Rename all jpg/jpeg files in the current directory with a datetime prefix.

    :param dest: destination path prefix
    :param year_prefix: if true, add the year as a path segment
    :param dry_run: if true, do not actually rename files
    :return: list of new filenames
    """
    filenames: List[str] = []
    for idx, fn in enumerate(glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.JPG")):
        try:
            filenames.append(rename_exif(fn, dest, year_prefix, dry_run))
        except Exception as exc:
            print(f"error renaming {fn}: {exc}")
    return filenames


def rename_mp4(dest: str, year_prefix: bool, dry_run: bool) -> List[str]:
    """Rename all mp4 files in the current directory with a datetime prefix.

    :param dest: destination path prefix
    :param year_prefix: if true, add the year as a path segment
    :param dry_run: if true, do not actually rename files
    :return: list of new filenames
    """
    filenames: List[str] = []
    for idx, fn in enumerate(glob.glob("*.mp4")):
        prefix = f"{dest}/"
        if year_prefix:
            fn = fn.split("/")[-1]
            prefix = f"{dest}/{fn[:4]}/"
        final_filename = f"{prefix}{fn}"
        if dry_run:
            print("rename", fn, final_filename)
        else:
            os.rename(fn, final_filename)
        filenames.append(final_filename)
    return filenames


def remove_old(
    since: datetime, skip_before: Optional[datetime] = None, dry_run: bool = False
):
    """Remove jpg/jpeg files older than a datetime.

    :param since: remove files older than this date
    :param skip_before: skip files older than this date (probably bad/missing metadata)
    :param dry_run: if true, do not actually remove files
    """
    remove = 0
    for idx, fn in enumerate(glob.glob("**/*.jpg") + glob.glob("**/*.jpeg")):
        dt = None
        try:
            # try this first since it's simpler/faster
            dt = filename_datetime(fn)
        except ValueError:
            pass
        try:
            dt = exif_datetime(fn)
        except Exception:
            # print(f"{fn}\tskip: can't get date")
            continue
        dt_str = dt.strftime("%Y-%m-%d")
        if dt > since:
            # print(f"{fn}\tskip too new: {dt} > {since}")
            continue
        if skip_before and dt < skip_before:
            print(f"{fn}\tskip too old: {dt_str} < {skip_before.strftime('%Y-%m-%d')}")
            continue
        print(f"{fn}\tremove; {dt_str} <= {since.strftime('%Y-%m-%d')}")
        remove += 1
        if not dry_run:
            os.remove(fn)
    print(f"remove {remove}")

def extract_caption(fn: str) -> str:
    with open(fn, "rb") as image_file:
        img = Image(image_file)
    try:
        return img.image_description.strip()
    except Exception:
        return ""

def mp4_tag(filename: str) -> str:
    html = """<div class="col">
          <div class="card">
            <video class="card-img-top%s" loop muted playsinline autoplay>
              <source src="mp4/%s">
            </video>
            <div class="card-body">
              <p class="card-text">%s</p>
            </div>
          </div>
        </div>
        """
def jpg_tag(filename: str) -> str:
    portrait = {}
    panorama = {}
    # main
    text = '\n    <div class="card-body%s"><div class="card-text">%s</div></div>\n'
    html = """<div class="col">
      <div class="card">
        <img class="card-img-top%s" src="img/%s">%s
      </div>
    </div>"""
    meta = {}  # TODO:
    img_html = video_html = ""  # TODO:

    for key in sorted(meta.keys()):
        name = key.split(".")[0]
        extra = ""
        if name in portrait:
            extra = " portrait"
        if name in panorama:
            extra = " panorama"
        caption = text % (extra, meta[key]) if meta[key] else ""
        html = ""
        if "jpg" in key:
            html = img_html % (extra, key, caption)
        if "mp4" in key:
            html = video_html % (extra, key, key)
        # print('<!-- %s |%s| -->' % (key, caption))
        print(html)

    print("\n")

def filenames_to_html(filenames: List[str]):
    meta = {}
    for fn in [f for f in filenames if f.endswith("jpg")]:
        meta[fn] = extract_caption(fn)

def sync_to_s3(path: str, s3_bucket: str, filenames: List[str], dry_run: bool = False):
    os.chdir(path)
    print(f"\nsync files in {path} to s3://{s3_bucket}")
    if not filenames:
        return
    for idx, fn in enumerate(filenames):
        print(f"{idx+1}/{len(filenames)}")
        # convert to relative path
        fn = fn.replace(f"{path}/", "")
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