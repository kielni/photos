lint:
	black *.py scripts/*.py
	flake8 *.py scripts/*.py

# monthly
# make apple-setup
# review photos in ~/Pictures/staging
# make apple-generate

apple-setup:
    # copy favorited photos and live photos from the last 45 days to staging directory
    # re-encode mov to mp4
    python apple/main.py ~/Pictures/staging

apple-generate:
    # copy photos to S3 and ente sync folder
    python apple/main.py ~/Pictures/staging --sync


