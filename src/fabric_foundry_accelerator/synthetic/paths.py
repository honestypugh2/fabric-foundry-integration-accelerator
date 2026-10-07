"""Repository paths for synthetic data, semantic models and expected baselines."""

from pathlib import Path

DEFAULT_DATA_ROOT = Path("data/synthetic")


def raw_dir(data_root: Path, profile_id: str) -> Path:
    """Return the committed raw CSV directory for a profile."""
    return data_root / "raw" / profile_id


def semantic_model_path(data_root: Path, profile_id: str) -> Path:
    """Return the semantic model YAML path for a profile."""
    return data_root / "semantic" / profile_id / "semantic-model.yaml"


def expected_baseline_path(data_root: Path, profile_id: str) -> Path:
    """Return the committed expected-baseline JSON path for a profile."""
    return data_root / "expected" / f"{profile_id}.json"
