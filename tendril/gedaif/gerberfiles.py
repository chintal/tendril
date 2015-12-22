#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for gerberfiles
"""

from gerber.render.cairo_backend import PCBCairoContext
from gerber.render.cairo_backend import GerberCairoContext
from gerber.common import read
from gerber.render import theme


class TendrilPCBCairoContext(PCBCairoContext):

    outline_color = (0.0, 0.612, 0.396)
    outline_alpha = 1.0

    copper_color = theme.COLORS['enig copper']
    copper_alpha = 1.0

    mask_color = theme.COLORS['green soldermask']
    mask_alpha = 0.75

    silk_color = theme.COLORS['white']
    silk_alpha = 1.0

    drill_color = theme.COLORS['black']
    drill_alpha = 1.0

    layer_colors = [
        (0.804, 0.216, 0),
        (0.329, 0.545, 0.329),
        (0.545, 0.137, 0.137),
        (0.227, 0.373, 0.804),
        (0.78, 0.776, 0.251),
        (0.545, 0.451, 0.333),
        (0, 0.525, 0.545),
        (0.133, 0.545, 0.133),
    ]

    far_side = []

    def render_top_view(self, output_filename=None,
                        quick=False, nox=False):
        output_filename = '{0}.top.png'.format(output_filename)
        ctx = GerberCairoContext()

        if self.outline_color is not None:
            ctx.color = self.outline_color
        if self.outline_alpha is not None:
            ctx.alpha = self.outline_alpha
        outline = read(self.layers.outline)
        outline.render(ctx)

        if self.copper_color is not None:
            ctx.color = self.copper_color
        if self.copper_alpha is not None:
            ctx.alpha = self.copper_alpha
        copper = read(self.layers.top)
        copper.render(ctx)

        if self.mask_color is not None:
            ctx.color = self.mask_color
        if self.mask_alpha is not None:
            ctx.alpha = self.mask_alpha
        mask = read(self.layers.topmask)
        mask.render(ctx, invert=True)

        if self.silk_color is not None:
            ctx.color = self.silk_color
        if self.silk_alpha is not None:
            ctx.alpha = self.silk_alpha
        silk = read(self.layers.topsilk)
        silk.render(ctx)

        if self.drill_color is not None:
            ctx.color = self.drill_color
        if self.drill_alpha is not None:
            ctx.alpha = self.drill_alpha
        drill = read(self.layers.drill)
        drill.render(ctx)

        ctx.dump(output_filename)

    def render_bottom_view(self, output_filename=None,
                           quick=False, nox=False):
        output_filename = '{0}.bottom.png'.format(output_filename)
        ctx = GerberCairoContext()

        if self.outline_color is not None:
            ctx.color = self.outline_color
        if self.outline_alpha is not None:
            ctx.alpha = self.outline_alpha
        outline = read(self.layers.outline)
        outline.render(ctx)

        if self.copper_color is not None:
            ctx.color = self.copper_color
        if self.copper_alpha is not None:
            ctx.alpha = self.copper_alpha
        copper = read(self.layers.bottom)
        copper.render(ctx)

        if self.mask_color is not None:
            ctx.color = self.mask_color
        if self.mask_alpha is not None:
            ctx.alpha = self.mask_alpha
        mask = read(self.layers.bottommask)
        mask.render(ctx, invert=True)

        if self.silk_color is not None:
            ctx.color = self.silk_color
        if self.silk_alpha is not None:
            ctx.alpha = self.silk_alpha
        silk = read(self.layers.bottomsilk)
        silk.render(ctx)

        if self.drill_color is not None:
            ctx.color = self.drill_color
        if self.drill_alpha is not None:
            ctx.alpha = self.drill_alpha
        drill = read(self.layers.drill)
        drill.render(ctx)

        ctx.dump(output_filename)

    def render_devel_view(self, output_filename=None,
                          quick=False, nox=False):
        output_filename = '{0}.devel.png'.format(output_filename)
        ctx = GerberCairoContext()

        ctx.color = theme.COLORS['fr-4']
        ctx.alpha = 1.0
        outline = read(self.layers.outline)
        outline.render(ctx)

        ctx.color = self.copper_color
        bottompaste = read(self.layers.bottompaste)
        bottompaste.render(ctx)

        ctx.alpha = 0.9
        ctx.color = self.silk_color
        bottomsilk = read(self.layers.bottomsilk)
        bottomsilk.render(ctx)

        num_copper_layers = len(self.layers.internal)
        if self.layers.top is not None:
            num_copper_layers += 1
        if self.layers.bottom is not None:
            num_copper_layers += 1

        ctx.color = self.layer_colors[num_copper_layers - 1]
        bottom = read(self.layers.bottom)
        bottom.render(ctx)

        ctx.alpha = 0.5
        for idx, l in enumerate(self.layers.internal):
            layer = read(l)
            ctx.color = self.layer_colors[num_copper_layers - 2 - idx]
            layer.render(ctx)

        ctx.alpha = 0.9
        ctx.color = self.layer_colors[0]
        top = read(self.layers.top)
        top.render(ctx)

        ctx.color = self.silk_color
        topsilk = read(self.layers.topsilk)
        topsilk.render(ctx)

        ctx.color = self.copper_color
        toppaste = read(self.layers.toppaste)
        toppaste.render(ctx)

        ctx.color = theme.COLORS['black']
        ctx.alpha = 1.0
        drill = read(self.layers.drill)
        drill.render(ctx)

        ctx.dump(output_filename)

    def render(self, *args, **kwargs):
        self.layers = self.dialect(self.filenames)
        self.render_top_view(*args, **kwargs)
        self.render_bottom_view(*args, **kwargs)
        self.render_devel_view(*args, **kwargs)
