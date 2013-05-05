### PhotoBrowser

PhotoBrowser is a dynamic image gallery generator
written in Python. It is meant to be used for your
image selection process on your local computer.

It runs a web server and serves images from a
local directory to your Browser. This allows
you to take a look at the photos in this directory
and should give you a couple of options to
select the best ones / delete bad ones and more.

### Requirements

This project needs Python to run. It is being tested on Python 2.7 and Python 3.3 on Mac OS X and on Windows 2012 Server.

Python modules needed:

* CherryPy, a fast web server
* PIL (Pillow on Python 3.3), the Python Imaging Library
* Jinja2, a flexible HTML template engine

##### Installation on Windows 2012 Server

1. Install Python 3.3.
2. Install [distribute](http://www.lfd.uci.edu/~gohlke/pythonlibs/#distribute) and [pip](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip)
3. Use pip to install CherryPy: `set PATH=C:\Python33\Scripts;%PATH%` and `pip install cherrypy`
4. Install [Pillow](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pil)
5. Install [Jinja2](http://www.lfd.uci.edu/~gohlke/pythonlibs/#jinja2)
6. Run via `set PATH=C:\Python33;%PATH%` and `python C:\Repos\PhotoBrowser\photobrowser.py -p 2222 -s .\`

#### Some ideas:

* Display if there is a related raw file.
* Let the user slide through all the images using a JS caroussel.
* Let the user delete bad JPEGs.
* Include an API call to generate all thumbnails at once.
* Clean up image directories (delete orphaned RAW files).
* Add a search field to search for album names or a slider to restrict the dates of the albums displayed 

#### References

* [sigal](http://sigal.saimon.org) is a static image gallery generator written in Python. I could certainly learn a lot from that project.

