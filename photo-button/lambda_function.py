from datetime import datetime
import json
import os
import re
import random

import boto3
from twilio.rest import Client

'''
    environment
        TWILIO_ACCOUNT_SID
        TWILIO_AUTH_TOKEN
        FROM_NUMBER (iso-formatted number: +14081234567)
        TO_NUMBERS (space-delimited list of iso-formatted numbers)
        PHOTOS_BUCKET
'''

def send_photo(url):
    client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    url_dt = re.search(r'(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)(\d\d)(\d\d).*', url)
    # year, month, day, hour=0, minute=0, second=0
    dt = datetime(int(url_dt.group(1)), int(url_dt.group(2)), int(url_dt.group(3)),
        int(url_dt.group(4)), int(url_dt.group(5)), int(url_dt.group(6)))
    for number in os.environ['TO_NUMBERS'].split(' '):
        print('sending to %s' % number)
        message = client.messages.create(
            to=number,
            from_=os.environ['FROM_NUMBER'],
            body=dt.strftime('%A %B %-d %Y'),
            media_url=url)
        print('send %s' % message.sid)


def get_photos():
    s3 = boto3.client('s3')
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
    return list(manifest.get('photos', {}).values())


def get_photo_url():
    s3 = boto3.client('s3')
    photos = get_photos()
    random.seed(int(datetime.now().strftime('%s')))
    idx = random.randrange(len(photos))
    key = photos[idx]
    print('photo %s of %s = %s' % (idx, len(photos), key))
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': os.environ['PHOTOS_BUCKET'],
            'Key': key,
        })

def lambda_handler(event=None, context=None):
    url = get_photo_url()
    print('photo url %s' % url)
    send_photo(url)
