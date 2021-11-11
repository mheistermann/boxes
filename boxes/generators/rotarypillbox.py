#!/usr/bin/env python3
# Copyright (C) 2021 Martin Heistermann
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from boxes import Boxes, restore, holeCol
import math
from math import sin, cos, tan

def rad_to_deg(rad):
    return 180. / math.pi * rad

def interp(a, b, theta):
    x = (1 - theta) * a[0] + theta * b[0]
    y = (1 - theta) * a[1] + theta * b[1]
    return x, y

class RotaryPillBox(Boxes):
    """Rotary pill box made from multiple layers"""
    
    ui_group = "Misc"

    def __init__(self):
        Boxes.__init__(self)

        self.argparser.add_argument(
            "--diameter",  action="store", type=float, default=100.,
            help="disk diameter (mm)")
        self.argparser.add_argument(
            "--hole_diameter",  action="store", type=float, default=2.,
            help="center hole diameter (mm)")

        #TODO: use NutHole?
        self.argparser.add_argument(
            "--bottom_hole_diameter",  action="store", type=float, default=8.,
            help="bottom hole diameter in (to fit a bolt head) (mm)")
        self.argparser.add_argument(
            "--inset_inner_dist",  action="store", type=float, default=10,
            help="Distance of insets from inner hole (mm)")
        self.argparser.add_argument(
            "--inset_outer_dist",  action="store", type=float, default=7,
            help="Distance of insets from outside (mm)")
        self.argparser.add_argument(
            "--inset_inter_dist",  action="store", type=float, default=2,
            help="Distance between insets (mm)")
        self.argparser.add_argument(
            "--outer_rounding",  action="store", type=float, default=3,
            help="rounding of outer inset corners (%%)")
        self.argparser.add_argument(
            "--inner_rounding",  action="store", type=float, default=3,
            help="rounding of inner inset corners (%%)")

        self.argparser.add_argument(
            "--n",  action="store", type=int, default=8,
            help="Number of segments")

    @property
    def radius(self):
        return .5 * self.diameter

    @property
    def hole_radius(self):
        return .5 * self.hole_diameter

    @property
    def bottom_hole_radius(self):
        return .5 * self.bottom_hole_diameter

    @restore
    def bezier(self, a, b, c, d):
        self.moveTo(a[0], a[1], 0)
        self.ctx.curve_to(
                b[0]-a[0], b[1]-a[1],
                c[0]-a[0], c[1]-a[1],
                d[0]-a[0], d[1]-a[1])

    def closed_cubic_spline(self, cp):

        dbl = cp + cp
        for a, b, c, d in zip(cp, dbl[1:], dbl[2:], dbl[3:]):
            ab = interp(a, b, 2./3)
            bc1 = interp(b, c, 1./3)
            bc2 = interp(b, c, 2./3)
            cd = interp(c, d, 1./3)
            first = interp(ab, bc1, .5)
            last = interp(bc2, cd, .5)
            self.bezier(first, bc1, bc2, last)

    def angle(self, k):
        return (math.pi * 2 / self.n) * k

    @restore
    def magnet_hole(self, k, top):
        x = self.radius - self.inset_outer_dist/2
        self.ctx.rotate(self.angle(k+0.5))
        if top:
            magnet_radius = 3.9/2
            self.hole(x, 0, magnet_radius)
        else:
            magnet_w = magnet_h = 4.8
            magnet_r = 0.0
            self.rectangularHole(x, 0,
                    magnet_w, magnet_h, magnet_r)

    @restore
    @holeCol
    def pill_inset(self, k, extra_inner=0):

        inner_radius = self.hole_radius + self.inset_inner_dist + extra_inner
        outer_radius = self.radius - self.inset_outer_dist

        alpha = self.angle(0.5)
        # sin α = d_inter/2 / p_x
        p_x = (self.inset_inter_dist / 2) / sin(alpha)
        p_y = 0

        a = inner_radius - p_x
        if a < 0:
            print("Warning, inset_inner_dist too small (or inset_inter_dist too large)")

        c_x = inner_radius
        c_y = a * tan(alpha)

        e_x = p_x + cos(alpha) * (outer_radius - p_x)
        e_y = sin(alpha) * (outer_radius - p_x)

        self.ctx.rotate(self.angle(k))

        if 0:
            self.circle(0, 0, inner_radius)
            self.circle(0, 0, outer_radius)
            self.hole(p_x, 0, .5)
            self.hole(p_x, 0, .5)
            self.hole(c_x, c_y, .5)
            self.hole(c_x, -c_y, .5)
            self.hole(e_x, e_y, .5)
            self.hole(e_x, -e_y, .5)



        c = c_x, c_y
        e = e_x, e_y

        def ny(v):
            return v[0], -v[1]

        if 0:
            self.circle(0, 0, outer_radius)

        spoke=0.1
        bar=0.33
        baz = 0.33 * e_y
        baz = 0.3 * e_y

        self.closed_cubic_spline([
                    (c_x, c_y),
                    interp(c, e, spoke),
                    interp(c, e, 1-spoke),
                    (e_x, e_y),
                    (e_x+sin(alpha)*baz, e_y-cos(alpha)*baz),
                    (outer_radius, e_y*bar),
                    (outer_radius, 0),
                    (outer_radius, -e_y*bar),
                    (e_x+sin(alpha)*baz, -e_y+cos(alpha)*baz),
                    (e_x, -e_y),
                    ny(interp(c, e, 1-spoke)),
                    ny(interp(c, e, spoke)),
                    (c_x, -c_y),
                    #(inner_radius, -tmp_in),
                    (inner_radius, 0),
                    #(inner_radius, tmp_in),
                    ])


    def magnet_ring(self, top):
        for k in range(self.n):
            self.magnet_hole(k, top)

    def hole_disk(self, extra_inner, add_labels):
        self.circle(0, 0, self.diameter/2)
        self.hole(0, 0, self.hole_radius)
        labels = "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"
        labels = "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"
        text_rad = self.hole_radius + self.inset_inner_dist + extra_inner 
        for k, label in enumerate(labels):
            angle_rad = self.angle(k)
            self.pill_inset(k, extra_inner)
            if add_labels:
                self.text(label,
                        text_rad * cos(angle_rad),
                        text_rad * sin(angle_rad),
                        rad_to_deg(angle_rad) + 90,
                        align="center",
                        fontsize=3,
                        color=(0,0.5,0)
                        )

    def top_disk(self, holes=False):
        self.circle(0, 0, self.diameter/2)
        self.pill_inset(0)
        if holes:
            self.hole(0, 0, self.hole_radius)
            self.magnet_ring(top=True)

    def bottom_disk(self):
        self.circle(0, 0, self.diameter/2)
        #self.hole(0, 0, self.bottom_hole_radius)

    def render(self):
        extra = 5
        padding_mm = 3
        dist = self.diameter + padding_mm
        self.moveTo(0, -70) # escape from reference bar
        self.top_disk(holes=True)

        self.moveTo(dist, 0)
        self.top_disk(holes=False)

        self.moveTo(dist, 0)
        self.bottom_disk()

        self.moveTo(-dist * 2, -dist)
        self.hole_disk(0, False)
        self.magnet_ring(top=False)


        self.moveTo(dist, 0)
        self.hole_disk(extra, True)
        self.magnet_ring(top=False)
        self.pill_inset(0, color=(1,0,0))

        self.moveTo(dist, 0)
        self.hole_disk(extra, False)
