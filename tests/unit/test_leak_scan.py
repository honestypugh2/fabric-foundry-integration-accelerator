import subprocess
from pathlib import Path

import pytest
import yaml

from fabric_foundry_accelerator.privacy.leak_scan import (
    ALLOW_MARKER,
    Denylist,
    DenylistFile,
    FindingKind,
    add_terms_to_file,
    hash_term,
    list_repository_files,
    normalize_ngrams,
    normalize_term,
    scan_paths,
    scan_text,
)

SALT = "unit-test-salt-0123456789"
# Built at runtime so the repository leak scan does not flag this test file.
SAMPLE_GUID = "-".join(["1b4e28ba", "2fa1", "11d2", "883f", "0016d3cca427"])


def _kinds(text: str, denylist: Denylist | None = None) -> list[FindingKind]:
    return [f.kind for f in scan_text(text, path="x.md", denylist=denylist)]


def test_normalize_term_handles_case_separators_and_punctuation() -> None:
    assert normalize_term("  Contoso_River-Health! ") == "contoso river health"


def test_normalize_ngrams_produces_one_to_three_token_grams() -> None:
    grams = normalize_ngrams("Alpha beta GAMMA delta")
    assert {"alpha", "alpha beta", "alpha beta gamma", "delta"} <= grams
    assert "alpha beta gamma delta" not in grams


def test_hash_term_is_salted_and_normalized() -> None:
    assert hash_term("Contoso River", SALT) == hash_term("contoso_river", SALT)
    assert hash_term("contoso river", SALT) != hash_term("contoso river", SALT + "x")


@pytest.mark.parametrize(
    "line",
    ["Welcome to Contoso River lab", "the CONTOSO_RIVER model", "contosoriver demo"],
)
def test_denylist_matches_variants(line: str) -> None:
    denylist = Denylist(SALT, terms=["contoso river", "contosoriver"])
    assert _kinds(line, denylist) == [FindingKind.DENYLIST]


def test_denylist_does_not_flag_neutral_text_and_empty_denylist_is_inert() -> None:
    assert _kinds("regional healthcare provider", Denylist(SALT, terms=["contoso river"])) == []
    assert not Denylist(SALT).matches("anything at all")


def test_finding_detail_never_contains_matched_value() -> None:
    denylist = Denylist(SALT, terms=["contoso river"])
    [finding] = scan_text("Contoso River", path="a.md", denylist=denylist)
    assert "contoso" not in finding.render().lower()


def test_guid_detection_allows_nil_guid() -> None:
    assert _kinds(f"workspace {SAMPLE_GUID}") == [FindingKind.GUID]
    assert _kinds("synthetic 00000000-0000-0000-0000-00000000a001") == []
    not_synthetic = "00000000-0000-0000-" + "0001-00000000a001"  # built so this file stays clean
    assert _kinds(f"not synthetic {not_synthetic}") == [FindingKind.GUID]
    assert _kinds("placeholder 00000000-0000-0000-0000-000000000000") == []


@pytest.mark.parametrize(
    "secret",
    [
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "gh" + "p_" + "a" * 36,
        "AccountKey=" + "A" * 30,
        "sk-" + "ant-" + "b" * 24,
        'password = "' + "c" * 16 + '"',
        "eyJ" + "d" * 12 + ".eyJ" + "e" * 12 + "." + "f" * 12,
    ],
)
def test_secret_patterns_detected(secret: str) -> None:
    assert FindingKind.SECRET in _kinds(secret)


def test_email_detection_allows_reserved_domains() -> None:
    assert _kinds("contact someone@" + "corp.test") == [FindingKind.EMAIL]
    assert _kinds("contact someone@example.com") == []


def test_allow_marker_suppresses_line() -> None:
    line = f"{SAMPLE_GUID}  # {ALLOW_MARKER} documented sample"
    assert _kinds(line) == []


def _write_denylist(path: Path, hashes: list[str] | None = None) -> None:
    path.write_text(
        yaml.safe_dump({"version": 1, "salt": SALT, "hashes": hashes or []}), encoding="utf-8"
    )


def test_add_terms_writes_only_hashes_and_is_idempotent(tmp_path: Path) -> None:
    denylist_file = tmp_path / "denylist.yaml"
    _write_denylist(denylist_file)
    assert add_terms_to_file(denylist_file, ["Contoso River", "", "contoso_river"]) == 1
    assert add_terms_to_file(denylist_file, ["contoso river"]) == 0
    content = denylist_file.read_text(encoding="utf-8")
    assert "contoso" not in content.lower()
    assert hash_term("contoso river", SALT) in content


def test_add_terms_rejects_long_terms(tmp_path: Path) -> None:
    denylist_file = tmp_path / "denylist.yaml"
    _write_denylist(denylist_file)
    with pytest.raises(ValueError, match="at most 3 tokens"):
        add_terms_to_file(denylist_file, ["one two three four"])


def test_denylist_load_merges_local_file_and_environment(tmp_path: Path) -> None:
    denylist_file = tmp_path / "denylist.yaml"
    _write_denylist(denylist_file, [hash_term("alpha", SALT)])
    local = tmp_path / "local.txt"
    local.write_text("# comment\nbravo\n", encoding="utf-8")
    loaded = Denylist.load(
        denylist_file, local_terms_path=local, environ={"FFIA_LEAK_DENYLIST": "charlie\n"}
    )
    assert len(loaded) == 3
    assert loaded.salt == SALT
    assert all(loaded.matches(t) for t in ("alpha", "bravo", "charlie"))


def test_denylist_file_rejects_malformed_hashes() -> None:
    with pytest.raises(ValueError, match="malformed"):
        DenylistFile(salt=SALT, hashes=["not-a-hash"]).validated_hashes()


def test_scan_paths_skips_binary_excluded_and_large_files(tmp_path: Path) -> None:
    text_file = tmp_path / "a.txt"
    text_file.write_text(f"{SAMPLE_GUID}\n", encoding="utf-8")
    binary_file = tmp_path / "b.bin"
    binary_file.write_bytes(b"\0" + SAMPLE_GUID.encode())
    excluded = tmp_path / "c.txt"
    excluded.write_text(f"{SAMPLE_GUID}\n", encoding="utf-8")
    large = tmp_path / "d.txt"
    large.write_text("x" * 2_000_001, encoding="utf-8")
    findings = scan_paths(
        [text_file, binary_file, excluded, large, tmp_path / "missing.txt"],
        root=tmp_path,
        exclude=[excluded],
    )
    assert [(f.path, f.kind) for f in findings] == [("a.txt", FindingKind.GUID)]


def test_scan_paths_outside_root_uses_given_path(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    target = other / "e.txt"
    target.write_text(f"{SAMPLE_GUID}\n", encoding="utf-8")
    [finding] = scan_paths([target], root=tmp_path / "root")
    assert finding.path == target.as_posix()


def test_list_repository_files_without_git_walks_and_skips_dirs(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("k", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "skip.txt").write_text("s", encoding="utf-8")
    assert [p.name for p in list_repository_files(tmp_path)] == ["keep.txt"]


def test_list_repository_files_with_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    (tmp_path / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (tmp_path / "tracked.txt").write_text("t", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("i", encoding="utf-8")
    names = sorted(p.name for p in list_repository_files(tmp_path))
    assert names == [".gitignore", "tracked.txt"]
