import glob
import os
import re
from exif import Image

"""
    rename jpg files with prefix from Exif datetime field:
      IMG_123.jpg to 20200301_1200_123.jpg
"""

def rename_exif(orig):
    with open(orig, 'rb') as image_file:
        img = Image(image_file)
    # 2020:02:23 14:12:03
    dt = img.datetime.replace(' ', '_').replace(':', '')
    fn = re.sub('.*?_IMG', '', orig.replace(' ', '_'))
    updated = (dt+fn).lower()
    updated = updated.replace('.jpg', 'p.jpg')
    print('rename', orig, updated)
    os.rename(orig, updated)


def rename(orig):
    # 20190221_143905d8_dscn0245.jpg
    os.rename(orig, orig.replace('img', ''))

for fn in glob.glob('*.jpg'):
    if 'jpg' in fn.lower():
        rename(fn)
