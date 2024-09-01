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


def setup_pages(site: dict, current: str) -> dict:
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
    for el in tqdm(elements):
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

    for el_id in tqdm(to_add):
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
    return decimal if direction in "NE" else -decimal


def extract_exif(filename: str, size: int) -> dict:
    """Extract EXIF data from filename."""
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
        degrees, minutes, seconds = gps_info.get(
            GPS.GPSLongitude
        )  # (37.0, 25.0, 19.34)
        ref = gps_info.get(GPS.GPSLongitudeRef)  # 'E'
        context["longitude"] = degrees_to_decimal(degrees, minutes, seconds, ref)
    except Exception as e:
        context["error"] = f"error reading EXIF data from {filename}: {e}"
    return context


def render_photos(
    path: str, min_fn: str, max_fn: str, size: int, add_day_markers: bool = False
) -> List[str]:
    """Create list of card HTML by merging files between min_fn and max_fn with card template.

    Set in context: id, filename
    Add from EXIF if available: orientation, description, latitude, longitude
    """
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    card_template = env.get_template(f"card.jinja2")
    video_template = env.get_template(f"card_video.jinja2")
    day_template = env.get_template("day.jinja2")
    day_open_template = env.get_template("day_open.jinja2")
    day_close_template = env.get_template("day_close.jinja2")
    cards: List[str] = []
    filenames = sorted(os.listdir(f"{path}/album"))
    # get filenames between page["start"] and page["end"]
    filenames = [f for f in filenames if f >= min_fn and f <= max_fn]
    prev_day = None
    curr_day = None
    messages: List[str] = []
    for filename in tqdm(filenames):
        if match := re.search(r"(\d{8})_", filename):
            curr_day = match.group(1)
        if add_day_markers and curr_day and curr_day != prev_day:
            day_html = ""
            day_context = {"day": curr_day}
            if prev_day is not None:
                day_html = day_close_template.render(day_context)
            day_html += day_open_template.render(day_context)
            day_html += day_template.render(day_context)
            messages.append(f"adding day marker for {curr_day}")
            cards.append(day_html)
            prev_day = curr_day
        context = {
            "id": f"p-{filename.split('.')[0]}",  # id can't start with a number
            "filename": filename,
            "orientation": "landscape",
        }
        if filename.endswith(".jpg"):
            extra = extract_exif(f"{path}/album/{filename}", size)
            context.update(extra)
            if extra.get("error"):
                messages.append(extra["error"])
            card_html = card_template.render(context)
        else:
            messages.append(f"copying non-jpg file to {path}/web/img/{filename}")
            shutil.copy(f"{path}/album/{filename}", f"{path}/web/img/{filename}")
            card_html = video_template.render(context)
        cards.append(card_html)
    if add_day_markers and curr_day:
        cards.append(day_close_template.render({"day": curr_day}))
    print("\n".join(messages))
    return cards


def load_site(path: str) -> dict:
    with open(f"{path}/site.yml", "r") as f:
        return yaml.safe_load(f)
    # TODO: validate


def write_html(filename: str, html: str):
    print(f"Writing {filename}")
    with open(f"{filename}", "w") as f:
        f.write(html)


def render_index(path: str, context: dict):
    """Generate index.html by merging templates/index.jinja2 with context."""
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    # generate body of index.html and save as context
    context["pages"] = setup_pages(context, "index")
    context["content"] = env.get_template("index_body.jinja2").render(context)
    # merge index content with frame
    html = env.get_template("frame.jinja2").render(context)
    write_html(f"{path}/web/index.html", html)


def render_pages(path: str, initial: bool = False, page_name: Optional[str] = None):
    """Generate HTML for pages."""
    env = Environment(loader=FileSystemLoader(f"{path}/templates"))
    context = load_site(path)
    if initial:
        # TODO: merge? if contents of site changed; or ignore for now
        render_index(path, context)
    for page in context["pages"]:
        page_id = page["id"]
        if not initial and page_name and page_id != page_name:
            continue
        out_fn = f"{path}/web/{page_id}.html"
        print(f"Rendering {out_fn}")
        # generate page content
        context["pages"] = setup_pages(context, page_id)
        cards = render_photos(
            path,
            page["start"],
            page["end"],
            context["img_size"],
            add_day_markers=initial,
        )
        if initial:
            context["content"] = "\n".join(cards)
        else:
            context["content"] = merge_cards(out_fn, cards)
        # merge with frame
        context["content"] = env.get_template(f"page_body.jinja2").render(context)
        html = env.get_template("frame.jinja2").render(context)
        write_html(out_fn, html)
    os.system(f"npx prettier --write {path}/web/*.html")
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
    # copy map.js and style.css to path/web
    for key in ["map.js", "style.css"]:
        print(f"Copying {key} to {path}/web")
        shutil.copy(f"templates/{key}", f"{path}/web")
    # recursively copy templates to path/
    print(f"Copying templates to {path}")
    # copy templates/*.jinja2 to path/templates
    for filename in glob.glob("templates/*.jinja2"):
        shutil.copy(filename, f"{path}/templates")
    print(f"Copying support to {path}")
    shutil.copytree("templates/support", f"{path}/web/support", dirs_exist_ok=True)
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
