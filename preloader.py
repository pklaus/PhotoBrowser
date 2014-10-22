#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preloader for PhotoBrowser
uses Python3
"""

import sys

try:
    site = sys.argv[1]
except:
    sys.stderr.write("usage: " + sys.argv[0] + " SITE_URL [password]\n")
    sys.exit(2)
try:
    password = sys.argv[2]
except:
    password = None

import urllib.request
import urllib.parse
import http.cookiejar
import json

print("Logging in")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)
if password:
    data=[('password',password)] 
    response = urllib.request.urlopen(urllib.parse.urljoin(site, '/login?requesting=/'), urllib.parse.urlencode(data).encode('utf-8')).read()
    if "FAILED" in response.decode('utf-8'):
        print('bad credentials, exiting.')
        sys.exit(3)

response = urllib.request.urlopen(urllib.parse.urljoin(site, '/api/list/images')).read().decode('utf-8')
images = json.loads(response)['images']

print("Preloading images for " + site)

site = urllib.parse.urljoin(site, '/api/image/scaled/600/')
for image in images:
    print("Fetching {}.".format(image))
    image = urllib.parse.quote(image)
    urllib.request.urlopen(urllib.parse.urljoin(site, image)).read()

