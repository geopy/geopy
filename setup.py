#!/usr/bin/env python
"""
geopy
"""

from setuptools import setup, find_packages
from geopy import __version__ as version

INSTALL_REQUIRES = []
TESTS_REQUIRES = [
    'nose-cov',
    'pylint',
    'tox'
]


setup(
    name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    author='GeoPy Contributors',
    author_email='uijllji@gmail',
    url='https://github.com/geopy/geopy',
    download_url=(
        'https://github.com/geopy/geopy/archive/%s.tar.gz' % version
    ),
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRES,
    extras_require={
        "placefinder": ["requests_oauthlib>=0.4.0"],
        "timezone": ["pytz"],
    },
    license='MIT',
    keywords='geocode geocoding gis geographical maps earth distance',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
