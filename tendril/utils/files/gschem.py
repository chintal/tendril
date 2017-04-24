# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
gEDA schematic file parser module (:mod:`tendril.utils.files.gschem`)
=====================================================================

Detachable gEDA sch file parser and processing module. This component 
should perhaps be parcelled out into its own project. Additional 
functionality that's tightly coupled with the tendril core (or 
assumptions thereof) resides instead in :mod:`tendril.gedaif.gschem`. 
This division might need some reconsideration in the near future, and 
functionality which can be safely decoupled from the core should come 
here instead. It will later be proxied back into the core through 
`tendril.edaif` in the future. 

"""

import re
from collections import deque
from collections import namedtuple

from tendril.utils.fsutils import VersionedOutputFile

try:
    from tendril.utils import log
except ImportError:
    import logging as log

logger = log.get_logger(__name__, log.DEBUG)

try:
  basestring
except NameError:
  basestring = str


rex_vstring = re.compile(r'^v (?P<gsch_ver>\d+) (?P<file_ver>\d+)$')
rex_attribute = re.compile(r"^\s*(?P<name>[\S]+)\s*=(?P<value>[\S ]+)$")


map_color = {0: 'BACKGROUND_COLOR',
             1: 'PIN_COLOR',
             2: 'NET_ENDPOINT_COLOR',
             3: 'GRAPHIC_COLOR',
             4: 'NET_COLOR',
             5: 'ATTRIBUTE_COLOR',
             6: 'LOGIC_BUBBLE_COLOR',
             7: 'DOTS_GRID_COLOR',
             8: 'DETACHED_ATTRIBUTE_COLOR',
             9: 'TEXT_COLOR',
             10: 'BUS_COLOR',
             11: 'SELECT_COLOR',
             12: 'BOUNDINGBOX_COLOR',
             13: 'ZOOM_BOX_COLOR',
             14: 'STROKE_COLOR',
             15: 'LOCK_COLOR',
             16: 'OUTPUT_BACKGROUND_COLOR',
             17: 'FREESTYLE1_COLOR',
             18: 'FREESTYLE2_COLOR',
             19: 'FREESTYLE3_COLOR',
             20: 'FREESTYLE4_COLOR',
             21: 'JUNCTION_COLOR',
             22: 'MESH_GRID_MAJOR_COLOR',
             23: 'MESH_GRID_MINOR_COLOR'}

map_capstyle = {0: 'END NONE', 1: 'END SQUARE', 2: 'END ROUND'}

map_dashstyle = {0: 'TYPE SOLID', 1: 'TYPE DOTTED', 2: 'TYPE DASHED',
                 3: 'TYPE CENTER', 4: 'TYPE PHANTOM'}

map_filltype = {0: 'FILLING HOLLOW', 1: 'FILLING FILL', 2: 'FILLING MESH',
                3: 'FILLING HATCH', 4: 'FILLING VOID'}

map_pintype = {0: 'NORMAL PIN', 1: 'BUS PIN'}

map_shownamevalue = {0: 'SHOW NAME VALUE', 1: 'SHOW VALUE', 2: 'SHOW NAME'}

map_ripperdir = {0: 'NEW', 1: 'A', -1: 'B'}

map_alignment = {0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5',
                 6: '6', 7: '7', 8: '8'}

_map_bool = {0: False, 1: True}

map_selectable = _map_bool
map_mirror = _map_bool
map_whichend = _map_bool
map_visibility = _map_bool
map_embedded = _map_bool


GschParam = namedtuple('GschParam', 'name parser options typed_parser')


x = GschParam('x', int, None, None)
y = GschParam('y', int, None, None)
x1 = GschParam('x1', int, None, None)
y1 = GschParam('y1', int, None, None)
x2 = GschParam('x2', int, None, None)
y2 = GschParam('y2', int, None, None)

basename = GschParam('basename', str, None, None)
selectable = GschParam('selectable', int, map_selectable, None)
color = GschParam('color', int, map_color, None)
angle = GschParam('angle', int, None, None)
mirror = GschParam('mirror', int, map_mirror, None)
ripperdir = GschParam('ripperdir', int, map_ripperdir, None)
pintype = GschParam('pintype', int, map_pintype, None)
whichend = GschParam('whichend', int, map_whichend, None)
width = GschParam('width', int, None, None)
capstyle = GschParam('capstyle', int, map_capstyle, None)
dashstyle = GschParam('dashstyle', int, map_dashstyle, None)
dashlength = GschParam('dashlength', int, None, None)
dashspace = GschParam('dashspace', int, None, None)
boxwidth = GschParam('boxwidth', int, None, None)
boxheight = GschParam('boxheight', int, None, None)
filltype = GschParam('filltype', int, map_filltype, None)
fillwidth = GschParam('fillwidth', int, None, None)
angle1 = GschParam('angle1', int, None, None)
pitch1 = GschParam('pitch1', int, None, None)
angle2 = GschParam('angle2', int, None, None)
pitch2 = GschParam('pitch2', int, None, None)
radius = GschParam('radius', int, None, None)
startangle = GschParam('startangle', int, None, None)
sweepangle = GschParam('sweepangle', int, None, None)
size = GschParam('size', int, None, None)
visibility = GschParam('visibility', int, map_visibility, None)
show_name_value = GschParam('show_name_value', int, map_shownamevalue, None)
alignment = GschParam('alignment', int, map_alignment, None)
num_lines = GschParam('num_lines', int, None, None)
height = GschParam('height', int, None, None)
embedded = GschParam('embedded', int, map_embedded, None)
filename = GschParam('filename', str, None, None)


class GschFakeLines(deque):
    pass


class GschElementBase(object):
    code = None
    params = []

    def __init__(self, parent, lines, *args):
        for idx, arg in enumerate(args):
            try:
                param = self.params[idx]
            except IndexError:
                print("Error parsing line : {0} {1}\n Using {2} Params :"
                      "".format(self.code, args, self.__class__))
                for pdef in self.params:
                    print(pdef)
                raise
            v = param.parser(arg)
            if param.options is not None and v not in param.options.keys():
                raise ValueError
            setattr(self, '_' + param.name, v)
        self._parent = parent
        self._elements = []
        self._embedded_elements = []
        self._attributes = None
        self._embed = False
        self._get_multiline(lines)

    def add_element(self, element):
        if self.embed:
            self._embedded_elements.append(element)
        else:
            self._elements.append(element)

    def _get_multiline(self, lines):
        self._lines = []
        for i in range(getattr(self, '_num_lines', 0)):
            self._lines.append(lines.popleft())

    @property
    def parent(self):
        return self._parent

    @property
    def attributes(self):
        # TODO Handle Embedded Elements as well
        if self._attributes is None:
            self._attributes = {}
            for element in self._elements:
                if isinstance(element, GschElementText) and \
                                len(element._lines) == 1:
                    m = rex_attribute.match(element._lines[0])
                    if m:
                        self._attributes[m.group('name')] = m.group('value')
        return self._attributes

    def get_attribute(self, name):
        # TODO Handle Embedded Elements as well
        if name in self.attributes.keys():
            return self.attributes[name]
        else:
            return None

    def remove_attribute(self, name):
        # TODO Handle Embedded Elements as well
        for e in self._elements:
            if isinstance(e, GschElementText) and len(e._lines) == 1:
                m = rex_attribute.match(e._lines[0])
                if m and m.group('name') == name:
                    self._elements.remove(e)
                    self._attributes = None

    def set_attribute(self, name, value):
        # TODO Handle Embedded Elements as well
        result = False
        for e in self._elements:
            if isinstance(e, GschElementText) and len(e._lines) == 1:
                m = rex_attribute.match(e._lines[0])
                if m and m.group('name') == name:
                    if getattr(e, '_visibility', False):
                        result = True
                    e._lines = ["{0}={1}\n".format(name, value)]
                    self._attributes = None
        return result

    @property
    def _params(self):
        return [str(getattr(self, '_' + x.name)) for x in self.params]

    def write_out(self, f):
        params = ' '.join(self._params)
        f.write('{0} {1}\n'.format(self.code, params))
        self._write_lines(f)
        self._write_embedded_elements(f)
        self._write_elements(f)

    def _write_lines(self, f):
        if getattr(self, '_num_lines', 0):
            f.writelines(self._lines)

    def _write_embedded_elements(self, f):
        if len(self._embedded_elements):
            f.write('[\n')
            for element in self._embedded_elements:
                element.write_out(f)
            f.write(']\n')

    def _write_elements(self, f):
        if len(self._elements):
            f.write('{\n')
            for element in self._elements:
                element.write_out(f)
            f.write('}\n')

    @property
    def is_embedded(self):
        return False

    @property
    def embed(self):
        return self._embed

    @embed.setter
    def embed(self, value):
        if self.is_embedded:
            self._embed = value
        else:
            raise Exception


class GschElementComponent(GschElementBase):
    code = 'C'
    params = [x, y, selectable, angle, mirror, basename]

    @property
    def refdes(self):
        return self.get_attribute('refdes')

    @property
    def value(self):
        return self.get_attribute('value')

    @value.setter
    def value(self, value):
        self.set_attribute('value', value)

    @property
    def basename(self):
        return getattr(self, '_basename', None)

    @property
    def is_embedded(self):
        return self.basename.startswith('EMBEDDED')


class GschElementNet(GschElementBase):
    code = 'N'
    params = [x1, y1, x2, y2, color]


class GschElementBus(GschElementBase):
    code = 'U'
    params = [x1, y1, x2, y2, color, ripperdir]


class GschElementPin(GschElementBase):
    code = 'P'
    params = [x1, y1, x2, y2, color, pintype, whichend]


class GschElementLine(GschElementBase):
    code = 'L'
    params = [x1, y1, x2, y2, color, width, capstyle,
              dashstyle, dashlength, dashspace]


class GschElementBox(GschElementBase):
    code = 'B'
    params = [x, y, boxwidth, boxheight, color, width, capstyle,
              dashstyle, dashlength, dashspace, filltype, fillwidth,
              angle1, pitch1, angle2, pitch2]


class GschElementCircle(GschElementBase):
    code = 'V'
    params = [x, y, radius, color, width, capstyle, dashstyle, dashlength,
              dashspace, filltype, fillwidth, angle1, pitch1, angle2, pitch2]


class GschElementArc(GschElementBase):
    code = 'A'
    params = [x, y, radius, startangle, sweepangle, color, width,
              capstyle, dashstyle, dashlength, dashspace]


class GschElementText(GschElementBase):
    code = 'T'
    params = [x, y, color, size, visibility, show_name_value, angle,
              alignment, num_lines]


class GschElementPicture(GschElementBase):
    code = 'G'
    params = [x1, y1, width, height, angle, mirror, embedded]

    def _write_lines(self, f):
        f.write(self.filename)
        if getattr(self, '_embedded', True):
            f.writelines(self._encoded)

    def _get_multiline(self, lines):
        self.filename = lines.popleft()
        self._encoded = []
        if getattr(self, '_embedded', False):
            while lines[0].strip() != '.':
                self._encoded.append(lines.popleft())


class GschElementPath(GschElementBase):
    code = 'H'
    params = [color, width, capstyle, dashstyle, dashlength, dashspace,
              filltype, fillwidth, angle1, pitch1, angle2, pitch2, num_lines]


object_classes = [
    GschElementComponent, GschElementNet, GschElementBus,
    GschElementPin, GschElementLine, GschElementBox,
    GschElementCircle, GschElementArc, GschElementText,
    GschElementPicture, GschElementPath
]


class GschFile(object):
    codes = {x.code: x for x in object_classes}

    def __init__(self, fpath):
        self.fpath = fpath
        self._elements = []
        self._load_file()

    @property
    def components(self):
        return self._component_generator()

    def _component_generator(self):
        for e in self._elements:
            if isinstance(e, GschElementComponent) and e.refdes:
                yield e

    def get_component(self, refdes):
        for e in self.components:
            if e.refdes == refdes:
                return e

    def remove_component(self, refdes):
        for e in self.components:
            if e.refdes == refdes:
                self._elements.remove(e)

    @property
    def meta_components(self):
        return self._meta_component_generator()

    def _meta_component_generator(self):
        for e in self._elements:
            if isinstance(e, GschElementComponent) and not e.refdes:
                yield e

    def get_meta_components(self, regex):
        rval = []
        for e in self.meta_components:
            if regex.match(e.basename):
                rval.append(e)
        return rval

    def add_element(self, element):
        self._elements.append(element)

    def _get_version(self, lines):
        m = None
        while not m:
            m = rex_vstring.match(lines.popleft())
        self._gschver = m.group('gsch_ver')
        self._filever = m.group('file_ver')

    def _get_next_element(self, parent, lines):
        while not lines[0]:
            lines.popleft()
        line = lines.popleft()
        parts = line.split()
        code = parts[0]
        params = parts[1:]
        if code not in self.codes.keys():
            print("Error parsing line : '{0}'".format(line))
            raise AttributeError(line)
        return self.codes[code](parent, lines, *params)

    def _load_file(self):
        with open(self.fpath, 'r') as f:
            lines = deque(f.readlines())
        self._get_version(lines)
        block_level = 0
        targets = {0: self}
        element = None
        ntarget = None
        while len(lines):
            if lines[0].strip() == '[':
                if not element or not element.is_embedded:
                    raise Exception
                block_level += 1
                targets[block_level] = element
                targets[block_level].embed = True
                lines.popleft()
            if lines[0].strip() == ']':
                targets[block_level].embed = False
                ntarget = targets[block_level]
                block_level -= 1
                lines.popleft()
            if lines[0].strip() == '{':
                if not element:
                    raise Exception
                block_level += 1
                if ntarget:
                    targets[block_level] = ntarget
                    ntarget = None
                else:
                    targets[block_level] = element
                lines.popleft()
            if lines[0].strip() == '}':
                block_level -= 1
                lines.popleft()
            if not len(lines):
                break
            element = self._get_next_element(targets[block_level], lines)
            targets[block_level].add_element(element)

    def write_out(self, f):
        vf = None
        if isinstance(f, basestring):
            vf = VersionedOutputFile(f)
            f = vf.as_file()

        # Header
        f.write('v {0} {1}\n'.format(self._gschver, self._filever))

        # Write Elements
        for element in self._elements:
            element.write_out(f)

        if vf:
            vf.close()
