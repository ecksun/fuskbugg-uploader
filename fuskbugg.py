#!/usr/bin/python
"""
This is a python program that provides an interface to fuskbugg.se, it is
called "fuskbugg python uploader".

Copyright (C) 2011 Linus Wallgren
This file is part of fuskbugg python uploader.

This program  is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import httplib
import mimetypes
import sys
import json
import os
import random
import string
import argparse
import ConfigParser

DEBUG = False

# A simple container for constants and other data used throughout the program
class global_data:
    domain = "fuskbugg.se"
    FUSKBUGG_UPLOADER_VERSION = 0.12

# Send files as POST multipart/formdata data to the provided host at path
# (selector)
def post_multipart(host, selector, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    headers = {
        'User-Agent': 'Fuskbugg python uploader',
        'Content-Type': content_type
        }
    h.request('POST', selector, body, headers)
    res = h.getresponse()
    return res.status, res.reason, res.read()

# Encode files for use in a POST mutlipart/formdata request
def encode_multipart_formdata(fields, files):
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
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)

    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    if DEBUG:
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
    (_, _, read) = post_multipart(
        "fuskbugg.se", 
        "/fuskbugg/desktop-api.php", 
        [("userid", config.get("authentication", "user-id"))], 
        [("userfile", filename, data)]
    ) 
    if DEBUG:
        print read
    respons = json.loads(read)
    if respons["result"]:
        return (True, respons["url"])
    else:
        return (False, "The sever responded with an error: %s" % (respons["msg"]))

# Fetch the names of all files uploaded with the configured user-id
def get_file_list():
    connection = httplib.HTTPConnection(global_data.domain)
    connection.request(
        "GET", 
        "/fuskbugg/desktop-filelist.php?userid=%s" % (config.get("authentication", "user-id")), 
    )
    respons_data = connection.getresponse().read()
    if DEBUG:
        print respons_data
    return json.loads(respons_data)

def print_file_list():
    respons = get_file_list()
    fields = {"url" : "URL", "ip" : "IP", "trash" : "In trash", "date" : "Upload date", "size": "Size"}
    max_widths = {}
    for file in respons:
        file["url"] = "%s%s" % (file["dir"], file["file"])
        for key, value in file.iteritems():
            if key not in fields:
                continue
            if key not in max_widths:
                max_widths[key] = 0
            max_widths[key] = max(len(fields[key]), max_widths[key], len(str(value)))

    for key in fields:
        print fields[key].ljust(max_widths[key]+2),
    print

    for file in respons:
        for key, value in file.iteritems():
            if key in fields:
                print str(value).ljust(max_widths[key]+2),
        print


# Checks validity according to fuskbuggs rules.
# If this check is overriden the server will still refuse the file, its purpose
# is to remove unnescesary POSTs to the server
def check_validity(filename):
    if os.path.getsize(filename) > 100e6:
        return (False, "File size to large")
    return (True, "")


config_file = os.path.expanduser("~") + "/.fuskbuggrc"
config = ConfigParser.SafeConfigParser()
config.read([config_file])
# Assumes that if no authentication section exist this is the first time the
# script is run
if not config.has_section("authentication"):
    config.add_section("authentication")
    # The user-id needs to be 13 digits
    config.set("authentication", "user-id", str(random.randint(1e12, 1e13-1)))
    print "A new user-id has automatically been generated for you and added to %s, it is %s." % (config_file, config.get("authentication", "user-id"))
    print "Save this ID as it is associated with the files you upload and can be used to access them again"

with open(config_file, 'wb') as configfile:
    config.write(configfile)


# If this file is executed directly treat all arguments as filenames and try to
# upload them to fuskbugg
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description="Upload files to fuskbugg", 
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
"""
Either -l of a FILE must be provided as argument in order for something to be
executed.

Before uploading each FILE need to pass certain tests, the tests are there in
order to ease the load on fuskbugg.se's servers and only try to mimic the
behaviour of the server. That is, if any test are bypassed the file might
simply be rejected by the server."""
    )

    arg_parser.add_argument("-v", "--version", action="version", version="%%(prog)s v%s" % (global_data.FUSKBUGG_UPLOADER_VERSION,), help="output version information and exit")
    arg_parser.add_argument("--user-id", type=int, metavar="UID", help="The user ID used to identify a user on fuskbugg, are generated per default and should mostly not be used")
    arg_parser.add_argument("-l", "--list", action="store_true", help="List files uploaded with the specified user-id")
    arg_parser.add_argument("-g", "--gui", action="store_true", help="Start the GUI")
    arg_parser.add_argument("FILE", nargs="*", help="The files to upload")
    args = arg_parser.parse_args()

    if DEBUG:
        print args

    if args.user_id != None:
        config.set("authentication", "user-id", str(args.user_id))

    uid_len = len(config.get("authentication", "user-id"))
    if uid_len != 13:
        print "User-id needs to be exactly 13 digits"
        sys.exit(1)

    if args.list:
        print_file_list()

    elif args.gui:
        from qt import run_gui
        run_gui()

    elif args.FILE:
        for file in args.FILE:
            (status, result) = post_file(file)
            if status:
                print "%s uploaded to URL %s" % (file, result)
            else:
                print result
    else:
        print "No action specified, see --help"
