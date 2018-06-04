from datetime import datetime
import os
import flask

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = os.environ.get('CLIENT_SECRETS_FILE', 'client_secret.json')
SCOPES = os.environ.get('OAUTH_SCOPES', 'https://www.googleapis.com/auth/drive.photos.readonly')
API_SERVICE_NAME = os.environ.get('API_SERVICE_NAME', 'photos')
API_VERSION = os.environ.get('API_VERSION', 'v2')

app = flask.Flask(__name__)
app.secret_key = datetime.now().strftime('%s')


@app.route('/')
def index():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = credentials_to_dict(flow.credentials)
    html = '<h1>credentials</h1>\n'
    for key in credentials:
        html += '<p><b>%s</b> = %s</p>\n' % (key, credentials[key])
    return html


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # set Authorized redirect URIs in API console to http://localhost:8080/oauth2callback
    print('\n<-> http://localhost:8080\n')
    app.run('localhost', 8080, debug=True)
    # go to http://localhost:8080
    # allow access
    # copy token and refresh token to AWS Lambda
