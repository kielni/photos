import json
import os
import requests

import boto3
from dateutil import parser
import google.oauth2.credentials

import google_auth

'''
environment
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    PHOTOS_REFRESH_TOKEN
    PHOTOS_ALBUM_ID
    PHOTOS_BUCKET
'''


def get_items(service, album_id, photos):
    items = []
    req = service.mediaItems().search(body={
        'pageSize': 500,
        'albumId': album_id
    })
    while req:
        results = req.execute()
        print('get_items: results=%s' % len(results.get('mediaItems', [])))
        for item in results['mediaItems']:
            if item['id'] in photos:
                continue
            meta = item['mediaMetadata']
            print('photo %s' % item['id'])
            items.append({
                'id': item['id'],
                'mimeType': item['mimeType'],
                'created': parser.parse(meta['creationTime']),
                'url': '%s=w%s-h%s' % (item['baseUrl'], meta['width'], meta['height'])
            })
        req = service.mediaItems().search_next(req, results)
    print('returning %s new items' % len(items))
    return items


def copy_file(s3, item, suffix=''):
    extensions = {'jpeg': 'jpg'}
    filename = '%s%s.%s' % (
        item['created'].strftime('%Y-%m-%d_%H%M%S'),
        suffix,
        extensions.get(item['mimeType'].split('/')[1]))
    print('copy %s to %s' % (item['id'], filename))
    req = requests.get(item['url'], stream=True)
    print(s3.put_object(
        Body=req.content,
        Bucket=os.environ['PHOTOS_BUCKET'],
        ContentType=item['mimeType'],
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
    print('\n* found album %s\n' % album_id)

    # get items
    items = get_items(service, album_id, photos)
    if not items:
        print('no new items')
        return
    for item in items:
        photos[item['id']] = copy_file(s3, item)
    print(s3.put_object(
        Body=json.dumps(manifest),
        Bucket=os.environ['PHOTOS_BUCKET'],
        ContentType='application/json',
        Key='manifest.json'))
    print('\n* wrote manifest: %s items' % len(manifest['photos']))

if __name__ == '__main__':
    lambda_handler()
