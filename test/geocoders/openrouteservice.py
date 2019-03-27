# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All rights reserved.
#
# Modifications Copyright (C) 2018 HeiGIT, University of Heidelberg.
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""Tests for the Pelias geocoding module."""

from __future__ import unicode_literals

import unittest
import warnings
from geopy.exc import GeocoderAuthenticationFailure
from geopy.compat import u

from geopy.geocoders.openrouteservice import openrouteservice
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


class BaseOpenrouteserviceTestCase(GeocoderTestBase):

    def test_api_key_error(self):
        with self.assertRaises(TypeError):
            openrouteservice()

    @classmethod
    def make_geocoder(cls, **kwargs):
        return openrouteservice(api_key=env.get('OPENROUTESERVICE_KEY'), **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = cls.make_geocoder()

    # geocode tests
    def test_exactly_one_false(self):
        result_exactly_one_false = self.geocode_run(
            {"query": "berliner straße 45",
             "exactly_one": False},
            {}
        )
        self.assertTrue(len(result_exactly_one_false) != 1)

    def test_empty_response(self):
        self.geocode_run(
            {"query": "wiuerhyfyj"},
            {},
            expect_failure=True
        )

    def test_geocoder(self):
        self.geocode_run(
            {"query": "berliner straße 45, heidelberg"},
            {"latitude": 49.418623, "longitude": 8.67583}
        )

    def test_boundary_rect(self):
        self.geocode_run(
            {"query": "heidelberg",
             "boundary_rect": [Point(50.611132, 6.756592), Point(47.665387, 11.557617)]},
            {"latitude": 49.418623, "longitude": 8.67583}
        )

    def test_boundary_rect_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.geocode_run(
                {"query": "berliner straße 45, heidelberg",
                 "boundary_rect": [8.667612, 49.42288, 8.685701, 49.412509]},
                {"latitude": 49.418623, "longitude": 8.67583}
            )
        self.assertEqual(1, len(w))

    def test_focus_point(self):
        result_focus = self.geocode_run(
            {"query": "Tour Eiffel",
             "focus_point": Point(48.868921, 2.305198),
             "exactly_one": False},
            {}
        )
        result_non_focus = self.geocode_run(
            {"query": "Tour Eiffel",
             "exactly_one": False},
            {}
        )
        self.assertNotAlmostEqual(result_focus[1].latitude, result_non_focus[1].latitude)
        self.assertNotAlmostEqual(result_focus[1].longitude, result_non_focus[1].longitude)

    # def test_invalid_focus_point(self):
    #     with self.assertRaises(Exception): # and warnings.catch_warnings(record=True) as w:
    #         # warnings.simplefilter('always')
    #         self.geocode_run(
    #             {"query": "Tour Eiffel",
    #              "focus_point": {Point(2.305198, 48.868921)}, #(48868921, 8667612), Point(2.305198, 48.868921)
    #              "exactly_one": False},
    #             {}
    #         )
    #     self.assertEqual(1, len(w))

    def test_circle_point(self):
        self.geocode_run(
            {"query": "berliner straße 45",
             "circle_point": Point(49.42288, 8.667612),
             "circle_radius": 10},
            {"latitude": 49.418579, "longitude": 8.675581}
        )
        self.geocode_run(
            {"query": "berliner straße 45"},
            {"latitude": 51.807666, "longitude": 10.331371}
        )

    def test_circle_point_missing_radius(self):
        with self.assertRaises(AttributeError):
            self.geocode_run(
                {"query": "berliner straße 45",
                 "circle_point": Point(49.42288, 8.667612)},
                {}
            )

    def test_circle_radius_missing_point(self):
        with self.assertRaises(AttributeError):
            self.geocode_run(
                {"query": "berliner straße 45",
                 "circle_radius": 10},
                {}
            )

    def test_country(self):
        result_country = self.geocode_run(
            {"query": "heidelberg",
             "country": "de",
             "exactly_one": False
             },
            {}
        )
        result_non_country = self.geocode_run(
            {"query": "heidelberg",
             "exactly_one": False
             },
            {}
        )
        self.assertNotAlmostEqual(len(result_country), len(result_non_country))

    def test_layers(self):
        self.geocode_run(
            {"query": "Tour Eiffel, france",
             "layers": ["address"]},
            {"latitude": 50.664732, "longitude": 3.214669, "address": '0 Rue De La Tour Eiffel'}
        )

    # TODO error
    def test_layers_error(self):
        with self.assertRaises(Exception):
            self.geocode_run(
                {"query": "Tour Eiffel",
                 "layers": "address"},
                {}
            )

    def test_sources(self):
        self.geocode_run(
            {"query": "Tour Eiffel, france",
             "sources": ["oa"]},
            {"latitude": 50.664732, "longitude": 3.214669, "address": '0 Rue De La Tour Eiffel'}
        )

    def test_sources_error(self):
        with self.assertRaises(Exception):
            self.geocode_run(
                {"query": "Tour Eiffel, france",
                 "sources": "oa"},
                {}
            )

    def test_size(self):
        result_size = self.geocode_run(
            {"query": "berliner straße 45",
             "size": 2,
             "exactly_one": False},
            {}
        )
        self.assertEqual(len(result_size), 2)

    def test_size_missing_exactly_one(self):
        with self.assertRaises(AttributeError):
            self.geocode_run(
                {"query": "berliner straße 45", "size": 2},
                {}
            )

    # reverse tests
    def test_reverse(self):
        self.reverse_run(
            {"query": Point(52.516756, 13.388332)},
            {"address": "Unter Den Linden 37"}
        )

    def test_reverse_circle_radius(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
        result_reverse_point = self.reverse_run(
            {"query": Point(48.858268, 2.294471),
             "circle_radius": 0.001,
             "exactly_one": False},
            {"address": 'Gros-Caillou'}
        )
        result_non_reverse_point = self.reverse_run(
            {"query": Point(48.858268, 2.294471),
             "exactly_one": False},
            {"address": '75056Y - A'}
        )
        self.assertNotAlmostEqual(len(result_reverse_point), len(result_non_reverse_point))
        self.assertTrue(len(result_reverse_point), 1)
        self.assertTrue(len(result_non_reverse_point), 10)

    def test_circle_radius_missing_exactly_one(self):
        with self.assertRaises(AttributeError):
            self.reverse_run({"query": Point(48.858268, 2.294471), "circle_radius": 0.001}, {})

    def test_reverse_layers(self):
        self.reverse_run(
            {"query": Point(48.858268, 2.294471),
             "layers": ["address"]},
            {"address": '5 Avenue Anatole France'}
        )

    def test_reverse_sources(self):
        self.reverse_run(
            {"query": Point(48.858268, 2.294471),
             "sources": ["oa"]},
            {"address": '6 Avenue Gustave Eiffel'}
        )

    def test_reverse_size(self):
        result_size = self.reverse_run(
            {"query": Point(48.858268, 2.294471),
             "size": 2,
             "exactly_one": False},
            {}
        )
        self.assertEqual(len(result_size), 2)


@unittest.skipUnless(
    bool(env.get('OPENROUTESERVICE_KEY')),
    "No OPENROUTESERVICE_KEY env variable set"
)
class OpenrouteserviceAuthenticationTestCase(BaseOpenrouteserviceTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return openrouteservice(api_key=env.get('OPENROUTESERVICE_KEY'), **kwargs)


if __name__ == '__main__':
    unittest.main()
