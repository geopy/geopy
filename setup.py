#!/usr/bin/env python
"""
geopy
"""

from setuptools import find_packages, setup

from geopy import __version__ as version

INSTALL_REQUIRES = [
    'geographiclib<2,>=1.49',
]


setup(
    name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    long_description=open('README.rst').read(),
    author='GeoPy Contributors',
    author_email='uijllji@gmail.com',
    url='https://github.com/geopy/geopy',
    download_url=(
        'https://github.com/geopy/geopy/archive/%s.tar.gz' % version
    ),
    packages=find_packages(exclude=["*test*"]),
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": [
            "coverage",
            "contextlib2; python_version<'3.0'",
            "flake8>=3.5.0,<3.6.0",
            "mock",
            "pytest>=3",
            "six",
            "sphinx",
            "sphinx_rtd_theme>=0.4.0",
        ],
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
