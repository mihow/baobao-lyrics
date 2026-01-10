# Task: Build Timing Validation System with Synthetic Audio

**Created**: 2025-12-31
**Status**: Planning
**Priority**: High (critical for quality assurance)

## Problem Statement

Current subtitle display issues:
- ✅ Chinese lyrics are correct
- ✅ Word highlighting timing mostly works
- ❌ Extra lyrics displayed simultaneously
- ❌ Phrases appear and disappear strangely
- ❓ Need systematic way to validate timing accuracy

## Objectives

1. **Create synthetic test audio** with known exact timings
2. **Build validation system** to verify timing accuracy
3. **Research TTML player support** comprehensively
4. **Fix subtitle display issues** based on findings

## Part 1: Synthetic Test Audio Generation

### Why Synthetic Audio?

- **Known ground truth**: Exact word timings from TTS metadata
- **Reproducible**: Same audio every time for testing
- **Controlled**: Clear pronunciation, no background music
- **Fast**: No need to manually annotate real audio

### Implementation Plan

**Tool**: edge-tts (already used in scripts/test_e2e_transcription.py)

**Test Audio Specifications**:
```python
# Simple, clear phrases with known timings
TEST_PHRASES = [
    ("one", 0.0, 0.5),      # Word, start_sec, end_sec
    ("two", 0.8, 1.3),
    ("three", 1.6, 2.1),
    ("four", 2.4, 2.9),
    ("five", 3.2, 3.7),
]

# Generate audio with pauses between words
# Record actual TTS timing metadata
# Compare with Whisper transcription output
```

**New file**: `scripts/generate_test_audio.py`

```python
#!/usr/bin/env python3
"""
Generate synthetic test audio with known exact timings.

Creates:
1. Test audio file with clear English words
2. Ground truth timing file (.json)
3. Reference SRT file with correct timings

Usage:
    python scripts/generate_test_audio.py
    # Creates: test_output/timing_test.mp3
    #          test_output/timing_test.ground_truth.json
    #          test_output/timing_test.reference.srt
"""

import asyncio
import json
from pathlib import Path
import edge_tts

async def generate_timed_audio():
    """Generate test audio with known word timings."""

    # Test phrases with exact timing requirements
    phrases = [
        "one",
        "pause",  # Silence marker
        "two",
        "pause",
        "three",
        "pause",
        "four",
        "pause",
        "five"
    ]

    # Build text with SSML for precise timing
    text = """
    <speak>
        <prosody rate="slow">
            one
            <break time="500ms"/>
            two
            <break time="500ms"/>
            three
            <break time="500ms"/>
            four
            <break time="500ms"/>
            five
        </prosody>
    </speak>
    """

    voice = "en-US-AriaNeural"
    output_path = Path("test_output/timing_test.mp3")

    # Generate audio and capture timing metadata
    communicate = edge_tts.Communicate(text, voice)

    # edge-tts provides word boundary events
    word_timings = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # Capture exact timing from TTS
                word_timings.append({
                    "word": chunk["text"],
                    "start_ms": chunk["offset"] / 10000,  # Convert to ms
                    "end_ms": (chunk["offset"] + chunk["duration"]) / 10000
                })

    # Save ground truth
    ground_truth_path = output_path.with_suffix(".ground_truth.json")
    with open(ground_truth_path, "w") as f:
        json.dump({
            "audio_file": str(output_path),
            "voice": voice,
            "word_timings": word_timings
        }, f, indent=2)

    # Generate reference SRT
    reference_srt = output_path.with_suffix(".reference.srt")
    with open(reference_srt, "w") as f:
        for i, timing in enumerate(word_timings, 1):
            if timing["word"] == "pause":
                continue
            start = format_srt_time(timing["start_ms"] / 1000)
            end = format_srt_time(timing["end_ms"] / 1000)
            f.write(f"{i}\n{start} --> {end}\n{timing['word']}\n\n")

    print(f"✓ Generated: {output_path}")
    print(f"✓ Ground truth: {ground_truth_path}")
    print(f"✓ Reference SRT: {reference_srt}")

    return output_path, ground_truth_path

def format_srt_time(seconds):
    """Format seconds as SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

### Test Audio Requirements

1. **Simple words**: Clear, distinct English words (one, two, three...)
2. **Controlled timing**: 500ms pauses between words
3. **Metadata capture**: Record exact TTS word boundaries
4. **Ground truth file**: JSON with actual timings
5. **Reference SRT**: Expected correct output

## Part 2: Validation System

### Goal

Compare Whisper transcription output against known ground truth timing.

**New file**: `scripts/validate_timing.py`

```python
#!/usr/bin/env python3
"""
Validate transcription timing accuracy against ground truth.

Compares:
- Whisper transcription output (baobao-generated SRT)
- Ground truth timing (from TTS metadata)

Metrics:
- Word timing error (mean, max, std dev)
- Missed words
- Extra words
- Timing drift over duration

Usage:
    # Generate test audio
    python scripts/generate_test_audio.py

    # Transcribe with baobao
    uv run baobao transcribe test_output/timing_test.mp3

    # Validate timing
    python scripts/validate_timing.py \
        test_output/timing_test.ground_truth.json \
        test_output/timing_test.srt
"""

import json
import sys
from pathlib import Path

def parse_srt(srt_path):
    """Parse SRT file and extract word timings."""
    # Parse SRT entries
    # Return list of (word, start_sec, end_sec)
    pass

def parse_ground_truth(json_path):
    """Load ground truth timings."""
    with open(json_path) as f:
        data = json.load(f)
    return [(t["word"], t["start_ms"]/1000, t["end_ms"]/1000)
            for t in data["word_timings"]]

def calculate_timing_error(ground_truth, transcription):
    """Calculate timing accuracy metrics."""
    errors = []

    # Match words between ground truth and transcription
    for gt_word, gt_start, gt_end in ground_truth:
        # Find matching word in transcription
        matched = find_matching_word(transcription, gt_word)

        if matched:
            trans_word, trans_start, trans_end = matched

            # Calculate timing errors
            start_error = abs(trans_start - gt_start)
            end_error = abs(trans_end - gt_end)

            errors.append({
                "word": gt_word,
                "start_error_ms": start_error * 1000,
                "end_error_ms": end_error * 1000,
                "ground_truth": (gt_start, gt_end),
                "transcribed": (trans_start, trans_end)
            })

    # Calculate statistics
    if errors:
        start_errors = [e["start_error_ms"] for e in errors]
        mean_error = sum(start_errors) / len(start_errors)
        max_error = max(start_errors)

        return {
            "mean_error_ms": mean_error,
            "max_error_ms": max_error,
            "num_words": len(errors),
            "detailed_errors": errors
        }

    return None

def main():
    ground_truth_path = sys.argv[1]
    srt_path = sys.argv[2]

    ground_truth = parse_ground_truth(ground_truth_path)
    transcription = parse_srt(srt_path)

    metrics = calculate_timing_error(ground_truth, transcription)

    print("\n=== Timing Validation Results ===\n")
    print(f"Mean timing error: {metrics['mean_error_ms']:.1f} ms")
    print(f"Max timing error: {metrics['max_error_ms']:.1f} ms")
    print(f"Words validated: {metrics['num_words']}")

    # Detailed errors
    print("\nPer-word errors:")
    for error in metrics["detailed_errors"]:
        print(f"  {error['word']:10s} - {error['start_error_ms']:5.1f} ms")
```

### Validation Metrics

1. **Mean timing error**: Average difference from ground truth
2. **Max timing error**: Worst-case drift
3. **Standard deviation**: Consistency of timing
4. **Word accuracy**: Missed or extra words
5. **Drift over time**: Does error accumulate?

### Acceptance Criteria

- Mean error < 100ms (acceptable for karaoke)
- Max error < 250ms (no egregious mistakes)
- 100% word recognition (all words found)
- No timing drift (errors don't accumulate)

## Part 3: Diagnose Subtitle Display Issues

### Current Problems

Based on user report:
1. **Extra lyrics displayed**: Multiple subtitle entries showing at once
2. **Strange appearance/disappearance**: Subtitles flicker or overlap

### Root Causes to Investigate

**Issue 1: Overlapping Timestamps**
```srt
# WRONG - overlapping times
1
00:00:01,000 --> 00:00:03,000
First line

2
00:00:02,500 --> 00:00:04,000
Second line overlaps!
```

**Issue 2: Word-level vs Line-level Timing**
- Karaoke mode creates one SRT entry per word
- Multiple words from same phrase shown simultaneously
- Need sequential, non-overlapping entries

**Issue 3: SRT Entry Duration**
- Too long: Multiple phrases pile up
- Too short: Subtitles flash and disappear

### Investigation Steps

1. **Examine generated SRT files**:
   ```bash
   # Check for overlapping timestamps
   cat songs/*.srt | grep -A 2 "^[0-9]$"
   ```

2. **Analyze karaoke mode output**:
   - How are word-level timestamps converted to SRT entries?
   - Are entries sequential or overlapping?

3. **Check transcribe.py SRT generation**:
   - `baobao/transcribe.py:120-146` - `save_srt()` method
   - Lines 155-185 - Karaoke word highlighting logic

### Potential Fixes

**Fix 1: Non-overlapping entries**
```python
# Ensure each entry ends before next begins
for i, seg in enumerate(segments):
    start = seg.start
    # End at next segment start, or natural end
    end = segments[i+1].start if i+1 < len(segments) else seg.end
```

**Fix 2: Karaoke mode - one word per entry**
```python
# Current: Highlights words in full phrase
# Better: Show one word at a time with full context

# Entry 1: 00:00:01.000 --> 00:00:01.500
# <font color="#00ff00">你</font> 是 我 陽光

# Entry 2: 00:00:01.500 --> 00:00:02.000
# 你 <font color="#00ff00">是</font> 我 陽光
```

**Fix 3: Use TTML instead of SRT**
- TTML supports word-level timing natively
- No need for overlapping entries
- Proper metadata structure

## Part 4: Research TTML Player Support

### Goal

Comprehensive survey of TTML subtitle support across players.

### Testing Methodology

**Test File**: Use existing `test_output/test_lyrics.ttml`

**Players to Test**:

**Desktop**:
- [x] mpv - ❌ NOT SUPPORTED (tested)
- [ ] VLC Media Player
- [ ] IINA (macOS)
- [ ] MPC-HC (Windows)
- [ ] Kodi/Plex media centers

**Mobile**:
- [ ] iOS default video player
- [ ] Apple Music app (should support - Apple's format)
- [ ] VLC for iOS/Android
- [ ] MX Player (Android)

**Web**:
- [ ] HTML5 `<video>` with TTML track
- [ ] Video.js player
- [ ] Plyr.io
- [ ] YouTube (accepts TTML uploads?)

**Specialized**:
- [ ] Aegisub (subtitle editor)
- [ ] Subtitle Edit
- [ ] SubtitleWorkshop

### Testing Template

For each player, document:
```markdown
### [Player Name] v[Version]

**Platform**: macOS/Windows/Linux/iOS/Android/Web
**Test Date**: 2025-12-31
**Test File**: test_output/test_lyrics.ttml

**Results**:
- ✅/❌ Loads TTML file
- ✅/❌ Displays Chinese text
- ✅/❌ Displays pinyin (x-roman)
- ✅/❌ Displays translation (x-translation)
- ✅/❌ Word-level timing works
- ✅/❌ Line-level timing works

**Notes**:
[Observations about display quality, bugs, etc.]

**Recommendation**:
✅ Recommended / ⚠️ Limited support / ❌ Not supported
```

### Research Questions

1. **Apple Music TTML**: Does Apple Music app support its own format?
2. **HTML5 TTML**: Can we embed in web player?
3. **TTML vs WebVTT**: Is WebVTT better supported?
4. **Conversion tools**: Easy TTML → SRT/WebVTT conversion?

### Expected Outcome

**Decision Matrix**:
- If 3+ major players support TTML → Make it default
- If only Apple ecosystem → Keep as optional format
- If no major support → Stick with SRT, document limitations

## Part 5: Implementation Plan

### Phase 1: Build Test Infrastructure (Day 1)

1. ✅ Create `scripts/generate_test_audio.py`
2. ✅ Generate synthetic audio with known timings
3. ✅ Create `scripts/validate_timing.py`
4. ✅ Run baseline validation test

**Deliverable**: Working validation system

### Phase 2: Diagnose and Fix (Day 2)

1. Run validation on current transcription output
2. Identify specific timing issues
3. Examine SRT generation code (transcribe.py:120-185)
4. Implement fixes for overlapping entries
5. Test karaoke mode fixes

**Deliverable**: Improved subtitle timing

### Phase 3: TTML Research (Day 3)

1. Test TTML with VLC, IINA, web players
2. Document support matrix
3. Create TTML generation module (if worth it)
4. Test TTML output with validation system

**Deliverable**: TTML support decision + implementation

### Phase 4: Documentation (Day 4)

1. Document findings in `docs/claude/testing/`
2. Update README with player compatibility info
3. Add validation tests to test suite
4. Create user guide for timing validation

**Deliverable**: Complete documentation

## Success Criteria

- [ ] Synthetic audio generation works reliably
- [ ] Validation system reports accurate metrics
- [ ] Mean timing error < 100ms
- [ ] No overlapping subtitle entries
- [ ] Karaoke mode displays correctly
- [ ] TTML player support documented
- [ ] Clear decision on TTML vs SRT default

## Related Files

**To create**:
- `scripts/generate_test_audio.py`
- `scripts/validate_timing.py`
- `docs/claude/testing/ttml-player-support.md`

**To modify**:
- `baobao/transcribe.py` - Fix SRT generation logic (lines 120-185)
- Potentially create `baobao/ttml.py` - TTML generation module

**To examine**:
- Current SRT output files in `songs/`
- Karaoke mode output examples
- Test audio in `test_output/`

## Open Questions

1. **edge-tts timing precision**: Does it provide accurate word boundaries?
2. **Whisper word-level accuracy**: How close to ground truth?
3. **SRT limitations**: Is format the problem, or our implementation?
4. **TTML worth it**: Will improved format solve display issues?
5. **Player prevalence**: What do users actually use?

## Next Steps

1. Start with Phase 1: Build test infrastructure
2. Generate synthetic audio and validate current output
3. Based on findings, prioritize fixes vs format changes
4. Document TTML research in parallel
