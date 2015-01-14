"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from decimal import Decimal

E24 = map(Decimal, ['1.0', '1.1', '1.2', '1.3', '1.5', '1.6', '1.8', '2.0', '2.2', '2.4', '2.7', '3.0',
                    '3.3', '3.6', '3.9', '4.3', '4.7', '5.1', '5.6', '6.2', '6.8', '7.5', '8.2', '9.1'])
E12 = [elem for idx, elem in enumerate(E24) if idx % 2 == 0]
E6 = [elem for idx, elem in enumerate(E12) if idx % 2 == 0]
E3 = [elem for idx, elem in enumerate(E6) if idx % 2 == 0]

cap_ostrs = ['fF', 'pF', 'nF', 'uF', 'mF']


def gen_vals(series, ostrs, start=None, end=None):
    if start is None:
        in_range = True
    else:
        in_range = False
    vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())
    for ostr in ostrs:
        for decade in range(3):
            for value in series:
                valstr = vfmt(value * (10**decade))+ostr
                if in_range is False:
                    if valstr == start:
                        in_range = True
                if in_range is True:
                    yield valstr
                    if valstr == end:
                        return




