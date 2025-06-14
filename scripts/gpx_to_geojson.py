import argparse
from typing import Optional

from dateutil import tz
import geopandas as gpd
import gpxpy

"""
Convert GPX files to GeoJSON format.
"""


def main(src: str, tz_str: str = "America/Los_Angeles", route_id: Optional[str] = None):
    dest = src.replace(".gpx", ".geojson")
    local_tz = tz.gettz(tz_str)
    # read gpx to get start time
    with open(src, "r") as f:
        gpx = gpxpy.parse(f)
    start = (
        gpx.tracks[0]
        .segments[0]
        .points[0]
        .time.astimezone(local_tz)
        .strftime("%b %-d, %Y %-I:%M%p")
    )

    # read gpx into geopandas GeoDataFrame
    route = gpd.read_file(src, engine="pyogrio", layer="tracks")
    # geometry is a multilinestring
    route = route[["name", "geometry"]]
    route = route.to_crs("EPSG:4326")
    # name = route["name"][0]
    route["start"] = start
    if route_id:
        route["id"] = route_id
        route["url"] = f"https://www.strava.com/activities/{route_id}"
    route.to_file(dest, driver="GeoJSON")
    print(f"wrote {dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gpx", type=str, help="gpx file path")
    parser.add_argument(
        "--tz",
        type=str,
        default="America/Los_Angeles",
        help="timezone, default: America/Los_Angeles",
    )
    parser.add_argument("--route_id", type=str, help="route id")
    args = parser.parse_args()
    main(args.gpx, args.tz, args.route_id)
