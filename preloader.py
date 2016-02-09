#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preloader for PhotoBrowser
uses Python3
"""

import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys
import argparse
import time

def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site_url', metavar="SITE_URL",
                       help='URL to your PhotoBrowser site.')
    parser.add_argument('--password', '-p',
                       help='Provide the password to your site if needed.')
    parser.add_argument('--wait', '-w', type=float, default=1E-4,
                       help='Microseconds to wait after every fetched image. Default: 1E-4 s.')
    args = parser.parse_args()

    print("Logging in")

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    urllib.request.install_opener(opener)
    if args.password:
        data=[('password',args.password)]
        response = urllib.request.urlopen(urllib.parse.urljoin(args.site_url, '/login?requesting=/'), urllib.parse.urlencode(data).encode('utf-8')).read()
        if "FAILED" in response.decode('utf-8'):
            print('bad credentials, exiting.')
            sys.exit(3)

    response = urllib.request.urlopen(urllib.parse.urljoin(args.site_url, '/api/list/images')).read().decode('utf-8')
    images = json.loads(response)['images']

    print("Preloading images for " + args.site_url)

    base_url= urllib.parse.urljoin(args.site_url, '/api/image/scaled/600/')
    for image in images:
        print("Fetching {}.".format(image))
        image = urllib.parse.quote(image)
        urllib.request.urlopen(urllib.parse.urljoin(base_url, image)).read()
        if args.wait: time.sleep(args.wait)

if __name__ == "__main__":
    main()

