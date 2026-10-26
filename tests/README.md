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

Archives are built on the fly the same way — `zipfile` and `py7zr` can both
write archives, so the zip and 7z tests create theirs in-test and read the
entry CRCs straight back out of them. RAR is different, because no FOSS tool can
*create* a RAR archive (only extract from one); RARLAB's licence forbids
building a RAR compressor from their `unrar` source.
`tests/fixtures/rar-rom.rar` is therefore a real, pre-built archive checked into
the repo, with a single compressed entry, `rar-rom.bin`, containing the text
`rar-rom-contents` repeated 256 times. Tests still read its CRC back via
`rarfile`, so it behaves like the generated fixtures.

## What is covered

| Script           | File                   | Highlights                                                              |
|------------------|------------------------|-------------------------------------------------------------------------|
| `parse_pack.py`  | `test_parse_pack.py`   | SMDB contents/format, case-insensitive walk order, banned folders/suffixes |
| `verify_pack.py` | `test_verify_pack.py`  | correct / extra / missing / misplaced counts, mismatch report sections  |
| `build_pack.py`  | `test_build_pack.py`   | copy & hardlink strategies, zip/7z/rar extraction, corrupt-archive handling, missing report, skip-existing, graceful behavior w/out optional dependencies |
| `base_sorter.py` | `test_base_sorter.py`  | region/type sorting layout, disc grouping, file-type filter             |

## Running

```sh
python -m pip install -r requirements-dev.txt   # installs pytest
pytest                                           # from the repository root
```

The `build_pack.py` script optionally uses the `py7zr` and `rarfile` packages
for 7z and rar support; without them, those files are not recognized as
archives. The other scripts depend only on the Python standard library.
`requirements-dev.txt` installs both anyway so the full test suite runs by
default. `pytest` and `coverage` are the only required development
dependencies.

The rar extraction tests additionally need a rar utility on `PATH`, since
rarfile shells out to one. In Debian and Ubuntu that is `apt install
unrar-free`, which also installs an `unrar` alias that rarfile finds
automatically.

## Measuring coverage

Because the tests run each script as a **subprocess**, a plain `pytest --cov`
would only measure the test process and report almost no coverage of the
scripts. Instead we measure the child processes with `coverage.py` in
parallel mode: when `COVERAGE_PROCESS_START` is set, `conftest.py` launches
each script under `coverage run`, and the per-process data files are merged
afterwards.

```sh
export COVERAGE_FILE="$PWD/.coverage"        # absolute: tests run in temp dirs
export COVERAGE_PROCESS_START="$PWD/.coveragerc"

coverage erase
pytest                                       # children record coverage
coverage combine                             # merge the per-process data
coverage report                              # text summary (or: coverage html)
```

`COVERAGE_FILE` must be an absolute path: each test runs the script from a
temporary working directory, and without it the data files would be written
into (and lost with) those temp dirs.

### Current coverage

Roughly **95%** of statements (branch coverage enabled); the shared `htgdb`
package modules are at 100%. The lines that remain uncovered are deliberately
out of scope:

- **Windows long-path fallbacks** — the `\\?\`-prefixed `FileNotFoundError` /
  `OSError` retry paths in every script. They cannot run on Linux/macOS.
- **`if __name__ == '__main__'` guard branches** — only taken when a module is
  *imported* rather than executed, which the subprocess tests never do.
- **Unreachable defensive code** — e.g. build_pack's `raise` for an unknown
  `--file_strategy` (argparse already restricts the choices), and
  `RarArchive.handle_error`, which only a wholly unreadable file could reach:
  rarfile reports a damaged archive as one that ends early rather than
  raising.
- **`RarArchive`'s skip for directories and CRC-less entries** — the checked-in
  rar fixture holds a single ordinary entry with a CRC, and a RAR5 entry
  lacking one cannot be produced by any available tool.
- **`BaseArchive` abstract-method stubs** — `looks_like`, `_read_entries`,
  and `extract_entry` all just `raise NotImplementedError`. `BaseArchive`
  is never instantiated directly, so these methods never run by
  design; subclasses always override them.
- **parse_pack's non-ASCII filename handler** — reachable, but it calls
  `time.sleep(10)`, so exercising it would add a 10-second hang to the suite.
