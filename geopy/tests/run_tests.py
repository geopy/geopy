#!/usr/bin/env python
import unittest
import sys
from geopy.tests.test_backends import get_suite as get_backend_suite
from geopy.tests.test_gpx import get_suite as get_gpx_suite

def all_tests():
    # Test if BeautifulSoup is installed, since the microformat
    # parser relies on it.
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        BeautifulSoup = None
    
    tests = [
        get_backend_suite(),
        get_gpx_suite(),
    ]

    if BeautifulSoup:
        from test_microformats import get_suite as get_microformat_suite
        tests.append(get_microformat_suite())

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    tests = all_tests()
    failures = unittest.TextTestRunner(verbosity=2).run(tests)
