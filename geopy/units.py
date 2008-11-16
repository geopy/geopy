import math
from geopy import util

# Angles

def degrees(radians=0, arcminutes=0, arcseconds=0):
    deg = 0.
    if radians:
        deg = math.degrees(radians)
    if arcminutes:
        deg += arcminutes / arcmin(degrees=1.)
    if arcseconds:
        deg += arcseconds / arcsec(degrees=1.)
    return deg

def radians(degrees=0, arcminutes=0, arcseconds=0):
    if arcminutes:
        degrees += arcminutes / arcmin(degrees=1.)
    if arcseconds:
        degrees += arcseconds / arcsec(degrees=1.)
    return math.radians(degrees)

def arcminutes(degrees=0, radians=0, arcseconds=0):
    if radians:
        degrees += math.degrees(radians)
    if arcseconds:
        degrees += arcseconds / arcsec(degrees=1.)
    return degrees * 60.

def arcseconds(degrees=0, radians=0, arcminutes=0):
    if radians:
        degrees += math.degrees(radians)
    if arcminutes:
        degrees += arcminutes / arcmin(degrees=1.)
    return degrees * 3600.

rad = radians
arcmin = arcminutes
arcsec = arcseconds

# Lengths

def kilometers(meters=0, miles=0, feet=0, nautical=0):
    km = 0.
    if meters:
        km += meters / 1000.
    if feet:
        miles += feet / ft(1.)
    if nautical:
        km += nautical / nm(1.)
    km += miles * 1.609344
    return km

def meters(kilometers=0, miles=0, feet=0, nautical=0):
    meters = 0.
    kilometers += km(nautical=nautical, miles=miles, feet=feet)
    meters += kilometers * 1000.
    return meters

def miles(kilometers=0, meters=0, feet=0, nautical=0):
    mi = 0.
    if nautical:
        kilometers += nautical / nm(1.)
    if feet:
        mi += feet / ft(1.)
    if meters:
        kilometers += meters / 1000.
    mi += kilometers * 0.621371192
    return mi

def feet(kilometers=0, meters=0, miles=0, nautical=0):
    ft = 0.
    if nautical:
        kilometers += nautical / nm(1.)
    if meters:
        kilometers += meters / 1000.
    if kilometers:
        miles += mi(kilometers=kilometers)
    ft += miles * 5280
    return ft

def nautical(kilometers=0, meters=0, miles=0, feet=0):
    nm = 0.
    if feet:
        miles += feet / ft(1.)
    if miles:
        kilometers += km(miles=miles)
    if meters:
        kilometers += meters / 1000.
    nm += kilometers / 1.852
    return nm

km = kilometers
m = meters
mi = miles
ft = feet
nm = nautical