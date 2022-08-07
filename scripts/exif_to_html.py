import argparse
import re

from exif import Image

caption_re = [
    re.compile('.*?acdsee:caption="(.*?)".*', re.DOTALL),
    re.compile(".*?<acdsee:caption>(.*?)</acdsee:caption>.*", re.DOTALL),
]


def xmp(fn):
    with open(fn, "rb") as imgf:
        data = imgf.read()
    xmp_start = data.find(b"<x:xmpmeta")
    xmp_end = data.find(b"</x:xmpmeta")
    return data[xmp_start : xmp_end + 12].decode("utf-8")


def extract_xmp(fn):
    data = xmp(fn)
    # xml is annoying and position is inconsistent
    for exp in caption_re:
        match = exp.match(data, re.DOTALL)
        if match:
            return match.group(1)
    return ""


def extract_caption(fn):
    with open(fn, "rb") as image_file:
        img = Image(image_file)
    try:
        return img.image_description.strip()
    except:
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", type=str, nargs="+", help="Write HTML")
    args = parser.parse_args()

    meta = {}
    for fn in args.filenames:
        meta[fn] = extract_caption(fn) if "jpg" in fn else ""
        if not meta[fn]:
            meta[fn] = extract_xmp(fn) if "jpg" in fn else ""
    video = {}
    portrait = {}
    panorama = {}
    # main
    text = '\n    <div class="card-body%s"><div class="card-text">%s</div></div>\n'
    img_html = """<div class="col">
  <div class="card">
    <img class="card-img-top%s" src="img/%s">%s
  </div>
</div>"""
    video_html = """<div class="col">
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


if __name__ == "__main__":
    main()
