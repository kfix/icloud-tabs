#!/usr/bin/env python
# Format of request:
# {
#   "apns-token": "<data>",
#   "apps": [
#     {
#       "bundle-id": "com.apple.Safari",
#       "keys": [
#         {
#           "data": "<data>",
#           "name": ""
#         }
#       ],
#       "kvstore-id": "com.apple.Safari.SyncedTabs",
#       "registry-version": ""
#     }
#   ],
#   "service-id":"iOS"
# }

# Format of "keys" <data> blob:
# {
#   "DeviceName": "",
#   "LastModified": "YYYY-MM-DDTHH:MM:SSZ",
#   "Tabs": [
#     {
#       "Title": "",
#       "URL": ""
#     }
#   ]
# }

import urllib2

import StringIO
import gzip

import plistlib
import biplist
import base64
import time, datetime
import uuid
import pprint
import os

from update_config import *

# Request Header Constants
ICLOUD_SERVICE = "keyvalueservice.icloud.com"
USER_AGENT = "SyncedDefaults/91.30 (Mac OS X 10.9.1 (13B42))" #"SyncedDefaults/43.27 (Mac OS X 10.8.4 (12E55))"
X_MME_CLIENT_INFO = "<Macmini3,1> <Mac OS X;10.9.1;13B42> <com.apple.SyncedDefaults/91.30>" #"<MacBookAir4,2> <Mac OS X;10.8.4;12E55> <com.apple.SyncedDefaults/43.27>"

X_APPLE_REQUEST_UUID = str(uuid.uuid4()).upper()
X_APPLE_SCHEDULER_ID = "com.apple.syncedpreferences.browser"

#what a pile, replace with http://docs.python-requests.org/en/latest/ someday
class iCloudNodeRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_330(self, req, fp, code, msg, headers):
        '''330 received when apple wants us to redirect to a specific server node for a service after requesting something from its top-level CNAME'''
	mme_server = headers['X-Apple-MMe-Host'] #icloud server node: `p<00-NN>-exampleservice.icloud.com`
	newhdr = req.headers
	newhdr['Host'] = mme_server
	newurl = "%s://%s%s" % ( req.get_type(), mme_server, req.get_selector() )
	newreq = urllib2.Request(newurl, req.data, newhdr)
        return urllib2.urlopen(newreq)
icl_urlopen = urllib2.build_opener(iCloudNodeRedirectHandler)

def generate_plist(with_payload, tabs, uuid, name, registry_version="need-something-here"):
    b = {
          "DeviceName": name,
          "LastModified": datetime.datetime.fromtimestamp(time.mktime(time.gmtime())),
          "Tabs": tabs
        }

    # Write b into a binary plist and base64 encode it.
    out = StringIO.StringIO()
    biplist.writePlist(b, out)
    #plistlib.dump(b, out, fmt=plistlib.FMT_BINARY) #py3.4
    # There is a required 12 byte header here. Don't know what it's supposed to contain.
    b_encoded = "".join(map(chr, [1, 0, 0, 0, 0,  0, 0, 23, 0, 0, 0, 0])) + out.getvalue()

    p = {
          "apns-token": plistlib.Data(APNS_TOKEN),
          "apps": [
            {
              "bundle-id": "com.apple.Safari",
              "keys": [
                {
                  "data": plistlib.Data(b_encoded), #bytes(b_encoded) py3.4
                  "name": uuid # a unique id for your device
                }
              ],
              "kvstore-id": "com.apple.Safari.SyncedTabs",
              "registry-version": registry_version, # no idea
            }
          ],
          "service-id":"iOS"
        }

    if with_payload == False:
      p["apps"][0].pop("keys")

    # Write p into a regular plist and return its string value.
    out = StringIO.StringIO()
    plistlib.writePlist(p, out)
    return out.getvalue()


def dogzip(s):
    out = StringIO.StringIO()
    f = gzip.GzipFile(fileobj=out, mode='w')
    f.write(s)
    f.close()
    return out.getvalue()

def ungzip(s):
    data = StringIO.StringIO(s)
    gzipper = gzip.GzipFile(fileobj=data)
    html = gzipper.read()
    return html

def make_request(body):
  URL = "https://%s/sync" % ICLOUD_SERVICE

  zippedbody = dogzip(body)

  request = urllib2.Request(URL, headers={
      "Host": ICLOUD_SERVICE,
      "User-Agent" : USER_AGENT,
      "Accept": "*/*",
      "Content-Encoding": "gzip",
      "Accept-Language": "en-us",
      "Accept-Encoding": "gzip, deflate",
      "Content-Type": "text/xml", #"application/x-www-form-urlencoded",
      "Authorization": AUTHORIZATION,
      "Connection": "keep-alive", #being turned to close
      "Proxy-Connection": "keep-alive",
      "X-MMe-Client-Info": X_MME_CLIENT_INFO,
      "X-Apple-Request-UUID": X_APPLE_REQUEST_UUID,
      "X-Apple-Scheduler-ID": X_APPLE_SCHEDULER_ID,
      "Content-Length": len(zippedbody)
      }, 
      data=zippedbody)

  try:
      u = icl_urlopen.open(request)
  except urllib2.HTTPError, error:
      print 'E: POST %s => %s: %s' % (error.url, error.code, error.reason)
      print error.headers
      print error.read()
      raise urllib2.HTTPError, error

  data = u.read()

  return ungzip(data)

def update_tabs(tabs):
  # First make an empty (without tab data) request to get the latest registry string.
  payload_plist = generate_plist(False, [], DEVICE_UUID, DEVICE_NAME)
  response = make_request(payload_plist)
  response_plist = plistlib.readPlistFromString(response)
  registry_version = response_plist["apps"][0]["registry-version"]

  #print plistlib.writePlistToString(response_plist) 
  print registry_version
  # dump current tabs
  for device in response_plist["apps"][0]["keys"]:
     pprint.pprint(biplist.readPlistFromString(device["data"].data[12:]))
     #print plistlib.loads(device["data"][12:], fmt=plistlib.FMT_BINARY) #py3.4

  # Next use that string to make a request with a payload of tabs.
  payload_plist = generate_plist(True, tabs, DEVICE_UUID, DEVICE_NAME, registry_version=registry_version)
  upd_response = make_request(payload_plist)
  print plistlib.writePlistToString(plistlib.readPlistFromString(upd_response)) #dump update confirmation

if __name__ == '__main__':
  TABS = [
          {
            "Title": "XKCD",
            "URL": "http://xkcd.com/"
          },
          {
            "Title": "Stuff on Cats",
            "URL": "http://stuffonmycat.com/"
          }
        ]

  update_tabs(TABS)
