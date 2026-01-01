# 🐼 Baobao

Chinese lyrics transcription and learning tool - create time-synced subtitles with pinyin and translations.

## Features

- **Transcription**: Convert Chinese audio to time-synced SRT/LRC subtitles using Whisper
- **Word-level timing**: Karaoke-style word highlighting for sing-along
- **Pinyin**: Automatic romanization with tone marks
- **Translations**: LLM-powered English translations (via Ollama)
- **Learning modes**: Emoji-based (kid-friendly) or pedagogy-optimized formats

## Installation

```bash
# Install with UV (recommended)
uv sync

# Or with pip
pip install -e .
```

### Requirements

- Python 3.10+
- For transcription: `stable-ts` + `faster-whisper` (auto-installed)
- For enhancement: [Ollama](https://ollama.ai) running locally with `qwen3:4b` or similar Chinese-capable model
- For preview: [mpv](https://mpv.io/) media player (`sudo apt install mpv`)

## Usage

### Basic Transcription

```bash
# Transcribe audio to SRT with timestamps
baobao transcribe song.mp3

# Use smaller model for faster processing
baobao transcribe song.mp3 --model base

# Enable karaoke-style word highlighting
baobao transcribe song.mp3 --karaoke
```

### Enhance with Translations

```bash
# Add pinyin + English translations to existing SRT
baobao enhance lyrics.srt

# Emoji format (kid-friendly, visual)
baobao enhance lyrics.srt --format emoji

# Learning format (pinyin-first with tips)
baobao enhance lyrics.srt --format learn
```

### Full Pipeline

```bash
# Transcribe + enhance in one command
baobao process song.mp3

# With learning format
baobao process song.mp3 --format learn

# Just transcribe (skip LLM enhancement)
baobao process song.mp3 --skip-enhance
```

### Batch Processing

```bash
# Process all MP3s in a folder
baobao batch ./songs/

# Process WAV files
baobao batch ./songs/ --pattern "*.wav"
```

### Preview with Synced Subtitles

```bash
# Preview audio with subtitles (uses mpv)
baobao preview song.mp3

# Specify a subtitle file
baobao preview song.mp3 -s song.enhanced.srt

# Or use mpv directly
mpv --sub-file=song.srt song.mp3
```

## Output Formats

### Standard (--format full)

```
你是我陽光
nǐ shì wǒ yáng guāng
(You are my sunshine)
```

### Emoji (--format emoji)

```
你是我陽光
nǐ shì wǒ yáng guāng
(☀️ sunshine)
```

### Learning (--format learn)

```
nǐ shì wǒ yáng guāng
你是我陽光
(🎵 "nee sure woh yahng gwahng")
```

## Whisper Models

| Model    | Size   | Speed   | Accuracy  | Best For    |
| -------- | ------ | ------- | --------- | ----------- |
| tiny     | ~40MB  | Fastest | Lower     | Quick tests |
| base     | ~140MB | Fast    | Good      | Development |
| small    | ~460MB | Medium  | Better    | General use |
| medium   | ~1.5GB | Slow    | Very good | Quality     |
| large-v3 | ~3GB   | Slowest | Best      | Production  |

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run CLI directly
uv run baobao --help
```

## License

MIT
