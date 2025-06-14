
# Photos

Select photos to keep, share, and archive.

Break photos out of Apple jail with [osxphotos](https://github.com/RhetTbull/osxphotos),
collect photos from waterproof camera and other people. Set and extract metadata, organize, archive on S3,
create maps, and generate HTML.

## Everyday photos

Mark favorites in Apple Photos, then copy to ~/Pictures/staging:

```
source local.env
make apple-setup
```

Review photos in ~/Pictures/staging and delete unwanted. Archive on S3:
```
make apple-generate
```

## Trip photos

Export photos from all sources to ~/Pictures/trips/yyyy-mm-dd/all.

Review and copy good ones to ~/Pictures/trips/yyyy-mm-dd/album.

Add captions as EXIF description. Add pages to site.yml.

Create directory layout, resize, render HTML, and create GeoJSON:

```
make site-setup
```

Run local server in `web/` and view site on http://localhost:8000

```
python -m http.server
```

Update EXIF descriptions.

Edit photos.

Change selections in ~/Pictures/trips/yyyy-location/album.

Resize, merge HTML, and write GeoJSON:

```
make site-update
```

### Fix issues

#### Missing GPS 

```python site/gps_exif.py ~/Pictures/trips/2025-dest/album/filename.jpg  --print --lat 16.38923 --lng -86.34923```

#### ON1 Photo RAW

ON1 Photo RAW only supports non-destructive edits; this requires re-exporting after edits.

  - Copy files from `all` to `album_orig`; make edits.
  - Export edited files to `album` so that paths are as expected.
  - Set GPS to album since export ignores edits to original.

```
grep GPS update.log  | awk '{ src = $5; gsub("/album/", "/album_orig/", src); print "python site/gps_exif.py --print " $5 " --src " src}'
```

#### EXIF is ASCII

Most EXIF tags (especially older ones like ImageDescription, Artist, etc.) are defined to use ASCII encoding, which only supports characters in the 0–127 range. 

Characters like á (byte 0xC3) are part of UTF-8 or Latin-1, not plain ASCII 

#### Compress GeoJSON

Browsers can handle compressed files; set the filename and metadata to make this work:

```
cp photos.json photos_gz.json
gzip photos_gz.json
mv photos_gz.json.gz photos_gz.json
ls -lh photos*
```

## Tools

### Convert heic to jpg

```
mogrify -format jpg *.heic
```

### VLC preferences

  - Video: uncheck Show video within the main window
  - Interface | Main interface: uncheck Resize interface to the native video size
  - Playlist: check Play and pause

### LivePhotos

Re-encode, drop audio, and resize:

```
ls *.mov | awk -F '.' '{ print $1 }' | xargs -I {} ffmpeg -i {}.mov -an -s 768x576 {}.mp4
```

See [LivePhotos for the web](https://medium.com/@kielnicholls/embedding-livephotos-on-a-web-page-5dfa9b8b83e3).

Tag for LivePhotos

```
<video loop muted playsinline autoplay>
  <source src="img/IMG_1561.mp4">
</video>
```

## Initial setup

```
pip install -r requirements.txt
```

Download [ExifTool](https://exiftool.org)
Install [ffmpeg](https://ffmpeg.org)
