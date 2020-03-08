import argparse
import re

from exif import Image

caption_re = [
    re.compile('.*?acdsee:caption="(.*?)".*', re.DOTALL),
    re.compile('.*?<acdsee:caption>(.*?)</acdsee:caption>.*', re.DOTALL)
]


def extract_xmp(fn):
    data = xmp(fn)
    # xml is annoying and position is inconsistent
    for exp in caption_re:
        match = exp.match(data, re.DOTALL)
        if match:
            return match.group(1)
    return ''


def extract_caption(fn):
    with open(fn, 'rb') as image_file:
        img = Image(image_file)
    try:
        return img.image_description.strip()
    except:
        return ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', type=str, nargs='+', help='Write HTML')
    args = parser.parse_args()

    meta = {}
    for fn in args.filenames:
        meta[fn] = extract_caption(fn) if 'jpg'in fn else ''
    video = {}
    portrait = {
        '20200214_131425_0735_2', '20200214_133439_0739_2', '20200214_140432_9218_2',
        '20200215_110248d2_dscn0032', '20200215_111443d2_dscn0035', '20200215_113226d2_dscn0045',
        '20200215_112239d2_p1250108', '20200215_122709d2_p1220404',
        '20200215_120234d2_p1250113', '20200215_121139d2_p1250114', '20200215_122501d2_p1220398',
        '20200215_122507d2_p1220399', '20200215_122544d2_p1220400', '20200215_122548d2_p1220401',
        '20200215_122709d2_p122040', '20200215_130424d2_p1220432', '20200215_133245d2_p1220424',
        '20200215_134200d2_p1220429', '20200215_135540d2_p1250146', '20200215_135912d2_p1250149',
        '20200215_140453d2_p1250154', '20200215_140705d2_p1220435', '20200215_141215d2_p1220439',
        '20200215_143035d2_p1250173', '20200215_144930d2_p1220476', '20200215_145101d2_p1220481',
        '20200215_145308d2_p1220484', '20200216_194036_0512', '20200217_124007_0926',
        '20200217_124456_0929', '20200217_130233_0932',
        '20200217_134141_0942', '20200217_134150_0544', '20200221_114701_0736',
        '20200221_115813_0743p', '20200221_124921_0748p', '20200221_140639_0767p',
        '20200221_174232_0793p', '20200221_180130_0796p', '20200221_192120_1035',
        '20200222_133331_0806p', '20200222_134613_1048', '20200222_134718_0809p',
        '20200222_135700_0815sp', '20200222_171122_0845p',
        '20200215_110234d2_p1250113', '20200215_124200d2_p1220429',
        '20200215_125540d2_p1250146', 'img/20200215_130453d2_p1250154',
        '20200215_130705d2_p1220435', '20200215_131215d2_p1220439',
        '20200215_134930d2_p1220476', '20200215_135101d2_p1220481',
        '20200218_202259_0601', '20200218_202652_0610'
    }
    panorama = {
        '20200216_140000_0899_2', '20200217_135227_0546', '20200220_154822_0692',
        '20200220_164818_0708'
    }
    # main
    text = '\n    <div class="card-body%s"><div class="card-text">%s</div></div>\n'
    img_html = '''<div class="col-md-12 col-lg-6">
  <div class="card">
    <img class="card-img-top%s" src="img/%s">%s
  </div>
</div>'''
    video_html = '''<div class="col-md-12 col-lg-6">
  <div class="card">
    <video class="card-img-top%s" loop muted playsinline autoplay>
      <source src="mp4/%s">
    </video>
    <div class="card-body">
      <p class="card-text">%s</p>
    </div>
  </div>
</div>
'''
    for key in sorted(meta.keys()):
        name = key.split('.')[0]
        extra = ''
        if name in portrait:
            extra = ' portrait'
        if name in panorama:
            extra = ' panorama'
        caption = text % (extra, meta[key]) if meta[key] else ''
        html = ''
        if 'jpg' in key:
            html = img_html % (extra, key, caption)
        if 'mp4' in key:
            html = video_html % (extra, key, key)
        #print('<!-- %s |%s| -->' % (key, caption))
        print(html)

    print('\n')

if __name__ == '__main__':
    main()
