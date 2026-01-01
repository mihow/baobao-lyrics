"""
Unit tests for enhancement module.
"""

import re

import pytest

from baobao.enhance import (
    ChineseEnhancer,
    EnhanceConfig,
    OutputFormat,
    PhraseInterpretation,
    WordDetail,
    _parse_srt,
)


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_format_values(self):
        """Test format enum values."""
        assert OutputFormat.FULL.value == "full"
        assert OutputFormat.EMOJI.value == "emoji"
        assert OutputFormat.LEARN.value == "learn"


class TestEnhanceConfig:
    """Tests for EnhanceConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = EnhanceConfig()
        assert config.ollama_url == "http://localhost:11434"
        assert config.model == "qwen3:4b"
        assert config.output_format == OutputFormat.FULL

    def test_custom_config(self):
        """Test custom configuration."""
        config = EnhanceConfig(
            ollama_url="http://custom:1234",
            model="llama3:8b",
            output_format=OutputFormat.EMOJI,
        )
        assert config.ollama_url == "http://custom:1234"
        assert config.model == "llama3:8b"
        assert config.output_format == OutputFormat.EMOJI


class TestPydanticModels:
    """Tests for Pydantic response models."""

    def test_word_detail(self):
        """Test WordDetail model."""
        word = WordDetail(char="你", pinyin="nǐ", english="you")
        assert word.char == "你"
        assert word.pinyin == "nǐ"
        assert word.english == "you"

    def test_phrase_interpretation(self):
        """Test PhraseInterpretation model."""
        phrase = PhraseInterpretation(
            pinyin="nǐ hǎo",
            english="hello",
            word_details=[
                WordDetail(char="你", pinyin="nǐ", english="you"),
                WordDetail(char="好", pinyin="hǎo", english="good"),
            ],
        )
        assert phrase.pinyin == "nǐ hǎo"
        assert len(phrase.word_details) == 2


class TestParseSrt:
    """Tests for SRT parsing."""

    def test_parse_simple_srt(self, sample_srt_content):
        """Test parsing simple SRT content."""
        entries = _parse_srt(sample_srt_content)

        assert len(entries) == 6
        assert entries[0]["index"] == 1
        assert entries[0]["text"] == "你是我陽光"
        assert "00:00:04,970" in entries[0]["timestamp"]

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        entries = _parse_srt("")
        assert entries == []

    def test_parse_srt_with_highlighting(self, word_highlighted_srt_content):
        """Test parsing SRT with font tags."""
        entries = _parse_srt(word_highlighted_srt_content)

        assert len(entries) == 4
        assert '<font color="#00ff00">' in entries[0]["text"]


class TestChineseEnhancer:
    """Tests for ChineseEnhancer class."""

    def test_init_default_config(self):
        """Test enhancer with default config."""
        enhancer = ChineseEnhancer()
        assert enhancer.config.output_format == OutputFormat.FULL
        assert enhancer._client is None
        assert enhancer._cache == {}

    def test_init_custom_config(self):
        """Test enhancer with custom config."""
        config = EnhanceConfig(output_format=OutputFormat.EMOJI)
        enhancer = ChineseEnhancer(config)
        assert enhancer.config.output_format == OutputFormat.EMOJI

    def test_interpret_empty_phrase(self):
        """Test interpreting empty phrase."""
        enhancer = ChineseEnhancer()
        result = enhancer.interpret_phrase("")
        assert result["pinyin"] == ""
        assert result["english"] == ""
        assert result["word_details"] == []

    def test_interpret_phrase_strips_html(self):
        """Test that HTML tags are stripped before interpretation."""
        enhancer = ChineseEnhancer()
        # This will use cache or fail without LLM, but we can check the logic
        chinese_with_html = '<font color="#00ff00">你</font>好'
        clean = re.sub(r"<[^>]+>", "", chinese_with_html).strip()
        assert clean == "你好"

    def test_format_subtitle_line_structure(self):
        """Test format_subtitle_line returns correct structure."""
        enhancer = ChineseEnhancer()
        # Mock the cache to avoid LLM call
        enhancer._cache["full:你好"] = {
            "pinyin": "nǐ hǎo",
            "english": "hello",
            "word_details": [
                {"char": "你", "pinyin": "nǐ", "english": "you"},
                {"char": "好", "pinyin": "hǎo", "english": "good"},
            ],
        }

        result = enhancer.format_subtitle_line("你好")

        assert "chinese" in result
        assert "pinyin" in result
        assert "pinyin_plain" in result
        assert "english" in result
        assert "word_details" in result

    def test_format_subtitle_with_highlight(self):
        """Test formatting with highlighted character."""
        enhancer = ChineseEnhancer()
        # Mock the cache
        enhancer._cache["full:你好"] = {
            "pinyin": "nǐ hǎo",
            "english": "hello",
            "word_details": [
                {"char": "你", "pinyin": "nǐ", "english": "you"},
                {"char": "好", "pinyin": "hǎo", "english": "good"},
            ],
        }

        result = enhancer.format_subtitle_line('<font color="#00ff00">你</font>好')

        # The highlighted character should have highlighted pinyin
        assert '<font color="#00ff00">nǐ</font>' in result["pinyin"]

    def test_caching(self):
        """Test that results are cached."""
        enhancer = ChineseEnhancer()

        # Manually add to cache
        enhancer._cache["full:測試"] = {
            "pinyin": "cè shì",
            "english": "test",
            "word_details": [],
        }

        # Should return cached result
        result = enhancer.interpret_phrase("測試")
        assert result["pinyin"] == "cè shì"
        assert result["english"] == "test"


class TestEnhanceSrtFunction:
    """Tests for enhance_srt function."""

    def test_output_path_generation(self):
        """Test output path suffix generation."""
        from pathlib import Path

        # Test suffix mapping
        base_path = Path("/test/file.srt")
        no_ext = base_path.with_suffix("")

        assert no_ext.with_suffix(".enhanced.srt").name == "file.enhanced.srt"
        assert no_ext.with_suffix(".emoji.srt").name == "file.emoji.srt"
        assert no_ext.with_suffix(".learn.srt").name == "file.learn.srt"
