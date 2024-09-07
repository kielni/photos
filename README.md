
# photos

Goal: select photos to keep, share, and archive efficiently and consistently.

## overview

Get photos from phones and waterproof camera to Mac.
Select the good ones and copy to Amazon Photos album (for sharing) and S3 (for archiving).
For trips, add captions, generate HTML, and resize for web.
Delete uninteresting old photos from phone and Amazon Photos.

Select photos form iPhone photos: rate, then copy to staging
Copy all from staging to to staging/to-family-share
From iPhoto
  - import from staging/to-family-share
  - from Imports, share to Family share
  - ?? remove duplicates: sort by date taken
  - export unmodified originals to family-share-export
Move family-share-export/* to staging
Batch rename with Exif datetime filename
Sort by filename
De-dupe

### everyday photos

  - Copy photos from phones (automatically) and waterproof camera (manually) to Mac.
  - Review photos with ACDSee and add a rating to the good ones.
  - Copy rated photos to `~/Pictures/staging` directory.
  - Standardize filenames to `datetime-index.ext`.
  - Move to <code>~/Pictures/amazon-keep/_year_</code> to sync to Amazon Photos album.
  - Sync to <code>s3://photos-bucket/_year_</code> for archiving.
  - Delete photos over 2 years old from `~/Pictures/amazon-phone`.

### trip photos

  - Copy photos from phones (automatically) and waterproof camera (manually) to a trip directory on Mac: <code>~/Pictures/trips/_year-destination_/all</code>.
  - Review photos with ACDSee and add a rating to the good ones.
  - Copy rated photos to <code>~/Pictures/trips/_year-destination_/album</code> directory.
  - Standardize filenames to `datetime-index.ext`: `python rename_exif_date.py`
  - Re-encode LivePhotos: `python mov_to_mp4.py`
  - Crop, edit, and add captions to Exif metadata.
  - Sync `album` to <code>s3://photos-bucket/_year-destination_</code> for archiving.
  - Resize for website to <code>~/Pictures/trips/_year-destination_/web</code> directory.
  - Generate HTML by merging a template with filenames and captions from Exif metadata.

## setup

### directory layout

from `~/Pictures`

  - `amazon-keep` -> `amazon-sync/Amazon\ Drive/keep/amazon-photos` - photos for sharing
    - `2021` - one directory per year
      - `2021-09-01_070723_414.jpg` - filename is datetime and number from camera
    - `2021-Grand-Canyon` - full size photos, one directory per trip
  - `amazon-phone` -> `amazon-sync/Amazon\ Drive/Pictures` - Amazon Photos apps sync phone and Mac
    - `Kimberly's\ iPhone`
  - `staging` - to be synced to Amazon Photos and S3
  - `trips` - trip photos, website, photo books
    - `2021-Grand-Canyon`
      - `all` - all photos from all sources
      - `album` - selected photos
      - `web` - photos resized for web, html, css, and support files

### tools
  - [icloudpd](https://github.com/icloud-photos-downloader/icloud_photos_downloader) to get LivePhotos from iCloud to local filesystem
  - [exif](https://pypi.org/project/exif/) python package to get Exif metadata from photos
  - [imagemagick](https://imagemagick.org/index.php) to convert `heic` to `jpg`
  - [ffmpeg](https://www.ffmpeg.org/) to re-encode video
  - [ACDsee Photo Studio](https://www.acdsee.com/en/products/photo-studio-mac/) for reviewing, editing, and captioning photos
  - [Amazon Photos](https://apps.apple.com/us/app/amazon-photos/id621574163) to sync photos from phones and share full-size photos with limited audience
  - [VLC](https://www.videolan.org/) for viewing videos

```
pip install -r util/requirements.txt
brew install --with-libheif imagemagick
brew install ffmpeg
```

## to Mac

### photos from iPhones
  - automatic: Amazon Photos app syncs from phone to `~/Pictures/amazon-phone`
  - manual: AirDrop to <code>~/Pictures/trips/_year-destination_/all</code>
  - from iCloud:
    - Export | Unmodified original
    - copy to <code>~/Pictures/trips/_year-destination_/all</code>

### LivePhotos from iCloud
  - download from Live album to `icloud-live-photos`
  - re-encode to mp4, drop audio, rename with datetime in name, move to single directory (from nested)

```
icloudpd --directory $PHOTOS_ROOT/icloud-live-photos --username $ICLOUD_USERNAME -a Live --until-found 3
python monthly.py --prep
```

### convert heic to jpg

```
mogrify -format jpg *.heic
```

## select

### jpg

  - create <code>~/Pictures/trips/_year-destination_/album</code> directory
  - rename with EXIF date: `python photos/scripts/rename_exif_date.py`
  - in ACDSee, sort by name
  - select photos by adding a rating
  - copy rated photos to `album` (trips) or `staging` (everyday)


### LivePhotos

VLC preferences
  - Video: uncheck Show video within the main window
  - Interface | Main interface: uncheck Resize interface to the native video size
  - Playlist: check Play and pause

Drag all .mov to VLC.  Copy good ones to <code>~/Pictures/trips/_year-destination_/album</code>

## process

### jpg

  - add captions in Exif description
  - edit / crop (original aspect ratio)
  - rotate if browser rotates based on Exif

```
magick 20200215_143035d2_p1250173.jpg -rotate 90 20200215_143035d2_p1250173.jpg
```

### LivePhotos

Re-encode, drop audio, and resize:

trips:

```
ls *.mov | awk -F '.' '{ print $1 }' | xargs -I {} ffmpeg -i {}.mov -an -s 768x576 {}.mp4
```

See [LivePhotos for the web](https://medium.com/@kielnicholls/embedding-livephotos-on-a-web-page-5dfa9b8b83e3)

## export

Export full size photos
  - rename with date prefix
  - copy from `album` to <code>amazon-keep/_year-destination_</code> to sync to Amazon Photos.
  - sync `album` to <code>s3://photos-bucket/_year-destination_</code> for archiving.

everyday:

```
python monthly.py
```


Copy to <code>~/Pictures/trips/_year-destination_/web</code> and resize:

```
mogrify -path img -resize 800x800 -format jpg *.jpg
```

Generate html from template and files

```
python exif_to_html.py *.jpg > content.html
```

Tag for LivePhotos

```
<video loop muted playsinline autoplay>
  <source src="img/IMG_1561.mp4">
</video>
```

Review web version from localhost:8000

```
cd web
python -m http.server
```

Publish: sync `web` to <code>s3://website-bucket/_year-destination_</code>

aws s3 cp s3://$WEB_BUCKET/ s3://$WEB_BUCKET/ --exclude "*" --include "*.jpg" --include "*.png" --include "*.mp4" --recursive --metadata-directive REPLACE --acl public-read --cache-control max-age=2592000,public --dry-run


https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/getting-started-cloudfront-overview.html

GeoJSON from EXIF: `python to_geojson.py filename --lat S --trailing_comma`

```
ls img/*.jpg | xargs -L 1 python ~/home/photos/scripts/to_geojson.py --lat S --trailing_comma | tee photo.json
cp tanzania.json tanzania_gz.json
gzip tanzania_gz.json
mv tanzania_gz.json.gz tanzania_gz.json
aws s3 cp tanzania.json s3://paulandkimberly.com/2024-Tanzania/tanzania.json --content-encoding gzip --content-type application/json
aws s3 cp tanzania.json s3://www.paulandkimberly.com/2024-Tanzania/tanzania.json --content-encoding gzip --content-type application/json
aws s3 cp tanzania_gz.json s3://paulandkimberly.com/2024-Tanzania/tanzania_gz.json --content-encoding gzip --content-type application/json
aws s3 cp tanzania_gz.json s3://www.paulandkimberly.com/2024-Tanzania/tanzania_gz.json --content-encoding gzip --content-type application/json
```
