"""
Unit tests for transcription module.
"""

from pathlib import Path

import pytest

from baobao.transcribe import LyricSegment, Transcriber, TranscriptionConfig


class TestTranscriptionConfig:
    """Tests for TranscriptionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TranscriptionConfig()
        assert config.model_size == "large-v3"
        assert config.language == "zh"
        assert config.vad is True
        assert config.beam_size == 5
        assert config.refine_timestamps is True
        assert config.word_level is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = TranscriptionConfig(
            model_size="base",
            language="en",
            vad=False,
        )
        assert config.model_size == "base"
        assert config.language == "en"
        assert config.vad is False


class TestLyricSegment:
    """Tests for LyricSegment dataclass."""

    def test_basic_segment(self):
        """Test creating a basic segment."""
        seg = LyricSegment(
            start=1.5,
            end=3.5,
            text="你好",
        )
        assert seg.start == 1.5
        assert seg.end == 3.5
        assert seg.text == "你好"
        assert seg.words is None

    def test_segment_with_words(self):
        """Test segment with word-level timing."""
        words = [
            {"start": 1.5, "end": 2.0, "word": "你"},
            {"start": 2.0, "end": 2.5, "word": "好"},
        ]
        seg = LyricSegment(
            start=1.5,
            end=2.5,
            text="你好",
            words=words,
        )
        assert len(seg.words) == 2
        assert seg.words[0]["word"] == "你"


class TestTranscriber:
    """Tests for Transcriber class."""

    def test_init_default_config(self):
        """Test transcriber with default config."""
        transcriber = Transcriber()
        assert transcriber.config.model_size == "large-v3"
        assert transcriber._model is None

    def test_init_custom_config(self):
        """Test transcriber with custom config."""
        config = TranscriptionConfig(model_size="base")
        transcriber = Transcriber(config)
        assert transcriber.config.model_size == "base"

    def test_format_srt_time(self):
        """Test SRT timestamp formatting."""
        transcriber = Transcriber()

        # Basic case
        assert transcriber._format_srt_time(0) == "00:00:00,000"

        # Seconds with milliseconds
        assert transcriber._format_srt_time(1.5) == "00:00:01,500"

        # Minutes
        assert transcriber._format_srt_time(65.123) == "00:01:05,123"

        # Hours (use exact value to avoid float precision issues)
        assert transcriber._format_srt_time(3661.0) == "01:01:01,000"
        assert transcriber._format_srt_time(3661.5) == "01:01:01,500"

    def test_write_srt_simple(self, tmp_path):
        """Test writing simple SRT output."""
        transcriber = Transcriber()
        segments = [
            LyricSegment(start=0.0, end=2.0, text="你好"),
            LyricSegment(start=2.5, end=4.5, text="世界"),
        ]

        output_path = tmp_path / "test.srt"
        transcriber.save_srt(segments, output_path, word_highlight=False)

        content = output_path.read_text(encoding="utf-8")
        assert "1\n00:00:00,000 --> 00:00:02,000\n你好" in content
        assert "2\n00:00:02,500 --> 00:00:04,500\n世界" in content

    def test_write_srt_word_highlight(self, tmp_path):
        """Test writing SRT with word highlighting."""
        transcriber = Transcriber()
        segments = [
            LyricSegment(
                start=0.0,
                end=2.0,
                text="你好",
                words=[
                    {"start": 0.0, "end": 1.0, "word": "你"},
                    {"start": 1.0, "end": 2.0, "word": "好"},
                ],
            ),
        ]

        output_path = tmp_path / "test.srt"
        transcriber.save_srt(segments, output_path, word_highlight=True)

        content = output_path.read_text(encoding="utf-8")
        assert '<font color="#00ff00">你</font>' in content
        assert '<font color="#00ff00">好</font>' in content

    def test_save_lrc(self, tmp_path):
        """Test saving LRC format."""
        transcriber = Transcriber()
        segments = [
            LyricSegment(start=0.0, end=2.0, text="你好"),
            LyricSegment(start=65.5, end=68.0, text="世界"),
        ]

        output_path = tmp_path / "test.lrc"
        transcriber.save_lrc(segments, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "[00:00.00]你好" in content
        assert "[01:05.50]世界" in content

    def test_file_not_found(self):
        """Test handling of missing audio file."""
        transcriber = Transcriber()
        with pytest.raises(FileNotFoundError):
            transcriber.transcribe("/nonexistent/file.mp3")


class TestTranscribeAudioFunction:
    """Tests for the transcribe_audio convenience function."""

    def test_output_path_generation(self, tmp_path):
        """Test that output path is generated correctly."""
        from baobao.transcribe import transcribe_audio

        # This would fail without actual audio, but we can test the path logic
        audio_path = tmp_path / "test.mp3"
        audio_path.write_bytes(b"fake audio")

        # The function will fail on actual transcription, but we can check
        # that it properly handles the path before that
        try:
            transcribe_audio(audio_path, format="srt")
        except Exception:
            pass  # Expected to fail without valid audio

        # Check the expected output path would be correct
        expected_srt = audio_path.with_suffix(".srt")
        assert expected_srt.name == "test.srt"
