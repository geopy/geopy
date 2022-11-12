#!/usr/bin/env python

from setuptools import setup

from geopy import __version__ as version

EXTRAS_DEV_LINT = [
    "flake8>=5.0,<5.1",
    "isort>=5.10.0,<5.11.0",
]

EXTRAS_DEV_TEST = [
    "coverage",
    "pytest-asyncio>=0.17",
    "pytest>=3.10",
    "sphinx<=4.3.2",  # `docutils` from sphinx is used in tests
]

EXTRAS_DEV_DOCS = [
    "readme_renderer",
    "sphinx<=4.3.2",
    "sphinx-issues",
    "sphinx_rtd_theme>=0.5.0",
]

setup(
    download_url=(
        'https://github.com/geopy/geopy/archive/%s.tar.gz' % version
    ),
    extras_require={
        "dev": sorted(set(
            EXTRAS_DEV_LINT +
            EXTRAS_DEV_TEST +
            EXTRAS_DEV_DOCS
        )),
        "dev-lint": EXTRAS_DEV_LINT,
        "dev-test": EXTRAS_DEV_TEST,
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
)
