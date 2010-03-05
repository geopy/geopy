from setuptools import setup, find_packages

install_requires = []

# Test if we have built-in JSON - Python 2.6+, 3.0+.
# Older Python versions require simplejson.
try:
    import json
except ImportError:
    install_requires.append('simplejson')

setup(name='geopy',
      version='0.94',
      description='Python Geocoding Toolbox',
      author='Brian Beck',
      author_email='exogen@gmail.com',
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
