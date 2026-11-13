import warnings
from collections import UserDict
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from geopy.exc import GeocoderQueryError
from geopy.geocoders import Bing, Geocodio, Geolake, Here, HereV7, Nominatim
from test.geocoders.base import DummySyncAdapter


@pytest.fixture(params=[Bing, Geocodio, Geolake, Here, HereV7, Nominatim])
def geocoder(request):
    cls = request.param
    kwargs = {'adapter_factory': DummySyncAdapter, 'user_agent': 'geopy-test'}
    if cls is Here:
        kwargs['apikey'] = 'test-key'
    elif cls is not Nominatim:
        kwargs['apikey' if cls is HereV7 else 'api_key'] = 'test-key'
    return cls(**kwargs)


def geocode(geocoder, query):
    if isinstance(geocoder, HereV7):
        return geocoder.geocode(components=query)
    return geocoder.geocode(query)


def test_unsupported_structured_keys_warn_and_stay_out_of_request(geocoder):
    key = 'locality' if isinstance(geocoder, Bing) else 'city'
    query = UserDict({key: 'Test City', 'cityy': 'private-value', 'unknown': 1})
    with patch.object(geocoder, '_call_geocoder') as call:
        with pytest.warns(UserWarning, match='cityy') as recorded:
            geocode(geocoder, query)
    assert len(recorded) == 1
    assert 'unknown' in str(recorded[0].message)
    assert 'private-value' not in str(recorded[0].message)
    assert recorded[0].filename == __file__
    params = parse_qs(urlparse(call.call_args.args[0]).query)
    if isinstance(geocoder, HereV7):
        assert params['qq'] == ['city=Test City']
    else:
        assert params[key] == ['Test City']
    assert 'cityy' not in params
    assert 'unknown' not in params
    assert query == {key: 'Test City', 'cityy': 'private-value', 'unknown': 1}


def test_supported_structured_keys_do_not_warn(geocoder):
    key = 'locality' if isinstance(geocoder, Bing) else 'city'
    with patch.object(geocoder, '_call_geocoder'):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')
            geocode(geocoder, {key: 'Test City'})
    assert not recorded


def test_non_string_unsupported_keys_warn(geocoder):
    with patch.object(geocoder, '_call_geocoder'):
        with pytest.warns(UserWarning, match='123'):
            geocode(geocoder, {'city': 'Test City', 123: 'ignored', None: 'ignored'})


def test_here_v7_unknown_only_components_still_raise():
    geocoder = HereV7('test-key', adapter_factory=DummySyncAdapter)
    with pytest.warns(UserWarning, match='cityy'):
        with pytest.raises(GeocoderQueryError, match='must not be empty'):
            geocoder.geocode(components={'cityy': 'Test City'})


def test_free_text_queries_do_not_warn(geocoder):
    with patch.object(geocoder, '_call_geocoder') as call:
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')
            geocoder.geocode('Test City')
    assert not recorded
    params = parse_qs(urlparse(call.call_args.args[0]).query)
    key = 'query' if isinstance(geocoder, Bing) else (
        'searchtext' if isinstance(geocoder, Here) else 'q'
    )
    assert params[key] == ['Test City']


def test_all_supported_structured_keys_do_not_warn(geocoder):
    query = dict.fromkeys(geocoder.structured_query_params, 'value')
    with patch.object(geocoder, '_call_geocoder') as call:
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')
            geocode(geocoder, query)
    assert not recorded
    params = parse_qs(urlparse(call.call_args.args[0]).query)
    if isinstance(geocoder, HereV7):
        assert set(params['qq'][0].split(';')) == {
            '%s=value' % key for key in query
        }
    else:
        assert all(params[key] == ['value'] for key in query)
