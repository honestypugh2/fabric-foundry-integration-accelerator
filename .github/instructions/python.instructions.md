---
applyTo: "src/**/*.py,tests/**/*.py"
---

# Python instructions

- Target Python 3.14. Use full type annotations. Code must pass `pyright` (strict) and
  `ruff check` / `ruff format`.
- Use Google-style docstrings for public APIs. Comments explain *why*, not *what*.
- Use Pydantic models at external boundaries, `pathlib.Path` for paths, and UTC-aware
  `datetime`.
- Inject dependencies. No global cloud clients and no import-time side effects.
- Raise explicit exceptions. `except Exception` is allowed only at controlled translation
  boundaries, and only with a reason.
- Tests:
  - Use `pytest` with `tmp_path` and `monkeypatch`. No network in unit tests.
  - Build secret-like or GUID-like fixtures at runtime so the repository leak scan stays clean.
  - Mark live tests `@pytest.mark.live`; they must be opt-in.
- Never log tokens, secrets, PHI, PII or customer identifiers.
