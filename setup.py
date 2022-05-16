#!/usr/bin/env python

from setuptools import find_packages, setup

from geopy import __version__ as version

INSTALL_REQUIRES = [
    'geographiclib<3,>=1.49',
]

EXTRAS_DEV_TESTFILES_COMMON = [
]

EXTRAS_DEV_LINT = [
    "flake8>=3.8.0,<3.9.0",
    "isort>=5.6.0,<5.7.0",
]

EXTRAS_DEV_TEST = [
    "coverage",
    "pytest-asyncio>=0.17",
    "pytest>=3.10",
    "sphinx",  # `docutils` from sphinx is used in tests
]

EXTRAS_DEV_DOCS = [
    "readme_renderer",
    "sphinx",
    "sphinx-issues",
    "sphinx_rtd_theme>=0.5.0",
]

setup(
    name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    long_description=open('README.rst').read(),
    maintainer='Kostya Esmukov',
    maintainer_email='kostya@esmukov.ru',
    url='https://github.com/geopy/geopy',
    download_url=(
        'https://github.com/geopy/geopy/archive/%s.tar.gz' % version
    ),
    packages=find_packages(exclude=["*test*"]),
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": sorted(set(
            EXTRAS_DEV_TESTFILES_COMMON +
            EXTRAS_DEV_LINT +
            EXTRAS_DEV_TEST +
            EXTRAS_DEV_DOCS
        )),
        "dev-lint": (EXTRAS_DEV_TESTFILES_COMMON +
                     EXTRAS_DEV_LINT),
        "dev-test": (EXTRAS_DEV_TESTFILES_COMMON +
                     EXTRAS_DEV_TEST),
        "dev-docs": EXTRAS_DEV_DOCS,
        "aiohttp": ["aiohttp"],
        "requests": [
            "urllib3>=1.24.2",
            # ^^^ earlier versions would work, but a custom ssl
            # context would silently have system certificates be loaded as
            # trusted: https://github.com/urllib3/urllib3/pull/1566

            "requests>=2.16.2",
            # ^^^ earlier versions would work, but they use an older
            # vendored version of urllib3 (see note above)
        ],
        "timezone": ["pytz"],
    },
    license='MIT',
    keywords='geocode geocoding gis geographical maps earth distance',
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
