import configparser
from pathlib import Path

from packaging.requirements import Requirement
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


def test_aiohttp_extra_includes_yarl():
    setup_cfg = Path(__file__).resolve().parent.parent / "setup.cfg"
    parser = configparser.ConfigParser()
    parser.read(setup_cfg, encoding="utf-8")
    raw_reqs = parser["options.extras_require"]["aiohttp"]
    packages = {
        Requirement(line).name.lower()
        for line in raw_reqs.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert {"aiohttp", "yarl"} <= packages
