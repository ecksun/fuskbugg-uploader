#!/usr/bin/python
import httplib
import mimetypes
import sys
import json
import os
import random
import string

FUSKBUGG_UPLOADER_NAME = "Fuskbugg uploader"
FUSKBUGG_UPLOADER_VERSION = 0.11

# Send files as POST multipart/formdata data to the provided host at path
# (selector)
def post_multipart(host, selector, files):
    content_type, body = encode_multipart_formdata(files)
    h = httplib.HTTPConnection(host)
    headers = {
        'User-Agent': 'Fuskbugg python uploader',
        'Content-Type': content_type
        }
    h.request('POST', selector, body, headers)
    res = h.getresponse()
    return res.status, res.reason, res.read()

# Encode files for use in a POST mutlipart/formdata request
def encode_multipart_formdata(files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """

    random_string = ''.join(random.choice(string.ascii_letters) for x in range(32))
    # BOUNDARY Should just be a unique string, hence the random data on the end
    BOUNDARY = '--The_Boundary_and_random:%s' % (random_string)

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
    print body
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

# Get the content type from a filename
def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# Post a file to fuskbugg provided its filename as a string
def post_file(filename):
    (status, reason) = check_validity(filename)
    if not status:
        return (False, "%s is not a valid file: %s" % (filename, reason))
    fh = open(filename)
    data = fh.read()
    fh.close()
    (_, _, read) = post_multipart("fuskbugg.se", "/fuskbugg/desktop.php",  [("userfile", filename, data)]) 
    # print read
    respons = json.loads(read)
    if respons["result"]:
        return (True, respons["url"])
    else:
        return (False, "The sever responded with an error: %s" % (respons["msg"]))

# Checks validity according to fuskbuggs rules.
# If this check is overriden the server will still refuse the file, its purpose
# is to remove unnescesary POSTs to the server
def check_validity(filename):
    if os.path.getsize(filename) > 100e6:
        return (False, "File size to large")
    return (True, "")


# If this file is executed directly treat all arguments as filenames and try to
# upload them to fuskbugg
if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg == "--help":
            print """Usage: fuskbugg.py [OPTION]... [FILE]...
Uploads each FILE to fuskbugg.se

Options
    --help      display this help and exit
    --version   output version information and exit

Before uploading each FILE need to pass certain tests, the tests
are there in order to ease the load on fuskbugg.se's servers and
only try to mimic the behaviour of the server. That is, if any test
are bypassed the file might simply be rejected by the server."""
            sys.exit(0)
        if arg == "--version":
            print "%s %s" % (FUSKBUGG_UPLOADER_NAME, FUSKBUGG_UPLOADER_VERSION)
            sys.exit(0)
        (status, result) = post_file(arg)
        if status:
            print "%s uploaded to URL %s" % (arg, result)
        else:
            print result
