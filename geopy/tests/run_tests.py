#!/usr/bin/env python
import unittest
import sys
from test_gpx import get_suite as get_gpx_suite
from test_microformats import get_suite as get_microformat_suite

def all_tests():
    return unittest.TestSuite([
        get_gpx_suite(),
        get_microformat_suite(),
    ])

if __name__ == '__main__':
    tests = all_tests()
    failures = unittest.TextTestRunner(verbosity=2).run(tests)
