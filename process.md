# photo website process

## photos

### export

from iPhone
  - AirDrop to ~/Downloads
  - copy to /Volumes/media/Pictures/event

from iCloud
  - Export | Unmodified original
  - copy to /Volumes/media/Pictures/event

convert heic to jpg
  - `brew install --with-libheif imagemagick`
  - `mogrify -format jpg *.heic`

### select

  - in ACDSee, sort by date taken
  - select photos by adding a rating
  - copy rated photos to `album` directory (parallel to `event`)
  - rename to add date prefix from exif: IMG_123.jpg to 20200301_1200_123.jpg with `scripts/rename_exif_date.py`

### jpg

  - add captions in EXIF description
  - edit / crop (original aspect ratio)
  - rotate if browser rotates based on EXIF: `magick 20200215_143035d2_p1250173.jpg -rotate 90 20200215_143035d2_p1250173.jpg`

### LivePhoto

See [LivePhotos for the web](https://medium.com/@kielnicholls/embedding-livephotos-on-a-web-page-5dfa9b8b83e3)

#### select

  - download `.mov` files to file server `Pictures/year/topic`
  - VLC: Video | Half size, Preferences | Video | uncheck Show video within the main window
  - open in VLC and select
  - copy to `selected`

#### re-encode and resize

`ls *.mov | awk -F '.' '{ print $1 }' | xargs -I {} ffmpeg -i {}.mov -an -s 768x576 {}.mp4`

#### HTML

```
<video loop muted playsinline autoplay>
  <source src="img/IMG_1561.mp4">
</video>
```

## web

  - resize: `mogrify -path img -resize 800x800 -format jpg *.jpg`
  - update `exif_to_html.py` with portrait and panorama keys
  - run `exif_to_html.py *.jpg > content.html` to generate HTML with captioned photos

## publish

  - copy to file server: /Volumes/media/web/trips/event
  - sync to S3: `./sync.sh`
