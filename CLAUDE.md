# Baobao - AI Assistant Guide

This document provides context for AI assistants working on the Baobao project.

## Project Overview

**Baobao** (宝宝 - "baby/treasure") is a Chinese lyrics transcription and learning tool that creates time-synced subtitles with pinyin romanization and English translations. Primary use case: helping children and language learners sing along with Chinese songs.

**Version**: 0.1.0 (Early Release)
**Status**: Active development, feature-complete
**Language**: Python 3.12+

## Architecture

### Core Modules (1,199 lines production code)

```
baobao/
├── transcribe.py    # Whisper-based audio transcription (254 lines)
├── enhance.py       # LLM-based pinyin/translation enhancement (428 lines)
├── cli.py          # Typer CLI interface (510 lines)
└── __init__.py     # Package exports

tests/              # 857 lines of tests
├── test_transcribe.py
├── test_enhance.py
└── test_e2e.py
```

### 1. Transcription Pipeline (`transcribe.py`)

**Key Classes**:
- `TranscriptionConfig`: Whisper model configuration
- `LyricSegment`: Dataclass for timed lyrics with word-level detail
- `Transcriber`: Main transcription engine

**Dependencies**:
- `stable-ts` - Word-level timestamp extraction
- `faster-whisper` - Optimized Whisper inference

**Features**:
- Lazy-loads Whisper models (tiny/base/small/medium/large-v3)
- Voice Activity Detection (VAD) for music handling
- Word-level timestamps for karaoke highlighting
- Outputs: SRT or LRC format

**Default Config**:
```python
model_size: "large-v3"
language: "zh"
vad_filter: True
beam_size: 5
word_timestamps: True
```

### 2. Enhancement Pipeline (`enhance.py`)

**Key Classes**:
- `EnhanceConfig`: LLM configuration
- `ChineseEnhancer`: Instructor + Ollama integration
- `OutputFormat`: Enum (FULL, EMOJI, LEARN)

**Pydantic Models** (for structured LLM output):
- `WordDetail`: Character-level pinyin + English
- `PhraseInterpretation`: Phrase-level analysis with grammar/culture notes
- `LearningLyricLine`: Pedagogy-optimized output

**Features**:
- Phrase-level caching (avoids redundant LLM calls)
- Multiple output formats for different learning contexts
- Graceful fallback when LLM unavailable
- HTML tag stripping for compatibility

**Default Config**:
```python
ollama_url: "http://localhost:11434"
model_name: "qwen3:4b"
output_format: OutputFormat.FULL
```

### 3. CLI Interface (`cli.py`)

**Commands**:
```bash
baobao transcribe <audio>           # Transcribe to SRT/LRC
baobao enhance <srt>                # Add pinyin/translation
baobao process <audio>              # Full pipeline
baobao batch <directory>            # Batch processing
baobao preview <audio> --srt <file> # mpv playback
baobao --version
```

**Key Features**:
- Rich console output with progress bars
- Karaoke mode (`--karaoke`) for word highlighting
- Flexible model selection
- Error tracking in batch mode

## Output Formats

All formats generate 3-line subtitle entries with timestamps:

### FULL (Standard)
```srt
1
00:00:01,000 --> 00:00:03,000
你是我陽光
nǐ shì wǒ yáng guāng
(You are my sunlight)
```

### EMOJI (Kid-Friendly)
```srt
1
00:00:01,000 --> 00:00:03,000
你是我陽光
nǐ shì wǒ yáng guāng
(☀️ sunshine)
```

### LEARN (Pedagogical)
```srt
1
00:00:01,000 --> 00:00:03,000
nǐ shì wǒ yáng guāng
你是我陽光
☀️ Like the sun! Hold up emoji and say together!
```

### Karaoke Mode
Word-level highlighting with HTML color tags:
```html
<font color="#00ff00">你</font> 是 我 陽光
```

## Development Workflow

### Setup
```bash
# Install dependencies
uv sync

# Install Ollama (for enhancement)
# Download from https://ollama.ai
ollama pull qwen3:4b

# Run tests
uv run pytest
uv run pytest -m e2e  # E2E tests only
uv run pytest --cov   # With coverage
```

### Testing Strategy

**Test Markers**:
- `@pytest.mark.e2e` - End-to-end tests (require audio/Ollama)
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.requires_ollama` - Requires Ollama server

**Test Coverage**:
- Unit tests: Config validation, data models, parsing logic
- Integration tests: Transcriber/Enhancer initialization
- E2E tests: Full pipeline with real audio files

**Test Data**:
- Sample audio: `/songs/你是我陽光 You Are My Sunshine.mp3`
- Test outputs: `/test_output/`

### Code Quality Standards

**Current State**:
- Zero TODO/FIXME/HACK/BUG markers
- Proper error handling with graceful fallbacks
- Type hints throughout
- Comprehensive docstrings

**When Contributing**:
- Maintain clean separation between transcribe/enhance/CLI
- Add tests for new features
- Use Pydantic for data validation
- Follow existing naming conventions
- Keep dependencies minimal

## Common Tasks

### Adding a New Output Format

1. Add enum to `OutputFormat` in `enhance.py`
2. Create Pydantic model if needed
3. Update `ChineseEnhancer._enhance_line()` with new format logic
4. Add CLI flag in `cli.py`
5. Add tests in `test_enhance.py` and `test_e2e.py`

### Supporting a New LLM Provider

1. Add config class in `enhance.py`
2. Create adapter following `ChineseEnhancer` pattern
3. Update CLI to accept provider selection
4. Add integration tests

### Adding a New Transcription Model

1. Update `MODEL_SIZES` dict in `transcribe.py`
2. Test with various audio samples
3. Document performance characteristics

## Key Design Decisions

1. **Why Ollama?** Local-first approach for privacy and cost (no API keys)
2. **Why stable-ts over vanilla Whisper?** Word-level timestamps for karaoke
3. **Why SRT over custom format?** Universal compatibility with media players
4. **Why caching?** LLM calls are slow; repeated phrases common in songs
5. **Why Pydantic?** Structured output from LLMs requires strict validation

## Performance Characteristics

- **Transcription**: ~1-2 minutes for 3-minute song (large-v3 on CPU)
- **Enhancement**: ~5-10 seconds per line with qwen3:4b
- **Caching hit rate**: ~60-80% for repetitive lyrics

## Known Limitations

1. **Ollama required**: Enhancement needs local LLM server
2. **Chinese-focused**: Other languages untested
3. **Music handling**: VAD helps but not perfect for heavy instrumentation
4. **Accuracy**: Whisper quality depends on audio clarity and model size

## Dependencies

**Core**:
- stable-ts>=2.16.0
- faster-whisper>=1.0.0
- typer>=0.12.0
- rich>=13.0.0
- instructor>=1.0.0
- pydantic>=2.0.0

**Optional Runtime**:
- Ollama (enhancement)
- mpv (preview)

**Dev**:
- pytest>=8.0.0
- pytest-cov>=4.0.0

## File Naming Conventions

```
song.mp3              # Original audio
song.srt              # Transcribed lyrics
song.enhanced.srt     # With pinyin + English (FULL)
song.emoji.srt        # Emoji format
song.learn.srt        # Learning format
song.karaoke.srt      # With word highlighting
song.lrc              # LRC format (alternative to SRT)
```

## Troubleshooting

**"Could not connect to Ollama"**
- Start Ollama: `ollama serve`
- Pull model: `ollama pull qwen3:4b`

**Poor transcription quality**
- Try larger model: `--model large-v3`
- Check audio quality (clear vocals)
- Adjust VAD settings if needed

**LLM output parsing errors**
- Handled gracefully with fallback
- Check Ollama model compatibility
- Try different model (qwen2.5 also works)

## Future Enhancement Ideas

- [ ] Web interface for batch processing
- [ ] Support for other languages (Japanese, Korean)
- [ ] Custom LLM prompts via config
- [ ] Cloud LLM provider support (OpenAI, Anthropic)
- [ ] Audio preprocessing (noise reduction, vocal isolation)
- [ ] Export to Anki flashcards
- [ ] Mobile app integration

## Resources

- [Whisper Documentation](https://github.com/openai/whisper)
- [stable-ts Documentation](https://github.com/jianfch/stable-ts)
- [Ollama Documentation](https://ollama.ai/docs)
- [SRT Format Specification](https://en.wikipedia.org/wiki/SubRip)
