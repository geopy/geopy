import datetime
import time
from unittest.mock import patch

import pytest

from geopy.adapters import get_retry_after


@pytest.mark.parametrize(
    "headers, expected_retry_after",
    [
        ({}, None),
        ({"retry-after": "42"}, 42),
        ({"retry-after": "Wed, 21 Oct 2015 07:28:44 GMT"}, 43),
        ({"retry-after": "Wed, 21 Oct 2015 06:28:44 GMT"}, 0),
        ({"retry-after": "Wed"}, None),
    ],
)
def test_get_retry_after(headers, expected_retry_after):
    current_time = datetime.datetime(
        2015, 10, 21, 7, 28, 1, tzinfo=datetime.timezone.utc
    ).timestamp()
    with patch.object(time, "time", return_value=current_time):
        assert expected_retry_after == get_retry_after(headers)
