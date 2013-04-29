#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import route, run, static_file, get, request, template, response, redirect, error
import pprint
import re
import glob

@get('/')
def list_images():
    response.headers['Content-Type'] = 'text/plain; charset=UTF8'
    return pprint.pformat(glob.glob('*JPG'))

@get('/images')
def show_images():
    retval = ""
    for image in glob.glob('*JPG'):
        retval += "<img src='/image/%s'>\n" % image
    return retval

@route('/image/<path:path>')
def callback(path):
    return static_file(path, root='./')

@error(404)
def error404(error):
    return "Error 404 - The requested document does not exist."

run(host='0.0.0.0', port=8080, debug=True, reloader=True)
#run(host='0.0.0.0', port=8080)
#run(host='0.0.0.0', server='cherrypy', port=8080)

