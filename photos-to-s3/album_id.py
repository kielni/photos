import os
import sys

import google_auth

def lookup_album_id(service, title):
    album_id = None
    req = service.albums().list()
    print('lookup_album_id: %s' % title)
    while req and not album_id:
        results = req.execute()
        #print('lookup_album_id: results=%s' % len(results.get('albums', [])))
        for album in results['albums']:
            #print('\talbum %s\t%s' % (title, album['id']))
            if album['title'] == title:
                album_id = album['id']
                break
        req = service.albums().list_next(req, results)
    print('returning album_id %s' % album_id)
    return album_id

if __name__ == '__main__':
    service = google_auth.service()
    print('\n* album_id\t%s' % lookup_album_id(service, sys.argv[1]))
