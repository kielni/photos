import os

from apiclient.discovery import build
import google.oauth2.credentials

import google_auth

def service():
    credentials = google.oauth2.credentials.Credentials(
        'access_token',
        refresh_token=os.environ['PHOTOS_REFRESH_TOKEN'],
        token_uri='https://accounts.google.com/o/oauth2/token',
        client_id=os.environ['GOOGLE_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_CLIENT_SECRET'])
    return build('photoslibrary', 'v1', credentials=credentials)
