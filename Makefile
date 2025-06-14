lint:
	black *.py */*.py
	flake8 *.py */*.py

# copy favorited photos and live photos from the last 45 days to staging directory
# re-encode mov to mp4
apple-setup:
	python apple/main.py

# copy photos to S3 and ente sync folder
apple-generate:
	python apple/main.py --sync

site-start:
	cp site/site.yml ~/Pictures/trips/2024-01-01/site.yml
	echo "edit site.yml then run make site-setup"

# create directory layout, resize, render HTML, create GeoJSON
site-setup:
	cd site
	python main.py ~/Pictures/trips/2024-01-01 setup

# update - resize, merge HTML, write GeoJSON
site-update:
	cd site
	python main.py ~/Pictures/trips/2024-01-01 update

# sync site to S3
site-sync:
	cd site
	python main.py ~/Pictures/trips/2024-01-01 sync
