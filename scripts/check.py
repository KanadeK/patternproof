"""Run the complete PatternProof release-equivalent gate."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path
from typing import Any, cast

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_NAMES = {"cells.csv", "overlay.png", "report.html", "report.json"}


def _uv() -> str:
    executable = shutil.which("uv")
    if executable is None:
        raise RuntimeError("uv is required; install it from https://docs.astral.sh/uv/")
    return executable


def _run(
    stage: str,
    command: list[str],
    *,
    cwd: Path = ROOT,
    expected: int = 0,
) -> None:
    print(f"\n[{stage}]", flush=True)
    print(f"$ {shlex.join(command)}", flush=True)
    environment = os.environ.copy()
    environment["UV_CACHE_DIR"] = str(ROOT / ".uv-cache")
    result = subprocess.run(command, cwd=cwd, env=environment, check=False)
    if result.returncode != expected:
        raise RuntimeError(
            f"{stage} exited {result.returncode}; expected {expected}: {shlex.join(command)}"
        )


def _project_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = cast(dict[str, Any], payload["project"])
    return cast(str, project["version"])


def _assert_same_example(expected: Path, actual: Path) -> None:
    if expected.suffix == ".png":
        with Image.open(expected) as expected_image, Image.open(actual) as actual_image:
            same = (
                expected_image.mode,
                expected_image.size,
                expected_image.tobytes(),
            ) == (actual_image.mode, actual_image.size, actual_image.tobytes())
    else:
        same = expected.read_bytes() == actual.read_bytes()
    if not same:
        raise RuntimeError(f"generated example differs from committed fixture: {actual.name}")


def _verify_report(path: Path, expected_counts: dict[str, int]) -> None:
    names = {item.name for item in path.iterdir() if item.is_file()}
    if names != ARTIFACT_NAMES:
        raise RuntimeError(f"report artifact set differs: expected {ARTIFACT_NAMES}, got {names}")
    payload = json.loads((path / "report.json").read_text(encoding="utf-8"))
    if payload["summary"]["counts"] != expected_counts:
        raise RuntimeError(f"report counts differ: {payload['summary']['counts']}")


def _reproduce_examples(temporary: Path) -> None:
    generated = temporary / "generated-examples"
    _run(
        "Regenerate examples",
        [sys.executable, "scripts/generate_examples.py", "--output", str(generated)],
    )
    for name in ("pattern.json", "clean.png", "defects.png"):
        _assert_same_example(ROOT / "examples" / name, generated / name)

    reports = temporary / "source-reports"
    command = [sys.executable, "-m", "patternproof", "analyze"]
    _run(
        "Source clean example",
        [
            *command,
            str(ROOT / "examples" / "pattern.json"),
            str(ROOT / "examples" / "clean.png"),
            "--out",
            str(reports / "clean"),
        ],
    )
    _run(
        "Source defect example",
        [
            *command,
            str(ROOT / "examples" / "pattern.json"),
            str(ROOT / "examples" / "defects.png"),
            "--out",
            str(reports / "defects"),
        ],
        expected=1,
    )
    _verify_report(reports / "clean", {"background": 22, "match": 42})
    _verify_report(
        reports / "defects",
        {"background": 22, "empty": 1, "match": 39, "uncertain": 1, "wrong": 1},
    )


def _write_examples_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for source in sorted(item for item in (ROOT / "examples").iterdir() if item.is_file()):
            info = zipfile.ZipInfo(f"patternproof-examples/{source.name}", (2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)


def _verify_packages(wheel: Path, source_distribution: Path, version: str) -> None:
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
    required_wheel = {
        "patternproof/__init__.py",
        "patternproof/analysis.py",
        "patternproof/cli.py",
        "patternproof/color.py",
        "patternproof/loader.py",
        "patternproof/model.py",
        "patternproof/reporting.py",
        f"patternproof-{version}.dist-info/METADATA",
        f"patternproof-{version}.dist-info/entry_points.txt",
    }
    if missing := required_wheel - wheel_names:
        raise RuntimeError(f"wheel is missing required files: {sorted(missing)}")
    if any(name.startswith(("tests/", "docs/", "examples/")) for name in wheel_names):
        raise RuntimeError("wheel contains repository-only files")

    prefix = f"patternproof-{version}/"
    with tarfile.open(source_distribution, "r:gz") as archive:
        source_names = set(archive.getnames())
    required_source = {
        f"{prefix}LICENSE",
        f"{prefix}README.md",
        f"{prefix}pyproject.toml",
        f"{prefix}src/patternproof/cli.py",
    }
    if missing := required_source - source_names:
        raise RuntimeError(f"source distribution is missing required files: {sorted(missing)}")

    unsafe_markers = ("/.env", ".pem", ".key", "/.git/", "/.venv/", "__pycache__")
    package_names = wheel_names | source_names
    if unsafe := sorted(
        name for name in package_names if any(mark in name for mark in unsafe_markers)
    ):
        raise RuntimeError(f"package contains unsafe path(s): {unsafe}")


def _build_assets(uv: str, temporary: Path, version: str) -> tuple[Path, ...]:
    built = temporary / "built"
    _run("Build wheel and source distribution", [uv, "build", "--out-dir", str(built)])
    wheel = built / f"patternproof-{version}-py3-none-any.whl"
    source_distribution = built / f"patternproof-{version}.tar.gz"
    if not wheel.is_file() or not source_distribution.is_file():
        raise RuntimeError("uv build did not produce the expected wheel and source distribution")
    _verify_packages(wheel, source_distribution, version)

    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    release_wheel = output / wheel.name
    release_source = output / source_distribution.name
    shutil.copyfile(wheel, release_wheel)
    shutil.copyfile(source_distribution, release_source)
    examples = output / f"patternproof-{version}-examples.zip"
    _write_examples_archive(examples)

    assets = (release_wheel, release_source, examples)
    checksums = output / "SHA256SUMS"
    checksums.write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets
        ),
        encoding="ascii",
        newline="\n",
    )
    return (*assets, checksums)


def _venv_path(venv: Path, windows_name: str, unix_name: str) -> Path:
    return venv / (f"Scripts/{windows_name}" if os.name == "nt" else f"bin/{unix_name}")


def _smoke_test_wheel(uv: str, temporary: Path, wheel: Path) -> None:
    venv = temporary / "wheel-venv"
    _run("Create clean wheel environment", [uv, "venv", str(venv), "--python", sys.executable])
    python = _venv_path(venv, "python.exe", "python")
    executable = _venv_path(venv, "patternproof.exe", "patternproof")
    _run("Install built wheel", [uv, "pip", "install", "--python", str(python), str(wheel)])
    _run("Check installed dependencies", [uv, "pip", "check", "--python", str(python)])

    smoke = temporary / "installed-smoke"
    smoke.mkdir()
    _run("Installed version", [str(executable), "--version"], cwd=smoke)
    _run(
        "Installed clean example",
        [
            str(executable),
            "analyze",
            str(ROOT / "examples" / "pattern.json"),
            str(ROOT / "examples" / "clean.png"),
            "--out",
            str(smoke / "clean"),
        ],
        cwd=smoke,
    )
    _run(
        "Installed defect example",
        [
            str(executable),
            "analyze",
            str(ROOT / "examples" / "pattern.json"),
            str(ROOT / "examples" / "defects.png"),
            "--out",
            str(smoke / "defects"),
        ],
        cwd=smoke,
        expected=1,
    )
    invalid = smoke / "invalid.json"
    invalid.write_text("[]\n", encoding="utf-8")
    _run(
        "Installed invalid input",
        [
            str(executable),
            "analyze",
            str(invalid),
            str(ROOT / "examples" / "clean.png"),
            "--out",
            str(smoke / "invalid-report"),
        ],
        cwd=smoke,
        expected=2,
    )
    if (smoke / "invalid-report").exists():
        raise RuntimeError("invalid installed run left an output directory")
    _verify_report(smoke / "clean", {"background": 22, "match": 42})
    _verify_report(
        smoke / "defects",
        {"background": 22, "empty": 1, "match": 39, "uncertain": 1, "wrong": 1},
    )


def _verify_tag(version: str) -> None:
    if os.environ.get("GITHUB_REF_TYPE") != "tag":
        return
    expected = f"v{version}"
    actual = os.environ.get("GITHUB_REF_NAME")
    if actual != expected:
        raise RuntimeError(f"release tag {actual!r} does not match package version {expected!r}")


def main() -> int:
    uv = _uv()
    version = _project_version()
    _verify_tag(version)
    _run("Lockfile", [uv, "lock", "--check"])
    python_paths = ["src", "tests", "scripts"]
    _run("Formatting", [sys.executable, "-m", "ruff", "format", "--check", *python_paths])
    _run("Lint", [sys.executable, "-m", "ruff", "check", *python_paths])
    _run("Types", [sys.executable, "-m", "mypy", "src", "tests", "scripts"])
    with tempfile.TemporaryDirectory(prefix=".patternproof-check-", dir=ROOT) as name:
        temporary = Path(name)
        _run(
            "Tests and branch coverage",
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(temporary / "pytest"),
                "--cov=patternproof",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
            ],
        )
        _run(
            "Dependency audit",
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--cache-dir",
                str(ROOT / ".pip-audit-cache"),
                "--progress-spinner",
                "off",
            ],
        )
        _reproduce_examples(temporary)
        assets = _build_assets(uv, temporary, version)
        _smoke_test_wheel(uv, temporary, assets[0])

    print("\nPATTERNPROOF_GATE=PASS")
    for asset in assets:
        print(asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
