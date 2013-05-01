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
from bottle import route, run, get, request, template, response, redirect, error, abort, install
## needs  `pip install PIL`  :
from PIL import Image
from PIL.ExifTags import TAGS
### ------ Internal Dependencies
from hacks import static_file

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

def clean_url_path(path):
    try:
        path = os.path.normpath(path.encode('latin1').decode('utf8'))
    except UnicodeEncodeError:
        path = os.path.normpath(path)
    return path

@get('/')
def index_page():
    retval = "<h3>Navigation</h3>"
    retval += "<ul>"
    retval += "<li><a href='/images'>Show All Images</a></li>"
    retval += "<li><a href='/albums'>Show All Albums</a></li>"
    retval += "</ul>\n"
    retval += "<h3>Some Random Images</h3>\n"
    images = glob.glob(IMG_FILTER)
    images = random.sample(images, 12)
    for image in images:
        retval += "<a name='%s'></a>" % image
        retval += "<a href='/show/%s'>" % image
        retval += "<img src='/scaled-image/220/%s'>" % image
        retval += "</a>\n"
    return retval

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
def albums():
    images = glob.glob(IMG_FILTER)
    albums = [os.path.split(image)[0] for image in images]
    albums = [album for album in albums if len(album)>0]
    if len(albums) == 0:
        return "No albums found"
    albums = set(albums)
    albums = sorted_albums(albums)
    retval = ""
    album_images = dict()
    for album in albums:
        album_images[album] = []
    for image in images:
        album_images[os.path.split(image)[0]].append(image)
    for album in albums:
        # display the album name
        retval += "<a name='%s'></a>" % album
        retval += "<a href='/album/%s'>" % album
        match = re.match('^(\d+)-(\d+)-(\d+)_', album)
        if match:
            date = [int(number) for number in match.groups()]
            retval += "<h3>%s</h3>\n" % ' '.join(album.split('_')[1:]).replace('-',' ')
            retval += "<div>%04d-%02d-%02d</div>\n" % tuple(date)
        else:
            retval += "<h3>%s</h3>" % album
        retval += "</a>\n"
        # show the first x images
        i = 0
        for album_image in album_images[album]:
            i += 1
            if i >= 7: break
            retval += "<a name='%s'></a>" % album_image
            retval += "<a href='/show/%s'>" % album_image
            retval += "<img src='/scaled-image/220/%s'>" % album_image
            retval += "</a>\n"
    return retval

@get('/album/<album:path>')
def show_album(album):
    album = clean_url_path(album)
    return show_images(album)

@get('/images')
def show_images(album=None):
    retval = ""
    images = glob.glob(IMG_FILTER)
    if album:
        images = [image for image in images if os.path.split(image)[0] == album]
        retval += "<a href='/images'>Show All Images</a> | <a href='/albums'>Show All Albums</a>"
        retval += "<h3>Album: %s</h3>" % album
    for image in images:
        retval += "<a name='%s'></a>" % image
        retval += "<a href='/show/%s'>" % image
        retval += "<img src='/scaled-image/220/%s'>" % image
        retval += "</a>\n"
    return retval

@route('/show/<filename:path>')
def full_size_page(filename):
    filename = clean_url_path(filename)
    images = glob.glob(IMG_FILTER)
    retval = ""
    retval += """
<script>
//window.onload = function()
//{
  document.onkeyup = function(event)
  {
    var e = (!event) ? window.event : event;
    switch(e.keyCode)
    {
      case 37:
        //window.location.href = document.getElementById('previous').href;
        document.getElementById('previous').click();
        break;
      case 39:
        //window.location.href = document.getElementById('next').href;
        document.getElementById('next').click();
        break;
      case 38:
        //window.location.href = document.getElementById('up').href;
        document.getElementById('up').click();
        break;
    }
  };
//};
// ----- or the jQuery solution:
// ---   see http://digitalraindrops.net/2012/05/keyboard-navigation-for-wordpress-posts/
// ---   or  http://jqueryfordesigners.com/adding-keyboard-navigation/
//$(document.documentElement).keyup(function (event) {
//  // handle cursor keys
//  if (event.keyCode == 37) {
//    // go left
//    $('#previous').find('a').click();
//  } else if (event.keyCode == 39) {
//    // go right
//    $('#next').find('a').click();
//  }
//});
</script>
"""
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
    retval += "<center>"
    if previous:
        retval += "<a id='previous' href='/show/%s'>← previous</a> | " % previous
    retval += "<a href='/images#%s'>All Images</a> | " % filename
    album = os.path.split(filename)[0]
    if album:
        retval += "<a id='up' href='/album/%s#%s'>Album View</a> | " % (album, filename)
    retval += "<a href='/image/%s'>Full Size Image</a>" % filename 
    if next:
        retval += " | <a id='next' href='/show/%s'>next →</a>" % next
    retval += "<br />"
    retval += "<img src='/scaled-image/950/%s' />" % filename
    retval += "</center>"
    if next:
        retval += "<img style='display:none' src='/scaled-image/950/%s' />" % next
    if previous:
        retval += "<img style='display:none' src='/scaled-image/950/%s' />" % previous
    return retval

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

