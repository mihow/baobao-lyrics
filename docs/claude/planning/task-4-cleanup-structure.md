# Task 4: Clean Up Project Structure

**Status**: Ready to implement
**Complexity**: Low
**Dependencies**: None (can do independently)

## Objective

Organize project structure by moving test files from root directory into the proper `tests/` directory and ensuring all functionality is properly separated into modules and CLI.

## Current State Issues

### Test Files in Root Directory

**Legacy test files** (should be in `tests/`):
```
/home/michael/Projects/Leon/baobao/
├── test_transcription.py           (24,430 bytes - LARGEST)
├── test_e2e_transcription.py       (9,510 bytes)
├── test_english_transcription.py   (6,008 bytes)
```

**Properly organized tests** (already in `tests/`):
```
/home/michael/Projects/Leon/baobao/tests/
├── test_transcribe.py              (179 lines)
├── test_enhance.py                 (201 lines)
├── test_e2e.py                     (350 lines)
├── conftest.py                     (127 lines)
```

**Issue**: pytest.ini is configured to only run tests from `tests/` directory (`testpaths = tests`), so root-level test files are ignored by default pytest runs. This suggests they may be obsolete or superseded.

## Implementation Plan

### 1. Analyze Root-Level Test Files

**Before deleting**, verify if they contain unique test cases not covered by organized tests:

```bash
# Compare test coverage
wc -l test_*.py tests/test_*.py

# Check for unique functionality
grep -h "def test_" test_*.py | sort | uniq
grep -h "def test_" tests/test_*.py | sort | uniq
```

**Files to analyze**:
- `/home/michael/Projects/Leon/baobao/test_transcription.py` (24 KB - check for unique tests)
- `/home/michael/Projects/Leon/baobao/test_e2e_transcription.py` (9.5 KB)
- `/home/michael/Projects/Leon/baobao/test_english_transcription.py` (6 KB)

**Questions**:
1. Do root tests have functionality not in `tests/` tests?
2. Are they older versions that were refactored?
3. Are they working scripts vs proper test suites?

### 2. Decision Tree

**If root tests are superseded**:
- Move to `/home/michael/Projects/Leon/baobao/archive/` or delete
- Update CLAUDE.md to note removal

**If root tests have unique coverage**:
- Extract unique test cases
- Merge into proper test files in `tests/`
- Delete originals

**If root tests are working scripts** (not proper tests):
- Move to `/home/michael/Projects/Leon/baobao/scripts/` or `examples/`
- Rename without `test_` prefix to avoid confusion

### 3. Ensure All Functionality in Modules

**Review module organization**:

Current structure (good):
```
baobao/
├── __init__.py          # Package exports
├── cli.py               # CLI only (Typer commands)
├── transcribe.py        # Transcription logic
└── enhance.py           # Enhancement logic
```

**Verify**:
- [ ] No business logic in `cli.py` - only CLI argument handling
- [ ] All transcription logic in `transcribe.py`
- [ ] All enhancement logic in `enhance.py`
- [ ] Proper imports in `__init__.py`

**Check for hidden functionality**:
```bash
# Look for any Python files outside baobao/
find . -name "*.py" -not -path "./baobao/*" -not -path "./tests/*" -not -path "./.venv/*"
```

### 4. Directory Structure After Cleanup

**Proposed final structure**:
```
/home/michael/Projects/Leon/baobao/
├── baobao/                    # Main package
│   ├── __init__.py
│   ├── cli.py
│   ├── transcribe.py
│   ├── enhance.py
│   └── ttml.py            # New (from task 3)
├── tests/                     # All tests here
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_transcribe.py
│   ├── test_enhance.py
│   ├── test_ttml.py       # New (from task 3)
│   └── test_e2e.py
├── docs/
│   ├── claude/
│   │   ├── planning/
│   │   └── (future: sessions/, archive/)
│   └── reference/
├── songs/                     # Sample audio files
├── scripts/                   # Optional: utility scripts
│   └── (moved from root if any)
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── pytest.ini
└── uv.lock
```

**Remove from root**:
- `test_transcription.py`
- `test_e2e_transcription.py`
- `test_english_transcription.py`
- `test_output/` (if just test artifacts, not needed in repo)

**Keep in root** (standard project files):
- `CLAUDE.md`
- `CLAUDE.template.md` (optional - could move to `docs/`)
- `README.md`
- `pyproject.toml`
- `pytest.ini`
- `uv.lock`

### 5. Update Configuration Files

**pytest.ini** (already correct):
```ini
[pytest]
testpaths = tests
```

**pyproject.toml** - verify test paths if specified.

**.gitignore** - ensure test artifacts ignored:
```
test_output/
__pycache__/
*.pyc
.pytest_cache/
```

## Critical Files

**To analyze**:
- `/home/michael/Projects/Leon/baobao/test_transcription.py`
- `/home/michael/Projects/Leon/baobao/test_e2e_transcription.py`
- `/home/michael/Projects/Leon/baobao/test_english_transcription.py`

**To verify**:
- `/home/michael/Projects/Leon/baobao/baobao/cli.py` (no business logic)
- `/home/michael/Projects/Leon/baobao/.gitignore` (proper exclusions)

## Testing Requirements

After cleanup:
- [ ] All pytest tests still pass: `pytest`
- [ ] Coverage unchanged or improved: `pytest --cov`
- [ ] No functionality lost
- [ ] CLI commands work identically
- [ ] Import paths unchanged (no broken imports)

## Step-by-Step Execution

### Step 1: Read and Compare Test Files
```bash
# Quick comparison
head -50 test_transcription.py
head -50 tests/test_transcribe.py

# Check for unique test functions
diff <(grep "def test_" test_transcription.py | sort) \
     <(grep "def test_" tests/test_transcribe.py | sort)
```

### Step 2: Run Tests Before Changes
```bash
pytest --cov  # Baseline coverage
```

### Step 3: Create Archive or Merge

**If archiving**:
```bash
mkdir -p archive/old_tests
git mv test_*.py archive/old_tests/
```

**If merging**:
- Extract unique test cases manually
- Add to appropriate test file in `tests/`
- Delete originals

### Step 4: Clean Test Artifacts
```bash
# Remove test output directory if not needed
rm -rf test_output/  # Or add to .gitignore
```

### Step 5: Verify Structure
```bash
tree -L 2 -I '.venv|__pycache__|.pytest_cache'
```

### Step 6: Run Tests After Changes
```bash
pytest --cov  # Verify nothing broken
```

### Step 7: Commit
```bash
git add -A
git commit -m "Clean up project structure: move test files to tests/ directory"
```

## Questions Needing Validation

1. **What do root test files contain?**
   - Are they working scripts or proper tests?
   - Do they have unique coverage?
   - **Need to read** these files before deciding

2. **Should test_output/ be in repo?**
   - Looks like test artifacts
   - Should be in .gitignore?
   - Or is it sample output for documentation?

3. **Where to put CLAUDE.template.md?**
   - Keep in root?
   - Move to `docs/` or `docs/claude/`?
   - Or delete after using it to update CLAUDE.md?

4. **Create scripts/ directory?**
   - If root test files are working scripts, move here
   - Or integrate into CLI as commands?

## Recommendations

**Preferred approach**:
1. Read root test files to understand purpose
2. Extract any unique test cases → merge into `tests/`
3. Archive or delete root test files
4. Remove `test_output/` or add to .gitignore
5. Move `CLAUDE.template.md` to `docs/claude/` (reference)
6. Verify all tests pass
7. Commit with descriptive message

**Benefits**:
- Cleaner root directory
- All tests in one place
- Easier to run full test suite
- Better organization for new contributors

## Risks

**Risk**: Deleting files with unique functionality
- **Mitigation**: Read files carefully, extract unique tests first

**Risk**: Breaking imports if files import each other
- **Mitigation**: Check for cross-imports before moving

**Risk**: Losing historical context
- **Mitigation**: Archive rather than delete, or note in CLAUDE.md

## Success Criteria

- [ ] Root directory clean (only standard project files)
- [ ] All tests in `tests/` directory
- [ ] All tests pass with same or better coverage
- [ ] No business logic in CLI file
- [ ] Clear module separation maintained
- [ ] Documentation updated to reflect structure
