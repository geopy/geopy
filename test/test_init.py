import subprocess
import sys

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


def test_import_does_not_load_asyncio():
    code = "import sys, geopy; sys.exit('asyncio' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
