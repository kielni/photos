from datetime import datetime
import glob
import os
import re
import subprocess
from typing import Optional, List

from exif import Image
import piexif
from PIL import Image as PILImage

from dateutil import parser as date_parser


def mp4_path(input_path: str):
    filename = input_path.split("/")[-1]
    output_path = input_path.replace(filename.split(".")[-1], "mp4").lower()
    # try to get creation time from metadata
    creation_dt = get_mp4_datetime(input_path)
    if not creation_dt:
        return output_path
    # IMG_3417.MOV -> 2021-07-07_3417.mp4
    new_fn = creation_dt.strftime("%Y-%m-%d_%H%M%S")
    if match := re.search(r"_(\d+)\.", filename):
        new_fn += f"_{match.group(1)}"
    new_fn += ".mp4"
    output_path = f"{input_path.replace(filename, new_fn)}"
    return output_path


def to_mp4(input_path: str, size: Optional[str] = None) -> str:
    """Use ffmpeg to convert a .mov to .mp4.

    -i input file
    -an drop audio track
    -vcodec h264 use H.264 encoding
    -s target image size
    -y overwrite destination file
    -map_metadata 0 map preserve metadata
    -movflags use_metadata_tags -map_metadata 0
    """
    output_path = mp4_path(input_path)
    size_params = ["-s", size] if size else []
    command = (
        [
            "ffmpeg",
            "-i",
            input_path,
            "-movflags",
            "use_metadata_tags",
            "-map_metadata",
            "0",
            "-an",
        ]
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
    today_str = datetime.now().strftime("%Y-%m-%d")
    for idx, file_path in enumerate(files):
        print(f"{idx+1}/{len(files)} {file_path}")
        # 2021/07/04/IMG_3417.MOV -> 2021-07-04
        if match := re.search(r"(\d+)/(\d+)/(\d+)", file_path):
            dt_str = "-".join(match.groups())
        else:
            print(f"no date in {file_path}; using today")
            dt_str = today_str
        fn = file_path.split("/")[-1]  # IMG_3417.MOV
        match = re.search(r"_(\d+)\.", fn)
        index = match.group(1) if match else str(idx)
        mp4_out_fn = to_mp4(file_path, size)
        # dest/2021-07-07_3417.mp4
        out_fn = f"{dest}/{dt_str}_{index}.mp4"
        os.rename(mp4_out_fn, out_fn)
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
    :param keys: list of Exif keys to look for
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
                raise ValueError("no exif date")
            return date_parser.parse(f"{d.replace(':', '-')} {t}")
        except Exception as exc:
            print(f"{fn}\terror parsing: {exc}")
            pass
    return filename_datetime(fn)


def rename_exif(
    orig: str,
    dest: Optional[str] = None,
    year_prefix: bool = True,
    overwrite: bool = False,
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
    :param overwrite: if true, overwrite existing files
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
        return fn
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
    # if final_filename exists, skip
    if os.path.exists(final_filename) and not overwrite:
        print(f"skip: {final_filename} exists")
        if not dry_run:
            os.remove(orig)
        return final_filename
    if not dry_run:
        os.rename(orig, final_filename)
    return final_filename


def rename_jpg(
    src: str,
    dest: str,
    year_prefix: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """Rename all jpg/jpeg files in the current directory with a datetime prefix.

    :param src: source path prefix
    :param dest: destination path prefix
    :param year_prefix: if true, add the year as a path segment
    :param overwrite: if true, overwrite existing files
    :param dry_run: if true, do not actually rename files
    :return: list of new filenames
    """
    if src and not src.endswith("/"):
        src += "/"
    filenames: List[str] = []
    for idx, fn in enumerate(
        glob.glob(f"{src}*.JPG") + glob.glob(f"{src}*.jpg") + glob.glob(f"{src}*.jpeg")
    ):
        try:
            filenames.append(rename_exif(fn, dest, year_prefix, overwrite, dry_run))
        except Exception as exc:
            print(f"error renaming {fn}: {exc}")
    return filenames


def rename_mp4(
    src: str,
    dest: str,
    year_prefix: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """Rename all mp4 files in the current directory with a datetime prefix.

    :param src: source path prefix
    :param dest: destination path prefix
    :param year_prefix: if true, add the year as a path segment
    :param overwrite: if true, overwrite existing files
    :param dry_run: if true, do not actually rename files
    :return: list of new filenames
    """
    if src and not src.endswith("/"):
        src += "/"
    filenames: List[str] = []
    for idx, full_path in enumerate(glob.glob(f"{src}*.mp4")):
        fn = full_path.split("/")[-1]
        prefix = f"{dest}/"
        if year_prefix:
            prefix = f"{dest}/{fn[:4]}/"
        final_filename = f"{prefix}{fn}"
        if os.path.exists(final_filename) and not overwrite:
            print(f"skip: {final_filename} exists")
            if not dry_run:
                os.remove(fn)
            continue
        if dry_run:
            print("rename", full_path, final_filename)
        else:
            os.rename(full_path, final_filename)
        filenames.append(final_filename)
    return filenames


def get_mp4_datetime(file_path: str) -> Optional[datetime]:
    """Extract datetime metadata from an MP4 file using ffmpeg."""
    command = ["ffmpeg", "-i", file_path, "-dump", "-"]
    process = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    lines = process.stderr.splitlines() + process.stdout.splitlines()
    lines = [line for line in lines if "creation_time" in line]
    if not lines:
        return None
    # creation_time   : 2024-12-24T16:43:17.000000Z
    if match := re.search(r"(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)", lines[0]):
        return datetime.fromisoformat(match.group(1))
    return None


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
    except Exception as exc:
        print(f"error reading caption from {fn}: {exc}")
        return ""


def mp4_tag(filename: str) -> str:
    return f"""<div class="col">
           <div class="card">
             <video class="card-img-top%s" loop muted playsinline autoplay>
               <source src="{filename}">
             </video>
             <div class="card-body">
               <p class="card-text">%s</p>
             </div>
           </div>
         </div>
    """


def jpg_tag(filename: str) -> str:
    portrait: dict[str, str] = {}
    panorama: dict[str, str] = {}
    # main
    text = '\n    <div class="card-body%s"><div class="card-text">%s</div></div>\n'
    html = """<div class="col">
      <div class="card">
        <img class="card-img-top%s" src="img/%s">%s
      </div>
    </div>"""
    meta: dict[str, str] = {}  # TODO:
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
    return ""


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
        command = [
            "aws",
            "s3",
            "cp",
            fn,
            f"s3://{s3_bucket}/{fn}",
            "--no-progress",
            "--storage-class",
            "STANDARD_IA",
        ]
        print(" ".join(command))
        if not dry_run:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            print(process.stdout)


def gps_float_to_dms(
    deg_float: float,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Convert decimal degrees to degrees, minutes, seconds."""
    deg_abs = abs(deg_float)
    minutes, seconds = divmod(deg_abs * 3600, 60)
    degrees, minutes = divmod(minutes, 60)

    return (int(degrees), 1), (int(minutes), 1), (int(seconds * 100), 100)


def write_gps_exif(dest: str, lat: float, lng: float):
    # exif sometimes raises an exception when setting fields
    # piexif is more robust
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: gps_float_to_dms(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lng >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: gps_float_to_dms(abs(lng)),
    }
    exif_dict = {"GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)
    print(f"writing {gps_ifd}")

    img = PILImage.open(dest)
    img.save(dest, exif=exif_bytes)
    print(f"wrote {dest}")


def print_gps_exif(dest: str):
    """Print GPS EXIF data from destination image."""
    dest_img = Image(dest)
    fields = set(dest_img.list_all())
    gps_fields = [f for f in fields if f.lower().startswith("gps")]
    for field in gps_fields:
        print(f"{field}\t{getattr(dest_img, field)}")


def copy_gps_exif(src: str, dest: str):
    """Copy GPS EXIF data from source image to destination image."""
    src_img = PILImage.open(src)
    src_exif = piexif.load(src_img.info.get("exif", b""))
    gps_ifd = src_exif.get("GPS")
    if not gps_ifd:
        print(f"{src} has no GPS data.")
        return
    print(f"writing {gps_ifd}")
    dest_img = PILImage.open(dest)
    dest_exif = piexif.load(dest_img.info.get("exif", b""))
    dest_exif["GPS"] = gps_ifd
    dest_img.save(dest, "jpeg", exif=piexif.dump(dest_exif))
    print(f"wrote {dest}")


def to_degrees(deg: float) -> tuple[float, float, float]:
    """Convert decimal degrees to degrees, minutes, seconds."""
    deg_abs = abs(deg)
    minutes, seconds = divmod(deg_abs * 3600, 60)
    degrees, minutes = divmod(minutes, 60)

    return degrees, minutes, seconds


def set_gps_exif(dest: str, lat: float, lng: float):
    write_gps_exif(dest, lat, lng)
