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
from functools import partial
from datetime import date
### ------ External Dependencies
## needs  `pip install bottle`  :
from bottle import route, run, get, request, response, redirect, error, abort, install, TEMPLATE_PATH
from bottle import jinja2_template as template
from bottle import jinja2_view
## needs  `pip install PIL`  :
from PIL import Image
from PIL.ExifTags import TAGS
### ------ Internal Dependencies
from hacks import static_file

# possible images sizes (height and width):
HEIGHTS = [220, 330, 400, 600, 780, 800, 950, 1200, 1800, 2400]
DEFAULT_HEIGHT = 780
DEFAULT_THUMB_HEIGHT = 220
THUMBS_DIR = './.thumbs'
IMG_FILTER = '*.[jJ][pP][gG]'
TEMPLATE_PATH.append(os.path.join(os.path.split(os.path.realpath(__file__))[0],'views'))
STATIC_PATH = os.path.join(os.path.split(os.path.realpath(__file__))[0],'static')
JPEG_QUALITY = 80
IMAGE_FOLDER = './'
IMAGE_REGEX = None

filter_dict = {}
view = partial(jinja2_view,
          template_settings={'filters': filter_dict})

def filter(func):
	"""Decorator to add the function to filter_dict"""
	filter_dict[func.__name__] = func
	return func

@filter
def remove_date(text):
    try:
        return re.match('^\d+-\d+-\d+_(.*)', text).groups()[0].replace('-',' ').replace('_',', ')
    except AttributeError:
        return None

@filter
def extract_date(text):
    try:
        return date(*[int(number) for number in re.match('^(\d+)-(\d+)-(\d+)_', text).groups()])
    except AttributeError:
        return None

@filter
def format_date(dt):
    return dt.strftime("%a, %d %B %Y")

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def all_images():
    return [IMAGE_REGEX.match(image).group(1) for image in glob.glob(IMG_FILTER)]

def clean_url_path(path):
    try:
        path = os.path.normpath(path.encode('latin1').decode('utf8'))
    except UnicodeEncodeError:
        path = os.path.normpath(path)
    return path

@get('/')
@view('home.jinja2')
def index_page():
    images = all_images()
    images = random.sample(images, 12)
    return dict(images=images, thumb_height=DEFAULT_THUMB_HEIGHT)

@get('/api/list_images')
def list_images():
    response.headers['Content-Type'] = 'text/plain; charset=UTF8'
    return pprint.pformat(all_images())

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
    images = all_images()
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
    return dict(albums=albums, album_images=album_images, thumb_height=DEFAULT_THUMB_HEIGHT)

@get('/album/<album:path>')
def show_album(album):
    album = clean_url_path(album)
    return show_images(album)

@get('/images')
@view('images.jinja2')
def show_images(album=None):
    images = all_images()
    if album:
        images = [image for image in images if os.path.split(image)[0] == album]
    return dict(images=images, album=album, thumb_height=DEFAULT_THUMB_HEIGHT)

@route('/show/<filename:path>')
@view('show.jinja2')
def show_large_image(filename):
    filename = clean_url_path(filename)
    if filename not in all_images():
        abort(404, "image not found")
    images = all_images()
    height = request.query.height
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
    try:
        exif = named_exif( clean_exif_data( get_exif_data(os.path.join(IMAGE_FOLDER, filename))))
        for item in ['Model', 'FocalLength', 'FNumber', 'ExposureTime', 'ISOSpeedRatings', 'ExifImageWidth', 'ExifImageHeight']:
            if not item in exif: exif = None
    except:
        exif = None
    return dict(album=album, filename=filename, next=next, previous=previous, height=height, exif=exif, filesize=os.path.getsize(os.path.join(IMAGE_FOLDER, filename))/(1024.*1024.))

@route('/image/<filename:path>')
def full_size_image(filename):
    filename = clean_url_path(filename)
    return static_file(filename, root=IMAGE_FOLDER)


def get_exif_data(filename):
    im = Image.open(filename)
    exif = im._getexif()
    ret = dict()
    for tag, value in exif.items():
        ret[tag] = value
    return ret

def clean_exif_data(exif_data):
    ret_exif = dict()
    for tag, value in exif_data.items():
        if type(value) == str:
            value = value.rstrip('\0')
        if type(value) == bytes:
            value = value.rstrip(b'\x00')
        ret_exif[tag] = value
    return ret_exif
    
def structure_exif_data(exif_data):
    ret_exif = dict()
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        ret_exif[tag] = dict(name=decoded, value=value)
    return ret_exif

def named_exif(exif_data):
    ret_exif = dict()
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        ret_exif[decoded] = value
    return ret_exif

@route('/exif/<filename:path>')
def json_exif_information(filename):
    """
    Return EXIF information in JSON format.
    A dictionary is being returned containing the EXIF key numbers as keys and
    an dictionary containing the name and value of the respective EXIF tag.
    """
    filename = clean_url_path(filename)
    if not filename in all_images():
        abort(404, "image not found")
    try:
        exif = structure_exif_data( clean_exif_data( get_exif_data(os.path.join(IMAGE_FOLDER, filename))))
        ret = dict()
        for tag, content in exif.items():
            if type(content['value']) == bytes:
                content['value'] = repr(content['value'])
            if content['name'] == 'MakerNote': continue
            ret[tag] = content
        return ret
    except IOError:
        abort(500, "cannot extract EXIF information for '%s'" % filename)

@route('/scaled-image/<height:int>/<filename:path>')
def scaled_image(height, filename):
    filename = clean_url_path(filename)
    if filename not in all_images():
        abort(404, "image not found")
    if height not in HEIGHTS:
        abort(404, "No scaled image of that height available.")
    outfile = os.path.splitext(filename)[0] + ".thumbnail.%d.jpg" % height
    if os.path.isfile(os.path.join(THUMBS_DIR, outfile)):
        return static_file(outfile, root=THUMBS_DIR)
    try:
        im = Image.open(os.path.join(IMAGE_FOLDER, filename))
        size = (height*2, height)
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
        im.save(os.path.join(THUMBS_DIR, outfile), "JPEG", quality=JPEG_QUALITY)
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
    parser.add_argument('-q', '--jpeg-quality', type=int, default=JPEG_QUALITY, help='Set the quality of the thumbnail JPEGs (1-100).')
    parser.add_argument('-d', '--debug', action='store_true',
    help='Start in debug mode (with verbose HTTP error pages.')
    parser.add_argument('FOLDER', default=IMAGE_FOLDER, help='The folder with your images [default: ./]')
    args = parser.parse_args()
    IMAGE_FOLDER = os.path.abspath(args.FOLDER)
    IMAGE_REGEX = re.compile('^' + re.escape(IMAGE_FOLDER + os.sep) + '(.*)')
    THUMBS_DIR = os.path.abspath(args.thumbs_dir)
    try:
        mkdir_p(THUMBS_DIR)
    except:
        sys.exit('Could not create the thumbnail folder. Exiting')
    if args.subdirs:
        IMG_FILTER = IMAGE_FOLDER + '/*/' + IMG_FILTER
    if args.jpeg_quality not in range(0,101):
        args.error('JPEG quality must be in the range of 0-100.')
    JPEG_QUALITY = args.jpeg_quality
    if args.debug:
        run(host='0.0.0.0', port=args.port, debug=True, reloader=True)
    else:
        #run(host='0.0.0.0', port=args.port)
        run(host='0.0.0.0', server='cherrypy', port=args.port)

