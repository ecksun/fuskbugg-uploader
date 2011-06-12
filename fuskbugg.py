#!/usr/bin/python
import httplib
import mimetypes
import sys
import json

def post_multipart(host, selector, files):
    content_type, body = encode_multipart_formdata(files)
    h = httplib.HTTPConnection(host)
    headers = {
        'User-Agent': 'bajskorv',
        'Content-Type': content_type
        }
    h.request('POST', selector, body, headers)
    res = h.getresponse()
    return res.status, res.reason, res.read()

def encode_multipart_formdata(files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def post_file(filename):
    fh = open(filename)
    data = fh.read()
    fh.close()
    (_, _, read) = post_multipart("fuskbugg.se", "/fuskbugg/desktop.php",  [("userfile", filename, data)]) 
    respons = json.loads(read)
    return respons["url"]

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        print post_file(arg)
