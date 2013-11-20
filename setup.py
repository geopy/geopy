"""
geopy
"""

from setuptools import setup, find_packages

install_requires = []
tests_require = [
    'nose-cov',
    'pylint',
    'tox'
]

version = "0.97" # pylint: disable=C0103

setup(
    name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    author='GeoPy Contributors',
    author_email='mike@tig.as', # subject to change
    url='https://github.com/geopy/geopy',
    download_url = 'https://github.com/geopy/geopy/archive/release-%s.tar.gz' % version,
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
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
        "Programming Language :: Python :: 3",
    ]
)
