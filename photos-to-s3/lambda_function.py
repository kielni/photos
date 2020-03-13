import json
import os
import requests

import boto3
from dateutil import parser
import google.oauth2.credentials

import google_auth

"""
environment
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    PHOTOS_REFRESH_TOKEN
    PHOTOS_ALBUM_ID
    PHOTOS_BUCKET

photos API: https://github.com/googleapis/google-api-python-client
"""


def get_items(service, album_id, photos):
    items = []
    body = {'pageSize': 100, 'albumId': album_id}
    req = service.mediaItems().search(body=body)
    max_items = int(os.environ.get('MAX_UPLOADS', 100))
    while True:
        results = req.execute()
        print('get_items: results=%s items=%s' % (len(results.get('mediaItems', [])), len(items)))
        #print(' '.join([item['id'][:20] for item in results['mediaItems']]))
        for item in results['mediaItems']:
            if item['id'] in photos:
                continue
            meta = item['mediaMetadata']
            created = parser.parse(meta['creationTime'])
            print('photo %s\t%s' % (item['id'][:40], created.strftime('%Y-%m-%d')))
            items.append({
                'id': item['id'],
                'mimeType': item['mimeType'],
                'created': created,
                'url': '%s=w%s-h%s' % (item['baseUrl'], meta['width'], meta['height'])
            })
            if len(items) >= max_items:
                break
        if not results.get('nextPageToken') or len(items) >= max_items:
            break
        body['pageToken'] = results['nextPageToken']
        req = service.mediaItems().search(body=body)
    print('returning %s new items' % len(items))
    return items


def copy_file(s3, item, suffix=''):
    extensions = {'jpeg': 'jpg'}
    filename = '%s/%s%s.%s' % (
        item['created'].strftime('%Y'),
        item['created'].strftime('%Y-%m-%d_%H%M%S'),
        suffix,
        extensions.get(item['mimeType'].split('/')[1]))
    print('copy %s to %s' % (item['id'][:40], filename))
    req = requests.get(item['url'], stream=True)
    print(s3.put_object(
        Body=req.content,
        Bucket=os.environ['PHOTOS_BUCKET'],
        ContentType=item['mimeType'],
        StorageClass='STANDARD_IA',
        Key=filename))
    return filename


def lambda_handler(event=None, context=None):
    service = google_auth.service()
    s3 = boto3.client('s3')

    # load bucket contents metadata
    manifest = {'photos': {}}
    try:
        data = s3.get_object(
            Bucket=os.environ['PHOTOS_BUCKET'],
            Key='manifest.json')
        if data:
            manifest = json.loads(data['Body'].read())
    except Exception as e:
        print('error loading manifest: %s' % e)
        pass
    photos = manifest['photos']
    print('\n* loaded %s keys\n' % (len(photos)))

    # get album
    album_id = os.environ['PHOTOS_ALBUM_ID']
    if not album_id:
        print('cannot find album %s' % os.environ['PHOTOS_ALBUM_ID'])
        return
    print('\n* looking for album %s\n' % album_id)

    # get items
    items = get_items(service, album_id, photos)
    if not items:
        print('no new items')
        return
    print('%s items' % len(items))
    for idx, item in enumerate(items):
        print('\n%s/%s' % (idx+1, len(items)))
        photos[item['id']] = copy_file(s3, item)
    print(s3.put_object(
        Body=json.dumps(manifest),
        Bucket=os.environ['PHOTOS_BUCKET'],
        ContentType='application/json',
        Key='manifest.json'))
    print('\n* wrote manifest: %s items' % len(manifest['photos']))

if __name__ == '__main__':
    lambda_handler()
