#!/usr/bin/env python3
"""
Test script to validate stable-ts + faster-whisper for Chinese lyrics transcription.
Tests the core challenging parts:
1. Can we load the model?
2. Can we transcribe Chinese audio with word-level timestamps?
3. Are the timestamps accurate enough for LRC files?
4. LLM-based pinyin and English translation for learning

Uses Instructor + Ollama for reliable structured output extraction with Pydantic models.
Instructor provides automatic validation and retries for robust JSON parsing.
"""

import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:4b"  # Good for Chinese, fast enough for per-phrase processing

# Output format options
OUTPUT_FORMAT_FULL = "full"  # Full English translation
OUTPUT_FORMAT_EMOJI = "emoji"  # Emoji + brief keywords (saves space)
OUTPUT_FORMAT_LEARN = "learn"  # Optimized for learning: pinyin-first with highlights


# First, check if we can import the required packages
def check_dependencies():
    """Check and install required packages."""
    missing = []

    try:
        import stable_whisper

        print(f"✓ stable-ts version: {stable_whisper.__version__}")
    except ImportError:
        missing.append("stable-ts")

    try:
        import faster_whisper

        print(f"✓ faster-whisper available")
    except ImportError:
        missing.append("faster-whisper")

    try:
        import instructor

        print(f"✓ instructor available")
    except ImportError:
        missing.append("instructor")

    try:
        import pydantic

        print(f"✓ pydantic version: {pydantic.__version__}")
    except ImportError:
        missing.append("pydantic")

    if missing:
        print(f"\n⚠ Missing packages: {missing}")
        print("Installing...")
        import subprocess

        for pkg in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])
        print("Installed. Please re-run the script.")
        sys.exit(1)

    return True


# Pydantic models for structured LLM output
from pydantic import BaseModel, Field


class WordDetail(BaseModel):
    """Details for a single Chinese character."""

    char: str = Field(description="The Chinese character")
    pinyin: str = Field(description="Pinyin with tone marks (e.g., nǐ, hǎo)")
    english: str = Field(description="Brief English meaning or emoji")


class PhraseInterpretation(BaseModel):
    """Interpretation of a Chinese phrase for language learning."""

    pinyin: str = Field(description="Full pinyin of the phrase with tone marks")
    english: str = Field(
        description="Brief English translation (2-5 words) or emoji + keyword"
    )
    word_details: List[WordDetail] = Field(description="Per-character breakdown")


class LearningLyricLine(BaseModel):
    """Optimized lyric line for language learning - designed by LLM for pedagogy."""

    pinyin_spaced: str = Field(
        description="Pinyin with spaces between syllables for clarity"
    )
    literal_gloss: str = Field(
        description="Word-by-word English gloss matching pinyin order"
    )
    natural_english: str = Field(description="Natural English translation")
    sing_along_tip: str = Field(
        description="Brief pronunciation tip or memory hook (emoji welcome)"
    )
    word_details: List[WordDetail] = Field(description="Per-character breakdown")


class ChineseLyricInterpreter:
    """Uses Instructor + Ollama for reliable structured output extraction."""

    def __init__(
        self,
        model: str = OLLAMA_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        output_format: str = OUTPUT_FORMAT_FULL,
    ):
        self.model = model
        self.base_url = base_url
        self.output_format = output_format
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the instructor client."""
        if self._client is None:
            import instructor

            # Use instructor's from_provider for Ollama - handles all the complexity
            self._client = instructor.from_provider(
                f"ollama/{self.model}",
                mode=instructor.Mode.JSON,  # JSON mode works best with qwen
            )
        return self._client

    def _get_cache_key(self, chinese_text: str) -> str:
        """Create cache key from text and format."""
        return f"{self.output_format}:{chinese_text}"

    # Cache for interpreted phrases
    _cache: dict = {}

    def interpret_phrase(self, chinese_text: str) -> dict:
        """
        Get pinyin and English for a Chinese phrase using Instructor.

        Uses Pydantic models for guaranteed structured output with automatic retries.
        """
        # Clean the text (remove highlighting tags if any)
        clean_text = re.sub(r"<[^>]+>", "", chinese_text).strip()

        if not clean_text:
            return {"pinyin": "", "english": "", "word_details": []}

        # Check cache
        cache_key = self._get_cache_key(clean_text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Use learning-optimized format
        if self.output_format == OUTPUT_FORMAT_LEARN:
            return self._interpret_for_learning(clean_text, cache_key)

        # Build the prompt based on output format
        if self.output_format == OUTPUT_FORMAT_EMOJI:
            format_instruction = """For english fields: use 1-2 emojis + optional 1-2 word hint.
Examples: "☀️ sunshine", "❤️ love", "😊 happy", "🌧️ rain"
Keep it visual and minimal for children."""
        else:
            format_instruction = """For english fields: use simple 2-5 word translations.
Use simple words appropriate for children learning Chinese."""

        prompt = f"""Analyze this Chinese phrase for a children's learning song.

Chinese: {clean_text}

{format_instruction}

Rules:
- Use standard pinyin with tone marks (ā á ǎ à, ē é ě è, ī í ǐ ì, etc.)
- word_details should have one entry per Chinese character
- Keep translations brief and child-friendly

/no_think"""

        try:
            # Instructor handles validation and retries automatically
            result = self.client.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=PhraseInterpretation,
                max_retries=2,
                timeout=30.0,
            )

            # Convert Pydantic model to dict for caching
            result_dict = {
                "pinyin": result.pinyin,
                "english": result.english,
                "word_details": [
                    {"char": w.char, "pinyin": w.pinyin, "english": w.english}
                    for w in result.word_details
                ],
            }

            self._cache[cache_key] = result_dict
            return result_dict

        except Exception as e:
            print(f"  ⚠ Instructor error for '{clean_text}': {e}")
            # Fallback: return basic structure
            fallback = {
                "pinyin": clean_text,
                "english": "?",
                "word_details": [
                    {"char": c, "pinyin": "?", "english": "?"}
                    for c in clean_text
                    if c.strip()
                ],
            }
            self._cache[cache_key] = fallback
            return fallback

    def _interpret_for_learning(self, clean_text: str, cache_key: str) -> dict:
        """
        Get learning-optimized interpretation with pedagogy focus.

        The LLM designs the best learning experience for each phrase.
        """
        prompt = f"""You are a Chinese language teacher creating sing-along lyrics for children.

Analyze this Chinese phrase and create the BEST learning format:

Chinese: {clean_text}

Design your response to help a child:
1. SING the pinyin correctly (spaced clearly, with tone marks)
2. UNDERSTAND what each word means (literal word-by-word gloss)
3. REMEMBER it (a fun tip, rhyme, or emoji memory hook)

Rules for pinyin_spaced:
- Space between each syllable: "nǐ hǎo" not "nǐhǎo"
- Always use tone marks: ā á ǎ à, ē é ě è, ī í ǐ ì, ū ú ǔ ù, ǖ ǘ ǚ ǜ
- This is what they'll read while singing!

Rules for literal_gloss:
- Match the pinyin word order exactly
- Use simple words a child knows
- Example: "nǐ hǎo" → "you good" (not "hello")

Rules for sing_along_tip:
- Make it memorable! Use emojis, rhymes, or fun associations
- Keep it SHORT (fits on one line)
- Example: "🎵 Sounds like 'knee how' - bend your knee and say hi!"

/no_think"""

        try:
            result = self.client.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=LearningLyricLine,
                max_retries=2,
                timeout=30.0,
            )

            result_dict = {
                "pinyin": result.pinyin_spaced,
                "pinyin_spaced": result.pinyin_spaced,
                "literal_gloss": result.literal_gloss,
                "english": result.natural_english,
                "sing_along_tip": result.sing_along_tip,
                "word_details": [
                    {"char": w.char, "pinyin": w.pinyin, "english": w.english}
                    for w in result.word_details
                ],
            }

            self._cache[cache_key] = result_dict
            return result_dict

        except Exception as e:
            print(f"  ⚠ Learning interpret error for '{clean_text}': {e}")
            fallback = {
                "pinyin": clean_text,
                "pinyin_spaced": clean_text,
                "literal_gloss": "?",
                "english": "?",
                "sing_along_tip": "",
                "word_details": [
                    {"char": c, "pinyin": "?", "english": "?"}
                    for c in clean_text
                    if c.strip()
                ],
            }
            self._cache[cache_key] = fallback
            return fallback

    def format_subtitle_line(
        self, chinese: str, highlight_idx: Optional[int] = None
    ) -> dict:
        """
        Format a subtitle line with pinyin and English.

        Args:
            chinese: The Chinese text (may contain <font> highlighting)
            highlight_idx: Index of character being highlighted (if any)
        """
        # Extract clean text and find highlighted character
        clean_text = re.sub(r"<[^>]+>", "", chinese).strip()

        # Find which character is highlighted in original
        highlight_match = re.search(r"<font[^>]*>([^<]+)</font>", chinese)
        highlighted_char = highlight_match.group(1) if highlight_match else None

        # Get interpretation
        interp = self.interpret_phrase(clean_text)

        pinyin = interp.get("pinyin", "")
        english = interp.get("english", "")
        word_details = interp.get("word_details", [])

        # Build pinyin line with highlighting
        if highlighted_char and word_details:
            pinyin_parts = []
            for detail in word_details:
                char = detail.get("char", "")
                py = detail.get("pinyin", "")
                if char == highlighted_char:
                    pinyin_parts.append(f'<font color="#00ff00">{py}</font>')
                else:
                    pinyin_parts.append(py)
            pinyin_highlighted = " ".join(pinyin_parts)
        else:
            pinyin_highlighted = pinyin

        return {
            "chinese": chinese,
            "pinyin": pinyin_highlighted,
            "pinyin_plain": pinyin,
            "english": english,
            "word_details": word_details,
        }


def test_llm_connection():
    """Test that Ollama is accessible."""
    print("\n--- Testing LLM Connection ---")
    try:
        import requests

        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            print(f"✓ Ollama connected. Available models: {len(models)}")

            # Check if our preferred model is available
            if any(OLLAMA_MODEL.split(":")[0] in m for m in models):
                print(f"✓ Model '{OLLAMA_MODEL}' available")
            else:
                print(f"⚠ Model '{OLLAMA_MODEL}' not found. Available: {models[:5]}...")
            return True
    except Exception as e:
        print(f"⚠ Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
        print("  Make sure Ollama is running: docker ps | grep ollama")
        return False


def test_transcription(audio_path: str, model_size: str = "base"):
    """
    Test transcription on a single audio file.

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
                    Using large-v3 by default for best Chinese accuracy.
    """
    import stable_whisper

    print(f"\n{'='*60}")
    print(f"Testing transcription: {Path(audio_path).name}")
    print(f"Model: {model_size} (optimized for accuracy)")
    print(f"{'='*60}\n")

    # Load model (uses faster-whisper by default if available)
    print("Loading model (large-v3 is ~3GB, first run will download)...")
    model = stable_whisper.load_model(model_size)
    print("✓ Model loaded\n")

    # Transcribe with Chinese language hint
    # Using settings optimized for accuracy over speed
    print("Transcribing (this may take a few minutes for accuracy)...")
    result = model.transcribe(
        audio_path,
        language="zh",  # Chinese
        vad=True,  # Voice Activity Detection (good for music)
        regroup=True,  # Regroup words into natural segments
        beam_size=5,  # Higher beam size for better accuracy
        best_of=5,  # Consider more candidates
        condition_on_previous_text=True,  # Better context
    )

    # Refine timestamps for maximum accuracy (slower but more precise)
    print("Refining timestamps for precision...")
    model.refine(audio_path, result)

    print("✓ Transcription complete\n")

    # Show results with timestamps
    print("--- Results with timestamps ---\n")
    for segment in result.segments:
        start = segment.start
        end = segment.end
        text = segment.text.strip()
        print(f"[{start:06.2f}s - {end:06.2f}s] {text}")

        # Show word-level timestamps for first segment only (as sample)
        if (
            segment == result.segments[0]
            and hasattr(segment, "words")
            and segment.words
        ):
            print("\n  Word-level timestamps (first segment):")
            for word in segment.words[:5]:  # First 5 words
                print(f"    [{word.start:.2f}s - {word.end:.2f}s] '{word.word}'")
            if len(segment.words) > 5:
                print(f"    ... and {len(segment.words) - 5} more words")
            print()

    # Export to LRC format
    lrc_path = Path(audio_path).with_suffix(".test.lrc")
    result.to_srt_vtt(str(lrc_path).replace(".lrc", ".srt"))  # SRT for testing
    print(f"\n✓ Saved SRT to: {lrc_path.with_suffix('.srt')}")

    # Also save as LRC-style text
    print("\n--- LRC Preview ---\n")
    for segment in result.segments[:5]:  # First 5 lines
        mins = int(segment.start // 60)
        secs = segment.start % 60
        print(f"[{mins:02d}:{secs:05.2f}]{segment.text.strip()}")
    if len(result.segments) > 5:
        print(f"... and {len(result.segments) - 5} more lines")

    return result


def process_srt_with_llm(
    srt_path: str,
    output_path: Optional[str] = None,
    output_format: str = OUTPUT_FORMAT_FULL,
):
    """
    Process an existing SRT file and add pinyin + English translations.
    Creates a new enhanced SRT file.

    Args:
        srt_path: Path to input SRT file
        output_path: Path for output (default: adds .enhanced before .srt)
        output_format: OUTPUT_FORMAT_FULL, OUTPUT_FORMAT_EMOJI, or OUTPUT_FORMAT_LEARN
    """
    print(f"\n{'='*60}")
    print(f"Processing SRT with LLM: {Path(srt_path).name}")
    print(f"Output format: {output_format}")
    print(f"{'='*60}\n")

    # Initialize interpreter
    interpreter = ChineseLyricInterpreter(output_format=output_format)

    # Read SRT file
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse SRT entries
    entries = []
    current_entry = {}

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(current_entry)
                current_entry = {}
        elif line.isdigit() and not current_entry:
            current_entry["index"] = int(line)
        elif "-->" in line:
            current_entry["timestamp"] = line
        elif current_entry:
            current_entry["text"] = current_entry.get("text", "") + line

    if current_entry:
        entries.append(current_entry)

    print(f"Found {len(entries)} subtitle entries")

    # Process unique phrases first (for caching efficiency)
    unique_phrases = set()
    for entry in entries:
        clean = re.sub(r"<[^>]+>", "", entry.get("text", "")).strip()
        if clean:
            unique_phrases.add(clean)

    print(f"Unique phrases to interpret: {len(unique_phrases)}")
    print("\nInterpreting phrases with LLM...")

    # Pre-interpret all unique phrases
    for i, phrase in enumerate(unique_phrases):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(unique_phrases)}")
        interpreter.interpret_phrase(phrase)

    print("✓ All phrases interpreted\n")

    # Build enhanced SRT based on format
    enhanced_entries = []

    if output_format == OUTPUT_FORMAT_LEARN:
        # Learning format: PINYIN is primary (what they sing from), with highlighting
        for entry in entries:
            text = entry.get("text", "")
            result = interpreter.format_subtitle_line(text)
            interp = interpreter.interpret_phrase(re.sub(r"<[^>]+>", "", text).strip())

            # PINYIN FIRST (large, highlighted) - this is what learners sing!
            # Then Chinese characters below for reference
            # Then meaning hint
            lines = [
                result["pinyin"],  # PINYIN with highlighting (sing this!)
                result["chinese"],  # Chinese characters (reference)
                interp.get("sing_along_tip", "")
                or f"({interp.get('literal_gloss', interp.get('english', ''))})",
            ]

            enhanced_entries.append(
                {
                    "index": entry.get("index", 0),
                    "timestamp": entry.get("timestamp", ""),
                    "text": "\n".join(lines),
                }
            )
    else:
        # Original format: Chinese first
        for entry in entries:
            text = entry.get("text", "")
            result = interpreter.format_subtitle_line(text)

            # Create multi-line subtitle: Chinese (highlighted), Pinyin, English
            lines = [
                result["chinese"],  # Original with highlighting
                result["pinyin"],  # Pinyin (also highlighted)
                f"({result['english']})",  # English in parentheses
            ]

            enhanced_entries.append(
                {
                    "index": entry.get("index", 0),
                    "timestamp": entry.get("timestamp", ""),
                    "text": "\n".join(lines),
                }
            )

    # Write enhanced SRT
    if output_path is None:
        format_suffixes = {
            OUTPUT_FORMAT_EMOJI: ".emoji.srt",
            OUTPUT_FORMAT_LEARN: ".learn.srt",
            OUTPUT_FORMAT_FULL: ".enhanced.srt",
        }
        suffix = format_suffixes.get(output_format, ".enhanced.srt")
        output_path = str(Path(srt_path).with_suffix("").with_suffix(suffix))

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in enhanced_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['timestamp']}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"✓ Saved enhanced SRT to: {output_path}")

    # Show preview
    print("\n--- Enhanced SRT Preview ---\n")
    for entry in enhanced_entries[:5]:
        print(f"{entry['index']}")
        print(f"{entry['timestamp']}")
        print(f"{entry['text']}")
        print()

    if len(enhanced_entries) > 5:
        print(f"... and {len(enhanced_entries) - 5} more entries")

    return output_path


def main():
    """Main test function."""
    # Determine which model will be used
    whisper_model = "large-v3"  # Default model for best Chinese accuracy

    print("\n" + "=" * 60)
    print("  stable-ts + faster-whisper Chinese Transcription Test")
    print("  with LLM-based Pinyin & English Translation")
    print(f"  Whisper Model: {whisper_model}")
    print("=" * 60 + "\n")

    # Check dependencies first
    check_dependencies()

    # Test LLM connection
    llm_available = test_llm_connection()

    # Check for --llm-only mode (just process existing SRT)
    if (
        "--llm-only" in sys.argv
        or "--enhance" in sys.argv
        or "--emoji" in sys.argv
        or "--learn" in sys.argv
    ):
        if not llm_available:
            print("❌ LLM not available. Cannot enhance SRT.")
            sys.exit(1)

        # Determine output format
        if "--learn" in sys.argv:
            output_format = OUTPUT_FORMAT_LEARN
        elif "--emoji" in sys.argv:
            output_format = OUTPUT_FORMAT_EMOJI
        else:
            output_format = OUTPUT_FORMAT_FULL

        # Find SRT file
        srt_file = None
        for arg in sys.argv[1:]:
            if arg.endswith(".srt") and Path(arg).exists():
                srt_file = arg
                break

        if not srt_file:
            # Look for test SRT
            songs_dir = Path(__file__).parent / "songs"
            srt_files = list(songs_dir.glob("*.test.srt"))
            if srt_files:
                srt_file = str(srt_files[0])

        if srt_file:
            process_srt_with_llm(srt_file, output_format=output_format)
            print("\n" + "=" * 60)
            print("  ENHANCEMENT COMPLETE ✓")
            print("=" * 60)
        else:
            print("❌ No SRT file found to enhance")
            sys.exit(1)
        return

    # Find a test audio file
    songs_dir = Path(__file__).parent / "songs"
    audio_files = list(songs_dir.glob("*.mp3"))

    if not audio_files:
        print(f"No MP3 files found in {songs_dir}")
        print("Please provide a path to an audio file as argument.")
        sys.exit(1)

    # Use first file or command line argument
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        test_file = sys.argv[1]
    else:
        # Pick a short/simple song for testing
        test_file = None
        for f in audio_files:
            if "两只老虎" in f.name or "15" in f.name:
                test_file = str(f)
                break
        if not test_file:
            test_file = str(audio_files[0])

    print(f"Test file: {test_file}\n")

    # Run test with 'large-v3' model for best Chinese accuracy
    try:
        # result = test_transcription(test_file, model_size="base")
        result = test_transcription(test_file, model_size="large-v3")

        # If LLM available, also create enhanced version
        if llm_available:
            srt_path = Path(test_file).with_suffix(".test.srt")
            if srt_path.exists():
                print("\n" + "-" * 40)
                print("Creating LLM-enhanced version...")
                process_srt_with_llm(str(srt_path))

        print("\n" + "=" * 60)
        print("  TEST PASSED ✓")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Check timestamp accuracy against the audio")
        print("  2. If good, use 'large-v3' model for production")
        print("  3. Build full batch processing script")
        if llm_available:
            print("  4. Check the .enhanced.srt file for pinyin/English")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
