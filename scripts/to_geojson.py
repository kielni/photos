import argparse
import json

from exif import Image


def extract_caption(fn):
    with open(fn, "rb") as image_file:
        img = Image(image_file)
    try:
        return img.image_description.strip()
    except Exception:
        return ""


def main(filename: str, lat_hemi: str, lng_hemi: str, trailing_comma: bool):
    lat_multiplier = -1 if lat_hemi == "S" else 1
    lng_multiplier = -1 if lng_hemi == "W" else 1
    with open(filename, "rb") as f:
        img = Image(f)
    (lat_deg, lat_min, lat_sec) = img.gps_latitude
    (lng_deg, lng_min, lng_sec) = img.gps_longitude
    lat = (lat_deg + (lat_min / 60 + lat_sec / 3600)) * lat_multiplier
    lng = (lng_deg + (lng_min / 60 + lng_sec / 3600)) * lng_multiplier
    altitude = img.gps_altitude if hasattr(img, "gps_altitude") else 0
    out = {
        "geometry": {"coordinates": [lng, lat, altitude], "type": "Point"},
        "properties": {"image": filename, "icon": "photo"},
        "type": "Feature",
    }
    description = extract_caption(filename)
    if description:
        out["properties"]["description"] = description
    extra = "," if trailing_comma else ""
    print(f"{json.dumps(out, indent=2)}{extra}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    # force sign on lat/lng if gps_latitude_ref/gps_longitude_ref is unavailable
    parser.add_argument("--lat", type=str, help="N or S")
    parser.add_argument("--lng", type=str, help="E or W")
    # for cut and paste into a geojson file
    parser.add_argument("--trailing_comma", action="store_true")
    args = parser.parse_args()
    main(args.filename, args.lat, args.lng, args.trailing_comma)
