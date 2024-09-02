import argparse
import glob
import os
import re
import shutil
from typing import List, Dict, Any, Set, Optional

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from PIL import Image, ImageOps
from PIL.ExifTags import Base
from PIL.ExifTags import GPS
from tqdm import tqdm
import yaml

"""
site.yml
  path - path leaf ("2024-Tanzania")
  destination
  highlight_image
  path

page
  page.id - page key
  page.text
  page.active - set when generating

cards
  card.id
  card.orientation
  card.filename
  card.description
"""


def set_active_page(site: dict, current: str) -> dict:
    for page in site["pages"]:
        page["active"] = "active" if page["id"] == current else ""
    return site["pages"]


def merge_cards(filename: str, cards: List[str]) -> str:
    """Merge edited html with generated photo cards.

    merge elements with data-source="file"
      - if id exists in cards but not in html, add where id is greater than previous
      - if id exists in html but not in cards, remove
      - if id exists in both, replace with cards version
    """
    attrs = {"data-source": "file"}
    parsed_cards = [BeautifulSoup(card, "html.parser") for card in cards]
    # each element in array is a BeautifulSoup object; use find to get the
    # containing div
    card_ids: Set[str] = set()
    cards_by_id: Dict[str, BeautifulSoup] = {}
    for card in parsed_cards:
        el = card.find(attrs=attrs)
        card_id = el.get("id")
        card_ids.add(card_id)
        cards_by_id[card_id] = el
    with open(filename, "r") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.find_all(attrs=attrs)
    html_ids = set([el.get("id") for el in elements])
    to_add: List[str] = sorted(list(card_ids - html_ids))
    prev_el = None
    messages: List[str] = []
    for el in elements:
        # if id exists in html but not in cards, remove
        if el.get("id") and el.get("id") not in cards_by_id:
            messages.append(f"removing {el.get('id')}; not in album")
            el.decompose()
            continue
        # if id exists in cards but not in html, add where id is greater than previous
        if to_add and to_add[0] < str(el.get("id")):
            add_after = prev_el if prev_el else el
            messages.append(f"adding card {to_add[0]} after {add_after.get('id')}")
            card = cards_by_id.get(to_add.pop(0))
            add_after.append(card)
        prev_el = el
        # if id exists in both, replace with cards version
        # messages.append(f"updating card {el.get('id')}")
        # print(".", end="")
        el.replace_with(cards_by_id.get(el.get("id")))

    for el_id in to_add:
        messages.append(f"adding card {el_id} after {prev_el.get('id')}")
        prev_el.append(cards_by_id.get(el_id))
    print("\n".join(messages))
    # only return the content section
    content = soup.find(attrs={"data-source": "files"})
    return str("\n".join([str(el) for el in content.children]))


def degrees_to_decimal(
    degrees: float, minutes: float, seconds: float, direction: str
) -> float:
    """Convert degrees, minutes, seconds to decimal."""
    decimal = float(degrees + minutes / 60 + seconds / 3600)
    # round to 5 decimals (1 meter)
    decimal = round(decimal, 5)
    return decimal if direction in "NE" else -decimal


def read_exif_resize(filename: str, size: int) -> dict:
    """Extract EXIF data from filename and write resized image to web/img."""
    context: Dict[str, Any] = {"error": None}
    try:
        img = Image.open(filename)
        # filename is full path
        new_filename = filename.replace("/album/", "/web/img/")
        ImageOps.contain(img, [size, size]).save(new_filename)
        context["orientation"] = "landscape" if img.width > img.height else "portrait"
        exif_data = img.getexif()
        context["description"] = exif_data.get(Base.ImageDescription, "").strip()
        gps_info = exif_data.get_ifd(Base.GPSInfo)
        degrees, minutes, seconds = gps_info.get(GPS.GPSLatitude)  # (6.0, 45.0, 54.34)
        ref = gps_info.get(GPS.GPSLatitudeRef)  # 'S'
        context["latitude"] = degrees_to_decimal(degrees, minutes, seconds, ref)
        degrees, minutes, seconds = gps_info.get(GPS.GPSLongitude)  # (37.0, 2.0, 9.34)
        ref = gps_info.get(GPS.GPSLongitudeRef)  # 'E'
        context["longitude"] = degrees_to_decimal(degrees, minutes, seconds, ref)
        context["altitude"] = round(float(gps_info.get(GPS.GPSAltitude, 0)), 5)
    except Exception as e:
        context["error"] = f"{filename}: invalid EXIF data: {e}"
    return context


def open_day(path: str, curr_day: str) -> str:
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    return env.get_template("day_open.jinja2").render({"day": curr_day})


def close_day(path: str, curr_day: str) -> str:
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    return env.get_template("day_close.jinja2").render({"day": curr_day})


def render_new_day(path: str, curr_day: str, prev_day: str) -> str:
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    html = close_day(path, curr_day) if prev_day else ""
    template = env.get_template("day.jinja2")
    return html + open_day(path, curr_day) + template.render({"day": curr_day})


def render_active_page(path: str, context: dict, initial: bool):
    """Render HTML from list of context objects in page_data.

    Render card HTML for each object in page_data. Add day markers between
    dates if initial run.
    """
    page_id = context["active_page"]
    out_fn = f"{path}/web/{page_id}.html"
    print(f"Rendering {out_fn}")

    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    card_template = env.get_template("card.jinja2")
    video_template = env.get_template("card_video.jinja2")
    cards: List[str] = []
    prev_day = curr_day = ""
    messages: List[str] = []

    for file_context in tqdm(context["page_data"], desc="render"):
        filename = file_context["filename"]
        if match := re.search(r"(\d{8})_", filename):
            curr_day = match.group(1)
        if initial and curr_day and curr_day != prev_day:
            messages.append(f"adding day marker for {curr_day}")
            cards.append(render_new_day(path, curr_day, prev_day))
        prev_day = curr_day
        if filename.endswith(".jpg"):
            cards.append(card_template.render(file_context))
        else:
            cards.append(video_template.render(file_context))

    if initial:
        if curr_day:
            cards.append(close_day(path, curr_day))
        context["content"] = "\n".join(cards)
    else:
        context["content"] = merge_cards(out_fn, cards)
    # create content body
    body_html = env.get_template("page_body.jinja2").render(context)
    context["content"] = body_html
    # merge with frame
    write_file(out_fn, env.get_template("frame.jinja2").render(context))


def gather_page_data(path: str, min_fn: str, max_fn: str, img_size: int) -> List[dict]:
    """Get data for each file between min_fn and max_fn.

    Return a dictionary for each file, containing id, filename, orientation. If available,
    get description, latitude, longitude, and altitude from EXIF data.
    Resize and copy files from album to web/img.
    """
    filenames = sorted(os.listdir(f"{path}/album"))
    # get filenames between min_fn and max_fn
    filenames = [f for f in filenames if min_fn <= f <= max_fn]
    messages: List[str] = []
    contexts: List[dict] = []
    for filename in tqdm(filenames, desc="gather"):
        context = {
            "id": f"p-{filename.split('.')[0]}",  # id can't start with a number
            "filename": filename,
            "orientation": "landscape",
        }
        if filename.endswith(".jpg"):
            extra = read_exif_resize(f"{path}/album/{filename}", img_size)
            context.update(extra)
            if extra.get("error"):
                messages.append(extra["error"])
        else:
            messages.append(f"copying non-jpg file to {path}/web/img/{filename}")
            shutil.copy(f"{path}/album/{filename}", f"{path}/web/img/{filename}")
        contexts.append(context)
    print("\n".join(messages))
    return contexts


def load_site(path: str) -> dict:
    with open(f"{path}/site.yml", "r") as f:
        return yaml.safe_load(f)
    # TODO: validate


def write_file(filename: str, html: str):
    print(f"Writing {filename}")
    with open(f"{filename}", "w") as f:
        f.write(html)


def render_index(path: str, context: dict):
    page = "index"
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    context["pages"] = set_active_page(context, page)
    context["content"] = env.get_template(f"{page}.jinja2").render(context)
    # merge index content with frame
    html = env.get_template("frame.jinja2").render(context)
    write_file(f"{path}/web/{page}.html", html)


def render_map(path: str, context: dict):
    page = "map"
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    context["pages"] = set_active_page(context, page)
    html = env.get_template(f"{page}.jinja2").render(context)
    write_file(f"{path}/web/{page}.html", html)


def render_pages(path: str, initial: bool = False, page_name: Optional[str] = None):
    """Generate HTML for pages."""
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    context = load_site(path)
    if initial:
        # TODO: merge? if contents of site changed; or ignore for now
        render_index(path, context)
        render_map(path, context)
    all_data: List[dict] = []
    for page in context["pages"]:
        print(f"\nStarting page {page['id']}: {page['start']} to {page['end']}")
        page_id = page["id"]
        context["active_page"] = page_id
        if page_name and page_id != page_name and not initial:
            continue
        # generate page content
        context["pages"] = set_active_page(context, page_id)
        page_data = gather_page_data(
            path, page["start"], page["end"], context["img_size"]
        )
        # print(f"{len(page_data)} files for {page_id}")
        context["page_data"] = page_data
        all_data += page_data
        render_active_page(path, context, initial)
    if not page_name:
        # only render geojson with complete data
        geo_data = [f for f in all_data if "latitude" in f and "longitude" in f]
        geo_json = env.get_template("geojson.jinja2").render({"features": geo_data})
        write_file(f"{path}/web/photos.json", geo_json)
    os.system(f"npx prettier --write {path}/web/*.html {path}/web/*.json")
    # TODO: git


def update(path: str, page_name: Optional[str]):
    """Rewrite HTML and GeoJSON from EXIF data."""
    # TODO: check in current HTML
    render_pages(path, initial=False, page_name=page_name)
    # TODO: write GeoJSON
    # TODO: check in new HTML


def setup(path: str):
    """Create layout, resize photos, create GeoJSON.

    path to .../yyyy-location directory. Must exist under path:
      site.yml - defines site layout
      album/ - original photos

    Create directory layout
      templates/ - copy of templates from this module
      web/
        img/ - resized photos
        index.html - generated from templates/index.jinja2
        photos.json - photo locations in GeoJSON format
        style.css
        html file for each key in site.yml pages
        support/ - copy from templates/support in this module

    Initialize local git in web/ and check in files.
    """
    # create web directory under path if it does not exist
    try:
        print(f"Creating {path}/web")
        os.mkdir(f"{path}/web")
    except FileExistsError:
        pass
    # create img/ directory under web if it does not exist
    try:
        os.mkdir(f"{path}/web/img")
    except FileExistsError:
        pass
    print("Copying templates")
    for pattern in ["*.png", "*.html", "*.js", "*.css"]:
        for filename in glob.glob(f"templates/{pattern}"):
            shutil.copy(filename, f"{path}/web")
    for filename in glob.glob("templates/*.jinja2"):
        shutil.copy(filename, f"{path}/templates")
    shutil.copytree("templates/support", f"{path}/web/support", dirs_exist_ok=True)
    shutil.copytree("templates/icons", f"{path}/web/icons", dirs_exist_ok=True)
    render_pages(path, initial=True)

    # setup git
    """
    print(f"Initializing git in {path}/web")
    os.chdir(f"{path}/web")
    os.system("git init")
    os.system("git add .")  # TODO: add or exclude img? big but can use for diffs
    os.system("git commit -m 'Initial commit'")
    """


def main(path: str, op: str, page_name: Optional[str]):
    if op == "setup":
        setup(path)
    elif op == "update":
        update(path, page_name)
    else:
        print(f"Unknown operation: {op}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str)
    """
    setup - create directory layout, resize, render HTML, create GeoJSON
    update - resize, merge HTML, write GeoJSON
    """
    parser.add_argument("op", type=str, help="setup, update")
    parser.add_argument("--page", type=str, help="update only specified page")
    args = parser.parse_args()
    main(args.path, args.op, args.page)
