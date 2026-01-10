#!/usr/bin/env python3
"""
Generate test audio with a PHRASE (multiple words) to validate karaoke mode.

This tests whether karaoke mode properly:
- Displays the full phrase in each subtitle entry
- Highlights only the current word
- Creates sequential entries with the same phrase text

Usage:
    python scripts/generate_phrase_test.py
"""

import asyncio
from pathlib import Path


async def generate_phrase_audio():
    """Generate test audio with a phrase (not individual words)."""
    import edge_tts

    # A phrase with multiple words - no periods between words
    text = "Mary had a little lamb"

    voice = "en-US-AriaNeural"
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "phrase_test.mp3"

    print(f"Generating phrase audio: '{text}'")
    print(f"Voice: {voice}")
    print(f"Output: {output_path}")

    communicate = edge_tts.Communicate(text, voice, rate="-20%")

    sentence_timings = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sentence_timings.append({
                    "text": chunk["text"],
                    "start_ms": chunk["offset"] / 10000,
                    "duration_ms": chunk["duration"] / 10000
                })

    print(f"✓ Audio generated: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")
    print(f"\nExpected behavior in karaoke mode:")
    print("  Each SRT entry should show the FULL phrase:")
    print("  1. <font color='#00ff00'>Mary</font> had a little lamb")
    print("  2. Mary <font color='#00ff00'>had</font> a little lamb")
    print("  3. Mary had <font color='#00ff00'>a</font> little lamb")
    print("  etc.")

    return output_path


async def main():
    print("\n" + "=" * 60)
    print("  PHRASE TEST AUDIO GENERATOR")
    print("=" * 60 + "\n")

    await generate_phrase_audio()

    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print("\n1. Transcribe with karaoke mode:")
    print("   uv run baobao transcribe scripts/test_output/phrase_test.mp3 --karaoke --model base")
    print("\n2. Manually inspect the SRT file:")
    print("   cat scripts/test_output/phrase_test.srt")
    print("\n3. Check if FULL phrase appears in each entry:")
    print("   - Each entry should have the complete phrase")
    print("   - Only one word should be highlighted per entry")
    print("   - All entries should have the same text content")
    print()


if __name__ == "__main__":
    asyncio.run(main())
