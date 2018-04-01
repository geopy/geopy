"""
Convert units.
"""

import math


# Angles

def degrees(radians=0, arcminutes=0, arcseconds=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    deg = 0.
    if radians:
        deg = math.degrees(radians)
    if arcminutes:
        deg += arcminutes / arcmin(degrees=1.)
    if arcseconds:
        deg += arcseconds / arcsec(degrees=1.)
    return deg

def radians(degrees=0, arcminutes=0, arcseconds=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    if arcminutes:
        degrees += arcminutes / arcmin(degrees=1.)
    if arcseconds:
        degrees += arcseconds / arcsec(degrees=1.)
    return math.radians(degrees)

def arcminutes(degrees=0, radians=0, arcseconds=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    if radians:
        degrees += math.degrees(radians)
    if arcseconds:
        degrees += arcseconds / arcsec(degrees=1.)
    return degrees * 60.

def arcseconds(degrees=0, radians=0, arcminutes=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    if radians:
        degrees += math.degrees(radians)
    if arcminutes:
        degrees += arcminutes / arcmin(degrees=1.)
    return degrees * 3600.


# Lengths

def kilometers(meters=0, miles=0, feet=0, nautical=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    ret = 0.
    if meters:
        ret += meters / 1000.
    if feet:
        ret += feet / ft(1.)
    if nautical:
        ret += nautical / nm(1.)
    ret += miles * 1.609344
    return ret

def meters(kilometers=0, miles=0, feet=0, nautical=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    return (kilometers + km(nautical=nautical, miles=miles, feet=feet)) * 1000

def miles(kilometers=0, meters=0, feet=0, nautical=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    ret = 0.
    if nautical:
        kilometers += nautical / nm(1.)
    if feet:
        kilometers += feet / ft(1.)
    if meters:
        kilometers += meters / 1000.
    ret += kilometers / 1.609344
    return ret

def feet(kilometers=0, meters=0, miles=0, nautical=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    ret = 0.
    if nautical:
        kilometers += nautical / nm(1.)
    if meters:
        kilometers += meters / 1000.
    if kilometers:
        miles += mi(kilometers=kilometers)
    ret += miles * 5280
    return ret

def nautical(kilometers=0, meters=0, miles=0, feet=0): # pylint: disable=W0621
    """
    TODO docs.
    """
    ret = 0.
    if feet:
        kilometers += feet / ft(1.)
    if miles:
        kilometers += km(miles=miles)
    if meters:
        kilometers += meters / 1000.
    ret += kilometers / 1.852
    return ret


# Compatible names

rad = radians # pylint: disable=C0103
arcmin = arcminutes # pylint: disable=C0103
arcsec = arcseconds # pylint: disable=C0103
km = kilometers # pylint: disable=C0103
m = meters # pylint: disable=C0103
mi = miles # pylint: disable=C0103
ft = feet # pylint: disable=C0103
nm = nautical # pylint: disable=C0103
