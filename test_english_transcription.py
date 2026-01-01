#!/usr/bin/env python3
"""
Quick test script to transcribe an English audio sample.

This generates a short English audio clip using edge-tts and transcribes it,
so you can evaluate the transcription quality and timing.

Usage:
    python test_english_transcription.py
"""

import asyncio
from pathlib import Path


async def generate_english_audio(output_path: Path) -> Path:
    """Generate English audio using edge-tts."""
    import edge_tts

    # Clear, simple English phrases with pauses
    text = """
    Hello, this is a test of the transcription system.
    The quick brown fox jumps over the lazy dog.
    One, two, three, four, five.
    Thank you for listening.
    """

    # Use a clear English voice
    voice = "en-US-AriaNeural"

    print(f"Generating audio with voice: {voice}")
    communicate = edge_tts.Communicate(text.strip(), voice, rate="-10%")
    await communicate.save(str(output_path))

    print(f"✓ Audio saved: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")
    return output_path


def transcribe_english(audio_path: Path, output_dir: Path) -> Path:
    """Transcribe English audio and save SRT."""
    import stable_whisper

    print(f"\nLoading Whisper model (base)...")
    model = stable_whisper.load_model("base")

    print(f"Transcribing: {audio_path.name}")
    result = model.transcribe(
        str(audio_path),
        language="en",
        vad=True,
        regroup=True,
    )

    # Refine timestamps
    print("Refining timestamps...")
    model.refine(str(audio_path), result)

    # Save simple SRT
    srt_path = output_dir / "english_test.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result.segments, 1):
            start = format_srt_time(seg.start)
            end = format_srt_time(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n\n")

    print(f"✓ SRT saved: {srt_path}")

    # Save word-level SRT
    word_srt_path = output_dir / "english_test.words.srt"
    with open(word_srt_path, "w", encoding="utf-8") as f:
        idx = 1
        for seg in result.segments:
            if hasattr(seg, "words") and seg.words:
                full_text = seg.text.strip()
                for word in seg.words:
                    w = word.word.strip()
                    if not w:
                        continue
                    start = format_srt_time(word.start)
                    end = format_srt_time(word.end)
                    # Highlight current word
                    highlighted = full_text.replace(
                        w, f'<font color="#00ff00">{w}</font>', 1
                    )
                    f.write(f"{idx}\n{start} --> {end}\n{highlighted}\n\n")
                    idx += 1
            else:
                start = format_srt_time(seg.start)
                end = format_srt_time(seg.end)
                f.write(f"{idx}\n{start} --> {end}\n{seg.text.strip()}\n\n")
                idx += 1

    print(f"✓ Word-level SRT saved: {word_srt_path}")

    # Save LRC
    lrc_path = output_dir / "english_test.lrc"
    with open(lrc_path, "w", encoding="utf-8") as f:
        for seg in result.segments:
            mins = int(seg.start // 60)
            secs = seg.start % 60
            f.write(f"[{mins:02d}:{secs:05.2f}]{seg.text.strip()}\n")

    print(f"✓ LRC saved: {lrc_path}")

    # Print results
    print("\n" + "=" * 60)
    print("TRANSCRIPTION RESULTS")
    print("=" * 60)
    for seg in result.segments:
        print(f"[{seg.start:6.2f}s - {seg.end:6.2f}s] {seg.text.strip()}")

        # Show word timing for first segment
        if seg == result.segments[0] and hasattr(seg, "words") and seg.words:
            print("\n  Word-level timing (first segment):")
            for word in seg.words[:8]:
                print(f"    [{word.start:5.2f}s - {word.end:5.2f}s] '{word.word}'")
            print()

    return srt_path


def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


async def main():
    """Run the English transcription test."""
    print("\n" + "=" * 60)
    print("  ENGLISH TRANSCRIPTION TEST")
    print("=" * 60 + "\n")

    # Output directory
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    audio_path = output_dir / "english_test.mp3"

    # Step 1: Generate audio
    print("Step 1: Generating English test audio...")
    await generate_english_audio(audio_path)

    # Step 2: Transcribe
    print("\nStep 2: Transcribing with Whisper...")
    srt_path = transcribe_english(audio_path, output_dir)

    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
    print(f"\nOutput files in: {output_dir}")
    print(f"  - english_test.mp3      (audio)")
    print(f"  - english_test.srt      (simple subtitles)")
    print(f"  - english_test.words.srt (word-level highlighting)")
    print(f"  - english_test.lrc      (LRC lyrics format)")

    print("\n" + "-" * 60)
    print("TO PREVIEW WITH SYNCED LYRICS:")
    print("-" * 60)
    print(
        """
Option 1: MPV (recommended - CLI)
  # Install: sudo apt install mpv
  mpv --sub-file=test_output/english_test.srt test_output/english_test.mp3

Option 2: VLC
  # Install: sudo apt install vlc
  # Open audio, then: Subtitle -> Add Subtitle File

Option 3: Audacious (GUI music player with LRC support)
  # Install: sudo apt install audacious
  # Supports .lrc files automatically if named same as audio

Option 4: lrcshow-x (terminal LRC viewer)
  # pip install lrcshow-x
  lrcshow test_output/english_test.lrc

Option 5: Aegisub (subtitle editor - best for fine-tuning)
  # Install: sudo apt install aegisub
  # Open audio + SRT, see waveform with timing
"""
    )


if __name__ == "__main__":
    asyncio.run(main())
