# Next Session: Implement Timing Validation System

**Date**: 2025-12-31
**Context**: 51% token usage (113K/200K)
**Repository**: https://github.com/mihow/baobao-lyrics

## Current State

### Completed Tasks
- ✅ Task 4: Project structure cleanup (scripts/, archive/)
- ✅ Task 2: Simplified CLI (removed `process` command)
- ✅ Added `baobao play` command for validation
- ✅ Tested TTML with mpv → **NOT SUPPORTED**
- ✅ Created comprehensive timing validation plan

### Active Issues

**Problem**: Subtitle display has issues
- ✅ Chinese lyrics display correctly
- ✅ Word timing mostly works
- ❌ Extra lyrics shown simultaneously
- ❌ Phrases appear/disappear strangely

**Root Cause**: Likely overlapping SRT entries or karaoke mode implementation

## Immediate Goal

Implement **Phase 1** of the timing validation system to diagnose and fix subtitle display issues.

See full plan: `docs/claude/planning/task-validation-system.md`

## Tasks for Next Session

### Phase 1: Build Test Infrastructure

**Task 1: Create Synthetic Test Audio Generator**

File: `scripts/generate_test_audio.py`

Requirements:
- Use edge-tts to generate clear English test audio
- Create simple counting words: "one", "two", "three", "four", "five"
- Add 500ms pauses between words using SSML `<break>` tags
- Capture TTS word boundary events for exact timing metadata
- Save outputs:
  - `test_output/timing_test.mp3` - Audio file
  - `test_output/timing_test.ground_truth.json` - Exact word timings from TTS
  - `test_output/timing_test.reference.srt` - Expected correct SRT output

Reference implementation: `scripts/test_english_transcription.py` (already uses edge-tts)

**Task 2: Create Timing Validation Script**

File: `scripts/validate_timing.py`

Requirements:
- Parse ground truth JSON (TTS word timings)
- Parse Whisper-generated SRT file
- Match words between ground truth and transcription
- Calculate timing error metrics:
  - Mean error (ms)
  - Max error (ms)
  - Standard deviation
  - Word accuracy (missed/extra words)
- Output validation report with per-word errors

**Task 3: Run Baseline Validation**

Commands:
```bash
# 1. Generate test audio with known timings
python scripts/generate_test_audio.py

# 2. Transcribe with baobao
uv run baobao transcribe test_output/timing_test.mp3

# 3. Validate timing accuracy
python scripts/validate_timing.py \
    test_output/timing_test.ground_truth.json \
    test_output/timing_test.srt

# 4. Test karaoke mode
uv run baobao transcribe test_output/timing_test.mp3 --karaoke
python scripts/validate_timing.py \
    test_output/timing_test.ground_truth.json \
    test_output/timing_test.karaoke.srt
```

**Expected Output**:
- Validation report showing timing errors
- Identification of any overlapping entries
- Karaoke mode issues quantified

### Phase 2: Fix Issues (After Phase 1 Complete)

Based on Phase 1 findings, fix issues in:
- `baobao/transcribe.py:120-146` - `save_srt()` method
- `baobao/transcribe.py:155-185` - Karaoke word highlighting

Potential fixes:
- Ensure non-overlapping SRT entries
- Fix karaoke mode to show one word at a time
- Adjust entry durations for smooth display

## Success Criteria

- [ ] Test audio generator produces reliable synthetic audio
- [ ] Ground truth timing metadata is accurate
- [ ] Validation script reports clear metrics
- [ ] Baseline validation completes successfully
- [ ] Issues are identified and quantified

## Files to Create

1. `scripts/generate_test_audio.py` (~150 lines)
2. `scripts/validate_timing.py` (~200 lines)
3. `test_output/timing_test.*` (generated files)

## Files to Reference

- `scripts/test_english_transcription.py:16-36` - edge-tts usage example
- `baobao/transcribe.py:120-185` - SRT generation code to potentially fix
- `docs/claude/planning/task-validation-system.md` - Full implementation plan

## Context for AI

**What we know**:
- Whisper transcription is accurate (correct words)
- Word-level timing exists (stable-ts provides it)
- Issue is in subtitle file generation or format
- mpv does NOT support TTML format
- SRT is the current default format

**What we need to find out**:
- Exact timing accuracy of current implementation
- Where overlapping entries occur
- How karaoke mode creates display issues
- Whether format (SRT) is limitation or implementation bug

**Deferred for later**:
- iPhone display solutions (Apple Music, VLC iOS, video)
- TTML comprehensive player research
- Task 3 (optional TTML implementation)
- Task 5 (embedded lyrics)

## Quick Start Command

```bash
cd /home/michael/Projects/Leon/baobao

# Start with Phase 1, Task 1
# Create scripts/generate_test_audio.py following the plan
```

## Notes

- Repository is at: https://github.com/mihow/baobao-lyrics
- All recent commits pushed and documented
- Testing guide exists: `docs/claude/planning/TESTING-TTML-SYLT.md`
- Use `baobao play` command to quickly validate subtitle output

---

**Prompt for next session**:

> Implement Phase 1 of the timing validation system. Start by creating `scripts/generate_test_audio.py` to generate synthetic test audio using edge-tts with known exact word timings. Follow the plan in `docs/claude/planning/task-validation-system.md`.
