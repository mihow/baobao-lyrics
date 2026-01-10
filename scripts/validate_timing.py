#!/usr/bin/env python3
"""
Validate SRT subtitle format and detect display issues.

Checks for:
- Overlapping timestamp entries (causes multiple subtitles displayed)
- Non-sequential timestamps (causes strange appearance/disappearance)
- Missing or extra words
- Unreasonable timing gaps or durations

Usage:
    # Generate test audio
    python scripts/generate_test_audio.py

    # Transcribe with baobao
    uv run baobao transcribe scripts/test_output/timing_test.mp3

    # Validate format
    uv run python scripts/validate_timing.py scripts/test_output/timing_test.srt

    # Or with expected words
    uv run python scripts/validate_timing.py scripts/test_output/timing_test.srt --expected one two three four five
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SRTEntry:
    """Represents a single SRT subtitle entry."""
    index: int
    start: float  # seconds
    end: float    # seconds
    text: str
    raw_text: str  # text with HTML tags

    @property
    def duration(self) -> float:
        return self.end - self.start

    def overlaps_with(self, other: "SRTEntry") -> bool:
        """Check if this entry overlaps with another."""
        return self.start < other.end and other.start < self.end


def parse_srt_time(time_str: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def parse_srt(srt_path: Path) -> list[SRTEntry]:
    """
    Parse SRT file into structured entries.

    Returns:
        List of SRTEntry objects
    """
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = content.strip().split("\n\n")

    for block in blocks:
        if not block.strip():
            continue

        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        try:
            # Line 0: entry number
            index = int(lines[0])

            # Line 1: timestamp (00:00:01,000 --> 00:00:02,000)
            timestamp_line = lines[1]
            start_str, end_str = timestamp_line.split(" --> ")
            start = parse_srt_time(start_str)
            end = parse_srt_time(end_str)

            # Line 2+: subtitle text
            raw_text = " ".join(lines[2:])

            # Strip HTML tags for analysis
            text = re.sub(r'<[^>]+>', '', raw_text)

            entries.append(SRTEntry(
                index=index,
                start=start,
                end=end,
                text=text.strip(),
                raw_text=raw_text
            ))
        except Exception as e:
            print(f"Warning: Failed to parse entry in block:\n{block}\nError: {e}")
            continue

    return entries


def validate_format(entries: list[SRTEntry], expected_words: list[str] | None = None) -> dict:
    """
    Validate SRT format and detect common issues.

    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []

    # Check 1: Overlapping entries
    overlaps = []
    for i, entry in enumerate(entries):
        for j in range(i + 1, len(entries)):
            other = entries[j]
            if entry.overlaps_with(other):
                overlaps.append((entry, other))

    if overlaps:
        issues.append({
            "type": "OVERLAPPING_ENTRIES",
            "count": len(overlaps),
            "message": f"Found {len(overlaps)} overlapping timestamp pairs (causes multiple subtitles displayed simultaneously)",
            "examples": overlaps[:3]  # Show first 3
        })

    # Check 2: Non-sequential timestamps
    non_sequential = []
    for i in range(len(entries) - 1):
        current = entries[i]
        next_entry = entries[i + 1]
        if current.end > next_entry.start:
            non_sequential.append((current, next_entry))

    if non_sequential:
        issues.append({
            "type": "NON_SEQUENTIAL",
            "count": len(non_sequential),
            "message": f"Found {len(non_sequential)} non-sequential timestamps",
            "examples": non_sequential[:3]
        })

    # Check 3: Unreasonable durations
    too_short = [e for e in entries if e.duration < 0.1]  # < 100ms
    too_long = [e for e in entries if e.duration > 10.0]  # > 10s

    if too_short:
        warnings.append({
            "type": "VERY_SHORT_DURATION",
            "count": len(too_short),
            "message": f"Found {len(too_short)} entries with duration < 100ms (may flash on screen)"
        })

    if too_long:
        warnings.append({
            "type": "VERY_LONG_DURATION",
            "count": len(too_long),
            "message": f"Found {len(too_long)} entries with duration > 10s (may be stuck on screen)"
        })

    # Check 4: Word accuracy (if expected words provided)
    if expected_words:
        transcribed_words = []
        for entry in entries:
            words = entry.text.lower().split()
            transcribed_words.extend([w.strip(".,!?;:") for w in words if w.strip(".,!?;:")])

        missing_words = set(expected_words) - set(transcribed_words)
        extra_words = []
        for word in transcribed_words:
            if word not in expected_words:
                extra_words.append(word)

        if missing_words:
            issues.append({
                "type": "MISSING_WORDS",
                "count": len(missing_words),
                "message": f"Missing expected words: {sorted(missing_words)}",
                "words": list(missing_words)
            })

        if extra_words:
            warnings.append({
                "type": "EXTRA_WORDS",
                "count": len(extra_words),
                "message": f"Found unexpected words: {extra_words}",
                "words": extra_words
            })

    # Check 5: Large gaps between entries
    large_gaps = []
    for i in range(len(entries) - 1):
        current = entries[i]
        next_entry = entries[i + 1]
        gap = next_entry.start - current.end
        if gap > 2.0:  # > 2 second gap
            large_gaps.append((current, next_entry, gap))

    if large_gaps:
        warnings.append({
            "type": "LARGE_GAPS",
            "count": len(large_gaps),
            "message": f"Found {len(large_gaps)} gaps > 2 seconds between entries"
        })

    return {
        "num_entries": len(entries),
        "total_duration": entries[-1].end if entries else 0,
        "issues": issues,
        "warnings": warnings,
        "entries": entries
    }


def main():
    """Run SRT format validation."""
    if len(sys.argv) < 2:
        print("Usage: python validate_timing.py <srt_file> [--expected word1 word2 ...]")
        sys.exit(1)

    srt_path = Path(sys.argv[1])

    if not srt_path.exists():
        print(f"Error: SRT file not found: {srt_path}")
        sys.exit(1)

    # Parse optional expected words
    expected_words = None
    if "--expected" in sys.argv:
        idx = sys.argv.index("--expected")
        expected_words = [w.lower() for w in sys.argv[idx + 1:]]

    print("\n" + "=" * 60)
    print("  SRT FORMAT VALIDATION")
    print("=" * 60)
    print(f"\nFile: {srt_path}")
    if expected_words:
        print(f"Expected words: {expected_words}")

    # Parse SRT
    entries = parse_srt(srt_path)

    if not entries:
        print("\n❌ Error: No entries found in SRT file")
        sys.exit(1)

    print(f"\nEntries: {len(entries)}")
    print(f"Duration: {entries[-1].end:.2f}s")

    # Validate
    results = validate_format(entries, expected_words)

    # Display issues
    has_issues = len(results["issues"]) > 0

    if has_issues:
        print("\n" + "=" * 60)
        print("  ISSUES FOUND")
        print("=" * 60)

        for issue in results["issues"]:
            print(f"\n❌ {issue['message']}")

            if issue["type"] == "OVERLAPPING_ENTRIES":
                for entry1, entry2 in issue["examples"]:
                    print(f"   Entry {entry1.index}: [{entry1.start:.3f}s - {entry1.end:.3f}s] '{entry1.text[:30]}'")
                    print(f"   Entry {entry2.index}: [{entry2.start:.3f}s - {entry2.end:.3f}s] '{entry2.text[:30]}'")
                    print(f"   -> Overlap: {max(0, entry1.end - entry2.start):.3f}s")
                    print()

    # Display warnings
    if results["warnings"]:
        print("\n" + "=" * 60)
        print("  WARNINGS")
        print("=" * 60)

        for warning in results["warnings"]:
            print(f"\n⚠  {warning['message']}")

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    print(f"\nTotal entries: {results['num_entries']}")
    print(f"Total duration: {results['total_duration']:.2f}s")
    print(f"Issues: {len(results['issues'])}")
    print(f"Warnings: {len(results['warnings'])}")

    # Display sample entries
    print("\n" + "-" * 60)
    print("Sample entries (first 5):")
    print("-" * 60)
    for entry in entries[:5]:
        print(f"{entry.index:3d}. [{entry.start:6.3f}s - {entry.end:6.3f}s] ({entry.duration:.3f}s) '{entry.text[:50]}'")

    # Overall result
    print("\n" + "=" * 60)
    if not has_issues:
        print("✅ NO FORMAT ISSUES FOUND")
    else:
        print("❌ FORMAT ISSUES DETECTED")
    print("=" * 60 + "\n")

    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
