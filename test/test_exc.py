import inspect

import pytest

import geopy.exc

error_classes = sorted(
    [
        v
        for v in (getattr(geopy.exc, name) for name in dir(geopy.exc))
        if inspect.isclass(v) and issubclass(v, geopy.exc.GeopyError)
    ],
    key=lambda cls: cls.__name__,
)


@pytest.mark.parametrize("error_cls", error_classes)
def test_init(error_cls):
    with pytest.raises(error_cls):
        raise error_cls("dummy")
