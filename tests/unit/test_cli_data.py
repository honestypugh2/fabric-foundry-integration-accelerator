import hashlib
from pathlib import Path

import pytest

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.synthetic.paths import raw_dir


def test_data_generate_check_passes_for_committed_files(
    data_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["data", "generate", "--check", "--data-root", str(data_root)]) == 0
    assert "hc-lab-7file-v1: matches generator" in capsys.readouterr().out


def test_data_generate_writes_and_check_detects_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "data"
    assert main(["data", "generate", "--profile", "hc-lab-7file-v1", "--data-root", str(root)]) == 0
    assert "patients.csv 200" in capsys.readouterr().out
    (raw_dir(root, "hc-lab-7file-v1") / "claims.csv").write_text("x\n", encoding="utf-8")
    assert (
        main(
            [
                "data",
                "generate",
                "--check",
                "--profile",
                "hc-lab-7file-v1",
                "--data-root",
                str(root),
            ]
        )
        == 1
    )
    assert "claims.csv differs" in capsys.readouterr().err


def test_data_build_reports_local_label(
    tmp_path: Path, data_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["data", "build", "--profile", "hc-lab-7file-v1", "--data-root", str(data_root)]
    assert main([*args, "--output-root", str(tmp_path), "--verbose"]) == 0
    out = capsys.readouterr().out
    assert "24 tables (bronze 7, silver 7, gold 10)" in out
    assert "baseline matched [LOCAL, no cloud operation]" in out
    assert "PASS" in out


def test_data_build_update_baseline_and_failure_paths(
    tmp_path: Path, data_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "data"
    for sub in ("raw/hc-lab-7file-v1", "semantic/hc-lab-7file-v1"):
        (root / sub).mkdir(parents=True)
        for source in (data_root / sub).iterdir():
            (root / sub / source.name).write_bytes(source.read_bytes())
    args = ["data", "build", "--profile", "hc-lab-7file-v1", "--data-root", str(root)]
    assert main(args) == 1  # no expected baseline yet
    assert "missing expected baseline" in capsys.readouterr().err
    assert main([*args, "--update-baseline"]) == 0
    assert "baseline written" in capsys.readouterr().out
    assert main(args) == 0
    patients = raw_dir(root, "hc-lab-7file-v1") / "patients.csv"
    patients.write_text(
        "\n".join(patients.read_text(encoding="utf-8").splitlines()[:-1]) + "\n", encoding="utf-8"
    )
    assert main(args) == 1
    assert "BUILD FAILED" in capsys.readouterr().err


def test_data_export_writes_verifiable_checksums(tmp_path: Path, data_root: Path) -> None:
    dest = tmp_path / "lab" / "data" / "raw"
    assert (
        main(
            [
                "data",
                "export",
                "--profile",
                "hc-lab-7file-v1",
                "--dest",
                str(dest),
                "--data-root",
                str(data_root),
            ]
        )
        == 0
    )
    sums = (dest / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert len(sums) == 7
    for line in sums:
        digest, name = line.split("  ")
        assert hashlib.sha256((dest / name).read_bytes()).hexdigest() == digest


def test_recovery_run_text_and_json(
    tmp_path: Path, data_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = [
        "recovery",
        "run",
        "--data-root",
        str(data_root),
        "--scenario",
        str(data_root / "recovery" / "scenario.yaml"),
    ]
    assert main([*base, "--work-dir", str(tmp_path / "a")]) == 0
    out = capsys.readouterr().out
    assert "[SIMULATED; cloud operation performed: NO]" in out
    assert "Recovered from weekly snapshot: YES" in out
    assert "Recoverable without the weekly snapshot: NO" in out
    assert main([*base, "--work-dir", str(tmp_path / "b"), "--json"]) == 0
    assert '"execution_label": "SIMULATED"' in capsys.readouterr().out
