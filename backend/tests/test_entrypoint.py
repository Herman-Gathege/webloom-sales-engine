import os
import stat
import subprocess
from pathlib import Path

ENTRYPOINT = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _run_entrypoint(tmp_path: Path, *, seed: str | None) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_marker = tmp_path / "python-ran"
    _write_executable(bin_dir / "alembic", "exit 0")
    _write_executable(bin_dir / "python", f'touch "{python_marker}"')

    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
    }
    env.pop("SEED_SAMPLE_DATA", None)
    if seed is not None:
        env["SEED_SAMPLE_DATA"] = seed

    subprocess.run(
        ["sh", str(ENTRYPOINT), "/bin/true"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert python_marker.exists() is (seed == "true")


def test_entrypoint_does_not_seed_samples_by_default(tmp_path: Path) -> None:
    _run_entrypoint(tmp_path, seed=None)


def test_entrypoint_seeds_samples_only_when_explicitly_enabled(tmp_path: Path) -> None:
    _run_entrypoint(tmp_path, seed="true")
