# photos

## Google Photos to S3

[photos-to-s3](photos-to-s3/lambda_function.py)
copy photos via Google Photos API to AWS S3 bucket

[deploy]((photos-to-s3/deploy.sh) as AWS Lambda function

[token-machine](photos-to-s3/token-machine)
run local service to get tokens via Google OAuth flow

[get album id](photos-to-s3/album_id.py) from album name using Google OAuth tokens

https://developers.google.com/api-client-library/python/
`pip install --upgrade google-api-python-client`


## details

- enable Photos API in Google API console
- generate and download OAuth credentials from Google API console
- copy `client_secret.json` to `token-machine`
- run token machine

    cd token-machine
    pip install -r requirements.txt
    python get_token.py

- authorize application and copy tokens
- set environment variables
  - GOOGLE_CLIENT_ID
  - GOOGLE_CLIENT_SECRET
  - PHOTOS_REFRESH_TOKEN
  - PHOTOS_BUCKET
- get album: run `python album_id.py _album name_` from `photos-to-s3`
- set environment variable PHOTOS_ALBUM_ID
- run (photos-to-s3/lambda_function.py)/lambda_handler
  - get `manifest.json` from S3 bucket
  - get items in Google Photos Album not in manifest
  - copy photos to S3 and add to manifest
  - update manifest file

## docs

[Photos Library API details](https://developers.google.com/resources/api-libraries/documentation/photoslibrary/v1/python/latest/photoslibrary_v1.mediaItems.html#search_next)

[run OAuth flow on command line](https://developers.google.com/api-client-library/python/guide/aaa_oauth)

[Photos library setup](https://developers.google.com/photos/library/guides/get-started) (but doesn't use python client)

[Google Python client library](https://developers.google.com/api-client-library/python/apis/photoslibrary/v1)
