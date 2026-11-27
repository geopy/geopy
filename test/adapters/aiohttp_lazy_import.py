import importlib.util
import os
import subprocess
import sys
from unittest.mock import patch

import pytest

import geopy.adapters
from geopy.adapters import AioHTTPAdapter


def _run_python(code):
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        repo_root if not existing else os.pathsep.join([repo_root, existing])
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def test_importing_geopy_does_not_import_aiohttp():
    code = (
        "import importlib.util, sys\n"
        "import geopy\n"
        "import geopy.adapters\n"
        "assert 'aiohttp' not in sys.modules\n"
        "assert 'yarl' not in sys.modules\n"
        "expected = (\n"
        "    importlib.util.find_spec('aiohttp') is not None\n"
        "    and importlib.util.find_spec('yarl') is not None\n"
        ")\n"
        "assert geopy.adapters.AioHTTPAdapter.is_available is expected\n"
    )
    _run_python(code)


def test_aiohttp_adapter_imports_aiohttp_lazily():
    if (
        importlib.util.find_spec("aiohttp") is None
        or importlib.util.find_spec("yarl") is None
    ):
        pytest.skip("aiohttp and yarl are not installed")

    code = (
        "import sys\n"
        "from geopy.adapters import AioHTTPAdapter\n"
        "assert 'aiohttp' not in sys.modules\n"
        "assert 'yarl' not in sys.modules\n"
        "adapter = AioHTTPAdapter(proxies={}, ssl_context=None)\n"
        "assert 'aiohttp' in sys.modules\n"
        "assert 'yarl' in sys.modules\n"
        "assert adapter.is_available is True\n"
    )
    _run_python(code)


def test_aiohttp_adapter_when_aiohttp_missing():
    code = (
        "import sys\n"
        "sys.modules['aiohttp'] = None\n"
        "from geopy.adapters import AioHTTPAdapter\n"
        "assert AioHTTPAdapter.is_available is False\n"
        "try:\n"
        "    AioHTTPAdapter(proxies={}, ssl_context=None)\n"
        "except ImportError as exc:\n"
        "    assert 'geopy[aiohttp]' in str(exc)\n"
        "else:\n"
        "    raise AssertionError('Expected ImportError')\n"
    )
    _run_python(code)


def test_aiohttp_adapter_raises_import_error_if_missing_at_init():
    with patch.dict(sys.modules, {"aiohttp": None}), patch.object(
        geopy.adapters, "aiohttp", None
    ), pytest.raises(ImportError, match=r"geopy\[aiohttp\]"):
        AioHTTPAdapter(proxies={}, ssl_context=None)
