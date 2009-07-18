#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2007       Johan Gonqvist <johan.gronqvist@gmail.com>
# Copyright (C) 2007       Gary Burton <gary.burton@zen.co.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Pubilc License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id: NarrativeWebWil2.py 10680 2008-05-06 06:47:22Z s_charette $

"""
Narrative Web Page generator.
"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import cgi
import os
import re
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import time
import locale
import shutil
import codecs
import tarfile
import operator
from gettext import gettext as _
from cStringIO import StringIO
from textwrap import TextWrapper
from unicodedata import normalize

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".WebPage")

#------------------------------------------------------------------------
#
# GRAMPS module
#
#------------------------------------------------------------------------
import gen.lib
import const
from GrampsCfg import get_researcher
import Sort
from gen.plug import PluginManager
from gen.plug.menu import PersonOption, NumberOption, StringOption, \
                          BooleanOption, EnumeratedListOption, FilterOption, \
                          NoteOption, MediaOption, DestinationOption
from ReportBase import (Report, ReportUtils, MenuReportOptions, CATEGORY_WEB,
                        Bibliography)
import Utils
import ThumbNails
import ImgManip
import Mime
from Utils import probably_alive
from QuestionDialog import ErrorDialog, WarningDialog
from BasicUtils import name_displayer as _nd
from DateHandler import displayer as _dd
from DateHandler import parser as _dp
from gen.proxy import PrivateProxyDb, LivingProxyDb
from gen.lib.eventroletype import EventRoleType

#------------------------------------------------------------------------
#
# constants
#
#------------------------------------------------------------------------
_NARRATIVE = "narrative.css"
_NARRATIVEPRINT = "narrative-print.css"
_PERSON = 0
_PLACE = 1
_INCLUDE_LIVING_VALUE = 99 # Arbitrary number
_NAME_COL  = 3

_MAX_IMG_WIDTH = 800   # resize images that are wider than this
_MAX_IMG_HEIGHT = 600  # resize images that are taller than this
_WIDTH = 160
_HEIGHT = 50
_VGAP = 10
_HGAP = 30
_SHADOW = 5
_XOFFSET = 5

# This information defines the list of styles in the Narrative Web
# options dialog as well as the location of the corresponding SCREEN
# stylesheets.
_CSS_FILES = [
    # First is used as default selection.
    [_("Basic-Ash"),            'Web_Basic-Ash.css'],
    [_("Basic-Cypress"),        'Web_Basic-Cypress.css'],
    [_("Basic-Lilac"),          'Web_Basic-Lilac.css'],
    [_("Basic-Peach"),          'Web_Basic-Peach.css'],
    [_("Basic-Spruce"),         'Web_Basic-Spruce.css'],
    [_("Mainz"),                'Web_Mainz.css'],
    [_("Nebraska"),             'Web_Nebraska.css'],
    [_("Visually Impaired"),    'Web_Visually.css'],

    [_("No style sheet"),  ''],
    ]

_CHARACTER_SETS = [
    # First is used as default selection.
    [_('Unicode (recommended)'), 'utf-8'],
    ['ISO-8859-1',  'iso-8859-1' ],
    ['ISO-8859-2',  'iso-8859-2' ],
    ['ISO-8859-3',  'iso-8859-3' ],
    ['ISO-8859-4',  'iso-8859-4' ],
    ['ISO-8859-5',  'iso-8859-5' ],
    ['ISO-8859-6',  'iso-8859-6' ],
    ['ISO-8859-7',  'iso-8859-7' ],
    ['ISO-8859-8',  'iso-8859-8' ],
    ['ISO-8859-9',  'iso-8859-9' ],
    ['ISO-8859-10', 'iso-8859-10' ],
    ['ISO-8859-13', 'iso-8859-13' ],
    ['ISO-8859-14', 'iso-8859-14' ],
    ['ISO-8859-15', 'iso-8859-15' ],
    ['koi8_r',      'koi8_r',     ],
    ]

_CC = [
    '',

    '<a rel="license" href="http://creativecommons.org/licenses/by/2.5/">'
    '<img alt="Creative Commons License - By attribution" '
    'title="Creative Commons License - By attribution" '
    'src="%(gif_fname)s" /></a>',

    '<a rel="license" href="http://creativecommons.org/licenses/by-nd/2.5/">'
    '<img alt="Creative Commons License - By attribution, No derivations" '
    'title="Creative Commons License - By attribution, No derivations" '
    'src="%(gif_fname)s" /></a>',

    '<a rel="license" href="http://creativecommons.org/licenses/by-sa/2.5/">'
    '<img alt="Creative Commons License - By attribution, Share-alike" '
    'title="Creative Commons License - By attribution, Share-alike" '
    'src="%(gif_fname)s" /></a>',

    '<a rel="license" href="http://creativecommons.org/licenses/by-nc/2.5/">'
    '<img alt="Creative Commons License - By attribution, Non-commercial" '
    'title="Creative Commons License - By attribution, Non-commercial" '
    'src="%(gif_fname)s" /></a>',

    '<a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/2.5/">'
    '<img alt="Creative Commons License - By attribution, Non-commercial, No derivations" '
    'title="Creative Commons License - By attribution, Non-commercial, No derivations" '
    'src="%(gif_fname)s" /></a>',

    '<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/2.5/">'
    '<img alt="Creative Commons License - By attribution, Non-commerical, Share-alike" '
    'title="Creative Commons License - By attribution, Non-commerical, Share-alike" '
    'src="%(gif_fname)s" /></a>'
    ]

_COPY_OPTIONS = [
        _('Standard copyright'),
        _('Creative Commons - By attribution'),
        _('Creative Commons - By attribution, No derivations'),
        _('Creative Commons - By attribution, Share-alike'),
        _('Creative Commons - By attribution, Non-commercial'),
        _('Creative Commons - By attribution, Non-commercial, No derivations'),
        _('Creative Commons - By attribution, Non-commercial, Share-alike'),
        _('No copyright notice'),
        ]


wrapper = TextWrapper()
wrapper.break_log_words = True
wrapper.width = 20

# This list of characters defines which hexadecimal entity certain
# 'special characters' with be transformed into for valid HTML
# rendering.  The variety of quotes with spaces are to assist in
# appropriately typesetting curly quotes and apostrophes.
html_escape_table = {
    "&"  : "&#38;",
    ' "'  : " &#8220;",
    '" '  : "&#8221; ",
    " '"  : " &#8216;",
    "' "  : "&#8217; ",
    "'s "  : "&#8217;s ",
    '"'  : "&#34;",
    "'"  : "&#39;",
    ">"  : "&#62;",
    "<"  : "&#60;",
    }

# This command then defines the 'html_escape' option for escaping
# special characters for presentation in HTML based on the above list.
def html_escape(text):
    """Produce entities within text."""
    L=[]
    for c in text:
        L.append(html_escape_table.get(c,c))
    return "".join(L)


def name_to_md5(text):
    """This creates an MD5 hex string to be used as filename."""
    return md5(text).hexdigest()

class BasePage:
    def __init__(self, title, options, archive, photo_list, gid):
        self.title_str = title
        self.gid = gid
        self.inc_download = options['incdownload']
        self.html_dir = options['target']
        self.copyright = options['cright']
        self.options = options
        self.archive = archive
        self.ext = options['ext']
        self.encoding = options['encoding']
        self.css = options['css']
        self.noid = options['nogid']
        self.linkhome = options['linkhome']
        self.showbirth = options['showbirth']
        self.showdeath = options['showdeath']
        self.showspouse = options['showspouse']
        self.showparents = options['showparents']
        self.showhalfsiblings = options['showhalfsiblings']
        self.use_intro = options['intronote'] != u""\
                    or options['introimg'] != u""
        self.use_contact = options['contactnote'] != u""\
                    or options['contactimg'] != u""
        self.use_gallery = options['gallery']
        self.header = options['headernote']
        self.footer = options['footernote']
        self.photo_list = photo_list
        self.usegraph = options['graph']
        self.graphgens = options['graphgens']
        self.use_home = self.options['homenote'] != "" or \
                        self.options['homeimg'] != ""
        self.page_title = ""
        self.warn_dir = True

    def store_file(self,archive, html_dir,from_path,to_path):
        if archive:
            archive.add(str(from_path),str(to_path))
        else:
            dest = os.path.join(html_dir,to_path)
            dirname = os.path.dirname(dest)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            if from_path != dest:
                shutil.copyfile(from_path,dest)
            elif self.warn_dir:
                WarningDialog(
                    _("Possible destination error") + "\n" +
                    _("You appear to have set your target directory "
                      "to a directory used for data storage. This "
                      "could create problems with file management. "
                      "It is recommended that you consider using "
                      "a different directory to store your generated "
                      "web pages."))
                self.warn_dir = False

    def copy_media(self,photo,store_ref=True):

        handle = photo.get_handle()
        if store_ref:
            lnk = (self.cur_name,self.page_title,self.gid)
            if self.photo_list.has_key(handle):
                if lnk not in self.photo_list[handle]:
                    self.photo_list[handle].append(lnk)
            else:
                self.photo_list[handle] = [lnk]

        ext = os.path.splitext(photo.get_path())[1]
        real_path = "%s/%s" % (self.build_path(handle, 'images'), handle+ext)
        thumb_path = "%s/%s" % (self.build_path(handle, ''), photo.get_description()+ext)
        return (real_path,thumb_path)

    def create_file(self, name):
        self.cur_name = self.build_name("", name)
        if self.archive:
            self.string_io = StringIO()
            of = codecs.EncodedFile(self.string_io,'utf-8',self.encoding,
                                    'xmlcharrefreplace')
        else:
            page_name = os.path.join(self.html_dir,self.cur_name)
            of = codecs.EncodedFile(open(page_name, "w"),'utf-8',
                                    self.encoding,'xmlcharrefreplace')
        return of

    def link_path(self, name,path):
        base = self.build_name("",name)
        path = "%s/%s" % (path, base)
        path = self.build_name(path, name)
        return path

    def create_link_file(self, name,path):
        self.cur_name = self.link_path(name,path)
        if self.archive:
            self.string_io = StringIO()
            of = codecs.EncodedFile(self.string_io,'utf-8',
                                    self.encoding,'xmlcharrefreplace')
        else:
            if path != "":
                dirname = "";
            else:
                dirname = os.path.join(self.html_dir,path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            page_name = self.build_name(dirname, name)
            of = codecs.EncodedFile(open(page_name, "w"),'utf-8',
                                    self.encoding,'xmlcharrefreplace')
        return of

    def close_file(self, of):
        if self.archive:
            tarinfo = tarfile.TarInfo(self.cur_name)
            tarinfo.size = len(self.string_io.getvalue())
            tarinfo.mtime = time.time()
            if os.sys.platform != "win32":
                tarinfo.uid = os.getuid()
                tarinfo.gid = os.getgid()
            self.string_io.seek(0)
            self.archive.addfile(tarinfo,self.string_io)
            of.close()
        else:
            of.close()

    def lnkfmt(self,text):
        return name_to_md5(text)

    def display_footer(self, of,db):
        if self.footer:
            note = db.get_note_from_gramps_id(self.footer)
            of.write('<div id="user_footer">\n')
            of.write('<p>')
            of.write(note.get(markup=True))
            of.write('</p>\n')
            of.write('</div>\n')
        if self.copyright == 0:
            of.write('<div id="copyright">\n')
            of.write('<p>')
            if self.author:
                self.author = self.author.replace(',,,','')
                year = time.localtime(time.time())[0]
                cright = _('&copy; %(year)d %(person)s') % {
                    'person' : self.author,
                    'year' : year }
                of.write('%s' % cright)
            of.write('</p>\n')
            of.write('</div>\n')
        elif self.copyright <=6:
            of.write('<div id="copyright">')
            text = _CC[self.copyright-1]
            if self.up:
                text = text.replace('#PATH#','../../../')
            else:
                text = text.replace('#PATH#','')
            of.write(text)
            of.write('</div>\n')
        of.write('</body>\n')
        of.write('</html>\n')

    def display_header(self, of,db,title,author="",up=False):
        self.up = up
        if up:
            path = "../"
        else:
            path = ""

        self.author = author

        of.write('<?xml version="1.0" encoding="iso-8859-1"?>\n')
        of.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n')
        of.write('    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
        of.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
        of.write('<head>\n')
        of.write('<link rel="stylesheet" type="text/css" href="tree.css" />\n')
        of.write('<title>%s</title>\n' % (title))
        of.write('</head>\n')
        of.write('<body>\n<p>')

        value = _dp.parse(time.strftime('%b %d %Y'))
        value = _dd.display(value)

        if self.linkhome:
            home_person_handle = db.get_default_handle()
            if home_person_handle:
                home_person = db.get_default_person()
                home_person_url = self.build_name(
                        self.build_path(home_person_handle, "", up),
                        home_person.handle)
                home_person_name = home_person.get_primary_name().get_regular_name()
                msg += _('<br />for <a href="%s">%s</a>') % (home_person_url, home_person_name)

        if self.header:
            note = db.get_note_from_gramps_id(self.header)
            of.write('<p>')
            of.write(note.get(markup=True))
            of.write('</p>\n')

        if self.use_home:
            index_page = "index"
            surname_page = "surnames"
            intro_page = "introduction"
        elif self.use_intro:
            index_page = ""
            surname_page = "surnames"
            intro_page = "index"
        else:
            index_page = ""
            surname_page = "index"
            intro_page = ""

        # Define 'self.currentsection' to correctly set navlink item CSS id
        # 'CurrentSection' for Navigation styling.
        # Use 'self.cur_name' to determine 'CurrentSection' for individual
        # elements for Navigation styling.
        self.currentsection = title

        if self.use_home:
            self.show_navlink(of,index_page,_('Home'),path)
        if self.use_intro:
            self.show_navlink(of,intro_page,_('Introduction'),path)
        self.show_navlink(of,surname_page,_('Surnames'),path)
        self.show_navlink(of,'individuals',_('Individuals'),path)
        self.show_navlink(of,'sources',_('Sources'),path)
        self.show_navlink(of,'places',_('Places'),path)
        if self.use_gallery:
            self.show_navlink(of,'gallery',_('Gallery'),path)
        if self.inc_download:
            self.show_navlink(of,'download',_('Download'),path)
        if self.use_contact:
            self.show_navlink(of,'contact',_('Contact'),path)
        of.write('</p>\n')

        # Give unique ID to 'content' div for styling specific sections separately.
        # Because of how this script was originally written, the appropriate section
        # ID is determined by looking for a directory or HTML file name to associate
        # with that section.
        if "index" in self.cur_name:
            divid = "Home"
        elif "introduction" in self.cur_name:
            divid = "Introduction"
        elif "surnames" in self.cur_name:
            divid = "Surnames"
        elif "srn" in self.cur_name:
            divid = "SurnameDetail"
        elif "individuals" in self.cur_name:
            divid = "Individuals"
        elif "ppl" in self.cur_name:
            divid = "IndividualDetail"
        elif "sources" in self.cur_name:
            divid = "Sources"
        elif "src" in self.cur_name:
            divid = "SourceDetail"
        elif "places" in self.cur_name:
            divid = "Places"
        elif "plc" in self.cur_name:
            divid = "PlaceDetail"
        elif "gallery" in self.cur_name:
            divid = "Gallery"
        elif "img" in self.cur_name:
            divid = "GalleryDetail"
        elif "download" in self.cur_name:
            divid = "Download"
        elif "contact" in self.cur_name:
            divid = "Contact"
        else:
            divid = ''
        if divid:
            divid = ' id="%s"' % divid

    def show_navlink(self, of, lpath, title, path):
        of.write('<a href="%s%s">%s</a>\n' % (lpath,self.ext,title))

    def display_first_image_as_thumbnail( self, of, db, photolist=None):

        if not photolist or not self.use_gallery:
            return

        photo_handle = photolist[0].get_reference_handle()
        photo = db.get_object_from_handle(photo_handle)
        mime_type = photo.get_mime_type()

        if mime_type:
            try:
                (real_path, newpath) = self.copy_media(photo)
                #self.media_link(of,photo_handle, newpath,'',up=True)
                of.write('<p><img src="images%s" alt="%s" /></p>\n' % (newpath, self.page_title))
            except (IOError,OSError),msg:
                WarningDialog(_("Could not add photo to page"),str(msg))
        else:
            descr = " ".join(wrapper.wrap(photo.get_description()))
            self.doc_link(of, photo_handle, descr, up=True)
            lnk = (self.cur_name, self.page_title, self.gid)
            if self.photo_list.has_key(photo_handle):
                if lnk not in self.photo_list[photo_handle]:
                    self.photo_list[photo_handle].append(lnk)
            else:
                self.photo_list[photo_handle] = [lnk]

    def display_additional_images_as_gallery( self, of, db, photolist=None):

        if not photolist or not self.use_gallery:
            return

        of.write('\n<h3>%s</h3>\n' % _('Gallery'))
        displayed = []
        for mediaref in photolist:

            photo_handle = mediaref.get_reference_handle()
            photo = db.get_object_from_handle(photo_handle)
            if photo_handle in displayed:
                continue
            mime_type = photo.get_mime_type()

            title = photo.get_description()
            if title == "":
                title = "(untitled)"
            if mime_type:
                try:
                    (real_path, newpath) = self.copy_media(photo)
                    descr = " ".join(wrapper.wrap(title))
                    #self.media_link(of, photo_handle, newpath, descr, up=False)
                    of.write('<p><img src="images%s" alt="%s" /></p>\n' % (newpath, self.page_title))
                except (IOError,OSError),msg:
                    WarningDialog(_("Could not add photo to page"),str(msg))
            else:
                try:
                    descr = " ".join(wrapper.wrap(title))
                    self.doc_link(of, photo_handle, descr, up=True)
                    lnk = (self.cur_name,self.page_title,self.gid)
                    if self.photo_list.has_key(photo_handle):
                        if lnk not in self.photo_list[photo_handle]:
                            self.photo_list[photo_handle].append(lnk)
                    else:
                        self.photo_list[photo_handle] = [lnk]
                except (IOError,OSError),msg:
                    WarningDialog(_("Could not add photo to page"),str(msg))
            displayed.append(photo_handle)

    def display_note_list(self, of,db, notelist=None):
        if not notelist:
            return

        for notehandle in notelist:
            note = db.get_note_from_handle(notehandle)
            format = note.get_format()
            text = note.get()
            try:
                text = unicode(text)
            except UnicodeDecodeError:
                text = unicode(str(text),errors='replace')

            if text:
                of.write('\n<h3>%s</h3>\n' % _('Narrative'))
                if format:
                    text = u"<pre>%s</pre>" % text
                else:
                    text = u"<br />".join(text.split("\n"))
                of.write('<p>%s</p>\n' % text)

    def display_url_list(self, of,urllist=None):
        if not urllist:
            return
        of.write('\n<h3>%s</h3>\n' % _('Weblinks'))
        of.write('<p>')

        index = 1
        for url in urllist:
            uri = url.get_path()
            descr = url.get_description()
            if not descr:
                descr = uri
            if url.get_type() == gen.lib.UrlType.EMAIL and not uri.startswith("mailto:"):
                of.write('<a href="mailto:%s">%s</a><br />\n' % (uri,descr))
            elif url.get_type() == gen.lib.UrlType.WEB_HOME and not uri.startswith("http://"):
                of.write('<a href="http://%s">%s</a><br />\n' % (uri,descr))
            elif url.get_type() == gen.lib.UrlType.WEB_FTP and not uri.startswith("ftp://"):
                of.write('<a href="ftp://%s">%s</a><br />\n' % (uri,descr))
            else:
                of.write('<a href="%s">%s</a><br />\n' % (uri,descr))
            index = index + 1
        of.write('</p>\n')

    def display_source_refs(self, of, db, bibli):
        if bibli.get_citation_count() == 0:
            return
        of.write('\n<h3>%s</h3>\n' % _('References'))
        of.write('<ol>\n')

        cindex = 0
        for citation in bibli.get_citation_list():
            cindex += 1
            # Add this source to the global list of sources to be displayed
            # on each source page.
            lnk = (self.cur_name, self.page_title, self.gid)
            shandle = citation.get_source_handle()
            if self.src_list.has_key(shandle):
                if lnk not in self.src_list[shandle]:
                    self.src_list[shandle].append(lnk)
            else:
                self.src_list[shandle] = [lnk]

            # Add this source and its references to the page
            source = db.get_source_from_handle(shandle)
            title = source.get_title()
            of.write('<li><a')
            self.source_link(of, source.gramps_id, title, source.gramps_id, True)
            of.write('</li>\n')
            for key,sref in citation.get_ref_list():

                tmp = []
                confidence = Utils.confidence.get(sref.confidence, _('Unknown'))
                if confidence == _('Normal'):
                    confidence = None
                for (label, data) in [(_('Date'), _dd.display(sref.date)),
                                      (_('Page'), sref.page),
                                      (_('Confidence'), confidence)]:
                    if data:
                        tmp.append("%s: %s" % (label, data))
                notelist = sref.get_note_list()
                for notehandle in notelist:
                    note = db.get_note_from_handle(notehandle)
                    tmp.append("%s: %s" % (_('Text'), note.get(True)))
                if len(tmp) > 0:
                    of.write('<li><a name="sref%d%s">' % (cindex,key))
                    of.write('; &nbsp; '.join(tmp))
                    of.write('</a></li>\n')
        of.write('</ol>\n')

    def display_references(self, of,db, handlelist):
        if not handlelist:
            return
        of.write('\n<h3>%s</h3>\n' % _('References'))
        of.write('<ol>\n')

        sortlist = sorted(handlelist,
                          key = operator.itemgetter(1),
                          cmp = locale.strcoll)

        for (path, name, gid) in sortlist:
            of.write('<li>')
            self.person_link(of, gid, name)
            of.write('</li>\n')
        of.write('</ol>\n')

    def build_path(self, handle, dirroot, up=False):
        path = ""
        if up:
            path = '../%s' % (dirroot)
        else:
            path = "%s" % (dirroot)
        return path

    def build_name(self, path, base):
        if path:
            return path + "/" + base + self.ext
        else:
            return base + self.ext

    def person_link(self, of,path, name,gid="",up=True):

        of.write('<a href="%s.html">%s' % (path, name))
        if not self.noid and gid != "":
            of.write(' [%s]' % gid)
        of.write('</a>')

    def surname_link(self, of, name, opt_val=None,up=False):
        handle = self.lnkfmt(name)
        dirpath = self.build_path(handle,'',up)

        of.write('<a href="%s%s">%s' % (name, self.ext, name))
        if opt_val != None:
            of.write('&nbsp;(%d)' % opt_val)
        of.write('</a>')

    def galleryNav_link(self,of,handle,name,up=False):
        dirpath = self.build_path(handle,'',up)
        of.write('<a href="%s%s">%s</a>' % (handle, self.ext, html_escape(name)))

    def media_ref_link(self,of,handle,name,up=False):
        dirpath = self.build_path(handle,'images',up)
        of.write('<a href="%s%s">%s</a>' % (handle, self.ext, html_escape(name)))

    def media_link(self, of, handle,path, name,up,usedescr=True):
        dirpath = self.build_path(handle,'',up)
        of.write('<a href="%s/%s%s">' % (dirpath, handle, self.ext))
        of.write('<img src="../%s" ' % path)
        of.write('alt="%s" /></a>' % name)
        if usedescr:
            of.write('<p>%s</p>\n' % html_escape(name))

    def doc_link(self, of, handle, name,up,usedescr=True):
        path = os.path.join('images','document.png')
        dirpath = self.build_path(handle, 'images', up)
        of.write('<a href="%s/%s%s">' % (dirpath, handle, self.ext))
        of.write('<img src="../%s" ' % path)
        of.write('alt="%s" /></a>' % html_escape(name))
        if usedescr:
            of.write('<p>%s</p>\n' % html_escape(name))

    def source_link(self, of, handle, name,gid="",up=False):
        dirpath = self.build_path(handle, '', up)
        of.write(' href="%s%s">%s' % (handle, self.ext, html_escape(name)))
        if not self.noid and gid != "":
            of.write('&nbsp;[%s]' % gid)
        of.write('</a>')

    def place_link(self, of, handle, name,gid="",up=False):
        dirpath = self.build_path(handle,'',up)
        of.write('<a href="%s%s">%s' % (handle, self.ext, html_escape(name)))

        if not self.noid and gid != "":
            of.write('&nbsp;[%s]' % gid)
        of.write('</a>')

    def place_link_str(self, handle, name,gid="",up=False):
        dirpath = self.build_path(handle,'',up)
        retval = '<a href="%s%s">%s' % (handle, self.ext, html_escape(name))

        if not self.noid and gid != "":
            retval = retval + '&nbsp;[%s]' % gid
        return retval + '</a>'

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class IndividualListPage(BasePage):

    def __init__(self, db, title, person_handle_list,
                 options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_file("individuals")
        self.display_header(of,db,_('Individuals'),
                            get_researcher().get_name())

        msg = _("This page contains an index of all the individuals in the "
                "database, sorted by their last names. Selecting the person&#8217;s "
                "name will take you to that person&#8217;s individual page.")

        of.write('<h3>%s</h3>\n' % _('Individuals'))
        of.write('<p id="description">%s</p>\n' % msg)
        of.write('<table summary="Individuals">\n')
        of.write('<tr>')
        of.write('<th>%s</th>' % _('Surname'))
        of.write('<th>%s</th>' % _('Name'))
        column_count = 2
        if self.showbirth:
            of.write('<th>%s</th>' % _('Birth'))
            column_count += 1
        if self.showdeath:
            of.write('<th>%s</th>' % _('Death'))
            column_count += 1
        if self.showspouse:
            of.write('<th>%s</th>' % _('Partner'))
            column_count += 1
        if self.showparents:
            of.write('<th>%s</th>' % _('Parents'))
            column_count += 1
        of.write('</tr>\n')

        person_handle_list = sort_people(db,person_handle_list)

        for (surname, handle_list) in person_handle_list:
            first = True
            for person_handle in handle_list:
                person = db.get_person_from_handle(person_handle)

                # surname column
                if first:
                    of.write('<tr><td colspan="3">&nbsp;</td></tr>\n')
                    of.write('<tr><td><a href="%s.html">%s</a>' % (surname ,surname))
                else:
                    of.write('<tr><td>&nbsp;')
                of.write('</td>')

                # firstname column
                of.write('<td>')
                path = self.build_path(person.handle,"",False)
                self.person_link(of, person.gramps_id,
                                 _nd.display_given(person))
                of.write('</td>')

                # birth column
                if self.showbirth:
                    of.write('<td>')
                    birth = ReportUtils.get_birth_or_fallback(db, person)
                    if birth:
                        if birth.get_type() == gen.lib.EventType.BIRTH:
                            of.write(_dd.display(birth.get_date_object()))
                        else:
                            of.write('<em>')
                            of.write(_dd.display(birth.get_date_object()))
                            of.write('</em>')
                    else:
                        of.write('&nbsp;')
                    
                    of.write('</td>')

                # death column
                if self.showdeath:
                    of.write('<td>')
                    death = ReportUtils.get_death_or_fallback(db, person)
                    if death:
                        if death.get_type() == gen.lib.EventType.DEATH:
                            of.write(_dd.display(death.get_date_object()))
                        else:
                            of.write('<em>')
                            of.write(_dd.display(death.get_date_object()))
                            of.write('</em>')
                    else:
                        of.write('&nbsp;')
                    of.write('</td>')

                # spouse (partner) column
                if self.showspouse:
                    of.write('<td>')
                    family_list = person.get_family_handle_list()
                    first_family = True
                    spouse_name = None
                    if family_list:
                        for family_handle in family_list:
                            family = db.get_family_from_handle(family_handle)
                            spouse_id = ReportUtils.find_spouse(person, family)
                            if spouse_id:
                                spouse = db.get_person_from_handle(spouse_id)
                                spouse_name = spouse.get_primary_name().get_regular_name()
                                if not first_family:
                                    of.write(', ')
                                of.write('%s' % spouse_name)
                                first_family = False
                    else:
                        of.write('&nbsp;')
                    of.write('</td>')

                # parents column
                if self.showparents:
                    of.write('<td>')
                    parent_handle_list = person.get_parent_family_handle_list()
                    if parent_handle_list:
                        parent_handle = parent_handle_list[0]
                        family = db.get_family_from_handle(parent_handle)
                        father_name = ''
                        mother_name = ''
                        father_id = family.get_father_handle()
                        mother_id = family.get_mother_handle()
                        father = db.get_person_from_handle(father_id)
                        mother = db.get_person_from_handle(mother_id)
                        if father:
                            father_name = father.get_primary_name().get_regular_name()
                        if mother:
                            mother_name = mother.get_primary_name().get_regular_name()
                        if mother and father:
                            of.write('%s %s' % (father_name, mother_name))
                        elif mother:
                            of.write('%s' % mother_name)
                        elif father:
                            of.write('%s' % father_name)
                    else:
                        of.write('&nbsp;')
                    of.write('</td>')

                # finished writing all columns
                of.write('</tr>\n')
                first = False

        of.write('</table>\n')
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class SurnamePage(BasePage):

    def __init__(self, db, title, person_handle_list, options, archive, media_list):

        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_link_file(title,'')
        self.display_header(of,db,title,get_researcher().get_name(),True)

        msg = _("This page contains an index of all the individuals in the "
                "database with the surname of %s. Selecting the person&#8217;s name "
                "will take you to that person&#8217;s individual page.") % title

        of.write('<h3>%s</h3>\n' % html_escape(title))
        of.write('<p id="description">%s</p>\n' % msg)
        of.write('<table summary="Surnames">\n')
        of.write('<tr>')
        of.write('<th>%s</th>' % _('Name'))
        if self.showbirth:
            of.write('<th>%s</th>' % _('Birth'))
        if self.showdeath:
            of.write('<th>%s</th>' % _('Death'))
        if self.showspouse:
            of.write('<th>%s</th>' % _('Partner'))
        if self.showparents:
            of.write('<th>%s</th>' % _('Parents'))
        of.write('</tr>\n')

        for person_handle in person_handle_list:

            # firstname column
            person = db.get_person_from_handle(person_handle)
            of.write('<tr>')
            of.write('<td>')
            path = self.build_path(person.handle,"",True)
            self.person_link(of, person.gramps_id,
                             person.get_primary_name().get_first_name())
            of.write('</td>')

            # birth column
            if self.showbirth:
                of.write('<td>')
                birth = ReportUtils.get_birth_or_fallback(db, person)
                if birth:
                    if birth.get_type() == gen.lib.EventType.BIRTH:
                        of.write(_dd.display(birth.get_date_object()))
                    else:
                        of.write('<em>')
                        of.write(_dd.display(birth.get_date_object()))
                        of.write('</em>')
                of.write('</td>')

            # death column
            if self.showdeath:
                of.write('<td>')
                death = ReportUtils.get_death_or_fallback(db, person)
                if death:
                    if death.get_type() == gen.lib.EventType.DEATH:
                        of.write(_dd.display(death.get_date_object()))
                    else:
                        of.write('<em>')
                        of.write(_dd.display(death.get_date_object()))
                        of.write('</em>')
                of.write('</td>')

            # spouse (partner) column
            if self.showspouse:
                of.write('<td>')
                family_list = person.get_family_handle_list()
                first_family = True
                spouse_name = None
                if family_list:
                    for family_handle in family_list:
                        family = db.get_family_from_handle(family_handle)
                        spouse_id = ReportUtils.find_spouse(person, family)
                        if spouse_id:
                            spouse = db.get_person_from_handle(spouse_id)
                            spouse_name = spouse.get_primary_name().get_regular_name()
                            if not first_family:
                                of.write(', ')
                            of.write('%s' % spouse_name)
                            first_family = False
                of.write('</td>')

            # parents column
            if self.showparents:
                of.write('<td>')
                parent_handle_list = person.get_parent_family_handle_list()
                if parent_handle_list:
                    parent_handle = parent_handle_list[0]
                    family = db.get_family_from_handle(parent_handle)
                    father_name = ''
                    mother_name = ''
                    father_id = family.get_father_handle()
                    mother_id = family.get_mother_handle()
                    father = db.get_person_from_handle(father_id)
                    mother = db.get_person_from_handle(mother_id)
                    if father:
                        father_name = father.get_primary_name().get_regular_name()
                    if mother:
                        mother_name = mother.get_primary_name().get_regular_name()
                    if mother and father:
                        of.write('<span class="father fatherNmother">%s</span> <span class="mother">%s</span>' % (father_name, mother_name))
                    elif mother:
                        of.write('<span class="mother">%s</span>' % mother_name)
                    elif father:
                        of.write('<span class="father">%s</span>' % father_name)
                of.write('</td>')

            # finished writing all columns
            of.write('</tr>\n')
        of.write('</table>\n')
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class PlaceListPage(BasePage):

    def __init__(self, db, title, place_handles, src_list, options, archive,
                 media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")
        of = self.create_file("places")
        self.display_header(of,db,_('Places'),
                            get_researcher().get_name())

        msg = _("This page contains an index of all the places in the "
                "database, sorted by their title. Clicking on a place&#8217;s "
                "title will take you to that place&#8217;s page.")

        of.write('<h2>%s</h2>\n' % _('Places'))
        of.write('<p>%s</p>\n' % msg )

        of.write('<table summary="Places">\n')
        of.write('<tr>')
        of.write('<th>%s</th>' % _('Letter'))
        of.write('<th>%s</th>' % _('Name'))
        of.write('</tr>\n')

        self.sort = Sort.Sort(db)
        handle_list = place_handles.keys()
        handle_list.sort(self.sort.by_place_title)
        last_letter = ''

        for handle in handle_list:
            place = db.get_place_from_handle(handle)
            n = ReportUtils.place_name(db, handle)

            if not n or len(n) == 0:
                continue

            letter = normalize('NFD', n)[0].upper()

            if letter != last_letter:
                last_letter = letter
                of.write('<tr><td colspan="2">&nbsp;</td></tr>\n')
                of.write('<tr><td>%s</td>' % last_letter)
                of.write('<td>')
                self.place_link(of,place.gramps_id, n,place.gramps_id)
                of.write('</td>')
                of.write('</tr>\n')
            else:
                of.write('<tr>')
                of.write('<td>&nbsp;</td>')
                of.write('<td>')
                self.place_link(of,place.gramps_id, n,place.gramps_id)
                of.write('</td>')
                of.write('</tr>\n')

        of.write('</table>\n')
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class PlacePage(BasePage):

    def __init__(self, db, title, place_handle, src_list, place_list, options,
                 archive, media_list):
        place = db.get_place_from_handle( place_handle)
        BasePage.__init__(self, title, options, archive, media_list,
                          place.gramps_id)
        of = self.create_link_file(place.gramps_id,"")
        self.page_title = ReportUtils.place_name(db,place_handle)
        self.display_header(of,db,"%s - %s" % (_('Places'), self.page_title), get_researcher().get_name(),up=True)

        media_list = place.get_media_list()
        self.display_first_image_as_thumbnail(of, db, media_list)

        of.write('<h2>Places:</h2>\n')
        of.write('<h3>%s</h3>\n\n' % html_escape(self.page_title.strip()))
        of.write('<table summary="Places">\n')

        if not self.noid:
            of.write('<tr>')
            of.write('<td>%s</td>' % _('GRAMPS ID'))
            of.write('<td>%s</td>' % place.gramps_id)
            of.write('</tr>\n')

        if place.main_loc:
            ml = place.main_loc
            for val in [(_('Street'),ml.street),
                        (_('City'),ml.city),
                        (_('Church Parish'),ml.parish),
                        (_('County'),ml.county),
                        (_('State/Province'),ml.state),
                        (_('Postal Code'),ml.postal),
                        (_('Country'),ml.country)]:
                if val[1]:
                    of.write('<tr>')
                    of.write('<td>%s</td>' % val[0])
                    of.write('<td>%s</td>' % val[1])
                    of.write('</tr>\n')

        if place.lat:
            of.write('<tr>')
            of.write('<td>%s</td>' % _('Latitude'))
            of.write('<td>%s</td>' % place.lat)
            of.write('</tr>\n')

        if place.long:
            of.write('<tr>')
            of.write('<td>%s</td>' % _('Longitude'))
            of.write('<td>%s</td>' % place.long)
            of.write('</tr>\n')

        of.write('</table>\n')

        if self.use_gallery:
            self.display_additional_images_as_gallery(of, db, media_list)
        self.display_note_list(of, db, place.get_note_list())
        self.display_url_list(of, place.get_url_list())
        self.display_references(of,db,place_list[place.handle])
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class MediaPage(BasePage):

    def __init__(self, db, title, handle, src_list, options, archive, media_list, info):

        (prev, next, page_number, total_pages) = info
        photo = db.get_object_from_handle(handle)
        BasePage.__init__(self, title, options, archive, media_list, photo.gramps_id)
        of = self.create_link_file(photo.gramps_id,"")

        self.db = db
        self.src_list = src_list

        mime_type = photo.get_mime_type()

        if mime_type:
            note_only = False
            newpath = self.copy_source_file(photo.get_description(), photo)
            target_exists = newpath != None
        else:
            note_only = True
            target_exists = False

        #self.copy_thumbnail(handle, photo)
        self.page_title = photo.get_description()
        self.display_header(of,db, "%s - %s" % (_('Gallery'), self.page_title), get_researcher().get_name(),up=True)

        of.write('\n<h3>%s</h3>\n<p>' % self.page_title)

        # gallery navigation
        if prev:
            self.galleryNav_link(of,db.get_object_from_handle(prev).gramps_id,_('Previous'),False)
        data = _('%(page_number)d of %(total_pages)d' ) % {
            'page_number' : page_number, 'total_pages' : total_pages }
        of.write(' %s ' % data)
        if next:
            self.galleryNav_link(of,db.get_object_from_handle(next).gramps_id,_('Next'),False)
        of.write('</p>\n<p>')

        if mime_type:
            if mime_type.startswith("image/"):
                if target_exists:
                    # if the image is spectacularly large, then force the client
                    # to resize it, and include a "<a href=" link to the actual
                    # image; most web browsers will dynamically resize an image
                    # and provide zoom-in/zoom-out functionality when the image
                    # is displayed directly
                    (width, height) = ImgManip.image_size(
                            Utils.media_path_full(self.db, photo.get_path()))
                    scale = 1.0
                    of.write('')
                    if width > _MAX_IMG_WIDTH or height > _MAX_IMG_HEIGHT:
                        # image is too large -- scale it down and link to the full image
                        scale = min(float(_MAX_IMG_WIDTH)/float(width), float(_MAX_IMG_HEIGHT)/float(height))
                        width = int(width * scale)
                        height = int(height * scale)
                        of.write('<a href="%s">' % newpath)
                    of.write('<img src="%s" alt="%s" />' % (newpath, html_escape(self.page_title)))
                    if scale <> 1.0:
                        of.write('</a>');

                else:
                    of.write('(%s)' % _("The file has been moved or deleted"))
            else:
                import tempfile

                dirname = tempfile.mkdtemp()
                thmb_path = os.path.join(dirname,"temp.png")
                if ThumbNails.run_thumbnailer(mime_type,
                                              Utils.media_path_full(self.db,
                                                            photo.get_path()),
                                              thmb_path, 320):
                    try:
                        path = "%s/%s.png" % (self.build_path(photo.handle,"preview"),photo.handle)
                        self.store_file(archive, self.html_dir, thmb_path, path)
                        os.unlink(thmb_path)
                    except IOError:
                        path = os.path.join('images','document.png')
                else:
                    path = os.path.join('images','document.png')
                os.rmdir(dirname)

                if target_exists:
                    of.write('<a href="%s" alt="%s" />' % (newpath, html_escape(self.page_title)))
                of.write('<img src="%s" alt="%s" />' % (path, html_escape(self.page_title)))
                if target_exists:
                    of.write('</a>')
                else:
                    of.write('(%s)' % _("The file has been moved or deleted"))
        else:
            path = os.path.join('images','document.png')
            of.write('<img src="%s" alt="%s" />' % (path, html_escape(self.page_title)))

        of.write('</p>\n<h3>%s</h3>\n' % html_escape(self.page_title.strip()))
        of.write('<table summary="Gallery">\n')

        if not self.noid:
            of.write('<tr>')
            of.write('<td>%s</td>' % _('GRAMPS ID'))
            of.write('<td>%s</td>' % photo.gramps_id)
            of.write('</tr>\n')
        if not note_only and not mime_type.startswith("image/"):
            of.write('<tr>')
            of.write('<td>%s</td>' % _('File type'))
            of.write('<td>%s</td>' % Mime.get_description(mime_type))
            of.write('</tr>\n')
        date = _dd.display(photo.get_date_object())
        if date != "":
            of.write('<tr>')
            of.write('<td>%s</td>' % _('Date'))
            of.write('<td>%s</td>' % date)
            of.write('</tr>\n')
        of.write('</table>\n')

        self.display_note_list(of, db, photo.get_note_list())
        self.display_attr_list(of, photo.get_attribute_list())
        self.display_media_sources(of, db, photo)
        self.display_references(of,db,media_list)
        self.display_footer(of,db)
        self.close_file(of)

    def display_media_sources(self, of, db, photo):
        self.bibli = Bibliography()
        for sref in photo.get_source_references():
            self.bibli.add_reference(sref)
        self.display_source_refs(of, db, self.bibli)

    def display_attr_list(self, of,attrlist=None):
        if not attrlist:
            return
        of.write('<h3>%s</h3>\n' % _('Attributes'))
        of.write('<table summary="Attributes">\n')

        for attr in attrlist:
            atType = str( attr.get_type() )
            of.write('<tr>')
            of.write('<td>%s</td>' % atType)
            of.write('<td>%s</td>' % attr.get_value())
            of.write('</tr>\n')
        of.write('</table>\n')

    def copy_source_file(self, handle,photo):
        ext = os.path.splitext(photo.get_path())[1]
        to_dir = self.build_path(handle,'images')
        newpath = to_dir + "/" + handle + ext

        fullpath = Utils.media_path_full(self.db, photo.get_path())
        try:
            if self.archive:
                self.archive.add(fullpath,str(newpath))
            else:
                to_dir = os.path.join(self.html_dir,to_dir)
                if not os.path.isdir(to_dir):
                    os.makedirs(to_dir)
                shutil.copyfile(fullpath,
                                os.path.join(self.html_dir, newpath))
            return newpath
        except (IOError,OSError),msg:
            error = _("Missing media object:") +                               \
                     "%s (%s)" % (photo.get_description(),photo.get_gramps_id())
            WarningDialog(error,str(msg))
            return None

    def copy_thumbnail(self, handle,photo):
        to_dir = self.build_path(handle,'thumb')
        to_path = os.path.join(to_dir, handle+".png")
        if photo.get_mime_type():
            from_path = ThumbNails.get_thumbnail_path(Utils.media_path_full(
                                                            self.db,
                                                            photo.get_path()),
                                                      photo.get_mime_type())
            if not os.path.isfile(from_path):
                from_path = os.path.join(const.IMAGE_DIR,"document.png")
        else:
            from_path = os.path.join(const.IMAGE_DIR,"document.png")

        if self.archive:
            self.archive.add(from_path,to_path)
        else:
            to_dir = os.path.join(self.html_dir,to_dir)
            dest = os.path.join(self.html_dir,to_path)
            if not os.path.isdir(to_dir):
                os.makedirs(to_dir)
            try:
                shutil.copyfile(from_path,dest)
            except IOError:
                print "Could not copy file"

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class SurnameListPage(BasePage):
    ORDER_BY_NAME = 0
    ORDER_BY_COUNT = 1
    def __init__(self, db, title, person_handle_list, options, archive,
                 media_list, order_by=ORDER_BY_NAME,filename="surnames"):

        BasePage.__init__(self, title, options, archive, media_list, "")
        if order_by == self.ORDER_BY_NAME:
            of = self.create_file(filename)
            self.display_header(of,db,_('Surnames'),get_researcher().get_name())
            of.write('\n<h3>%s</h3>\n' % _('Surnames'))
        else:
            of = self.create_file("surnames_count")
            self.display_header(of,db,_('Surnames by person count'),
                            get_researcher().get_name())
            of.write('\n<h3>%s</h3>\n' % _('Surnames by person count'))

        of.write('<p>%s</p>\n' % _(
            'This page contains an index of all the '
            'surnames in the database. Selecting a link '
            'will lead to a list of individuals in the '
            'database with this same surname.'))

        if order_by == self.ORDER_BY_COUNT:
            of.write('<table summary="Surnames">\n')
            of.write('<tr>')
        else:
            of.write('<table summary="Surnames">\n')
            of.write('<tr>')
        of.write('<th>%s</th>' % _('Letter'))

        if not self.use_home and not self.use_intro:
            of.write('<th><a href="%s%s">%s</a></th>' % ("index", self.ext,  _('Surname')))
        else:
            of.write('<th><a href="%s%s">%s</a></th>' % ("surnames", self.ext, _('Surname')))
        of.write('<th><a href="%s%s">%s</a></th>' % ("surnames_count", self.ext, _('Number of people')))
        of.write('</tr>\n')

        person_handle_list = sort_people(db,person_handle_list)
        if order_by == self.ORDER_BY_COUNT:
            temp_list = {}
            for (surname,data_list) in person_handle_list:
                index_val = "%90d_%s" % (999999999-len(data_list),surname)
                temp_list[index_val] = (surname,data_list)
            temp_keys = temp_list.keys()
            temp_keys.sort()
            person_handle_list = []
            for key in temp_keys:
                person_handle_list.append(temp_list[key])

        last_letter = ''
        last_surname = ''

        for (surname,data_list) in person_handle_list:
            if len(surname) == 0:
                continue

            # Get a capital normalized version of the first letter of
            # the surname
            letter = normalize('NFD',surname)[0].upper()

            if letter != last_letter:
                last_letter = letter
                of.write('<tr><td colspan="2">&nbsp;</td></tr>\n')
                of.write('<tr><td>%s</td>' % last_letter)
                of.write('<td>')
                self.surname_link(of,surname)
                of.write('</td>')
            elif surname != last_surname:
                of.write('<tr>')
                of.write('<td>&nbsp;</td>')
                of.write('<td>')
                self.surname_link(of,surname)
                of.write('</td>')
                last_surname = surname
            of.write('<td>%d</td>' % len(data_list))
            of.write('</tr>\n')

        of.write('</table>\n')
        self.display_footer(of,db)
        self.close_file(of)
        return

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class IntroductionPage(BasePage):

    def __init__(self, db, title, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")
        note_id = options['intronote']
        pic_id =  options['introimg']

        if self.use_home:
            of = self.create_file("introduction")
        else:
            of = self.create_file("index")

        author = get_researcher().get_name()
        self.display_header(of, db, _('Introduction'), author)

        of.write('<h2>%s</h2>\n' % _('Introduction'))

        if pic_id:
            obj = db.get_object_from_gramps_id(pic_id)
            mime_type = obj.get_mime_type()
            if mime_type and mime_type.startswith("image"):
                try:
                    (newpath, thumb_path) = self.copy_media(obj, False)
                    self.store_file(archive, self.html_dir,
                                    Utils.media_path_full(db,
                                                          obj.get_path()),
                                    newpath)
                    of.write('<img ')
                    of.write('src="%s" ' % newpath)
                    of.write('alt="%s" />' % obj.get_description())
                except (IOError, OSError), msg:
                    WarningDialog(_("Could not add photo to page"), str(msg))

        if note_id:
            note_obj = db.get_note_from_gramps_id(note_id)
            text = note_obj.get(markup=True)
            if note_obj.get_format():
                of.write(u'\t<pre>%s</pre>\n' % text)
            else:
                of.write(u'<br />'.join(text.split("\n")))

        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class HomePage(BasePage):

    def __init__(self, db, title, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        note_id = options['homenote']
        pic_id =  options['homeimg']
        of = self.create_file("index")
        author = get_researcher().get_name()
        self.display_header(of,db,_('Home'),author)

        of.write('\n<h3>%s</h3>\n' % _('Home'))

        if pic_id:
            obj = db.get_object_from_gramps_id(pic_id)
            mime_type = obj.get_mime_type()
            if mime_type and mime_type.startswith("image"):
                try:
                    (newpath, thumb_path) = self.copy_media(obj, False)
                    self.store_file(archive, self.html_dir, obj.get_path(),
                                    newpath)
                    of.write('<img ')
                    of.write('src="%s" ' % newpath)
                    of.write('alt="%s" />' % obj.get_description())
                except (IOError, OSError), msg:
                    WarningDialog(_("Could not add photo to page"), str(msg))

        if note_id:
            note_obj = db.get_note_from_gramps_id(note_id)
            text = note_obj.get(markup=True)
            if note_obj.get_format():
                of.write(u'\t<pre>%s</pre>' % text)
            else:
                of.write(u'<br />'.join(text.split("\n")))

        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class SourcesPage(BasePage):

    def __init__(self, db, title, handle_set, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_file("sources")
        author = get_researcher().get_name()
        self.display_header(of, db, _('Sources'), author)

        handle_list = list(handle_set)
        source_dict = {}

        #Sort the sources
        for handle in handle_list:
            source = db.get_source_from_handle(handle)
            key = source.get_title() + str(source.get_gramps_id())
            source_dict[key] = (source, handle)
        keys = source_dict.keys()
        keys.sort(locale.strcoll)

        msg = _("This page contains an index of all the sources in the "
                "database, sorted by their title. Clicking on a source&#8217;s "
                "title will take you to that source&#8217;s page.")

        of.write('<h3>%s</h3>\n' % _('Sources'))
        of.write('<p>')
        of.write(msg)
        of.write('</p>\n<ol>\n')
        for key in keys:
            (source, handle) = source_dict[key]
            of.write('<li><a')
            self.source_link(of, source.gramps_id,source.get_title())
            of.write('</li>\n')

        of.write('</ol>\n')
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class SourcePage(BasePage):

    def __init__(self, db, title, handle, src_list, options, archive,
                 media_list):
        source = db.get_source_from_handle( handle)
        BasePage.__init__(self, title, options, archive, media_list,
                          source.gramps_id)
        of = self.create_link_file(source.gramps_id,"")
        self.page_title = source.get_title()
        self.display_header(of,db,"%s - %s" % (_('Sources'), self.page_title),
                            get_researcher().get_name(),up=True)

        media_list = source.get_media_list()
        self.display_first_image_as_thumbnail(of, db, media_list)

        of.write('<h3>%s</h3>\n\n' % html_escape(self.page_title.strip()))
        of.write('<table summary="source">\n')

        grampsid = None
        if not self.noid:
            grampsid = source.gramps_id

        for (label,val) in [(_('GRAMPS ID'),grampsid),
                            (_('Author'),source.author),
                            (_('Publication information'),source.pubinfo),
                            (_('Abbreviation'),source.abbrev)]:
            if val:
                of.write('<tr>')
                of.write('<td>%s</td>' % label)
                of.write('<td>%s</td>' % val)
                of.write('</tr>\n')

        of.write('</table>\n')

        self.display_additional_images_as_gallery(of, db, media_list)
        self.display_note_list(of, db, source.get_note_list())
        self.display_references(of,db,src_list[source.handle])
        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class GalleryPage(BasePage):

    def __init__(self, db, title, handle_set, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_file("gallery")
        self.display_header(of,db, _('Gallery'), get_researcher().get_name())

        of.write('\n<h3>%s</h3>\n<p>' % _('Gallery'))

        of.write(_("This page contains an index of all the media objects "
                   "in the database, sorted by their title. Clicking on "
                   "the title will take you to that media object&#8217;s page."))
        of.write('</p>\n<ol>\n')

        self.db = db

        index = 1
        mlist = media_list.keys()
        sort = Sort.Sort(self.db)
        mlist.sort(sort.by_media_title)
        for handle in mlist:
            media = db.get_object_from_handle(handle)
            date = _dd.display(media.get_date_object())
            title = media.get_description()
            if title == "":
                title = "untitled"
            of.write('<li>')

            self.media_ref_link(of, media.get_gramps_id(), title)

            of.write('</li>\n')
            
        of.write('</ol>\n')

        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DownloadPage(BasePage):

    def __init__(self, db, title, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_file("download")
        self.display_header(of,db,_('Download'),
                            get_researcher().get_name())

        of.write('<h2>%s</h2>\n\n' % _('Download'))

        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class ContactPage(BasePage):

    def __init__(self, db, title, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list, "")

        of = self.create_file("contact")
        self.display_header(of,db,_('Contact'),
                            get_researcher().get_name())

        of.write('<h2>%s</h2>\n\n' % _('Contact'))
        of.write('<div id="summaryarea">\n')

        note_id = options['contactnote']
        pic_id = options['contactimg']
        if pic_id:
            obj = db.get_object_from_gramps_id(pic_id)
            mime_type = obj.get_mime_type()
            if mime_type and mime_type.startswith("image"):
                try:
                    (newpath, thumb_path) = self.copy_media(obj, False)
                    self.store_file(archive, self.html_dir,
                                    Utils.media_path_full(db,
                                                          obj.get_path()),
                                    newpath)
                    of.write('<img height="200" ')
                    of.write('src="%s" ' % newpath)
                    of.write('alt="%s" />' % obj.get_description())
                except (IOError, OSError), msg:
                    WarningDialog(_("Could not add photo to page"), str(msg))

        r = get_researcher()

        if r.name:
            of.write('<h3>%s</h3>\n' % r.name.replace(',,,',''))
        if r.addr:
            of.write('<span id="streetaddress">%s</span>\n' % r.addr)
        text = "".join([r.city,r.state,r.postal])
        if text:
            of.write('<span id="city">%s</span>\n' % r.city)
            of.write('<span id="state">%s</span>\n' % r.state)
            of.write('<span id="postalcode">%s</span>\n' % r.postal)
        if r.country:
            of.write('<span id="country">%s</span>\n' % r.country)
        if r.email:
            of.write('<span id="email"><a href="mailto:%s?subject=from GRAMPS Web Site">%s</a></span>\n' % (r.email,r.email))

        if note_id:
            note_obj = db.get_note_from_gramps_id(note_id)
            text = note_obj.get(markup=True)
            if note_obj.get_format():
                text = u"\t\t<pre>%s</pre>" % text
            else:
                text = u"<br />".join(text.split("\n"))
            of.write('<p>%s</p>\n' % text)

        self.display_footer(of,db)
        self.close_file(of)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class IndividualPage(BasePage):
    """
    This class is used to write HTML for an individual.
    """

    gender_map = {
        gen.lib.Person.MALE    : _('male'),
        gen.lib.Person.FEMALE  : _('female'),
        gen.lib.Person.UNKNOWN : _('unknown'),
        }

    def __init__(self, db, person, title, ind_list,
                 place_list, src_list, options, archive, media_list):
        BasePage.__init__(self, title, options, archive, media_list,
                          person.gramps_id)
        self.person = person
        self.db = db
        self.ind_list = ind_list
        self.src_list = src_list
        self.bibli = Bibliography()
        self.place_list = place_list
        self.sort_name = _nd.sorted(self.person)
        self.name = _nd.sorted(self.person)

        of = self.create_link_file(person.gramps_id,"")
        self.display_header(of,db, self.sort_name,
                            get_researcher().get_name(),up=True)
        self.display_ind_general(of)
        self.display_ind_events(of)
        self.display_attr_list(of, self.person.get_attribute_list())
        self.display_ind_parents(of)
        self.display_ind_relationships(of)
        self.display_addresses(of)

        media_list = []
        photolist = self.person.get_media_list()
        if len(photolist) > 1:
            media_list = photolist[1:]
        for handle in self.person.get_family_handle_list():
            family = self.db.get_family_from_handle(handle)
            media_list += family.get_media_list()
            for evt_ref in family.get_event_ref_list():
                event = self.db.get_event_from_handle(evt_ref.ref)
                media_list += event.get_media_list()
        for evt_ref in self.person.get_primary_event_ref_list():
            event = self.db.get_event_from_handle(evt_ref.ref)
            if event:
                media_list += event.get_media_list()

        self.display_additional_images_as_gallery(of, db, media_list)
        self.display_note_list(of, db, self.person.get_note_list())
        self.display_url_list(of, self.person.get_url_list())
        self.display_ind_sources(of)
        self.display_ind_pedigree(of)
        if self.usegraph:
            self.display_tree(of)
        self.display_footer(of,db)
        self.close_file(of)

    def display_attr_list(self, of,attrlist=None):
        if not attrlist:
            return
        of.write('\n<h3>%s</h3>\n' % _('Attributes'))
        of.write('<table summary="attributes">\n')

        for attr in attrlist:
            atType = str( attr.get_type() )
            of.write('<tr><td>%s:</td>' % atType)
            value = attr.get_value()
            value += self.get_citation_links( attr.get_source_references() )
            of.write('<td>%s</td></tr>\n' % value)
        of.write('</table>\n')
 
    def draw_box(self, of,center,col,person):
        top = center - _HEIGHT/2
        xoff = _XOFFSET+col*(_WIDTH+_HGAP)

        of.write('<div class="boxbg" style="top: %dpx; left: %dpx;">\n' % (top,xoff+1))
        of.write('<div class="box">')
        person_link = person.handle in self.ind_list
        if person_link:
            person_name = _nd.display(person)
            path = self.build_path(person.handle,"",False)
            fname = self.build_name(path,person.handle)
            self.person_link(of, person.gramps_id, person_name)
        else:
            of.write(_nd.display(person))
        of.write('</div>\n')
        of.write('</div>\n')
        of.write('<div class="shadow" style="top: %dpx; left: %dpx;"></div>\n' % (top+_SHADOW,xoff+_SHADOW))

    def extend_line(self, of,y0,x0):
        of.write('<div class="bvline" style="top: %dpx; left: %dpx; width: %dpx;"></div>\n' %
                 (y0,x0,_HGAP/2))
        of.write('<div class="gvline" style="top: %dpx; left: %dpx; width: %dpx;"></div>\n' %
                 (y0+_SHADOW,x0,_HGAP/2+_SHADOW))

    def connect_line(self, of,y0,y1,col):
        if y0 < y1:
            y = y0
        else:
            y = y1

        x0 = _XOFFSET + col * _WIDTH + (col-1)*_HGAP + _HGAP/2
        of.write('<div class="bvline" style="top: %dpx; left: %dpx; width: %dpx;"></div>\n' %
                 (y1,x0,_HGAP/2))
        of.write('<div class="gvline" style="top: %dpx; left: %dpx; width: %dpx;"></div>\n' %
                 (y1+_SHADOW,x0+_SHADOW,_HGAP/2+_SHADOW))
        of.write('<div class="bhline" style="top: %dpx; left: %dpx; height: %dpx;"></div>\n' %
                 (y,x0,abs(y0-y1)))
        of.write('<div class="ghline" style="top: %dpx; left: %dpx; height: %dpx;"></div>\n' %
                 (y+_SHADOW,x0+_SHADOW,abs(y0-y1)))

    def draw_connected_box(self, of,center1,center2,col, handle):
        if not handle:
            return None
        person = self.db.get_person_from_handle(handle)
        self.draw_box(of,center2,col,person)
        self.connect_line(of,center1,center2,col)
        return person

    def display_tree(self, of):
        if not self.person.get_main_parents_family_handle():
            return
        
        of.write('\n<h3>%s</h3>\n' % _('Ancestors'))

        of.write('<pre>\n')
        tree = MiniTree(self.db, self.person, of, self.ind_list, self.graphgens, self.ext)
        for line in tree.lines:
            if line: of.write(line + '\n')
        of.write('</pre>\n')

    def draw_tree(self, of,gen,maxgen,max_size, old_center, new_center,phandle):
        if gen > maxgen:
            return
        gen_offset = int(max_size / pow(2,gen+1))
        person = self.db.get_person_from_handle(phandle)
        if not person:
            return

        if gen == 1:
            self.draw_box(of, new_center,0,person)
        else:
            self.draw_connected_box(of, old_center, new_center,gen-1,phandle)

        if gen == maxgen:
            return

        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            line_offset = _XOFFSET + (gen)*_WIDTH + (gen-1)*_HGAP
            self.extend_line(of, new_center,line_offset)

            gen = gen + 1
            family = self.db.get_family_from_handle(family_handle)

            f_center = new_center-gen_offset
            f_handle = family.get_father_handle()
            self.draw_tree(of,gen,maxgen,max_size, new_center,f_center,f_handle)

            m_center = new_center+gen_offset
            m_handle = family.get_mother_handle()
            self.draw_tree(of,gen,maxgen,max_size, new_center,m_center,m_handle)

    def display_ind_sources(self, of):
        for sref in self.person.get_source_references():
            self.bibli.add_reference(sref)
        if self.bibli.get_citation_count() == 0:
            return
        self.display_source_refs(of, self.db, self.bibli)

    def display_ind_pedigree(self, of):

        parent_handle_list = self.person.get_parent_family_handle_list()
        if parent_handle_list:
            parent_handle = parent_handle_list[0]
            family = self.db.get_family_from_handle(parent_handle)
            father_id = family.get_father_handle()
            mother_id = family.get_mother_handle()
            mother = self.db.get_person_from_handle(mother_id)
            father = self.db.get_person_from_handle(father_id)
        else:
            family = None
            father = None
            mother = None

        of.write('\n<h3>%s</h3>\n<dl>' % _('Pedigree'))

        if father or mother:  
            of.write('<dt>')
            if father and mother:
                self.pedigree_person(of,father)
                of.write('</dt>\n<dd>\n<dl>\n<dt>+ ')
                self.pedigree_person(of,mother,True)
            elif father:
                self.pedigree_person(of,father)
            elif mother:
                of.write('+ ')
                self.pedigree_person(of,mother,True)
            of.write('</dt>\n')

        num = 0
        if family:
            for child_ref in family.get_child_ref_list():
                num = num + 1
                child_handle = child_ref.ref
                if child_handle == self.person.handle:
                    family_list = self.person.get_family_handle_list()
                    if family_list: 
                        of.write('<dd><dl><dt><strong>%d. %s</strong></dt>\n<dd>\n<dl>\n' % (num, self.name))
                        self.pedigree_family(of, num)
                        of.write('</dl></dd>\n</dl></dd>\n')
                    else:
                        of.write('<dd><strong>%d. %s</strong></dd>' % (num, self.name))
                else:
                    of.write('<dd>%d. ' % num)
                    child = self.db.get_person_from_handle(child_handle)
                    self.pedigree_person(of,child)
                    of.write('</dd>\n')
        else:
            of.write('<dt><strong>%s</strong></dt>' % self.name)
            self.pedigree_family2(of, 1)
        if father and mother:
            of.write('</dl>\n</dd>\n')
        of.write('</dl>\n')

    def display_ind_general(self, of):
        self.page_title = self.sort_name
        self.display_first_image_as_thumbnail(of, self.db,
                                              self.person.get_media_list())

        of.write('\n<h3>%s</h3>\n' % self.sort_name.strip())
            
        of.write('<table summary="general">\n')

        # GRAMPS ID
        if not self.noid:
            of.write('<tr><td>%s:</td>' % _('GRAMPS ID'))
            of.write('<td>%s</td>' % self.person.gramps_id)
            of.write('</tr>\n')

        # Names [and their sources]
        for name in [self.person.get_primary_name(),]+self.person.get_alternate_names():
            pname = _nd.display_name(name)
            pname += self.get_citation_links( name.get_source_references() )
            type = str( name.get_type() )
            of.write('<tr><td>%s:</td>' % _(type))
            of.write('<td>%s' % pname)
            of.write('</td></tr>\n')

        # Gender
        nick = self.person.get_nick_name()
        if nick:
            of.write('<tr><td>%s:</td>' % _('Nickname'))
            of.write('<td>%s</td>' % nick)
            of.write('</tr>\n')

        # Gender
        of.write('<tr><td>%s:</td>' % _('Gender'))
        gender = self.gender_map[self.person.gender]
        of.write('<td>%s</td>' % gender)
        of.write('</tr>\n</table>\n')

    def display_ind_events(self, of):
        evt_ref_list = self.person.get_event_ref_list()

        if not evt_ref_list:
            return

        of.write('\n<h3>%s</h3>\n' % _('Events'))
        of.write('<table summary="events">\n')

        for event_ref in evt_ref_list:
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                evt_name = str(event.get_type())

                if event_ref.get_role() == EventRoleType.PRIMARY:
                    of.write('<tr><td>%s:</td>' % evt_name)
                else:
                    of.write('<tr><td>%s (%s)</td>' \
                        % (evt_name, event_ref.get_role()))

                of.write('<td>')
                of.write(self.format_event(event, event_ref))
                of.write('</td></tr>\n')
        of.write('</table>\n')

    def display_addresses(self, of):
        alist = self.person.get_address_list()

        if len(alist) == 0:
            return

        of.write('\n<h3>%s</h3>\n<p>' % _('Addresses'))

        for addr in alist:
            location = ReportUtils.get_address_str(addr)
            location += self.get_citation_links( addr.get_source_references() )
            date = _dd.display(addr.get_date_object())

            of.write('%s %s<br />\n' % (location, date))

        of.write('</p>\n')

    def display_child_link(self, of, child_handle):
        use_link = child_handle in self.ind_list
        child = self.db.get_person_from_handle(child_handle)
        gid = child.get_gramps_id()
        if use_link:
            child_name = _nd.display(child)
            fname = gid + ".html"
            path = self.build_path(child_handle,"",False)
            self.person_link(of, gid,
                             child_name)
        else:
            of.write(_nd.display(child))

    def display_parent(self, of, handle, title, rel):
        use_link = handle in self.ind_list
        person = self.db.get_person_from_handle(handle)
        of.write('<td>%s:</td>' % title)
        of.write('<td>')
        val = person.gramps_id
        if use_link:
            path = self.build_path(handle,"",False)
            #fname = self.build_name(path,handle)
            fname = val + ".html"
            self.person_link(of, val, _nd.display(person))
        else:
            of.write(_nd.display(person))
        if rel != gen.lib.ChildRefType.BIRTH:
            of.write('&nbsp;&nbsp;&nbsp;(%s)' % str(rel))
        of.write('</td>')

    def display_ind_parents(self, of):
        parent_list = self.person.get_parent_family_handle_list()

        if not parent_list:
            return

        of.write('\n<h3>%s</h3>\n' % _("Parents"))
        of.write('<table summary="parents">\n')

        first = True
        if parent_list:
            for family_handle in parent_list:
                family = self.db.get_family_from_handle(family_handle)

                # Get the mother and father relationships
                frel = ""
                mrel = ""
                sibling = set()
                child_handle = self.person.get_handle()
                child_ref_list = family.get_child_ref_list()
                for child_ref in child_ref_list:
                    if child_ref.ref == child_handle:
                        frel = str(child_ref.get_father_relation())
                        mrel = str(child_ref.get_mother_relation())

                if not first:
                    of.write('<tr><td colspan="2">&nbsp;</td>')
                    of.write('</tr>\n')
                else:
                    first = False

                father_handle = family.get_father_handle()
                if father_handle:
                    of.write('<tr>')
                    self.display_parent(of,father_handle,_('Father'),frel)
                    of.write('</tr>\n')
                mother_handle = family.get_mother_handle()
                if mother_handle:
                    of.write('<tr>')
                    self.display_parent(of,mother_handle,_('Mother'),mrel)
                    of.write('</tr>\n')

                first = False
                if len(child_ref_list) > 1:
                    of.write('<tr><td>%s:</td>' % _("Siblings"))
                    of.write('<td>')
                    of.write('<ol>\n')
                    for child_ref in child_ref_list:
                        child_handle = child_ref.ref
                        sibling.add(child_handle)   # remember that we've already "seen" this child
                        if child_handle != self.person.handle:
                            of.write('<li>')
                            self.display_child_link(of,child_handle)
                            of.write('</li>')
                    of.write('</ol>\n')
                    of.write('</td>')
                    of.write('</tr>\n')

                # Also try to identify half-siblings
                other_siblings = set()

                # if we have a known father...
                if father_handle and self.showhalfsiblings:
                    # 1) get all of the families in which this father is involved
                    # 2) get all of the children from those families
                    # 3) if the children are not already listed as siblings...
                    # 4) then remember those children since we're going to list them
                    father = self.db.get_person_from_handle(father_handle)
                    for family_handle in father.get_family_handle_list():
                        family = self.db.get_family_from_handle(family_handle)
                        for step_child_ref in family.get_child_ref_list():
                            step_child_handle = step_child_ref.ref
                            if step_child_handle not in sibling:
                                if step_child_handle != self.person.handle:
                                    # we have a new step/half sibling
                                    other_siblings.add(step_child_ref.ref)

                # do the same thing with the mother (see "father" just above):
                if mother_handle and self.showhalfsiblings:
                    mother = self.db.get_person_from_handle(mother_handle)
                    for family_handle in mother.get_family_handle_list():
                        family = self.db.get_family_from_handle(family_handle)
                        for step_child_ref in family.get_child_ref_list():
                            step_child_handle = step_child_ref.ref
                            if step_child_handle not in sibling:
                                if step_child_handle != self.person.handle:
                                    # we have a new step/half sibling
                                    other_siblings.add(step_child_ref.ref)

                # now that we have all of the step-siblings/half-siblings, print them out
                if len(other_siblings) > 0:
                    of.write('<tr>')
                    of.write('<td>%s:</td>' % _("Half Siblings"))
                    of.write('<td>')
                    of.write('<ol>\n')
                    for child_handle in other_siblings:
                        self.display_child_link(of, child_handle)
                    of.write('</ol>\n')
                    of.write('</td></tr>\n')
        of.write('</table>\n')

    def display_ind_relationships(self, of):
        family_list = self.person.get_family_handle_list()
        if not family_list:
            return

        of.write('\n<h3>%s</h3>\n' % _("Families"))
        of.write('<table summary="families">\n')

        first = True
        for family_handle in family_list:
            family = self.db.get_family_from_handle(family_handle)
            self.display_spouse(of,family,first)
            first = False
            childlist = family.get_child_ref_list()
            if childlist:
                of.write('<tr><td>%s:</td>' % _("Children"))
                of.write('<td><ol>\n')
                for child_ref in childlist:
                    of.write('<li>')
                    self.display_child_link(of,child_ref.ref)
                    of.write('</li>\n')
                of.write('</ol></td></tr>\n')
        of.write('</table>\n')

    def display_spouse(self, of,family,first=True):
        gender = self.person.get_gender()
        reltype = family.get_relationship()

        if reltype == gen.lib.FamilyRelType.MARRIED:
            if gender == gen.lib.Person.FEMALE:
                relstr = _("Husband")
            elif gender == gen.lib.Person.MALE:
                relstr = _("Wife")
            else:
                relstr = _("Partner")
        else:
            relstr = _("Partner")

        spouse_id = ReportUtils.find_spouse(self.person,family)
        if spouse_id:
            spouse = self.db.get_person_from_handle(spouse_id)
            name = _nd.display(spouse)
        else:
            name = _("unknown")
        rtype = str(family.get_relationship())
        of.write('<tr><td>%s:</td>' % relstr)
        of.write('<td>')
        if spouse_id:
            use_link = spouse_id in self.ind_list
            gid = spouse.get_gramps_id()
            if use_link:
                spouse_name = _nd.display(spouse)
                path = self.build_path(spouse.handle,"",False)
                fname = self.build_name(path,spouse.handle)
                self.person_link(of, gid, spouse_name)
            else:
                of.write(name)
        of.write('</td></tr>\n')

        for event_ref in family.get_event_ref_list():
            event = self.db.get_event_from_handle(event_ref.ref)
            evtType = str(event.get_type())
            of.write('<tr><td>%s:</td>' % evtType)
            of.write('<td>')
            of.write(self.format_event(event, event_ref))
            of.write('</td></tr>\n')
        for attr in family.get_attribute_list():
            attrType = str(attr.get_type())
            of.write('<tr><td>%s:</td>' % attrType)
            of.write('<td>%s</td>' % attr.get_value())
            of.write('</tr>\n')
        notelist = family.get_note_list()
        for notehandle in notelist:
            note = self.db.get_note_from_handle(notehandle)
            if note:
                text = note.get()
                format = note.get_format()
                if text:
                    of.write('<tr><td>%s:</td>' % _('Narrative'))
                    of.write('<td><p>')
                    if format:
                        of.write(u"<pre>%s</pre>" % text )
                    else:
                        of.write(u"<br />".join(text.split("\n")))
                    of.write('</p>')
                    of.write('</td>')
                    of.write('</tr>\n')

    def pedigree_person(self, of, person, is_spouse=False):
        person_link = person.handle in self.ind_list
        person_name = _nd.display(person)
        if person_link:
            path = self.build_path(person.handle, "", False)
            fname = self.build_name(path, person.gramps_id)
            self.person_link(of, person.gramps_id, person_name)
        else:
            of.write(person_name)

    def pedigree_family(self, of, num):
        for family_handle in self.person.get_family_handle_list():
            rel_family = self.db.get_family_from_handle(family_handle)
            if rel_family:
                spouse_handle = ReportUtils.find_spouse(self.person,rel_family)
                if spouse_handle:
                    of.write('<dt>+ ')
                    spouse = self.db.get_person_from_handle(spouse_handle)
                    self.pedigree_person(of,spouse,True)
                    of.write('</dt>\n')
                childlist = rel_family.get_child_ref_list()
                if childlist:
                    num = 0
                    for child_ref in childlist:
                        num = num + 1
                        of.write('<dd>%d. ' % num)
                        child = self.db.get_person_from_handle(child_ref.ref)
                        self.pedigree_person(of,child)
                        of.write('</dd>\n')

    def pedigree_family2(self, of, num):
        for family_handle in self.person.get_family_handle_list():
            rel_family = self.db.get_family_from_handle(family_handle)
            if rel_family:
                spouse_handle = ReportUtils.find_spouse(self.person,rel_family)
                if spouse_handle:
                    of.write('<dd><dl><dt>+ ')
                    spouse = self.db.get_person_from_handle(spouse_handle)
                    self.pedigree_person(of,spouse,True)
                    of.write('</dt>\n')
                childlist = rel_family.get_child_ref_list()
                if childlist:
                    num = 0
                    for child_ref in childlist:
                        num = num + 1
                        of.write('<dd>%d. ' % num)
                        child = self.db.get_person_from_handle(child_ref.ref)
                        self.pedigree_person(of,child)
                        of.write('</dd>\n')
                if spouse_handle:
                    of.write('</dl></dd>')

    def format_event(self,event,event_ref):
        lnk = (self.cur_name, self.page_title, self.gid)
        descr = event.get_description()
        place_handle = event.get_place_handle()
        if place_handle:
            placeNm = self.db.get_place_from_handle( place_handle)
            if self.place_list.has_key(place_handle):
                if lnk not in self.place_list[place_handle]:
                    self.place_list[place_handle].append(lnk)
            else:
                self.place_list[place_handle] = [lnk]

            place = self.place_link_str(placeNm.gramps_id,
                                        ReportUtils.place_name(self.db,place_handle),
                                        up=True)
        else:
            place = u""

        date = _dd.display(event.get_date_object())
        tmap = {'description' : descr, 'date' : date, 'place' : place}

        if descr and date and place:
            text = _('%(description)s,&nbsp;&nbsp;%(date)s&nbsp;&nbsp;at&nbsp;&nbsp;%(place)s') % tmap
        elif descr and date:
            text = _('%(description)s,&nbsp;&nbsp;%(date)s&nbsp;&nbsp;') % tmap
        elif descr and place:
            text = _('%(description)s&nbsp;&nbsp;at&nbsp;&nbsp;%(place)s') % tmap
        elif descr:
            text = descr
        elif date and place:
            text = _('%(date)s&nbsp;&nbsp;at&nbsp;&nbsp;%(place)s') % tmap
        elif date:
            text = date
        elif place:
            text = place
        else:
            text = '\n'
        text += self.get_citation_links( event.get_source_references() )

        # if the event or event reference has a attributes attached to it,
        # get the text and format it correctly
        attr_list = event.get_attribute_list()
        attr_list.extend(event_ref.get_attribute_list())
        for attr in attr_list:
            text += _("<br />%(type)s: %(value)s") % {
                'type'     : attr.get_type(),
                'value'    : attr.get_value() }

        # if the event or event reference has a note attached to it,
        # get the text and format it correctly
        notelist = event.get_note_list()
        notelist.extend(event_ref.get_note_list())
        for notehandle in notelist:
            note = self.db.get_note_from_handle(notehandle)
            if note:
                note_text = note.get()
                format = note.get_format()
                if note_text:
                    if format:
                        text += u"<pre>%s</pre>" % note_text
                    else:
                        text += u"<br />".join(note_text.split("\n"))
        return text

    def get_citation_links(self, source_ref_list):
        gid_list = []
        lnk = (self.cur_name, self.page_title, self.gid)
        text = ""

        for sref in source_ref_list:
            handle = sref.get_reference_handle()
            source = self.db.get_source_from_handle(handle)
            gid_list.append(sref)

            if self.src_list.has_key(handle):
                if lnk not in self.src_list[handle]:
                    self.src_list[handle].append(lnk)
            else:
                self.src_list[handle] = [lnk]

        if len(gid_list) > 0:
            text = text + " <sup>"
            for ref in gid_list:
                index,key = self.bibli.add_reference(ref)
                id = "%d%s" % (index+1,key)
                text = text + ' <a href="#sref%s">%s</a>' % (id,id)
            text = text + "</sup>"

        return text

#------------------------------------------------------------------------
#
# NavWebReport
#
#------------------------------------------------------------------------
class NavWebReport(Report):
    
    def __init__(self, database, options):
        """
        Create WebReport object that produces the report.

        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options         - instance of the Options class for this report
        """
        Report.__init__(self, database, options)
        menu = options.menu
        self.options = {}

        for optname in menu.get_all_option_names():
            menuopt = menu.get_option_by_name(optname)
            self.options[optname] = menuopt.get_value()

        if not self.options['incpriv']:
            self.database = PrivateProxyDb(database)
        else:
            self.database = database

        livinginfo = self.options['living']
        yearsafterdeath = self.options['yearsafterdeath']

        if livinginfo != _INCLUDE_LIVING_VALUE:
            self.database = LivingProxyDb(self.database,
                                          livinginfo,
                                          None,
                                          yearsafterdeath)

        filters_option = menu.get_option_by_name('filter')
        self.filter = filters_option.get_filter()

        self.target_path = self.options['target']
        self.copyright = self.options['cright']
        self.ext = self.options['ext']
        self.encoding = self.options['encoding']
        self.css = self.options['css']
        self.noid = self.options['nogid']
        self.linkhome = self.options['linkhome']
        self.showbirth = self.options['showbirth']
        self.showdeath = self.options['showdeath']
        self.showspouse = self.options['showspouse']
        self.showparents = self.options['showparents']
        self.showhalfsiblings = self.options['showhalfsiblings']
        self.title = self.options['title']
        self.sort = Sort.Sort(self.database)
        self.inc_gallery = self.options['gallery']
        self.inc_contact = self.options['contactnote'] != u""\
                       or self.options['contactimg'] != u""
        self.inc_download = self.options['incdownload']
        self.use_archive = self.options['archive']
        self.use_intro = self.options['intronote'] != u""\
                    or self.options['introimg'] != u""
        self.use_home = self.options['homenote'] != u"" or\
                        self.options['homeimg'] != u""

    def write_report(self):
        if not self.use_archive:
            dir_name = self.target_path
            if dir_name == None:
                dir_name = os.getcwd()
            elif not os.path.isdir(dir_name):
                parent_dir = os.path.dirname(dir_name)
                if not os.path.isdir(parent_dir):
                    ErrorDialog(_("Neither %s nor %s are directories") % \
                                (dir_name,parent_dir))
                    return
                else:
                    try:
                        os.mkdir(dir_name)
                    except IOError, value:
                        ErrorDialog(_("Could not create the directory: %s") % \
                                    dir_name + "\n" + value[1])
                        return
                    except:
                        ErrorDialog(_("Could not create the directory: %s") % \
                                    dir_name)
                        return

            try:
                image_dir_name = os.path.join(dir_name, 'images')
                if not os.path.isdir(image_dir_name):
                    os.mkdir(image_dir_name)

                image_dir_name = os.path.join(dir_name, 'thumb')
                if not os.path.isdir(image_dir_name):
                    os.mkdir(image_dir_name)
            except IOError, value:
                ErrorDialog(_("Could not create the directory: %s") % \
                            image_dir_name + "\n" + value[1])
                return
            except:
                ErrorDialog(_("Could not create the directory: %s") % \
                            image_dir_name)
                return
            archive = None
        else:
            if os.path.isdir(self.target_path):
                ErrorDialog(_('Invalid file name'),
                            _('The archive file must be a file, not a directory'))
                return
            try:
                archive = tarfile.open(self.target_path,"w:gz")
            except (OSError,IOError),value:
                ErrorDialog(_("Could not create %s") % self.target_path,
                            value)
                return

        self.progress = Utils.ProgressMeter(_("Generate HTML reports"),'')

        # Build the person list
        ind_list = self.build_person_list()

        # Generate the CSS file if requested
        if self.css != '':
            self.write_css(archive,self.target_path,self.css)

        # Copy Mainz Style Images
        imgs = ["Web_Mainz_Bkgd.png",
                "Web_Mainz_Header.png",
                "Web_Mainz_Mid.png",
                "Web_Mainz_MidLight.png",
                "document.png",
                "favicon.ico"]
        # Copy the Creative Commons icon if the a Creative Commons
        # license is requested
        if 0 < self.copyright < 7:
            imgs += ["somerights20.gif"]

        for f in imgs:
            from_path = os.path.join(const.IMAGE_DIR, f)
            to_path = os.path.join("images", f)
            self.store_file(archive, self.target_path, from_path, to_path)

        place_list = {}
        source_list = {}
        self.photo_list = {}

        self.base_pages(self.photo_list, archive)
        self.person_pages(ind_list, place_list, source_list, archive)
        self.surname_pages(ind_list, archive)
        self.place_pages(place_list, source_list, archive)
        if self.inc_gallery:
            self.gallery_pages(self.photo_list, source_list, archive)
        self.source_pages(source_list, self.photo_list, archive)

        if archive:
            archive.close()
        self.progress.close()

    def build_person_list(self):
        """
        Builds the person list. Gets all the handles from the database
        and then applies the cosen filter:
        """

        # gets the person list and applies the requested filter
        ind_list = self.database.get_person_handles(sort_handles=False)
        self.progress.set_pass(_('Filtering'),1)
        ind_list = self.filter.apply(self.database,ind_list)
        return ind_list

    def write_css(self,archive, html_dir,css_file):
        """
        Copy the CSS file to the destination.
        """
        if archive:
            fname = os.path.join(const.DATA_DIR, css_file)
            archive.add(fname,_NARRATIVE)
            gname = os.path.join(const.DATA_DIR, "Web_Basic-Ash.css")
            archive.add(gname,_NARRATIVEPRINT)
        else:
            shutil.copyfile(os.path.join(const.DATA_DIR, css_file),
                            os.path.join(html_dir,_NARRATIVE))
            shutil.copyfile(os.path.join(const.DATA_DIR, "Web_Basic-Ash.css"),
                            os.path.join(html_dir,_NARRATIVEPRINT))

    def person_pages(self, ind_list, place_list, source_list, archive):

        self.progress.set_pass(_('Creating individual pages'), len(ind_list) + 1)
        self.progress.step()    # otherwise the progress indicator sits at 100%
                                # for a short while from the last step we did,
                                # which was to apply the privacy filter

        IndividualListPage(
            self.database, self.title, ind_list,
            self.options, archive, self.photo_list)

        for person_handle in ind_list:
            self.progress.step()
            person = self.database.get_person_from_handle(person_handle)

            IndividualPage(
                self.database, person, self.title, ind_list,
                place_list, source_list, self.options, archive, self.photo_list)

    def surname_pages(self, ind_list, archive):
        """
        Generates the surname related pages from list of individual
        people.
        """

        local_list = sort_people(self.database,ind_list)
        self.progress.set_pass(_("Creating surname pages"),len(local_list))

        if self.use_home or self.use_intro:
            defname="surnames"
        else:
            defname="index"

        SurnameListPage(
            self.database, self.title, ind_list, self.options, archive,
            self.photo_list, SurnameListPage.ORDER_BY_NAME,defname)

        SurnameListPage(
            self.database, self.title, ind_list, self.options, archive,
            self.photo_list, SurnameListPage.ORDER_BY_COUNT,"surnames_count")

        for (surname, handle_list) in local_list:
            SurnamePage(self.database, surname, handle_list,
                        self.options, archive, self.photo_list)
            self.progress.step()

    def source_pages(self, source_list, photo_list, archive):

        self.progress.set_pass(_("Creating source pages"),len(source_list))

        SourcesPage(self.database,self.title, source_list.keys(),
                    self.options, archive, photo_list)

        for key in list(source_list):
            SourcePage(self.database, self.title, key, source_list,
                       self.options, archive, photo_list)
            self.progress.step()


    def place_pages(self, place_list, source_list, archive):

        self.progress.set_pass(_("Creating place pages"),len(place_list))

        PlaceListPage(
            self.database, self.title, place_list, source_list, self.options,
            archive, self.photo_list)

        for place in place_list.keys():
            PlacePage(
                self.database, self.title, place, source_list, place_list,
                self.options, archive, self.photo_list)
            self.progress.step()

    def gallery_pages(self, photo_list, source_list, archive):
        import gc
        self.progress.set_pass(_("Creating media pages"),len(photo_list))

        GalleryPage(self.database, self.title, source_list,
                    self.options, archive, self.photo_list)

        prev = None
        total = len(self.photo_list)
        photo_keys = self.photo_list.keys()
        sort = Sort.Sort(self.database)
        photo_keys.sort(sort.by_media_title)

        index = 1
        for photo_handle in photo_keys:
            gc.collect() # Reduce memory usage when there are many images.
            if index == total:
                next = None
            else:
                next = photo_keys[index]
            MediaPage(self.database, self.title, photo_handle, source_list,
                      self.options, archive, self.photo_list[photo_handle],
                      (prev, next, index, total))
            self.progress.step()
            prev = photo_handle
            index += 1

    def base_pages(self, photo_list, archive):

        if self.use_home:
            HomePage(self.database, self.title, self.options, archive, photo_list)

        if self.inc_contact:
            ContactPage(self.database, self.title, self.options,
                        archive, photo_list)

        if self.inc_download:
            DownloadPage(self.database, self.title, self.options,
                         archive, photo_list)

        if self.use_intro:
            IntroductionPage(self.database, self.title, self.options,
                             archive, photo_list)

    def store_file(self,archive, html_dir,from_path,to_path):
        """
        Store the file in the destination.
        """
        if archive:
            archive.add(from_path,to_path)
        else:
            shutil.copyfile(from_path, os.path.join(html_dir,to_path))

#------------------------------------------------------------------------
#
# NavWebOptions
#
#------------------------------------------------------------------------
class NavWebOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """
    __INCLUDE_LIVING_VALUE = 99 # Arbitrary number

    def __init__(self, name, dbase):
        self.__db = dbase
        self.__archive = None
        self.__target = None
        self.__pid = None
        self.__filter = None
        self.__graph = None
        self.__graphgens = None
        self.__living = None
        self.__yearsafterdeath = None
        MenuReportOptions.__init__(self, name, dbase)

    def add_menu_options(self, menu):
        """
        Add options to the menu for the web calendar.
        """
        self.__add_report_options(menu)
        self.__add_page_generation_options(menu)
        self.__add_privacy_options(menu)
        self.__add_advanced_options(menu)

    def __add_report_options(self, menu):
        """
        Options on the "Report Options" tab.
        """
        category_name = _("Report Options")

        self.__archive = BooleanOption(_('Store web pages in .tar.gz archive'),
                                       False)
        self.__archive.set_help(_('Whether to store the web pages in an '
                                  'archive file'))
        menu.add_option(category_name, 'archive', self.__archive)
        self.__archive.connect('value-changed', self.__archive_changed)

        self.__target = DestinationOption(_("Destination"),
                                    os.path.join(const.USER_HOME,"NAVWEB"))
        self.__target.set_help( _("The destination directory for the web "
                                  "files"))
        menu.add_option(category_name, "target", self.__target)

        self.__archive_changed()

        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
               _("Select filter to restrict people that appear on web files"))
        menu.add_option(category_name, "filter", self.__filter)
        self.__filter.connect('value-changed', self.__filter_changed)

        self.__pid = PersonOption(_("Filter Person"))
        self.__pid.set_help(_("The center person for the filter"))
        menu.add_option(category_name, "pid", self.__pid)
        self.__pid.connect('value-changed', self.__update_filters)

        self.__update_filters()

        title = StringOption(_("Web site title"), _('My Family Tree'))
        title.set_help(_("The title of the web site"))
        menu.add_option(category_name, "title", title)

        ext = EnumeratedListOption(_("File extension"), ".html" )
        for etype in ['.html', '.htm', '.shtml', '.php', '.php3', '.cgi']:
            ext.add_item(etype, etype)
        ext.set_help( _("The extension to be used for the web files"))
        menu.add_option(category_name, "ext", ext)

        cright = EnumeratedListOption(_('Copyright'), 0 )
        index = 0
        for copt in _COPY_OPTIONS:
            cright.add_item(index, copt)
            index += 1
        cright.set_help( _("The copyright to be used for the web files"))
        menu.add_option(category_name, "cright", cright)

        encoding = EnumeratedListOption(_('Character set encoding'), _CHARACTER_SETS[0][1] )
        for eopt in _CHARACTER_SETS:
            encoding.add_item(eopt[1], eopt[0])
        encoding.set_help( _("The encoding to be used for the web files"))
        menu.add_option(category_name, "encoding", encoding)

        css = EnumeratedListOption(_('Stylesheet'), _CSS_FILES[0][1])
        for style in _CSS_FILES:
            css.add_item(style[1], style[0])
        css.set_help( _("The style sheet to be used for the web pages"))
        menu.add_option(category_name, "css", css)

        self.__graph = BooleanOption(_("Include ancestor graph"), True)
        self.__graph.set_help(_('Whether to include an ancestor graph '
                                      'on each individual page'))
        menu.add_option(category_name, 'graph', self.__graph)
        self.__graph.connect('value-changed', self.__graph_changed)

        self.__graphgens = EnumeratedListOption(_('Graph generations'), 15)
        self.__graphgens.add_item(2, "2")
        self.__graphgens.add_item(3, "3")
        self.__graphgens.add_item(4, "4")
        self.__graphgens.add_item(5, "5")
        self.__graphgens.add_item(8, "8")
        self.__graphgens.add_item(10, "10")
        self.__graphgens.add_item(12, "12")
        self.__graphgens.add_item(15, "15")
        self.__graphgens.set_help( _("The number of generations to include in "
                                     "the ancestor graph"))
        menu.add_option(category_name, "graphgens", self.__graphgens)

        self.__graph_changed()

    def __add_page_generation_options(self, menu):
        """
        Options on the "Page Generation" tab.
        """
        category_name = _("Page Generation")

        homenote = NoteOption(_('Home page note'))
        homenote.set_help( _("A note to be used on the home page"))
        menu.add_option(category_name, "homenote", homenote)

        homeimg = MediaOption(_('Home page image'))
        homeimg.set_help( _("An image to be used on the home page"))
        menu.add_option(category_name, "homeimg", homeimg)

        intronote = NoteOption(_('Introduction note'))
        intronote.set_help( _("A note to be used as the introduction"))
        menu.add_option(category_name, "intronote", intronote)

        introimg = MediaOption(_('Introduction image'))
        introimg.set_help( _("An image to be used as the introduction"))
        menu.add_option(category_name, "introimg", introimg)

        contactnote = NoteOption(_("Publisher contact note"))
        contactnote.set_help( _("A note to be used as the publisher contact"))
        menu.add_option(category_name, "contactnote", contactnote)

        contactimg = MediaOption(_("Publisher contact image"))
        contactimg.set_help( _("An image to be used as the publisher contact"))
        menu.add_option(category_name, "contactimg", contactimg)

        headernote = NoteOption(_('HTML user header'))
        headernote.set_help( _("A note to be used as the page header"))
        menu.add_option(category_name, "headernote", headernote)

        footernote = NoteOption(_('HTML user footer'))
        footernote.set_help( _("A note to be used as the page footer"))
        menu.add_option(category_name, "footernote", footernote)

        gallery = BooleanOption(_("Include images and media objects"), True)
        gallery.set_help(_('Whether to include a gallery of media objects'))
        menu.add_option(category_name, 'gallery', gallery)

        incdownload = BooleanOption(_("Include download page"), False)
        incdownload.set_help(_('Whether to include a database download option'))
        menu.add_option(category_name, 'incdownload', incdownload)

        nogid = BooleanOption(_('Suppress GRAMPS ID'), False)
        nogid.set_help(_('Whether to include the Gramps ID of objects'))
        menu.add_option(category_name, 'nogid', nogid)

    def __add_privacy_options(self, menu):
        """
        Options on the "Privacy" tab.
        """
        category_name = _("Privacy")

        incpriv = BooleanOption(_("Include records marked private"), False)
        incpriv.set_help(_('Whether to include private objects'))
        menu.add_option(category_name, 'incpriv', incpriv)

        self.__living = EnumeratedListOption(_("Living People"),
                                             _INCLUDE_LIVING_VALUE )
        self.__living.add_item(LivingProxyDb.MODE_EXCLUDE_ALL, 
                               _("Exclude"))
        self.__living.add_item(LivingProxyDb.MODE_INCLUDE_LAST_NAME_ONLY, 
                               _("Include Last Name Only"))
        self.__living.add_item(LivingProxyDb.MODE_INCLUDE_FULL_NAME_ONLY, 
                               _("Include Full Name Only"))
        self.__living.add_item(_INCLUDE_LIVING_VALUE, 
                               _("Include"))
        self.__living.set_help(_("How to handle living people"))
        menu.add_option(category_name, "living", self.__living)
        self.__living.connect('value-changed', self.__living_changed)

        self.__yearsafterdeath = NumberOption(_("Years from death to consider "
                                                 "living"), 30, 0, 100)
        self.__yearsafterdeath.set_help(_("This allows you to restrict "
                                          "information on people who have not "
                                          "been dead for very long"))
        menu.add_option(category_name, 'yearsafterdeath',
                        self.__yearsafterdeath)

        self.__living_changed()

    def __add_advanced_options(self, menu):
        """
        Options on the "Advanced" tab.
        """
        category_name = _("Advanced")

        linkhome = BooleanOption(_('Include link to home person on every '
                                   'page'), False)
        linkhome.set_help(_('Whether to include a link to the home person'))
        menu.add_option(category_name, 'linkhome', linkhome)

        showbirth = BooleanOption(_("Include a column for birth dates on the "
                                    "index pages"), True)
        showbirth.set_help(_('Whether to include a birth column'))
        menu.add_option(category_name, 'showbirth', showbirth)

        showdeath = BooleanOption(_("Include a column for death dates on the "
                                    "index pages"), False)
        showdeath.set_help(_('Whether to include a death column'))
        menu.add_option(category_name, 'showdeath', showdeath)

        showspouse = BooleanOption(_("Include a column for partners on the "
                                    "index pages"), False)
        showspouse.set_help(_('Whether to include a partners column'))
        menu.add_option(category_name, 'showspouse', showspouse)

        showparents = BooleanOption(_("Include a column for parents on the "
                                      "index pages"), False)
        showparents.set_help(_('Whether to include a parents column'))
        menu.add_option(category_name, 'showparents', showparents)

        showhalfsiblings = BooleanOption(_("Include a column for half-siblings"
                                           " on the index pages"), False)
        showhalfsiblings.set_help(_("Whether to include a half-siblings "
                                    "column"))
        menu.add_option(category_name, 'showhalfsiblings', showhalfsiblings)

    def __archive_changed(self):
        """
        Update the change of storage: archive or directory
        """
        if self.__archive.get_value() == True:
            self.__target.set_extension(".tar.gz")
            self.__target.set_directory_entry(False)
        else:
            self.__target.set_directory_entry(True)

    def __update_filters(self):
        """
        Update the filter list based on the selected person
        """
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = ReportUtils.get_person_filters(person, False)
        self.__filter.set_filters(filter_list)

    def __filter_changed(self):
        """
        Handle filter change. If the filter is not specific to a person,
        disable the person option
        """
        filter_value = self.__filter.get_value()
        if filter_value in [1, 2, 3, 4]:
            # Filters 1, 2, 3 and 4 rely on the center person
            self.__pid.set_available(True)
        else:
            # The rest don't
            self.__pid.set_available(False)

    def __graph_changed(self):
        """
        Handle enabling or disabling the ancestor graph
        """
        self.__graphgens.set_available(self.__graph.get_value())

    def __living_changed(self):
        """
        Handle a change in the living option
        """
        if self.__living.get_value() == self.__INCLUDE_LIVING_VALUE:
            self.__yearsafterdeath.set_available(False)
        else:
            self.__yearsafterdeath.set_available(True)

    def make_default_style(self, default_style):
        """Make the default output style for the Web Pages Report."""
        pass


def sort_people(db, handle_list):
    flist = set(handle_list)

    sname_sub = {}
    sortnames = {}

    for person_handle in handle_list:
        person = db.get_person_from_handle(person_handle)
        primary_name = person.get_primary_name()

        if primary_name.group_as:
            surname = primary_name.group_as
        else:
            surname = db.get_name_group_mapping(primary_name.surname)

        sortnames[person_handle] = _nd.sort_string(primary_name)

        if sname_sub.has_key(surname):
            sname_sub[surname].append(person_handle)
        else:
            sname_sub[surname] = [person_handle]

    sorted_lists = []
    temp_list = sname_sub.keys()
    temp_list.sort(locale.strcoll)
    for name in temp_list:
        slist = map(lambda x: (sortnames[x],x),sname_sub[name])
        slist.sort(lambda x,y: locale.strcoll(x[0],y[0]))
        entries = map(lambda x: x[1], slist)
        sorted_lists.append((name,entries))
    return sorted_lists

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class MiniTree:
    """
    This is one dirty piece of code, that is why I made it it's own
    class.  I'm sure that someone with more knowledge of GRAMPS can make
    it much cleaner.
    """
    def __init__(self,db,person,doc,the_map,depth,ext):
        self.map = the_map
        self.db = db
        self.doc = doc
        self.depth = depth
        self.ext = ext
        self.person = person
        self.lines_map = {} 
        self.draw_parents(person,2**(self.depth-1),'',self.depth,1)
        keys = self.lines_map.keys()
        keys.sort()
        self.lines = [ self.lines_map[key] for key in keys ]

    def draw_parents(self,person,position,indent,generations,topline):

        name = person.get_primary_name().get_regular_name()
        self.lines_map[position] = ""

        if topline and indent:
            # if we're on top (father's) line, replace last '|' with space
            self.lines_map[position] += indent[:-1] + ' '
        else:
            self.lines_map[position] += indent

        if person and person.get_handle():
            self.lines_map[position] += "<a href='%s%s'>%s</a>" % (person.get_gramps_id(),
                                                           self.ext, name)
        else:
            self.lines_map[position] += "<u>%s</u>" % name

        # We are done with this generation
        generations = generations - 1
        if not generations: return

        offset = 2**(generations-1)

        family_handle = person.get_main_parents_family_handle()
        if not family_handle: return

        family = self.db.get_family_from_handle(family_handle)
        father_handle = family.get_father_handle()
        mother_handle = family.get_mother_handle()

        if topline:
            # if we're on top (father's) line, replace last '|' with space
            # then add '|' to the end for the next generation
            if indent:
                father_indent = indent[:-1] + ' ' + ' ' * len(name) + '|'
            else:
                father_indent = ' ' * len(name) + '|'
            mother_indent = indent + ' ' * len(name) + '|'
        else:
            # if we're not on top (i.e. mother's) line, remove last '|'
            # from next mother's indent, then add '|' to both
            father_indent = indent + ' ' * len(name) + '|'
            mother_indent = indent[:-1] + ' ' + ' ' * len(name) + '|'

        if father_handle:
            father = self.db.get_person_from_handle(father_handle)
            next_pos = position - offset 
            self.lines_map[position] += '|'
            self.draw_parents(father,next_pos,father_indent,generations,1)
            
        if mother_handle:
            mother = self.db.get_person_from_handle(mother_handle)
            next_pos = position + offset
            self.draw_parents(mother,next_pos,mother_indent,generations,0)

    def draw_father(self, person, name, line, indent):
        self.draw_string(line, indent, '|')
        self.draw_string(line-1, indent+1, "")
        self.draw_link(line-1, person, name)

    def draw_mother(self, person, name, line, indent):
        self.draw_string(line+1, indent, '|')
        self.draw_link(line+1, person, name)

    def draw_string(self, line, indent, text):
        self.lines[line] += ' ' * (indent-len(self.lines[line])) + text

    def draw_link(self, line, person, name):
        if person and person.get_handle():
            self.lines[line] += "<a href='%s%s'>%s</a>" % (person.get_gramps_id(),
                                                           self.doc.ext, name)
        else:
            self.lines[line] += "<u>%s</u>" % name

#-------------------------------------------------------------------------
#
#            Register Plugin
#
# -------------------------------------------
pmgr = PluginManager.get_instance()
pmgr.register_report(
    name = 'wilsnavwebpage',
    category = CATEGORY_WEB,
    report_class = NavWebReport,
    options_class = NavWebOptions,
    modes = PluginManager.REPORT_MODE_GUI | PluginManager.REPORT_MODE_CLI,
    translated_name = _("Wil's Narrated Web Site"),
    status = _("Stable"),
    author_name = "Donald N. Allingham, William Bell",
    author_email = "don@gramps-project.org",
    description = _("Produces web (HTML) pages for individuals, or a set of "
                    "individuals"),
    )

