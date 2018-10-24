import pickle
import unittest

import pytz
import pytz.tzinfo

from geopy.compat import u
from geopy.timezone import Timezone, from_timezone_name


class TimezoneTestCase(unittest.TestCase):

    timezone_name = u("Europe/Moscow")

    def test_create_from_timezone_name(self):
        raw = dict(foo="bar")
        tz = from_timezone_name(self.timezone_name, raw)

        self.assertEqual(tz.raw['foo'], 'bar')
        self.assertIsInstance(tz.pytz_timezone, pytz.tzinfo.BaseTzInfo)

    def test_create_from_pytz_timezone(self):
        pytz_timezone = pytz.timezone(self.timezone_name)
        tz = Timezone(pytz_timezone)
        self.assertIs(tz.pytz_timezone, pytz_timezone)

    def test_string(self):
        raw = dict(foo="bar")
        tz = from_timezone_name(self.timezone_name, raw)
        self.assertEqual(str(tz), self.timezone_name)

    def test_repr(self):
        raw = dict(foo="bar")
        pytz_timezone = pytz.timezone(self.timezone_name)
        tz = Timezone(pytz_timezone, raw)
        self.assertEqual(repr(tz), "Timezone(%s)" % repr(pytz_timezone))

    def test_eq(self):
        tz = pytz.timezone("Europe/Paris")
        raw1 = dict(a=1)
        raw2 = dict(a=1)
        self.assertEqual(Timezone(tz, raw1), Timezone(tz, raw2))

    def test_ne(self):
        tz1 = pytz.timezone("Europe/Paris")
        tz2 = pytz.timezone("Europe/Prague")
        raw = {}
        self.assertNotEqual(Timezone(tz1, raw), Timezone(tz2, raw))

    def test_picklable(self):
        raw = dict(foo="bar")
        tz = from_timezone_name(self.timezone_name, raw)
        # https://docs.python.org/2/library/pickle.html#data-stream-format
        for protocol in (0, 1, 2, -1):
            pickled = pickle.dumps(tz, protocol=protocol)
            tz_unp = pickle.loads(pickled)
            self.assertEqual(tz, tz_unp)

    def test_with_unpicklable_raw(self):
        some_class = type('some_class', (object,), {})
        raw_unpicklable = dict(missing=some_class())
        del some_class
        tz_unpicklable = from_timezone_name(self.timezone_name, raw_unpicklable)
        for protocol in (0, 1, 2, -1):
            with self.assertRaises((AttributeError, pickle.PicklingError)):
                pickle.dumps(tz_unpicklable, protocol=protocol)
