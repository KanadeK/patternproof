from importlib.metadata import version

import patternproof


def test_public_version_uses_installed_package_metadata() -> None:
    assert patternproof.__version__ == version("patternproof")
