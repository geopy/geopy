import importlib
import inspect
import pkgutil

import pytest

import geopy.geocoders
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder

skip_modules = [
    "geopy.geocoders.base",  # doesn't contain actual geocoders
    "geopy.geocoders.osm",  # deprecated
]

geocoder_modules = sorted(
    [
        importlib.import_module(name)
        for _, name, _ in pkgutil.iter_modules(
            geopy.geocoders.__path__, "geopy.geocoders."
        )
        if name not in skip_modules
    ],
    key=lambda m: m.__name__,
)

geocoder_classes = sorted(
    {
        v
        for v in (
            getattr(module, name) for module in geocoder_modules for name in dir(module)
        )
        if inspect.isclass(v) and issubclass(v, Geocoder) and v is not Geocoder
    },
    key=lambda cls: cls.__name__,
)


def assert_no_varargs(sig):
    assert not [
        str(p)
        for p in sig.parameters.values()
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ], (
        "Geocoders must not have any (*args) or (**kwargs). "
        "See CONTRIBUTING.md for explanation."
    )


def test_all_geocoders_are_exported_from_package():
    expected = {cls.__name__ for cls in geocoder_classes}
    actual = set(dir(geopy.geocoders))
    not_exported = expected - actual
    assert not not_exported, (
        "These geocoders must be exported (via imports) "
        "in geopy/geocoders/__init__.py"
    )


def test_all_geocoders_are_listed_in_all():
    expected = {cls.__name__ for cls in geocoder_classes}
    actual = set(geopy.geocoders.__all__)
    not_exported = expected - actual
    assert not not_exported, (
        "These geocoders must be listed in the `__all__` tuple "
        "in geopy/geocoders/__init__.py"
    )


def test_all_geocoders_are_listed_in_service_to_geocoder():
    assert set(geocoder_classes) == set(geopy.geocoders.SERVICE_TO_GEOCODER.values()), (
        "All geocoders must be listed in the `SERVICE_TO_GEOCODER` dict "
        "in geopy/geocoders/__init__.py"
    )


@pytest.mark.parametrize("geocoder_module", geocoder_modules, ids=lambda m: m.__name__)
def test_geocoder_module_all(geocoder_module):
    current_all = geocoder_module.__all__
    expected_all = tuple(
        cls.__name__
        for cls in geocoder_classes
        if cls.__module__ == geocoder_module.__name__
    )
    assert expected_all == current_all


@pytest.mark.parametrize("geocoder_cls", geocoder_classes)
def test_init_method_signature(geocoder_cls):
    method = geocoder_cls.__init__
    sig = inspect.signature(method)

    assert_no_varargs(sig)

    sig_timeout = sig.parameters["timeout"]
    assert sig_timeout.kind == inspect.Parameter.KEYWORD_ONLY
    assert sig_timeout.default is DEFAULT_SENTINEL

    sig_proxies = sig.parameters["proxies"]
    assert sig_proxies.kind == inspect.Parameter.KEYWORD_ONLY
    assert sig_proxies.default is DEFAULT_SENTINEL

    sig_user_agent = sig.parameters["user_agent"]
    assert sig_user_agent.kind == inspect.Parameter.KEYWORD_ONLY
    assert sig_user_agent.default is None

    sig_ssl_context = sig.parameters["ssl_context"]
    assert sig_ssl_context.kind == inspect.Parameter.KEYWORD_ONLY
    assert sig_ssl_context.default is DEFAULT_SENTINEL

    sig_adapter_factory = sig.parameters["adapter_factory"]
    assert sig_adapter_factory.kind == inspect.Parameter.KEYWORD_ONLY
    assert sig_adapter_factory.default is None


@pytest.mark.parametrize("geocoder_cls", geocoder_classes)
def test_geocode_method_signature(geocoder_cls):
    # Every geocoder should have at least a `geocode` method.
    method = geocoder_cls.geocode
    sig = inspect.signature(method)

    assert_no_varargs(sig)

    # The first arg (except self) must be called `query`:
    sig_query = list(sig.parameters.values())[1]
    assert sig_query.name == "query"
    assert sig_query.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    # The rest must be kwargs-only:
    sig_kwargs = list(sig.parameters.values())[2:]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in sig_kwargs), (
        "All method args except `query` must be keyword-only "
        "(i.e. separated with an `*`)."
    )

    # kwargs must contain `exactly_one`:
    sig_exactly_one = sig.parameters["exactly_one"]
    assert sig_exactly_one.default is True, "`exactly_one` must be True"

    # kwargs must contain `timeout`:
    sig_timeout = sig.parameters["timeout"]
    assert sig_timeout.default is DEFAULT_SENTINEL, "`timeout` must be DEFAULT_SENTINEL"


@pytest.mark.parametrize(
    "geocoder_cls",
    [cls for cls in geocoder_classes if getattr(cls, "reverse", None)],
)
def test_reverse_method_signature(geocoder_cls):
    # `reverse` method is optional.
    method = geocoder_cls.reverse
    sig = inspect.signature(method)

    assert_no_varargs(sig)

    # First arg (except self) must be called `query`:
    sig_query = list(sig.parameters.values())[1]
    assert sig_query.name == "query"
    assert sig_query.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    # The rest must be kwargs-only:
    sig_kwargs = list(sig.parameters.values())[2:]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in sig_kwargs), (
        "All method args except `query` must be keyword-only "
        "(i.e. separated with an `*`)."
    )

    # kwargs must contain `exactly_one`:
    sig_exactly_one = sig.parameters["exactly_one"]
    assert sig_exactly_one.default is True, "`exactly_one` must be True"

    # kwargs must contain `timeout`:
    sig_timeout = sig.parameters["timeout"]
    assert sig_timeout.default is DEFAULT_SENTINEL, "`timeout` must be DEFAULT_SENTINEL"


@pytest.mark.parametrize(
    "geocoder_cls",
    [cls for cls in geocoder_classes if getattr(cls, "reverse_timezone", None)],
)
def test_reverse_timezone_method_signature(geocoder_cls):
    method = geocoder_cls.reverse_timezone
    sig = inspect.signature(method)

    assert_no_varargs(sig)

    # First arg (except self) must be called `query`:
    sig_query = list(sig.parameters.values())[1]
    assert sig_query.name == "query"
    assert sig_query.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    # The rest must be kwargs-only:
    sig_kwargs = list(sig.parameters.values())[2:]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in sig_kwargs), (
        "All method args except `query` must be keyword-only "
        "(i.e. separated with an `*`)."
    )

    # kwargs must contain `timeout`:
    sig_timeout = sig.parameters["timeout"]
    assert sig_timeout.default is DEFAULT_SENTINEL, "`timeout` must be DEFAULT_SENTINEL"


@pytest.mark.parametrize("geocoder_cls", geocoder_classes)
def test_no_extra_public_methods(geocoder_cls):
    methods = {
        n
        for n in dir(geocoder_cls)
        if not n.startswith("_") and inspect.isfunction(getattr(geocoder_cls, n))
    }
    allowed = {
        "geocode",
        "reverse",
        "reverse_timezone",
    }
    assert methods <= allowed, (
        "Geopy geocoders are currently allowed to only have these methods: %s" % allowed
    )
