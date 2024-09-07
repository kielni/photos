lint:
	black *.py scripts/*.py
	flake8 *.py scripts/*.py

apple-setup:
    # copy favorited photos and live photos from the last 45 days to staging directory
    # re-encode mov to mp4
    python apple/main.py ~/Pictures/staging

apple-generate:
    # copy photos to S3 and ente sync folder
    python apple/main.py ~/Pictures/staging --sync

site-setup:
    # create directory layout, resize, render HTML, create GeoJSON
    python photos/main.py ~/Pictures/trips/2024-01-01 setup

site-update:
    # update - resize, merge HTML, write GeoJSON
    python photos/main.py ~/Pictures/trips/2024-01-01 update

site-sync:
    # sync site to S3
    python photos/main.py ~/Pictures/trips/2024-01-01 sync
