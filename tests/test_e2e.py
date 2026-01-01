"""
End-to-end integration tests for baobao.

These tests require:
- Real audio files in the songs/ directory
- Ollama running with qwen3:4b model (for LLM tests)
- GPU recommended for faster transcription

Run with: pytest tests/test_e2e.py -v -s
Skip slow tests: pytest tests/test_e2e.py -v -m "not slow"
"""

import os
from pathlib import Path

import pytest

# Markers for test categorization
pytestmark = [pytest.mark.e2e]


def ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def has_audio_files() -> bool:
    """Check if test audio files exist."""
    songs_dir = Path(__file__).parent.parent / "songs"
    return any(songs_dir.glob("*.mp3"))


# Skip conditions
skip_no_ollama = pytest.mark.skipif(
    not ollama_available(), reason="Ollama not available"
)

skip_no_audio = pytest.mark.skipif(
    not has_audio_files(), reason="No audio files in songs/ directory"
)


class TestTranscriptionE2E:
    """End-to-end transcription tests."""

    @skip_no_audio
    @pytest.mark.slow
    def test_transcribe_real_audio_base_model(self, sample_audio_path, tmp_path):
        """Test transcription with base model (faster)."""
        from baobao.transcribe import transcribe_audio

        output_path = tmp_path / "output.srt"

        result = transcribe_audio(
            audio_path=sample_audio_path,
            output_path=output_path,
            model_size="base",  # Faster for testing
            format="srt",
            word_highlight=False,
        )

        assert result.exists()
        content = result.read_text(encoding="utf-8")

        # Verify SRT structure
        assert "-->" in content  # Has timestamps
        lines = content.strip().split("\n")
        assert len(lines) > 3  # Has some content

        # Should contain Chinese characters
        chinese_chars = [c for c in content if "\u4e00" <= c <= "\u9fff"]
        assert len(chinese_chars) > 0, "No Chinese characters in transcription"

    @skip_no_audio
    @pytest.mark.slow
    def test_transcribe_with_word_highlighting(self, sample_audio_path, tmp_path):
        """Test transcription with karaoke-style word highlighting."""
        from baobao.transcribe import transcribe_audio

        output_path = tmp_path / "output.srt"

        result = transcribe_audio(
            audio_path=sample_audio_path,
            output_path=output_path,
            model_size="base",
            format="srt",
            word_highlight=True,
        )

        content = result.read_text(encoding="utf-8")

        # Should have font tags for highlighting
        assert '<font color="#00ff00">' in content

    @skip_no_audio
    @pytest.mark.slow
    def test_transcribe_lrc_format(self, sample_audio_path, tmp_path):
        """Test LRC format output."""
        from baobao.transcribe import transcribe_audio

        output_path = tmp_path / "output.lrc"

        result = transcribe_audio(
            audio_path=sample_audio_path,
            output_path=output_path,
            model_size="base",
            format="lrc",
        )

        content = result.read_text(encoding="utf-8")

        # LRC format: [MM:SS.ss]lyrics
        assert content.startswith("[")
        assert "]" in content


class TestEnhancementE2E:
    """End-to-end enhancement tests."""

    @skip_no_ollama
    def test_enhance_srt_full_format(self, temp_srt_file):
        """Test enhancing SRT with full translations."""
        from baobao.enhance import OutputFormat, enhance_srt

        result = enhance_srt(
            srt_path=temp_srt_file,
            output_format=OutputFormat.FULL,
        )

        assert result.exists()
        content = result.read_text(encoding="utf-8")

        # Should have original Chinese
        assert "你是我陽光" in content or "你是我阳光" in content

        # Should have pinyin (look for tone marks or pinyin patterns)
        has_pinyin = any(c in content for c in "āáǎàēéěèīíǐìōóǒòūúǔù")
        # Or check for common pinyin syllables
        has_pinyin_pattern = any(
            p in content.lower() for p in ["ni", "shi", "wo", "yang", "guang"]
        )
        assert has_pinyin or has_pinyin_pattern, "No pinyin found in output"

    @skip_no_ollama
    def test_enhance_srt_emoji_format(self, temp_srt_file):
        """Test enhancing SRT with emoji format."""
        from baobao.enhance import OutputFormat, enhance_srt

        result = enhance_srt(
            srt_path=temp_srt_file,
            output_format=OutputFormat.EMOJI,
        )

        content = result.read_text(encoding="utf-8")

        # Should contain Chinese and likely some emoji
        assert "陽光" in content or "阳光" in content

    @skip_no_ollama
    def test_enhance_srt_learn_format(self, temp_srt_file):
        """Test enhancing SRT with learning format."""
        from baobao.enhance import OutputFormat, enhance_srt

        result = enhance_srt(
            srt_path=temp_srt_file,
            output_format=OutputFormat.LEARN,
        )

        content = result.read_text(encoding="utf-8")

        # Learning format should have Chinese
        assert "你" in content or "我" in content

    @skip_no_ollama
    def test_enhance_existing_enhanced_srt(self, sample_srt_path, tmp_path):
        """Test enhancing the actual test SRT file."""
        from baobao.enhance import OutputFormat, enhance_srt

        output_path = tmp_path / "enhanced.srt"

        result = enhance_srt(
            srt_path=sample_srt_path,
            output_path=output_path,
            output_format=OutputFormat.FULL,
        )

        assert result.exists()
        content = result.read_text(encoding="utf-8")

        # Should be a valid SRT
        assert "-->" in content
        # Should have multiple entries
        assert content.count("-->") >= 3


class TestFullPipelineE2E:
    """End-to-end tests for the complete pipeline."""

    @skip_no_audio
    @skip_no_ollama
    @pytest.mark.slow
    def test_full_pipeline(self, sample_audio_path, tmp_path):
        """Test complete pipeline: transcribe -> enhance."""
        from baobao.enhance import OutputFormat, enhance_srt
        from baobao.transcribe import transcribe_audio

        # Step 1: Transcribe
        srt_path = tmp_path / "transcribed.srt"
        transcribe_audio(
            audio_path=sample_audio_path,
            output_path=srt_path,
            model_size="base",
            format="srt",
        )

        assert srt_path.exists()

        # Step 2: Enhance
        enhanced_path = enhance_srt(
            srt_path=srt_path,
            output_format=OutputFormat.FULL,
        )

        assert enhanced_path.exists()
        content = enhanced_path.read_text(encoding="utf-8")

        # Final output should have:
        # - Timestamps
        assert "-->" in content
        # - Chinese characters
        chinese_chars = [c for c in content if "\u4e00" <= c <= "\u9fff"]
        assert len(chinese_chars) > 0
        # - Multiple lines per entry (Chinese + pinyin + English)
        entries = content.split("\n\n")
        multi_line_entries = [e for e in entries if e.count("\n") >= 3]
        assert len(multi_line_entries) > 0


class TestKnownPhraseAccuracy:
    """Tests for accuracy on known phrases."""

    @skip_no_ollama
    @pytest.mark.parametrize(
        "chinese,expected_pinyin_part,expected_english_parts",
        [
            ("你好", "hǎo", ["hello", "hi"]),
            ("謝謝", "xiè", ["thank"]),
            ("我愛你", "ài", ["love"]),
        ],
    )
    def test_phrase_interpretation(
        self, chinese, expected_pinyin_part, expected_english_parts
    ):
        """Test that common phrases are interpreted correctly."""
        from baobao.enhance import ChineseEnhancer

        enhancer = ChineseEnhancer()

        # Skip if can't connect
        if not enhancer.check_connection():
            pytest.skip("Ollama not available")

        result = enhancer.interpret_phrase(chinese)

        # Check pinyin contains expected part (case insensitive)
        pinyin_lower = result["pinyin"].lower()
        assert (
            expected_pinyin_part.lower() in pinyin_lower
            or expected_pinyin_part.replace("ǎ", "a")
            .replace("è", "e")
            .replace("ì", "i")
            .replace("ài", "ai")
            in pinyin_lower
        ), f"Expected '{expected_pinyin_part}' in '{result['pinyin']}'"

        # Check English contains at least one expected word
        english_lower = result["english"].lower()
        found = any(exp in english_lower for exp in expected_english_parts)
        assert (
            found
        ), f"Expected one of {expected_english_parts} in '{result['english']}'"


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self):
        """Test CLI help command."""
        from typer.testing import CliRunner

        from baobao.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "baobao" in result.stdout.lower() or "chinese" in result.stdout.lower()

    def test_cli_version(self):
        """Test CLI version command."""
        from typer.testing import CliRunner

        from baobao.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_cli_transcribe_help(self):
        """Test transcribe command help."""
        from typer.testing import CliRunner

        from baobao.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["transcribe", "--help"])

        assert result.exit_code == 0
        assert "audio" in result.stdout.lower()

    def test_cli_enhance_help(self):
        """Test enhance command help."""
        from typer.testing import CliRunner

        from baobao.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["enhance", "--help"])

        assert result.exit_code == 0
        assert "srt" in result.stdout.lower()

    def test_cli_transcribe_missing_file(self):
        """Test transcribe with missing file."""
        from typer.testing import CliRunner

        from baobao.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["transcribe", "/nonexistent/file.mp3"])

        assert result.exit_code != 0
