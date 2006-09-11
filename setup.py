from setuptools import setup, find_packages

setup(name='geopy',
      version='0.92',
      description='Python Geocoding Toolbox',
      author='Brian Beck',
      author_email='exogen@gmail.com',
      url='http://exogen.case.edu/projects/geopy/',
      packages=find_packages(),
      license='MIT',
      keywords='geocode geocoding gis geographical maps earth',
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
