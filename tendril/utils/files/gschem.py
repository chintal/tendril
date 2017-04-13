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
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""

import re
from collections import deque

from tendril.utils.types.cartesian import CartesianPoint
from tendril.utils.types.cartesian import CartesianLineSegment
from tendril.utils.fsutils import VersionedOutputFile
from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)

try:
  basestring
except NameError:
  basestring = str


rex_vstring = re.compile(ur'^v (?P<gsch_ver>\d+) (?P<file_ver>\d+)$')

# TODO Constuct regular expressions from parameter definitions
# and/or use partial regexes instead?
rex_el_line = re.compile(ur'^L (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>\d+) (?P<dashstyle>-?\d+) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+)$')  # noqa
rex_el_picture = re.compile(ur'^G (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<width>\d+) (?P<height>\d+) (?P<angle>\d+) (?P<mirrored>[01]) (?P<embedded>[01])$')  # noqa
rex_el_box = re.compile(ur'^B (?P<x>-?\d+) (?P<y>-?\d+) (?P<boxwidth>-?\d+) (?P<boxheight>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[012]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+)$')  # noqa
rex_el_circle = re.compile(ur'^V (?P<x>-?\d+) (?P<y>-?\d+) (?P<radius>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[0]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+)$')  # noqa
rex_el_arc = re.compile(ur'^A (?P<x>-?\d+) (?P<y>-?\d+) (?P<radius>-?\d+) (?P<startangle>-?\d+) (?P<sweepangle>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[0]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+)$')  # noqa
rex_el_text = re.compile(ur'^T (?P<x>-?\d+) (?P<y>-?\d+) (?P<color>\d+) (?P<size>\d+) (?P<visibility>[01]) (?P<show_name_value>[012]) (?P<angle>\d+) (?P<alignment>[0-8]) (?P<num_lines>\d+)$')  # noqa
rex_el_net = re.compile(ur'^N (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+)$')  # noqa
rex_el_bus = re.compile(ur'^U (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<ripperdir>-?\d)$')  # noqa
rex_el_pin = re.compile(ur'^P (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<pintype>[01]) (?P<whichend>[01])$')  # noqa
rex_el_component = re.compile(ur'^C (?P<x>-?\d+) (?P<y>-?\d+) (?P<selectable>[01]) (?P<angle>\d+) (?P<mirror>[01]) (?P<basename>[\w.+ -]*)$')  # noqa
rex_el_path = re.compile(ur'^H (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[012]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+) (?P<num_lines>[\d]+)$')  # noqa

rex_block_start = re.compile(ur'^\s*[{]\s*$')
rex_block_end = re.compile(ur'^\s*[}]\s*$')


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
             23: 'MESH_GRID_MINOR_COLOR'
             }

map_capstyle = {0: 'END NONE',
                1: 'END SQUARE',
                2: 'END ROUND'
                }

map_dashstyle = {0: 'TYPE SOLID',
                 1: 'TYPE DOTTED',
                 2: 'TYPE DASHED',
                 3: 'TYPE CENTER',
                 4: 'TYPE PHANTOM'
                 }

map_filltype = {0: 'FILLING HOLLOW',
                1: 'FILLING FILL',
                2: 'FILLING MESH',
                3: 'FILLING HATCH',
                4: 'FILLING VOID'
                }

map_pintype = {0: 'NORMAL PIN',
               1: 'BUS PIN'
               }

map_shownamevalue = {0: 'SHOW NAME VALUE',
                     1: 'SHOW VALUE',
                     2: 'SHOW NAME'
                     }


class GschPoint(CartesianPoint):
    unit = 'mil'

    def __init__(self, parent, x, y):
        super(GschPoint, self).__init__(x, y)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class GschLine(CartesianLineSegment):
    def __init__(self, parent, p1, p2):
        super(GschLine, self).__init__(p1, p2)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class GschElementBase(object):
    def __init__(self, parent, lines, **kwargs):
        for k, v in kwargs.items():
            try:
                setattr(self, k, int(v))
            except ValueError:
                setattr(self, k, v)
        self._parent = parent
        self._elements = []
        self._get_multiline(lines)

    def add_element(self, element):
        self._elements.append(element)

    def _get_multiline(self, lines):
        return

    @property
    def parent(self):
        return self._parent

    @property
    def active_point(self):
        return []

    @property
    def active_points(self):
        rval = self.active_point
        for element in self._elements:
            rval += element.active_points
        return rval

    @property
    def passive_line(self):
        return []

    @property
    def passive_lines(self):
        rval = self.passive_line
        for element in self._elements:
            rval += element.passive_lines
        return rval

    def write_out(self, f):
        raise NotImplementedError

    def _write_elements(self, f):
        if len(self._elements):
            f.write('{\n')
            for element in self._elements:
                element.write_out(f)
            f.write('}\n')


class GschElementComponent(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementComponent, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        params = (self.x, self.y, self.selectable,
                  self.angle, self.mirror, self.basename)
        f.write('C {0} {1} {2} {3} {4} {5}\n'.format(*params))
        self._write_elements(f)


class GschElementNet(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementNet, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        params = (self.x1, self.y1, self.x2, self.y2, self.color)
        f.write('N {0} {1} {2} {3} {4}\n'.format(*params))
        self._write_elements(f)


class GschElementBus(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementBus, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        p = (self.x1, self.y1, self.x2, self.y2, self.color, self.ripperdir)
        f.write('U {0} {1} {2} {3} {4} {5}\n'.format(*p))
        self._write_elements(f)


class GschElementPin(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPin, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        # TODO Untested
        p = (self.x1, self.y1, self.x2, self.y2, self.color,
             self.pintype, self.whichend)
        f.write('P {0} {1} {2} {3} {4} {5} {6}\n'.format(*p))
        self._write_elements(f)


class GschElementLine(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementLine, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        p = (self.x1, self.y1, self.x2, self.y2, self.color, self.width,
             self.capstyle, self.dashstyle, self.dashlength, self.dashspace)
        f.write('L {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}\n'.format(*p))
        self._write_elements(f)


class GschElementBox(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementBox, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        # TODO Untested
        p = (self.x, self.y, self.boxwidth, self.boxheight,
             self.color, self.width, self.capstyle,
             self.dashstyle, self.dashlength, self.dashspace,
             self.filltype, self.fillwidth,
             self.angle1, self.pitch1, self.angle2, self.pitch2)
        f.write('B {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} '
                '{12} {13} {14} {15}\n'.format(*p))
        self._write_elements(f)


class GschElementCircle(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementCircle, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        # TODO Untested
        p = (self.x, self.y, self.radius, self.color, self.width, self.capstyle,
             self.dashstyle, self.dashlength, self.dashspace,
             self.filltype, self.fillwidth,
             self.angle1, self.pitch1, self.angle2, self.pitch2)
        f.write('V {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} '
                '{12} {13} {14}\n'.format(*p))
        self._write_elements(f)


class GschElementArc(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementArc, self).__init__(parent, lines, **kwargs)

    def write_out(self, f):
        # TODO Untested
        p = (self.x, self.y, self.radius, self.startangle, self.sweepangle,
             self.color, self.width, self.capstyle,
             self.dashstyle, self.dashlength, self.dashspace)
        f.write('A {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}\n'.format(*p))
        self._write_elements(f)


class GschElementText(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementText, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self._lines = []
        for i in range(int(self.num_lines)):
            self._lines.append(lines.popleft())

    def write_out(self, f):
        params = (self.x, self.y, self.color, self.size,
                  self.visibility, self.show_name_value, self.angle,
                  self.alignment, self.num_lines)
        f.write('T {0} {1} {2} {3} {4} {5} {6} {7} {8}\n'.format(*params))
        f.writelines(self._lines)
        self._write_elements(f)


class GschElementPicture(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPicture, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self.fpath = lines.popleft()
        self._encoded = []
        if self.embedded == 1:
            line = None
            while line.strip() != '.':
                self._encoded.append(lines.popleft())


class GschElementPath(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPath, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self._segments = []
        for i in range(int(self.num_lines)):
            self._segments.append(lines.popleft())


class GschFile(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self._elements = []
        self._load_file()

    def add_element(self, element):
        self._elements.append(element)

    def _get_version(self, lines):
        m = None
        while not m:
            m = rex_vstring.match(lines.popleft())
        self._gschver = m.group('gsch_ver')
        self._filever = m.group('file_ver')

    @staticmethod
    def _get_next_element(parent, lines):
        line = None
        while not line:
            line = lines.popleft()
        # TODO
        # Consider refactor that allows the details of the format to reside
        # within the object classes instead.
        if line.startswith('L'):
            return GschElementLine(parent, lines=lines,
                                   **rex_el_line.match(line).groupdict())
        elif line.startswith('G'):
            return GschElementPicture(parent, lines=lines,
                                      **rex_el_picture.match(line).groupdict())
        elif line.startswith('B'):
            return GschElementBox(parent, lines=lines,
                                  **rex_el_box.match(line).groupdict())
        elif line.startswith('V'):
            return GschElementCircle(parent, lines=lines,
                                     **rex_el_circle.match(line).groupdict())
        elif line.startswith('A'):
            return GschElementArc(parent, lines=lines,
                                  **rex_el_arc.match(line).groupdict())
        elif line.startswith('T'):
            return GschElementText(parent, lines=lines,
                                   **rex_el_text.match(line).groupdict())
        elif line.startswith('N'):
            return GschElementNet(parent, lines=lines,
                                  **rex_el_net.match(line).groupdict())
        elif line.startswith('U'):
            return GschElementBus(parent, lines=lines,
                                  **rex_el_bus.match(line).groupdict())
        elif line.startswith('P'):
            return GschElementPin(parent, lines=lines,
                                  **rex_el_pin.match(line).groupdict())
        elif line.startswith('C'):
            return GschElementComponent(
                parent, lines=lines, **rex_el_component.match(line).groupdict()
            )
        elif line.startswith('H'):
            return GschElementPath(parent, lines=lines,
                                   **rex_el_path.match(line).groupdict())
        else:
            raise AttributeError(line)

    def _load_file(self):
        with open(self.fpath, 'r') as f:
            lines = deque(f.readlines())
        self._get_version(lines)
        block_level = 0
        targets = {0: self}
        element = None
        while len(lines):
            if rex_block_start.match(lines[0]):
                if not element:
                    raise Exception
                block_level += 1
                targets[block_level] = element
                lines.popleft()
            elif rex_block_end.match(lines[0]):
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
