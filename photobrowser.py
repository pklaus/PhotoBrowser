#!/usr/bin/env python
# -*- coding: utf-8 -*-

### ------ Built-in Python dependencies
import pprint
import glob
import os, sys
import errno
import re
import argparse
import random
### ------ External Dependencies
## needs  `pip install bottle`  :
from bottle import route, run, get, request, response, redirect, error, abort, install, TEMPLATE_PATH
from bottle import jinja2_view as view, jinja2_template as template
## needs  `pip install PIL`  :
from PIL import Image
from PIL.ExifTags import TAGS
### ------ Internal Dependencies
from hacks import static_file

# possible images sizes (height and width):
SIZES = [220, 330, 400, 600, 800, 950, 1200, 2400]
THUMBS_DIR = './.thumbs'
IMG_FILTER = '*.[jJ][pP][gG]'
TEMPLATE_PATH.append(os.path.join(os.path.split(os.path.realpath(__file__))[0],'views'))
STATIC_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0],'static')

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def clean_url_path(path):
    try:
        path = os.path.normpath(path.encode('latin1').decode('utf8'))
    except UnicodeEncodeError:
        path = os.path.normpath(path)
    return path

@get('/')
@view('home.jinja2')
def index_page():
    images = glob.glob(IMG_FILTER)
    images = random.sample(images, 12)
    return dict(images=images)

@get('/api/list_images')
def list_images():
    response.headers['Content-Type'] = 'text/plain; charset=UTF8'
    return pprint.pformat(glob.glob(IMG_FILTER))

def sorted_albums( l ): 
    """ Sort the given iterable in the way that humans expect.
        see http://stackoverflow.com/a/2669120/183995
    """ 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

@get('/albums')
@view('albums.jinja2')
def albums():
    images = glob.glob(IMG_FILTER)
    albums = [os.path.split(image)[0] for image in images]
    albums = [album for album in albums if len(album)>0]
    if len(albums) == 0:
        return "No albums found"
    albums = set(albums)
    albums = sorted_albums(albums)
    # Sort images into albums
    album_images = dict()
    for album in albums:
        album_images[album] = []
    for image in images:
        album_images[os.path.split(image)[0]].append(image)
    # Purge the list of album_images
    for album in albums:
        album_images[album] = album_images[album][:6]
    return dict(albums=albums, album_images=album_images)

@get('/album/<album:path>')
def show_album(album):
    album = clean_url_path(album)
    return show_images(album)

@get('/images')
@view('images.jinja2')
def show_images(album=None):
    images = glob.glob(IMG_FILTER)
    if album:
        images = [image for image in images if os.path.split(image)[0] == album]
    return dict(images=images, album=album)

@route('/show/<filename:path>')
@view('show.jinja2')
def full_size_page(filename):
    filename = clean_url_path(filename)
    images = glob.glob(IMG_FILTER)
    previous, next = None, None
    for i in range(len(images)):
        current = images[i]
        if current == filename:
            try:
                next = images[i+1]
            except IndexError:
                pass
            break
        previous = current
    album = os.path.split(filename)[0]
    return dict(album=album, filename=filename, next=next, previous=previous)

@route('/image/<filename:path>')
def full_size_image(filename):
    filename = clean_url_path(filename)
    return static_file(filename, root='./')

@route('/scaled-image/<size:int>/<filename:path>')
def scaled_image(size, filename):
    filename = clean_url_path(filename)
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
        mkdir_p(os.path.split(os.path.join(THUMBS_DIR, outfile))[0])
        im.save(os.path.join(THUMBS_DIR, outfile), "JPEG")
    except IOError:
        abort(500, "cannot create thumbnail for '%s'" % filename)
    return static_file(outfile, root=THUMBS_DIR)

@route('/static/<path:path>')
def static(path):
    return static_file(path, root=STATIC_PATH)

@error(404)
def error404(error):
    return "Error 404 - The requested document does not exist."

CACHE_SECONDS = 3600
class CachePlugin(object):
    """ adopted from https://github.com/jtackaberry/stagehand/blob/master/src/web/server/__init__.py """
    name = 'cache'
    api = 2
    def apply(self, callback, context):
        cache = 'max-age=%d, public' % (CACHE_SECONDS, )

        def wrapper(*args, **kwargs):
            if cache and cache is not True:
                response.headers['Cache-Control'] = cache
            return callback(*args, **kwargs)

        return wrapper

install(CachePlugin())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run this in a folder of images to serve them on the web')
    parser.add_argument('-p', '--port', default='8080', help='The port to run the web server on.')
    parser.add_argument('-t', '--thumbs-dir', default=THUMBS_DIR, help='The directory to store thumbnails in.')
    parser.add_argument('-s', '--subdirs', action='store_true',
    help='Assume images to be stored in sub directories.')
    parser.add_argument('-d', '--debug', action='store_true',
    help='Start in debug mode (with verbose HTTP error pages.')
    parser.add_argument('FOLDER', default='./', help='The folder with your images [default: ./]')
    args = parser.parse_args()
    THUMBS_DIR = args.thumbs_dir
    try:
        mkdir_p(THUMBS_DIR)
    except:
        sys.exit('Could not create the thumbnail folder. Exiting')
    if args.subdirs:
        IMG_FILTER = '*/' + IMG_FILTER
    if args.debug:
        run(host='0.0.0.0', port=args.port, debug=True, reloader=True)
    else:
        #run(host='0.0.0.0', port=args.port)
        run(host='0.0.0.0', server='cherrypy', port=args.port)

