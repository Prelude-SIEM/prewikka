# Copyright (C) 2005-2014 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import stat
import time
import base64
import urllib
import os, os.path
import glob, tempfile

from prewikka import utils, siteconfig, cairoplot
from preludedbold import PreludeDBError

from xml.dom.minidom import parse, parseString

RED_STD = "c1292e"
ORANGE_STD = "F29324"
YELLOW_STD = "f8e930"
GREEN_STD = "7ab41d"
BLUE_STD = "528fc8"

COLOR_MAP = "528fc8", "7ab41d", "f8e930", "F29324", "c1292e", "874b94", "212483", \
            "487118", "ea752c", "8C0A14", "5F3269", "196d38"



def userToHex(user):
    if not user:
        return ""

    hval = ""
    for i in user:
        hval += hex(ord(i)).replace("0x", "")

    return hval


class ChartCommon:
    def __init__(self, user, width=800, height=450):
        self._user = user
        self._filename = None
        self._values = [ ]
        self._labels = [ ]
        self._has_title = False
        self._support_link = False
        self._width = width
        self._height = height
        self._color_map = COLOR_MAP
        self._names_map = {}
        self._color_map_idx = 0

    def hex2rgb(self, color):
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        return (r/255.0, g/255.0, b/255.0)

    def getWidth(self):
        return self._width

    def getHeight(self):
        return self._height

    def _colorMap2str(self):
        if type(self._color_map) not in (list, tuple):
            return None

        str = ""
        for color  in self._color_map:
            if len(str):
                str += ","

            str += color

        return str

    def getItemColor(self, str):
        if isinstance(self._color_map, dict):
            return self._color_map[str]

        color = self._color_map[self._color_map_idx % len(self._color_map)]
        self._color_map_idx += 1

        return color

    def setColorMap(self, plist):
        self._color_map = plist

    def getFilename(self):
        return self._filename

    def getHref(self):
        return self._href

    def setTitle(self, title):
        self.addTitle(title, "", 14)
        self._has_title = True

    def setValues(self, values):
        self._values = values

    def setLabels(self, labels):
        self._labels = labels

    def addLabelValuePair(self, label, value, link=None):
        self._labels.append(label)
        if self._support_link:
            self._values.append((value, utils.escape_html_string(link)))
        else:
            self._values.append(value)

    def _remove_old_chart_files(self, pathname, expire):
        directory = pathname + "_*"
        files = glob.glob(directory)

        used = None
        prev = None

        for f in files:
            mtime = os.stat(f)[stat.ST_MTIME]
            now = time.time()

            if not expire or (now - mtime) > (2 * expire):
                os.remove(f)

    def _getFilename(self, name, expire = None, uid=None, gid=None, suffix=".png"):
        old_mask = os.umask(0)
        basename = base64.urlsafe_b64encode(name.encode("utf-8"))
        pathname = os.path.join(siteconfig.htdocs_dir, "generated_images")

        user = base64.urlsafe_b64encode(self._user.login.encode("utf-8"))
        pathname = os.path.normpath(os.path.join(pathname, user))

        try:
            os.mkdir(pathname, 0755)
        except: pass
        if uid != None and gid != None:
            os.lchown(pathname, uid, gid)

        self._remove_old_chart_files(os.path.join(pathname, basename), expire)

        fd, self._filename = tempfile.mkstemp(prefix = basename + "_", suffix = suffix, dir = pathname)
        if uid != None and gid != None:
            os.lchown(self._filename, uid, gid)

        os.chmod(self._filename, 0644)

        self._href = urllib.quote("/prewikka/generated_images/%s" % (user or "") + "/" + os.path.basename(self._filename))
        os.umask(old_mask)

        return self._filename

class TimelineChartCommon(ChartCommon):
    def getType(self):
        return "None"

    def __init__(self, user, width, height):
        ChartCommon.__init__(self, user, width, height)
        self._got_value = False
        self._color_map_idx = 0
        self._assigned_colors = {}
        self._multiple_values = False
        self._total = []

    def enableMultipleValues(self, names_and_colors={}):
        self._multiple_values = True
        self._names_and_colors = names_and_colors

        self._values = utils.OrderedDict()
        for name in self._names_and_colors.keys():
                self._values[name] = []

    def getItemColor(self, name):
        if not self._multiple_values:
            return ChartCommon.getItemColor(self, name)

        if self._names_and_colors.has_key(name):
                return self._names_and_colors[name]

        if self._assigned_colors.has_key(name):
                return self._assigned_colors[name]

        color = self._assigned_colors[name] = ChartCommon.getItemColor(self, name)
        return color

    def _itemFromValue(self, value):
        if isinstance(value, tuple):
            return value
        return value, None

        if self._support_link:
                return value[0], utils.escape_html_string(value[1])
        else:
                return value[0]

    def addLabelValuesPair(self, label, values, total_link):
        empty = True
        for i in values.values():
            if i != 0:
                empty = False
                break

        if self._support_link and total_link:
            total_link = utils.escape_html_string(total_link)

        self._labels.append(label)

        clen = 0
        if self._values:
                clen = len(self._values.values()[0])

        total = 0
        for name in values.keys():
            if not self._values.has_key(name):
                if clen > 0:
                    self._values[name] = [(0, None) for i in range(0, clen)]
                else:
                    self._values[name] = []

            value = self._itemFromValue(values[name])
            self._values[name].append(value)

            total += value[0]

        self._total.append((total, total_link))

        for name in self._values.keys():
            if not values.has_key(name):
                self._values[name].append(self._itemFromValue(0))

        self._got_value = True

    def addLabelValuePair(self, label, values, link=None):
        if self._multiple_values or isinstance(values, dict):
            if not isinstance(self._values, dict):
                self._values = utils.OrderedDict()

            self.addLabelValuesPair(label, values, link)
        else:
            ChartCommon.addLabelValuePair(self, label, values, link)


class CairoDistributionChart(ChartCommon):
    def getType(self):
        return "None"

    def render(self, name, expire=None, suffix=".png", uid=None, gid=None):
        fname = self._getFilename(name, expire, uid, gid);

        color = []
        data = utils.OrderedDict()
        total = 0

        lv = zip(self._labels, self._values)
        lv.sort(lambda x, y: int(x[1] - y[1]))

        for l, v in lv:
            total += v

        if total:
            share = 100.0 / total

        for l, v in lv:
            l = str(l)
            data["%s (%d, %.2f%%)" % (l, v, share * v)] = v
            color.append(self.hex2rgb(self.getItemColor(l)))

        cairoplot.pie_plot(fname, data, self._width, self._height, gradient = True, shadow = True, colors=color)


class CairoTimelineChart(TimelineChartCommon):
    def render(self, name, expire=None, suffix=".png", uid=None, gid=None):
        fname = self._getFilename(name, expire, uid, gid);

        colors = []
        values = utils.OrderedDict()
        for name in self._values.keys():
            nname = name[0:min(len(name), 25)]
            if not values.has_key(nname):
                values[nname] = []

            for item in self._values[name]:
                values[nname].append(item[0])

            colors.append(self.hex2rgb(self.getItemColor(name)))

        cairoplot.dot_line_plot(fname, values, self._width, self._height, border=0, axis=True, grid=True,
                                x_labels = self._labels, series_legend=True, series_colors=colors)


class CairoStackedTimelineChart(TimelineChartCommon):
    def render(self, name, expire=None, suffix=".png", uid=None, gid=None):
        fname = self._getFilename(name, expire, uid, gid);

        colors = []
        legend = []
        labels = []
        data = []
        minval = 0
        maxval = 0

        values_items = self._values.items()

        for i in xrange(0, len(self._labels)):
            l = []
            total = 0
            for name, values in values_items:
                l.append(values[i])
                total += values[i]

            minval = min(minval, total)
            maxval = max(maxval, total)
            data.append(l)

        l = minval
        increment = maxval / 20.0
        for i in xrange(0, 20+1):
            labels.append("%.1f" % l)
            l += increment

        idx = 0

        for name, color in self._names_and_colors.values():
            if self._values.has_key(name):
                if color:
                    colors.append(self.hex2rgb(color))
                else:
                    colors.append(self.hex2rgb(COLOR_MAP[idx % len(COLOR_MAP)]))
                    idx += 1
                legend.append(name)

        cairoplot.vertical_bar_plot(fname, data, self._width, self._height, border=0, series_labels=legend, display_values=True, grid=True, rounded_corners=False, stack=True,
                                    three_dimension=False, y_labels=labels, x_labels = self._labels, colors=colors)


class CairoWorldChart(CairoDistributionChart):
    def needCountryCode(self):
        return False

class TimelineChart(object):
    def __new__(cls, user, width, height):
        o = CairoTimelineChart(user, width, height)
        o.isFlash = False
        return o

class StackedTimelineChart(object):
    def __new__(cls, user, width, height):
        o = CairoStackedTimelineChart(user, width, height)
        o.isFlash = False
        return o

class WorldChart(object):
    def __new__(cls, user, width, height):
        o = CairoWorldChart(user, width, height)
        o.isFlash = False
        return o

class DistributionChart(object):
    def __new__(cls, user, width, height):
        o = CairoDistributionChart(user, width, height)
        o.isFlash = True
        return o
