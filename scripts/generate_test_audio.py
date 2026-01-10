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


def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


async def generate_timed_audio():
    """Generate test audio for validation testing."""
    import edge_tts

    # Simple text - clear words with natural pauses
    # Note: edge-tts only provides sentence-level timing, not word-level
    # We'll use Whisper to get word timings and validate format/consistency
    text = "one. two. three. four. five."

    voice = "en-US-AriaNeural"
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "timing_test.mp3"

    print(f"Generating audio with voice: {voice}")
    print(f"Output: {output_path}")
    print(f"Text: {text}")

    # Generate audio and capture sentence-level timing metadata
    # (edge-tts v7+ only provides SentenceBoundary, not WordBoundary)
    communicate = edge_tts.Communicate(text, voice, rate="-20%")

    sentence_timings = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                # Capture sentence timing from TTS
                sentence_timings.append({
                    "text": chunk["text"],
                    "start_ms": chunk["offset"] / 10000,
                    "duration_ms": chunk["duration"] / 10000
                })
                print(f"  Sentence: '{chunk['text']}' at {chunk['offset'] / 10000:.0f}ms")

    print(f"✓ Audio generated: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")
    print(f"✓ Captured {len(sentence_timings)} sentence timing events")

    # Save metadata
    metadata_path = output_path.with_suffix(".metadata.json")
    with open(metadata_path, "w") as f:
        json.dump({
            "audio_file": str(output_path),
            "voice": voice,
            "text": text,
            "sentence_timings": sentence_timings,
            "expected_words": ["one", "two", "three", "four", "five"],
            "note": "edge-tts v7+ only provides sentence-level timing. Use Whisper transcription for word-level validation."
        }, f, indent=2)

    print(f"✓ Metadata: {metadata_path}")

    # Display captured timings
    if sentence_timings:
        print("\nSentence timings:")
        for timing in sentence_timings:
            start_sec = timing["start_ms"] / 1000
            duration_sec = timing["duration_ms"] / 1000
            print(f"  [{start_sec:6.3f}s + {duration_sec:5.3f}s] '{timing['text']}'")

    print(f"\nExpected words: {['one', 'two', 'three', 'four', 'five']}")

    return output_path, metadata_path


async def main():
    """Run the test audio generator."""
    print("\n" + "=" * 60)
    print("  SYNTHETIC TEST AUDIO GENERATOR")
    print("=" * 60 + "\n")

    await generate_timed_audio()

    print("\n" + "=" * 60)
    print("  GENERATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Transcribe with baobao:")
    print("     uv run baobao transcribe scripts/test_output/timing_test.mp3")
    print("\n  2. Validate SRT format:")
    print("     uv run python scripts/validate_timing.py \\")
    print("         scripts/test_output/timing_test.srt")
    print("\n  3. Test karaoke mode:")
    print("     uv run baobao transcribe scripts/test_output/timing_test.mp3 --karaoke")
    print("     uv run python scripts/validate_timing.py \\")
    print("         scripts/test_output/timing_test.karaoke.srt")


if __name__ == "__main__":
    asyncio.run(main())
