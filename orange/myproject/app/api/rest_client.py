# Author Ali Eghlima

import json
import urllib
import urlparse
import requests


class RestClient(object):

    def __init__(self, server_url, api_key=None):
        self.server_url = server_url.rstrip()
        self.api_key = api_key
        self.headers = {'content-type': 'application/json'}

    def make_headers(self, extra_headers=None, auth=True):
        headers = self.headers.copy()
        if auth:
            token = 'key=%s' % self.api_key
            headers.update({'Authorization': token})
        headers.update(extra_headers or {})
        return headers

    def post(self, path, data='', files=None, headers=None, auth=True,
             **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or {})
        return requests.post(self.server_url + path, data=data, files=files,
                             headers=headers, **kwargs)

    def delete(self, path, data='', headers=None, auth=True, **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or '')
        return requests.delete(self.server_url + path, data=data,
                               headers=headers, **kwargs)

    def put(self, path, data='', files=None, headers=None, auth=True,
            **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or '')
        return requests.put(self.server_url + path, data=data, files=files,
                            headers=headers, **kwargs)

    def get(self, path, params={}, headers=None, auth=True, **kwargs):
        url_parts = urlparse.urlparse(path)
        path = url_parts.path
        query = dict(urlparse.parse_qsl(url_parts.query))
        query.update(params)
        params = urllib.urlencode(query)

        headers = self.make_headers(extra_headers=headers, auth=auth)
        return requests.get(self.server_url + path, headers=headers,
                            params=params, **kwargs)


def test_client():
    server_url = 'http://myproject.com'
    api_key = 'xxxxx'
    client = RestClient(server_url, api_key)

    # get functions
    res = client.get('/api/v1/test/')
    print res.text
