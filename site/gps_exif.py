import argparse

from util.photos import set_gps_exif, copy_gps_exif, print_gps_exif

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dest", type=str)
    parser.add_argument("--src", type=str)
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lng", type=float)
    parser.add_argument("--print", action="store_true")
    parser.add_argument("--latlng", type=str)
    args = parser.parse_args()
    if args.lat is not None and args.lng is not None:
        set_gps_exif(args.dest, args.lat, args.lng)
    if args.latlng:
        # 15.74976, -86.75745
        (_lat, _lng) = args.latlng.split(",")
        set_gps_exif(args.dest, float(_lat), float(_lng))
    if args.src:
        copy_gps_exif(args.src, args.dest)
    if args.print:
        print_gps_exif(args.dest)
