#!/usr/bin/env python
# -*- coding: utf-8 -*-

### ------ Built-in Python dependencies
import pprint
import glob
import os, sys
import errno
import argparse
### ------ External Dependencies
## needs  `pip install bottle`  :
from bottle import route, run, static_file, get, request, template, response, redirect, error, abort
## needs  `pip install PIL`  :
import Image
from PIL.ExifTags import TAGS

# possible images sizes (height and width):
SIZES = [220, 330, 400, 600, 800, 950, 1200, 2400]
THUMBS_DIR = './.thumbs'
IMG_FILTER = '*.[jJ][pP][gG]'

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

@get('/')
def list_images():
    response.headers['Content-Type'] = 'text/plain; charset=UTF8'
    return pprint.pformat(glob.glob(IMG_FILTER))

@get('/images')
def show_images():
    retval = ""
    for image in glob.glob(IMG_FILTER):
        retval += "<a href='/show/%s'>" % image
        retval += "<img src='/scaled-image/220/%s'>" % image
        retval += "</a>\n"
    return retval

@route('/show/<filename:re:[a-zA-Z\._\-0-9]+>')
def full_size_page(filename):
    images = glob.glob(IMG_FILTER)
    retval = "<center>"
    previous = None
    for i in range(len(images)):
        current = images[i]
        if current == filename:
            next = None if i == len(images)-1 else images[i+1]
            break
        previous = current
    if previous:
        retval += "<a href='/show/%s'>← previous</a> | " % previous
    retval += "<a href='/image/%s'>Full Size Image</a>" % filename 
    if next:
        retval += " | <a href='/show/%s'>next →</a>" % next
    retval += "<br />"
    retval += "<img src='/scaled-image/950/%s' />" % filename
    retval += "</center>"
    return retval

@route('/image/<filename:re:[a-zA-Z\._\-0-9]+>')
def full_size_image(filename):
    return static_file(filename, root='./')

@route('/scaled-image/<size:int>/<filename:re:[a-zA-Z\._\-0-9]+>')
def scaled_image(size, filename):
    response.set_header('Cache-Control', 'max-age=3600')
    if size not in SIZES: abort(404, "No scaled image of that size available.")
    outfile = os.path.splitext(filename)[0] + ".thumbnail.%d.jpg" % size
    if os.path.isfile(os.path.join(THUMBS_DIR, outfile)):
        return static_file(outfile, root=THUMBS_DIR)
    if not os.path.isfile('./' + filename):
        abort(404, "image not found")
    try:
        im = Image.open('./' + filename)
        size = (size if size>800 else 800, size)
        exif = im._getexif()
        if exif != None:
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'Orientation':
                    if value == 3: im = im.rotate(180)
                    if value == 6: im = im.rotate(270)
                    if value == 8: im = im.rotate(90)
                    break
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(os.path.join(THUMBS_DIR, outfile), "JPEG")
    except IOError:
        abort(500, "cannot create thumbnail for '%s'" % filename)
    return static_file(outfile, root=THUMBS_DIR)

@error(404)
def error404(error):
    return "Error 404 - The requested document does not exist."

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run this in a folder of images to serve them on the web')
    parser.add_argument('-p', '--port', default='8080', help='The port to run the web server on.')
    parser.add_argument('-t', '--thumbs-dir', default='./.thumbs/', help='The directory to store thumbnails in.')
    parser.add_argument('-d', '--debug', action='store_true',
    help='Start in debug mode (with verbose HTTP error pages.')
    parser.add_argument('FOLDER', default='./', help='The folder with your images [default: ./]')
    args = parser.parse_args()
    THUMBS_DIR = args.thumbs_dir
    try:
        mkdir_p(THUMBS_DIR)
    except:
        sys.exit('Could not create the thumbnail folder. Exiting')
    if args.debug:
        run(host='0.0.0.0', port=args.port, debug=True, reloader=True)
    else:
        run(host='0.0.0.0', port=args.port)
    #run(host='0.0.0.0', server='cherrypy', port=8080)
    
