from setuptools import setup, find_packages

install_requires = []

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

version = __import__('geopy').get_version()

setup(name='geopy',
    version=version,
    description='Python Geocoding Toolbox',
    author='Mike Tigas', # update this as needed
    author_email='mike.tigas@gmail.com', # update this as needed
    url='http://www.geopy.org/',
    download_url='http://code.google.com/p/geopy/downloads/list',
    packages=find_packages(),
    install_requires=install_requires,
    test_suite = "geopy.tests.run_tests.all_tests",
    license='MIT',
    keywords='geocode geocoding gis geographical maps earth distance',
    classifiers=["Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
