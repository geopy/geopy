from setuptools import setup

install_requires = []
tests_require = [
    'nose-cov',
    'oauth2',
    'BeautifulSoup',
]

# Test if we have built-in JSON - Python 2.6+, 3.0+.
# Older Python versions require simplejson.
# Alternatively, if Django is installed, plug into the django
# copy of simplejson.
try:
    import json
except ImportError:
    try:
        import simplejson
    except ImportError:
        try:
            from django.utils import simplejson
        except:
            install_requires.append('simplejson')

# note: not automated since py3k cannot import geopy.get_version at
# install-time (since 2to3 has not yet run)
version = "0.96.0" # pylint: disable=C0103

setup(name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    author='GeoPy Contributors',
    author_email='mike@tig.as', # subject to change
    url='https://github.com/geopy/geopy',
    download_url = 'https://github.com/geopy/geopy/archive/%s.tar.gz' % version,
    packages=('geopy', ),
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
    ],
    use_2to3=True,
)
