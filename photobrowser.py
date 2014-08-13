#!/usr/bin/env python
# -*- coding: utf-8 -*-

### ------ Built-in Python dependencies
import pprint
import glob
import os, sys
import errno
import re
import argparse
from random import sample, choice, randint
import string
from functools import partial
from datetime import date
from fractions import Fraction
from ipaddress import ip_address
### ------ External Dependencies
def require_external(name, hint):
    sys.stderr.write('This script requires {}. {}\n'.format(name, hint))
    sys.exit(1)
try:
    from bottle import Bottle, run, request, response, redirect, error, abort, TEMPLATE_PATH
    from bottle import jinja2_template as template
    from bottle import jinja2_view
except ImportError:
    require_external('bottle', 'get it with `pip install bottle`')
try:
    from PIL import Image
    from PIL import ExifTags
except ImportError:
    require_external('PIL', 'get it with `pip install PIL`')
try:
    from beaker.middleware import SessionMiddleware
except ImportError:
    require_external('beaker', 'get it with `pip install beaker`')
try:
    from jinja2 import Template
except ImportError:
    require_external('jinja2', 'get it with `pip install jinja2`')
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
ADMIN_PASSWORD = None
ALLOW_CRAWLING = 'Disallow'

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
        return re.match('^\d+-\d+-\d+[_ ](.*)', text).groups()[0].replace('-',' ').replace('_',', ')
    except AttributeError:
        return None

@filter
def extract_date(text):
    try:
        return date(*[int(number) for number in re.match('^(\d+)-(\d+)-(\d+)[_ ]', text).groups()])
    except AttributeError:
        return None

@filter
def format_date(dt):
    ## German style:
    #return dt.strftime("%A, %d. %B %Y")
    ## English style:
    return dt.strftime("%a, %d %B %Y")


@filter
def format_focallength(exif_focallength):
    focallength = float(exif_focallength[0])/float(exif_focallength[1])
    return "{0:.1f}".format(focallength).rstrip('0').rstrip('.') + " mm"

@filter
def format_fnumber(exif_fnumber):
    fnumber = float(exif_fnumber[0])/float(exif_fnumber[1])
    return "f/{0:.2g}".format(fnumber)

@filter
def format_exposuretime(exif_exposure):
    exposure = Fraction(exif_exposure[0], exif_exposure[1])
    if exposure < 1.:
        if len(str(exposure)) > 6:
            exposure = Fraction(1, round(1/exposure))
        return "{0} sec".format(exposure)
    else:
        return "{0:.1f} sec".format(float(exposure))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def create_id(size=8):
    return ''.join([choice(string.ascii_letters + string.digits) for i in range(size)])

def clean_url_path(path):
    try:
        path = path.encode('latin1').decode('utf8')
    except UnicodeEncodeError:
        pass
    return path

pb = Bottle()
api = Bottle()

@pb.get('/')
@view('home.jinja2')
def index_page():
    images = all_images()
    try:
        images = sample(images, 12)
    except ValueError:
        images = images
    return dict(images=images, thumb_height=DEFAULT_THUMB_HEIGHT)

@api.get('/clear-cache')
def clear_cache():
    global CACHED_IMGs
    CACHED_IMGs[:] = []
    CACHED_ALBUMBs[:] = []
    CACHED_ALBUM_IMGS = dict()
    return dict(result='success')

@api.get('/list/images')
def list_images():
    return dict(images=all_images())

CACHED_IMGs = None
def all_images():
    global CACHED_IMGs
    if CACHED_IMGs: return CACHED_IMGs
    retl = []
    if type(IMG_FILTER) == list:
        for filter in IMG_FILTER:
            retl += [IMAGE_REGEX.match(image).group(1).replace('\\','/') for image in glob.glob(filter)]
    else:
        retl = [IMAGE_REGEX.match(image).group(1).replace('\\','/') for image in glob.glob(IMG_FILTER)]
    retl.sort()
    CACHED_IMGs = retl
    return retl

@api.get('/list/albums')
def list_albums():
    return dict(albums=all_albums())

CACHED_ALBUMBs = None
def all_albums():
    global CACHED_ALBUMBs
    if CACHED_ALBUMBs: return CACHED_ALBUMBs
    images = all_images()
    albums = [os.path.split(image)[0] for image in images]
    albums = [album for album in albums if len(album)>0]
    albums = set(albums)
    albums = sorted_albums(albums)
    CACHED_ALBUMBs = albums
    return albums

@api.get('/list/album_images')
def list_album_images():
    return dict(album_images=album_images())

CACHED_ALBUM_IMGS = None
def album_images():
    global CACHED_ALBUM_IMGS
    if CACHED_ALBUM_IMGS: return CACHED_ALBUM_IMGS
    images = all_images()
    albums = all_albums()
    # Sort images into albums
    album_images = dict()
    for album in albums:
        album_images[album] = []
    for image in images:
        album_images[os.path.split(image)[0]].append(image)
    CACHED_ALBUM_IMGS = album_images
    return album_images

@api.get('/list/albums')
def list_albums():
    return dict(albums=all_albums())

def sorted_albums( l ): 
    """ Sort the given iterable in the way that humans expect.
        see http://stackoverflow.com/a/2669120/183995
    """ 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

@pb.get('/albums')
@view('albums.jinja2')
def albums():
    albums = all_albums()
    if len(albums) == 0:
        return "No albums found"
    # Create partial list of album images:
    partial_album_images = album_images()
    for album in partial_album_images:
        partial_album_images[album] = partial_album_images[album][:6]
    return dict(albums=albums, album_images=partial_album_images, thumb_height=DEFAULT_THUMB_HEIGHT)

@pb.get('/album/<album:path>')
def show_album(album):
    album = clean_url_path(album)
    return show_images(album)

@pb.get('/images')
@view('images.jinja2')
def show_images(album=None):
    images = all_images()
    if album:
        images = [image for image in images if os.path.split(image)[0] == album]
    return dict(images=images, album=album, thumb_height=DEFAULT_THUMB_HEIGHT)

@pb.route('/show/<filename:path>')
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
        if not 'Model' in exif: exif['Model'] = 'unknown'
        pixsize = get_image_size(os.path.join(IMAGE_FOLDER, filename))
        exif['ExifImageWidth'] = pixsize[0]
        exif['ExifImageHeight'] = pixsize[1]
        for item in ['Model', 'FocalLength', 'FNumber', 'ExposureTime', 'ISOSpeedRatings', 'ExifImageWidth', 'ExifImageHeight']:
            if not item in exif: exif = None
    except:
        exif = None
    return dict(album=album, filename=filename, next=next, previous=previous, height=height, exif=exif, filesize=os.path.getsize(os.path.join(IMAGE_FOLDER, filename))/(1024.*1024.))

@api.route('/image/full/<filename:path>')
def full_size_image(filename):
    filename = clean_url_path(filename)
    dl = bool(request.query.get('dl', False))
    if dl:
        return static_file(filename, root=IMAGE_FOLDER, download=os.path.split(filename)[1])
    else:
        return static_file(filename, root=IMAGE_FOLDER)

def get_image_size(filepath):
    with Image.open(filepath) as img:
        return img.size

def get_exif_data(filename):
    with Image.open(filename) as im:
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
        decoded = ExifTags.TAGS.get(tag, tag)
        ret_exif[tag] = dict(name=decoded, value=value)
    return ret_exif

def named_exif(exif_data):
    ret_exif = dict()
    for tag, value in exif_data.items():
        decoded = ExifTags.TAGS.get(tag, tag)
        ret_exif[decoded] = value
    return ret_exif

@api.route('/exif/<filename:path>')
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
            if content['name'] == 'GPSInfo': continue
            ret[tag] = content
        return ret
    except IOError:
        abort(500, "cannot extract EXIF information for '%s'" % filename)

@api.route('/image/scaled/<height:int>/<filename:path>')
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
        with Image.open(os.path.join(IMAGE_FOLDER, filename)) as im:
            size = (height*2, height)
            exif = im._getexif()
            if exif != None:
                for tag, value in exif.items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    if decoded == 'Orientation':
                        if value == 3: im = im.rotate(180)
                        if value == 6: im = im.rotate(270)
                        if value == 8: im = im.rotate(90)
                        break
            im.thumbnail(size, Image.ANTIALIAS)
            mkdir_p(os.path.split(os.path.join(THUMBS_DIR, outfile))[0])
            im.save(os.path.join(THUMBS_DIR, outfile), "JPEG", quality=JPEG_QUALITY)
    except (IOError, NameError):
        abort(500, "cannot create thumbnail for '%s'" % filename)
    return static_file(outfile, root=THUMBS_DIR)

@pb.route('/static/<path:path>')
def static(path):
    return static_file(path, root=STATIC_PATH)

@error(404)
def error404(error):
    return "Error 404 - The requested document does not exist."

@pb.route('/robots.txt')
def robots():
    response.content_type = 'text/plain'
    return "User-agent: *\n{0}: /".format(ALLOW_CRAWLING)

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

pb.install(CachePlugin())

def auth(callback):
    def wrapper(*args, **kwargs):
        s = request.environ.get('beaker.session')
        if s.get('admin', False):
            return callback(*args, **kwargs)
        else:
            if ip_address(request.remote_addr).is_private:
                # visitors from local nets are automatically admins
                set_admin()
                return callback(*args, **kwargs)
            if request.path.startswith('/login') or request.path.startswith('/robots.txt'):
                return callback(*args, **kwargs)
            if request.path.startswith('/static'):
                return callback(*args, **kwargs)
            redirect('/login?requesting='+request.path)
    return wrapper

api.install(auth)

pb.mount('/api', api)

@pb.route('/login')
@view('login.jinja2')
def login():
    try:
        del response.headers['Cache-Control']
    except:
        pass
    return dict(requesting=request.query.get('requesting', '/'))

def check_login(name, password):
    return name == 'admin' and password == ADMIN_PASSWORD

@pb.route('/login', method='POST')
def do_login():
    try:
        del response.headers['Cache-Control']
    except:
        pass
    name     = request.forms.get('name')
    password = request.forms.get('password')
    if check_login(name, password):
        set_admin()
        redirect(request.query.get('requesting', '/'))
    return 'LOGIN FAILED'

def set_admin():
    s = request.environ.get('beaker.session')
    s['admin'] = True

pb.install(auth)

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 60*60*24*14,
    'session.data_dir': './.data',
    'session.auto': True,
    #'session.type': 'cookie',
    #'validate_key': 'zoJT9pWaQ2IM',
    #'encrypt_key': 'J7UolKPA1mIs'
    #'session.cookie_expires': 1200,
    #'session.auto': True
}

def define_caching(server):
    import memcache
    MC = memcache.Client([server], debug=0)
    MC_PREF = "PBMC_"
    MC_NS_KEY = MC.get(MC_PREF + "namespace_key");
    if not MC_NS_KEY :
        MC_NS_KEY = randint(1, 2147483648)
        MC.set(MC_PREF + "namespace_key", MC_NS_KEY)
    def caching(callback):
        def wrapper(*args, **kwargs):
            path = request.environ.get('PATH_INFO', '')
            if path.startswith('/show') or \
              path.startswith('/api/image'):
                key = MC_PREF + str(MC_NS_KEY) + path
                obj = MC.get(key)
                if not obj:
                    obj = callback(*args, **kwargs)
                    MC.set(key, obj)
                return obj
            else:
                return callback(*args, **kwargs)
        return wrapper
    return caching

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run this in a folder of images to serve them on the web')
    parser.add_argument('-p', '--port', default='8080', help='The port to run the web server on.')
    parser.add_argument('-6', '--ipv6', action='store_true',
    help='Listen to incoming connections via IPv6 instead of IPv4.')
    parser.add_argument('-t', '--thumbs-dir', default=THUMBS_DIR, help='The directory to store thumbnails in.')
    parser.add_argument('-a', '--admin-password', help='The admin password')
    parser.add_argument('-s', '--subdirs', action='store_true',
    help='Assume images to be stored in sub directories.')
    parser.add_argument('-c', '--allow-crawling', action='store_true',
    help='Allow Search engines to index the site (only useful if accessible without password).')
    parser.add_argument('-l', '--logfile', help='A logfile to log requests to.')
    parser.add_argument('-m', '--memcached', metavar='127.0.0.1:11211', help="Use a Memcached server for server side caching.")
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
        IMG_FILTER = [ IMAGE_FOLDER + '/' + IMG_FILTER, IMAGE_FOLDER + '/*/' + IMG_FILTER, IMAGE_FOLDER + '/*/*/' + IMG_FILTER]
    else:
        IMG_FILTER = IMAGE_FOLDER + '/' + IMG_FILTER
    if args.jpeg_quality not in range(0,101):
        parser.error('JPEG quality must be in the range of 0-100.')
    JPEG_QUALITY = args.jpeg_quality
    if args.debug and args.ipv6:
        parser.error('You cannot use IPv6 in debug mode, sorry.')
    if args.memcached:
        try:
            pb.install(define_caching(args.memcached))
        except ImportError:
            parser.error('You asked to use a memcached server. For this to work, install python3-memcached via pip.')
    if args.logfile:
        try:
            from requestlogger import WSGILogger, ApacheFormatter
        except ImportError:
            parser.error('You asked to log requests. For this to work, install wsgi-request-logger via pip.')
        from logging.handlers import TimedRotatingFileHandler
        handlers = [ TimedRotatingFileHandler(args.logfile, 'd', 7) , ]
        pb = WSGILogger(pb, handlers, ApacheFormatter())
    if args.admin_password:
        ADMIN_PASSWORD = args.admin_password
    else:
        ADMIN_PASSWORD = create_id(size=12)
    print("Admin Password Set To: {0}".format(ADMIN_PASSWORD))
    ALLOW_CRAWLING = 'Allow' if args.allow_crawling else 'Disallow'
    # As a last step, we replace the photobrowser pb with the session middleware.
    # If you do this earlier, Bottle plugins could not be added via .install() anymore.
    pb = SessionMiddleware(pb, session_opts)
    if args.debug:
        run(app=pb, host='0.0.0.0', port=args.port, debug=True, reloader=True)
    else:
        if args.ipv6:
            run(app=pb, host='::', server='cherrypy', port=args.port)
        else:
            run(app=pb, host='0.0.0.0', server='cherrypy', port=args.port)

