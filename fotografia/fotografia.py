#!/usr/bin/env python   
# -*- coding: utf-8 -*-

# Copyright (C) 2017 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import random
import re
from xml.etree import ElementTree as ET # para ver los XMl que devuelve flickrapi con ET.dump(resp)

import flickrapi

def savetable(filename, tablemark, table):
    f = open(filename, 'r')
    html = unicode(f.read(), 'utf-8')
    f.close()
    f = open(filename, 'w')
    before = html.split(u'<!-- %s -->' % tablemark)[0]
    after = html.split(u'<!-- /%s -->' % tablemark)[1]
    html = u'%s<!-- %s -->%s<!-- /%s -->%s' % (before, tablemark, table, tablemark, after)
    f.write(html.encode('utf-8'))
    f.close()

def main():
    #sets
    with open('flickr.token', 'r') as f:
        api_key, api_secret = f.read().strip().splitlines()
    
    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    flickruserid = '96396586@N07' #it isn't secret, don't worry
    print('Step 1: authenticate')
    if not flickr.token_valid(perms=u'read'):
        flickr.get_request_token(oauth_callback=u'oob')
        authorize_url = flickr.auth_url(perms=u'read')
        print(authorize_url)
        verifier = unicode(raw_input(u'Verifier code: '), 'utf-8')
        flickr.get_access_token(verifier)
    print('Step 2: use Flickr')
    resp = flickr.photosets.getList(user_id=flickruserid)
    xmlraw = ET.tostring(resp, encoding='utf8', method='xml')
    xmlraw = unicode(xmlraw, 'utf-8')
    photosets = re.findall(ur'(?im) date_create="(\d+)".*?date_update="(\d+)".*?id="(\d+)".*?photos="(\d+)".*?videos="(\d+)"[^<>]*?>\s*<title>([^<>]*?)</title>', xmlraw)
    flickrdone = []
    setrows = []
    c = 1
    for date_create, date_update, photosetid, photos, videos, title in photosets:
        print(photosetid, photos, videos, title, date_create, date_update)
        date_create = datetime.datetime.fromtimestamp(int(date_create))
        date_update = datetime.datetime.fromtimestamp(int(date_update))
        row = u"""
    <tr>
        <td>%s</td>
        <td><a href="https://www.flickr.com/photos/emijrp/albums/%s">%s</a></td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>""" % (c, photosetid, title, photos, videos, date_create.strftime("%Y-%m-%d"), date_update.strftime("%Y-%m-%d"))
        setrows.append(row)
        c += 1
    setstable = u"\n<script>sorttable.sort_alpha = function(a,b) { return a[0].localeCompare(b[0], 'es'); }</script>\n"
    setstable += u'\n<table class="wikitable sortable" style="text-align: center;">\n'
    setstable += u"""<tr>
        <th class="sorttable_numeric">#</th>
        <th class="sorttable_alpha">Título</th>
        <th class="sorttable_numeric">Fotos</th>
        <th class="sorttable_numeric">Vídeos</th>
        <th class="sorttable_alpha">Fecha de creación</th>
        <th class="sorttable_alpha">Fecha de actualización</th>
    </tr>"""
    setstable += u''.join(setrows)
    setstable += u'</table>\n'
    savetable('fotografia.wiki', 'tabla sets', setstable)
    
    #tagcloud
    blacklist = [
        'art', 
        'beach', 
        'calles', 
        'de', 
        'museum', 
        'painting', 
        'sea', 
        'spain', 
        'street', 
        'streets', 
    ]
    
    html = ''
    with open('flickrtags.html', 'r') as f:
        html = unicode(f.read(), 'utf-8')
    
    m = re.findall(ur'<a href="/photos/emijrp/tags/([^/]+?)/">([^<>]+?)</a>\s*</td>\s*<td>\s*([^<>]+?)\s*</td>\s*<td class="PhotoCount">\s*<b>(\d+)</b> elementos', html)
    tags = []
    for tag in m:
        tags.append([int(tag[3]), tag[0], tag[2]])
    
    tags.sort(reverse=True)
    c = 0
    cmax = 100
    toptags = []
    for count, tagurl, label in tags:
        skip = False
        for y in label.lower().split(', '):
            if y in [x.lower() for x in blacklist]:
                skip = True
        if skip:
            continue
        c += 1
        bestlabel = ''
        if ', ' in label:
            labels = label.split(', ')
            for label2 in labels:
                if label2 != label2.lower() or \
                    ' ' in label2:
                    bestlabel = label2
        if not bestlabel:
            bestlabel = label.split(', ')[0]
        toptags.append([count, tagurl, bestlabel])
        if c >= cmax:
            break
    
    print(toptags)
    cloud = []
    maxfontsize = 350.0
    minfontsize = 100.0
    maxcount  = toptags[0][0]
    mincount = toptags[-1][0]
    percent = (maxfontsize - minfontsize) / (maxcount - mincount)
    random.shuffle(toptags)
    for count, tagurl, label in toptags:
        size = minfontsize + ((count - mincount) * percent)
        cloud.append(u'<span style="font-size: %s%%;"><a href="https://www.flickr.com/search/?user_id=96396586@N07&sort=date-taken-desc&text=%s&view_all=1">%s</a></span>' % (size, tagurl, label))
    cloud = u' · '.join(cloud)
    savetable('fotografia.wiki', 'nube', cloud)

if __name__ == '__main__':
    main()
