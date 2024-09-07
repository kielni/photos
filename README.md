
# photos

Select photos to keep, share, and archive.

## !! new
apple - extract favorites from Apple Photos, add metadata, archive to S3, and sync with Ente

site - generate static site from photos and their metadata
## end new

## everyday photos

Copy favorited photos from Photos to ~/Pictures/staging:

```
make apple-setup
```

Review photos in ~/Pictures/staging and delete unwanted.

Copy to S3:
```
make apple-generate
```

## trip photos

Export photos from all sources to ~/Pictures/trips/yyyy-mm-dd/all. Review and copy good ones
to ~/Pictures/trips/yyyy-mm-dd/album.

Add captions as EXIF description. Add pages to site.yml.

Create directory layout, resize, render HTML, and create GeoJSON.

```
make site-setup
```

Run local serer and review http://localhost:8000

```
python -m http.server
```

Update EXIF descriptions, edit photos, a nd change selections in ~/Pictures/trips/yyyy-mm-dd/album.

Resize, merge HTML, and write GeoJSON.

```
make site-update
```

## tools

### convert heic to jpg

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

See [LivePhotos for the web](https://medium.com/@kielnicholls/embedding-livephotos-on-a-web-page-5dfa9b8b83e3)

Tag for LivePhotos

```
<video loop muted playsinline autoplay>
  <source src="img/IMG_1561.mp4">
</video>
```
