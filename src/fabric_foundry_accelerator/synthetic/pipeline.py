"""End-to-end local data pipeline: generate -> build -> validate against the expected baseline."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from fabric_foundry_accelerator.models.checks import CheckResult, failed
from fabric_foundry_accelerator.models.semantic import load_semantic_model
from fabric_foundry_accelerator.synthetic.baseline import (
    Baseline,
    compare_baselines,
    compute_baseline,
    load_baseline,
    quirk_checks,
    reconciliation_checks,
    write_baseline,
)
from fabric_foundry_accelerator.synthetic.generator import (
    RawManifest,
    check_raw,
    generate,
    load_manifest,
    write_raw,
)
from fabric_foundry_accelerator.synthetic.medallion import BuildResult, build_profile
from fabric_foundry_accelerator.synthetic.paths import (
    expected_baseline_path,
    raw_dir,
    semantic_model_path,
)
from fabric_foundry_accelerator.synthetic.profiles import DatasetProfile


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Outcome of building and validating one profile."""

    profile: str
    build: BuildResult
    baseline: Baseline
    checks: tuple[CheckResult, ...]
    baseline_differences: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return True when every check passed and the baseline matched."""
        return not failed(self.checks) and not self.baseline_differences


def generate_profile(profile: DatasetProfile, data_root: Path) -> RawManifest:
    """Generate raw CSVs and the manifest for a profile."""
    return write_raw(generate(profile), raw_dir(data_root, profile.id))


def check_profile(profile: DatasetProfile, data_root: Path) -> list[str]:
    """Return differences between committed raw files and a fresh generation."""
    return check_raw(generate(profile), raw_dir(data_root, profile.id))


def build_and_validate(
    profile: DatasetProfile,
    *,
    data_root: Path,
    output_root: Path | None = None,
    update_baseline: bool = False,
) -> ValidationReport:
    """Build Bronze/Silver/Gold from committed raw CSVs and validate against the baseline.

    Args:
        profile: Dataset profile to build.
        data_root: Root containing ``raw/``, ``semantic/`` and ``expected/``.
        output_root: Where layer Parquet files are written (defaults to ``data_root``).
        update_baseline: Write the computed baseline instead of comparing against it.
    """
    out = output_root or data_root
    model = load_semantic_model(semantic_model_path(data_root, profile.id))
    source = raw_dir(data_root, profile.id)
    build = build_profile(profile, raw_dir=source, output_root=out, semantic_model=model)
    manifest = load_manifest(source)
    baseline = compute_baseline(out, profile, manifest, model)
    checks = (
        *build.checks,
        *quirk_checks(manifest, baseline.diagnostics),
        *reconciliation_checks(baseline),
    )
    expected_path = expected_baseline_path(data_root, profile.id)
    if update_baseline:
        write_baseline(baseline, expected_path)
        differences: list[str] = []
    elif expected_path.is_file():
        differences = compare_baselines(load_baseline(expected_path), baseline)
    else:
        differences = [f"missing expected baseline {expected_path}; run with --update-baseline"]
    return ValidationReport(profile.id, build, baseline, checks, tuple(differences))


def export_raw(profile: DatasetProfile, data_root: Path, destination: Path) -> list[Path]:
    """Copy a profile's raw CSVs to ``destination`` and write ``SHA256SUMS`` for verification."""
    manifest = load_manifest(raw_dir(data_root, profile.id))
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    lines: list[str] = []
    for entry in manifest.files:
        target = destination / entry.name
        shutil.copyfile(raw_dir(data_root, profile.id) / entry.name, target)
        copied.append(target)
        lines.append(f"{entry.sha256}  {entry.name}")
    (destination / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return copied
