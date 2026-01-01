# Task 2: Simplify Default Behavior - Transcription Only

**Status**: Needs validation
**Complexity**: Medium
**Dependencies**: None

## Objective

Make the default behavior of Baobao much simpler: just transcribe songs and create accurate time-synced lyric files, without automatic enhancement (pinyin/translation).

## Problem Statement

**Current default behavior is confusing**:
- `baobao transcribe audio.mp3` → Chinese-only SRT (no pinyin/translation)
- `baobao process audio.mp3` → Full enhanced SRT with pinyin/translation (requires Ollama)
- Two commands for similar tasks creates confusion
- Enhancement should be optional/explicit, not automatic in `process`

## Desired Behavior

**New simplified workflow**:
```bash
# Default: just transcribe → time-synced lyrics
baobao audio.mp3                    # Simple, clear
# OR
baobao transcribe audio.mp3         # Explicit command

# Optional: add enhancement
baobao enhance lyrics.srt           # Explicitly opt-in
```

**Output**: Accurate time-synced lyric file (SRT or TTML) with Chinese text only.

## Implementation Changes

### 1. Make `transcribe` the Default Command

**File**: `/home/michael/Projects/Leon/baobao/baobao/cli.py`

**Option A**: Add default command handler (preferred)
```python
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, audio: str = typer.Argument(None)):
    """If no subcommand, assume transcribe."""
    if ctx.invoked_subcommand is None and audio:
        ctx.invoke(transcribe, audio=audio)
```

**Option B**: Make `transcribe` the default with `@app.command(default=True)`

**Changes required**:
- Modify CLI structure in `cli.py` (lines 50-72)
- Ensure backward compatibility with explicit `transcribe` command
- Update help text to reflect simpler workflow

### 2. Remove or Deprecate `process` Command

**Current `process` command** (lines 239-336):
- Combines transcribe + enhance
- Makes enhancement feel like default behavior
- Requires Ollama even if user just wants transcription

**Recommendation**: **Deprecate** `process` command entirely
- Users can chain commands: `baobao transcribe audio.mp3 && baobao enhance lyrics.srt`
- Or use shell scripts for batch workflows
- Reduces CLI surface area and confusion

**Alternative**: Keep `process` but rename to `process-with-enhancement` or similar to make it explicit

### 3. Update `batch` Command Defaults

**Current behavior** (lines 338-420):
- `--skip-enhance` flag (line 365) suggests enhancement is default
- Should flip to `--enhance` flag (opt-in)

**Changes**:
```python
# OLD
skip_enhance: bool = typer.Option(False, "--skip-enhance", "-s")

# NEW
enhance: bool = typer.Option(False, "--enhance", "-e")
```

Update logic at lines 395-406 to check `enhance` flag instead of `skip_enhance`.

### 4. Simplify Help Text and Examples

**Update**:
- README.md examples
- CLI help strings
- Error messages

**Emphasize**:
- Baobao transcribes songs by default
- Enhancement is optional (requires Ollama)
- Simple one-command workflow

## Critical Files to Modify

- `/home/michael/Projects/Leon/baobao/baobao/cli.py`:
  - `main()` function (lines 50-72) - add default command
  - `process()` command (lines 239-336) - deprecate or rename
  - `batch()` command (lines 338-420) - flip enhance flag
- `/home/michael/Projects/Leon/baobao/README.md` - update examples
- `/home/michael/Projects/Leon/baobao/tests/test_e2e.py` - update test expectations

## Questions Needing Validation

1. **Keep or remove `process` command?**
   - Remove entirely? (simpler)
   - Rename to be more explicit? (backward compatible)
   - Mark as deprecated? (gradual transition)

2. **Default command invocation syntax?**
   - `baobao audio.mp3` (cleanest)
   - `baobao transcribe audio.mp3` (more explicit)
   - Support both?

3. **Default output format after task 3?**
   - Should default be SRT or TTML?
   - Should we maintain SRT output for compatibility?

4. **Should `batch` keep enhancement option at all?**
   - Maybe remove entirely, force users to use two passes
   - Or keep as opt-in convenience

## Testing Requirements

- [ ] `baobao audio.mp3` works without subcommand
- [ ] `baobao transcribe audio.mp3` still works (backward compat)
- [ ] Help text reflects new simple workflow
- [ ] Batch command uses opt-in enhancement flag
- [ ] No Ollama errors when running default transcription
- [ ] Update E2E tests to match new behavior

## Risks

- **Breaking change** for existing users who rely on `process` command
- Need migration guide if removing `process`
- Batch workflows might need updating

## Recommendation

**Preferred approach**:
1. Add default command handler → `baobao audio.mp3` works
2. Deprecate `process` with warning message for 1-2 versions, then remove
3. Flip `batch` to use `--enhance` opt-in flag
4. Update all documentation and tests
5. Add migration guide in CHANGELOG

This creates the simplest, most intuitive workflow while maintaining compatibility.
