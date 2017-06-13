"""This module contains client that wrap requests and response to Knoema API"""

import json
import urllib.request
import datetime
import hmac
import base64
import hashlib
import random
import string
import io
import os
import apy_definitions as definition


def _random_string(length):
    return ''.join(random.choice(string.ascii_letters) for ii in range(length + 1))

def _string_to_binary(string_data):
    return string_data.encode()

def _crlf():
    return _string_to_binary('\r\n')


class Client:
    """This is client that wrap requests and response to Knoema API"""

    def __init__(self, host, appid=None, appsecret=None):
        self._host = host
        self._appid = appid
        self._appsecret = appsecret

    def _get_url(self, apipath):
        return 'http://{}{}'.format(self._host, apipath)

    def _get_request_headers(self):

        if not self._appid or not self._appsecret:
            return {'Content-Type' : 'application/json'}

        key = datetime.datetime.utcnow().strftime('%d-%m-%y-%H').encode()
        hashed = hmac.new(key, self._appsecret.encode(), hashlib.sha1)
        secrethash = base64.b64encode(hashed.digest()).decode('utf-8')
        auth = 'Knoema {}:{}:1.2'.format(self._appid, secrethash)

        return {
            'Content-Type' : 'application/json',
            'Authorization' : auth
            }

    def _api_get(self, obj, apipath, query=None):

        url = self._get_url(apipath)
        if query:
            url = '{}?{}'.format(url, query)

        headers = self._get_request_headers()
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)

        return obj(json.load(resp))

    def _api_post(self, responseobj, apipath, requestobj):

        url = self._get_url(apipath)

        jsondata = requestobj.savetojson()
        binary_data = jsondata.encode()

        headers = self._get_request_headers()
        req = urllib.request.Request(url, binary_data, headers)
        resp = urllib.request.urlopen(req)

        return responseobj(json.load(resp))

    def get_dataset(self, datasetid):
        """The method is getting information about dataset byt it's id"""

        path = '/api/1.0/meta/dataset/{}'
        return self._api_get(definition.Dataset, path.format(datasetid))

    def get_dimension(self, dataset, dimension):
        """The method is getting information about dimension with items"""

        path = '/api/1.0/meta/dataset/{}/dimension/{}'
        return self._api_get(definition.Dimension, path.format(dataset, dimension))

    def get_daterange(self, dataset):
        """The method is getting information about date range of dataset"""

        path = '/api/1.0/meta/dataset/{}/daterange'
        return self._api_get(definition.DateRange, path.format(dataset))

    def get_data(self, pivotrequest):
        """The method is getting data by pivot request"""

        path = '/api/1.0/data/pivot/'
        return self._api_post(definition.PivotResponse, path, pivotrequest)

    def upload_file(self, file):
        """The method is posting file to the remote server"""

        url = self._get_url('/api/1.0/upload/post')

        fcontent = FileContent(file)
        binary_data = fcontent.get_binary()

        headers = self._get_request_headers()
        req = urllib.request.Request(url, binary_data, headers)
        req.add_header('Content-type', fcontent.get_content_type())
        req.add_header('Content-length', len(binary_data))

        resp = urllib.request.urlopen(req)
        return definition.UploadPostResponse(json.load(resp))

    def upload_verify(self, file_location, dataset=None):
        """This method is verifiing posted file on server"""

        path = '/api/1.0/upload/verify'
        query = 'filePath={}'.format(file_location)
        if dataset:
            query = 'filePath={}&datasetId={}'.format(file_location, dataset)

        return self._api_get(definition.UploadVerifyResponse, path, query)

    def upload_submit(self, upload_request):
        """The method is submitting dataset upload"""

        path = '/api/1.0/upload/save'
        return self._api_post(definition.DatasetUploadResponse, path, upload_request)

    def upload_status(self, upload_id):
        """The method is checking status of uploaded dataset"""

        path = '/api/1.0/upload/status'
        query = 'id={}'.format(upload_id)
        return self._api_get(definition.DatasetUploadStatusResponse, path, query)


class FileContent(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self, file):
        self.file_name = os.path.basename(file)
        self.body = open(file, mode='rb').read()
        self.boundary = _random_string(30)

    def get_content_type(self):
        """Return a content type"""
        return 'multipart/form-data; boundary="{}"'.format(self.boundary)

    def get_binary(self):
        """Return a binary buffer containing the file content"""

        content_disp = 'Content-Disposition: form-data; name="file"; filename="{}"'

        stream = io.BytesIO()
        stream.write(_string_to_binary('--{}'.format(self.boundary)))
        stream.write(_crlf())
        stream.write(_string_to_binary(content_disp.format(self.file_name)))
        stream.write(_crlf())
        stream.write(_crlf())
        stream.write(self.body)
        stream.write(_crlf())
        stream.write(_string_to_binary('--{}--'.format(self.boundary)))
        stream.write(_crlf())

        return stream.getvalue()