import pytest
from packaging.version import Version

from geopy import __version__, __version_info__, get_version


def test_version():
    assert isinstance(__version__, str) and __version__


def test_version_info():
    expected_version_info = Version(__version__).release
    assert expected_version_info == __version_info__


def test_get_version():
    version = get_version()
    assert isinstance(version, str) and version == __version__


@pytest.mark.parametrize(
    "import_code, expected_modules_absent",
    [
        ("import geopy", ["aiohttp", "yarl"]),
        ("from geopy import adapters", ["aiohttp", "yarl"]),
        ("from geopy.geocoders import Nominatim", ["aiohttp", "yarl"]),
    ],
)
def test_import_does_not_eagerly_import_aiohttp(import_code, expected_modules_absent):
    import subprocess
    import sys

    assertions = " ".join(
        f"assert '{mod}' not in sys.modules, '{mod} should not be eagerly imported';"
        for mod in expected_modules_absent
    )
    code = f"import sys; {import_code}; {assertions}"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Failed with stderr: {result.stderr}"


def test_lazy_aiohttp_access_and_instantiation():
    try:
        import aiohttp  # noqa
        import yarl  # noqa
    except ImportError:
        pytest.skip("aiohttp or yarl is not installed")

    import subprocess
    import sys

    code = (
        "import sys\n"
        "from geopy import adapters\n"
        "assert 'aiohttp' not in sys.modules\n"
        "assert adapters.aiohttp_available\n"
        "assert 'aiohttp' not in sys.modules\n"
        "adapter = adapters.AioHTTPAdapter(proxies=None, ssl_context=None)\n"
        "assert 'aiohttp' in sys.modules\n"
        "assert adapters.aiohttp is not None\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
