# Tests

Characterization (a.k.a. "golden master") tests for the repository's Python
scripts. Their goal is to **capture the current behaviour** of the scripts so
that future changes can be made with confidence that nothing regresses.

## Approach

The tests are **black-box**: each script is driven through its real
command-line interface with `subprocess`, and the assertions are made against
the artifacts it produces — the generated SMDB file, the mismatch / missing
reports, the resulting directory tree, stdout, and the exit code.

Nothing in the production scripts is imported or modified. This is deliberate:
the scripts keep state in module-level globals and run `argparse` at import
time, so importing their functions in isolation would be unreliable, and
refactoring them to be importable would risk changing the very behaviour these
tests are meant to lock down.

Test fixtures build small ROM-like folder trees in pytest's `tmp_path`, and
expected SMDB lines are computed from the fixture content (see the helpers in
`conftest.py`), so the tests are self-contained and never touch real ROMs.

## What is covered

| Script           | File                   | Highlights                                                              |
|------------------|------------------------|-------------------------------------------------------------------------|
| `parse_pack.py`  | `test_parse_pack.py`   | SMDB contents/format, case-insensitive walk order, banned folders/suffixes |
| `verify_pack.py` | `test_verify_pack.py`  | correct / extra / missing / misplaced counts, mismatch report sections  |
| `build_pack.py`  | `test_build_pack.py`   | copy & hardlink strategies, zip extraction, missing report, skip-existing |
| `base_sorter.py` | `test_base_sorter.py`  | region/type sorting layout, disc grouping, file-type filter             |

## Running

```sh
python -m pip install -r requirements-dev.txt   # installs pytest
pytest                                           # from the repository root
```

The scripts themselves depend only on the Python standard library; `pytest`
is the sole development dependency.
