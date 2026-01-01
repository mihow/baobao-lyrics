# Task 5: Embed Time-Synced Lyrics in Audio Files

**Status**: Needs validation and player compatibility testing
**Complexity**: High
**Dependencies**: Tasks 2-3 (need finalized lyric format)

## Objective

Create audio files with embedded time-synced lyrics using industry-standard metadata formats. Support MP3 (ID3v2 SYLT), M4A, and MP4 formats, with focus on maximum player compatibility.

## Background Research

### Supported Formats

**1. MP3 with ID3v2 SYLT Frame (RECOMMENDED)**
- **Format**: Synchronized Lyrics/Text (SYLT)
- **Spec**: ID3v2.3.0 and ID3v2.4.0
- **Timing**: Milliseconds as integers
- **Data structure**: List of (text, timestamp_ms) tuples
- **Encoding**: UTF-8, UTF-16, Latin-1
- **Language**: ISO 639-2 three-letter code (e.g., "zho" for Chinese)
- **Compatibility**: Widest support among synchronized lyrics formats

**2. MP3 with ID3v2 USLT Frame (Fallback)**
- **Format**: Unsynchronized lyrics (static text)
- **Use**: Fallback for players without SYLT support
- **Can include both**: SYLT for sync + USLT for compatibility

**3. M4A/MP4/AAC**
- **Limited**: Only `©lyr` atom (unsynchronized)
- **No standard**: For time-synced lyrics
- **Recommendation**: Convert to MP3 for sync support, or use external .lrc files

### Python Library: Mutagen

**Why Mutagen**:
- Multi-format support (MP3, M4A, FLAC, OGG, etc.)
- Complete SYLT frame support
- Active development (last update: 2024)
- Python 3.10+ compatible
- Zero external dependencies
- Lossless metadata editing

**Installation**:
```toml
# Add to pyproject.toml
mutagen>=1.47.0
```

**Basic usage**:
```python
from mutagen.id3 import ID3, SYLT, USLT, Encoding

# Load MP3
audio = ID3("song.mp3")

# Add synchronized lyrics
audio.add(SYLT(
    encoding=Encoding.UTF8,
    lang="zho",  # Chinese
    format=2,  # Milliseconds
    type=1,  # Lyrics content
    desc="",  # Description
    text=[
        ("你是我陽光", 1000),
        ("nǐ shì wǒ yáng guāng", 1000),
        ("(You are my sunlight)", 1000),
        ("下一行", 4000),
    ]
))

# Save with ID3v2.4
audio.save(v2_version=4)
```

### Player Compatibility

**Players supporting SYLT**:
- **Desktop**: Winamp (with plugin), MusicBee, JetAudio, Lollypop (GNOME)
- **Mobile**: Stage Traxx 3 (iOS), some Android players
- **Limited**: VLC (partial), mpv (requires scripting)

**Reality check**: SYLT support is LIMITED compared to external .lrc files. Most modern players prefer:
1. External .lrc files (best compatibility)
2. Online lyrics services
3. USLT for static lyrics
4. SYLT as niche feature

### Recommended Strategy

**Dual-format approach** for maximum compatibility:
1. **Primary**: Generate external TTML/LRC files (universal support)
2. **Bonus**: Embed SYLT in MP3 for compatible players
3. **Fallback**: Embed USLT for all players

## Implementation Plan

### 1. Create Lyrics Embedding Module

**New file**: `/home/michael/Projects/Leon/baobao/baobao/embed.py`

**Key components**:
```python
from dataclasses import dataclass
from pathlib import Path
from mutagen.id3 import ID3, SYLT, USLT, Encoding
from mutagen.mp4 import MP4
from baobao.transcribe import LyricSegment

@dataclass
class EmbedConfig:
    """Configuration for lyrics embedding."""
    include_sylt: bool = True  # Synchronized lyrics
    include_uslt: bool = True  # Unsynchronized lyrics (fallback)
    language: str = "zho"  # ISO 639-2 code
    encoding: Encoding = Encoding.UTF8

    # Format options
    include_pinyin: bool = True
    include_translation: bool = True
    separate_lines: bool = True  # Each lyric type on separate timestamp


class LyricsEmbedder:
    """Embed time-synced lyrics into audio files."""

    def __init__(self, config: EmbedConfig | None = None):
        self.config = config or EmbedConfig()

    def embed_mp3(self, mp3_path: str, segments: list[LyricSegment],
                  output_path: str | None = None):
        """Embed SYLT and USLT into MP3 file."""
        # Convert segments to SYLT format
        sylt_data = self._segments_to_sylt(segments)
        uslt_data = self._segments_to_uslt(segments)

        # Load or create ID3 tags
        try:
            audio = ID3(mp3_path)
        except:
            audio = ID3()

        # Clear existing lyrics
        audio.delall("SYLT")
        audio.delall("USLT")

        # Add SYLT (synchronized)
        if self.config.include_sylt:
            audio.add(SYLT(
                encoding=self.config.encoding,
                lang=self.config.language,
                format=2,  # Milliseconds
                type=1,  # Lyrics
                desc="",
                text=sylt_data
            ))

        # Add USLT (unsynchronized fallback)
        if self.config.include_uslt:
            audio.add(USLT(
                encoding=self.config.encoding,
                lang=self.config.language,
                desc="",
                text=uslt_data
            ))

        # Save
        output = output_path or mp3_path
        audio.save(output, v2_version=4)

    def embed_m4a(self, m4a_path: str, segments: list[LyricSegment],
                  output_path: str | None = None):
        """Embed unsynchronized lyrics into M4A file."""
        # M4A only supports static lyrics
        audio = MP4(m4a_path)
        audio["©lyr"] = [self._segments_to_uslt(segments)]
        audio.save(output_path or m4a_path)

    def _segments_to_sylt(self, segments: list[LyricSegment]) -> list[tuple[str, int]]:
        """Convert LyricSegments to SYLT format: [(text, ms), ...]"""
        sylt_data = []

        for seg in segments:
            timestamp_ms = int(seg.start * 1000)

            # Add Chinese text
            sylt_data.append((seg.text, timestamp_ms))

            # Add pinyin if available and enabled
            if self.config.include_pinyin and hasattr(seg, 'pinyin') and seg.pinyin:
                sylt_data.append((seg.pinyin, timestamp_ms))

            # Add translation if available and enabled
            if self.config.include_translation and hasattr(seg, 'translation') and seg.translation:
                sylt_data.append((seg.translation, timestamp_ms))

        return sylt_data

    def _segments_to_uslt(self, segments: list[LyricSegment]) -> str:
        """Convert LyricSegments to unsynchronized lyrics (plain text)."""
        lines = []
        for seg in segments:
            lines.append(seg.text)
            if self.config.include_pinyin and hasattr(seg, 'pinyin') and seg.pinyin:
                lines.append(seg.pinyin)
            if self.config.include_translation and hasattr(seg, 'translation') and seg.translation:
                lines.append(seg.translation)
            lines.append("")  # Blank line between segments
        return "\n".join(lines)


def embed_lyrics(
    audio_path: str,
    lyrics_file: str,
    output_path: str | None = None,
    config: EmbedConfig | None = None
) -> str:
    """
    Embed lyrics into audio file.

    Supports:
    - MP3: SYLT (synchronized) + USLT (fallback)
    - M4A/MP4: USLT only (no sync support)

    Args:
        audio_path: Path to audio file
        lyrics_file: Path to TTML, SRT, or LRC file
        output_path: Optional output path (default: overwrite original)
        config: Embedding configuration

    Returns:
        Path to output file
    """
    # Auto-detect format and parse lyrics
    # Convert to LyricSegments
    # Embed based on audio format
    pass
```

### 2. Add CLI Command

**File**: `/home/michael/Projects/Leon/baobao/baobao/cli.py`

**New command**:
```python
@app.command()
def embed(
    audio: str = typer.Argument(..., help="Audio file (MP3, M4A, MP4)"),
    lyrics: str = typer.Argument(..., help="Lyrics file (TTML, SRT, LRC)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file"),
    no_sylt: bool = typer.Option(False, "--no-sylt", help="Skip synchronized lyrics"),
    no_uslt: bool = typer.Option(False, "--no-uslt", help="Skip unsynchronized lyrics"),
    no_pinyin: bool = typer.Option(False, "--no-pinyin", help="Skip pinyin"),
    no_translation: bool = typer.Option(False, "--no-translation", help="Skip translation"),
):
    """Embed time-synced lyrics into audio file."""

    from baobao.embed import embed_lyrics, EmbedConfig

    config = EmbedConfig(
        include_sylt=not no_sylt,
        include_uslt=not no_uslt,
        include_pinyin=not no_pinyin,
        include_translation=not no_translation,
    )

    console.print(f"[cyan]Embedding lyrics into {audio}...[/cyan]")

    try:
        output_file = embed_lyrics(audio, lyrics, output, config)
        console.print(f"[green]✓[/green] Lyrics embedded: {output_file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

**Usage**:
```bash
# Basic usage
baobao embed song.mp3 song.ttml

# With options
baobao embed song.mp3 song.enhanced.srt --output song_with_lyrics.mp3

# Skip certain features
baobao embed song.mp3 song.ttml --no-translation --no-pinyin
```

### 3. Integrate with Process Command

**Optional enhancement**: Add `--embed` flag to `process` command for all-in-one workflow:

```python
@app.command()
def process(
    audio: str,
    # ... existing params ...
    embed_lyrics: bool = typer.Option(False, "--embed", help="Embed lyrics in audio file"),
):
    """Full pipeline: transcribe, enhance, and optionally embed."""

    # ... existing transcribe + enhance logic ...

    # New: Embed if requested
    if embed_lyrics:
        from baobao.embed import embed_lyrics, EmbedConfig
        embed_lyrics(audio, output_srt, config=EmbedConfig())
```

### 4. Add Format Conversion Utilities

**Helper functions** in `embed.py`:
```python
def ttml_to_segments(ttml_path: str) -> list[LyricSegment]:
    """Parse TTML file to LyricSegments."""
    pass

def srt_to_segments(srt_path: str) -> list[LyricSegment]:
    """Parse SRT file to LyricSegments."""
    pass

def lrc_to_segments(lrc_path: str) -> list[LyricSegment]:
    """Parse LRC file to LyricSegments."""
    pass
```

These allow `embed` command to accept any lyric format.

### 5. Export to LRC Format

**Also add** (if not already in transcribe.py):
```python
def export_lrc(segments: list[LyricSegment], output_path: str):
    """Export segments to LRC format for maximum compatibility."""
    # LRC format: [mm:ss.xx]Lyrics text
    # Simple, widely supported
    pass
```

**CLI command**:
```bash
baobao export-lrc song.ttml song.lrc
```

## Critical Files

**New files**:
- `/home/michael/Projects/Leon/baobao/baobao/embed.py` (~400 lines)

**Modified files**:
- `/home/michael/Projects/Leon/baobao/baobao/cli.py`:
  - Add `embed` command (~50 lines)
  - Optionally add `--embed` flag to `process` command
- `/home/michael/Projects/Leon/baobao/pyproject.toml`:
  - Add `mutagen>=1.47.0` dependency

**New tests**:
- `/home/michael/Projects/Leon/baobao/tests/test_embed.py` (unit tests)
- Update E2E tests to test embedding workflow

## Dependencies

**Add to pyproject.toml**:
```toml
[project]
dependencies = [
    # ... existing ...
    "mutagen>=1.47.0",
]
```

## Questions Needing Validation

### 1. **Player Compatibility Testing**
- Does mpv support SYLT? (critical for `preview` command)
- Does VLC support SYLT?
- Which mobile players support SYLT?
- **Action needed**: Test embedded SYLT with common players

### 2. **SYLT Line Format**
- Should we put all three lines (Chinese, pinyin, English) at same timestamp?
- Or spread them out slightly (e.g., +100ms between each)?
- **Affects**: Display behavior in players

### 3. **Multi-Language SYLT**
- Can we embed multiple SYLT frames (one per language)?
- E.g., one for Chinese, one for pinyin, one for English?
- **Spec allows**: Multiple SYLT frames with different language codes
- **Player support**: Unknown, needs testing

### 4. **File Format Priority**
- Should we recommend MP3 over M4A for sync support?
- Or support both with clear documentation?
- **Recommendation**: MP3 for sync, M4A for quality, external .lrc for compatibility

### 5. **Integration with Enhancement**
- Should enhancement automatically embed lyrics?
- Or keep as separate step for flexibility?
- **Recommendation**: Separate step, but add `--embed` convenience flag

### 6. **Handling Enhanced vs Simple Lyrics**
- If lyrics file has pinyin/translation, embed them
- If simple transcription only, embed Chinese only
- Auto-detect based on SRT/TTML structure?

## Testing Requirements

- [ ] SYLT embeds correctly in MP3
- [ ] USLT embeds correctly in MP3
- [ ] M4A lyrics embed (static only)
- [ ] UTF-8 encoding works for Chinese
- [ ] Timestamps convert correctly (seconds → milliseconds)
- [ ] Multiple lyric lines at same timestamp work
- [ ] TTML → SYLT conversion works
- [ ] SRT → SYLT conversion works
- [ ] LRC → SYLT conversion works
- [ ] Embedded lyrics display in test players
- [ ] CLI `embed` command works
- [ ] Optional embedding in `process` command works

## Player Testing Checklist

**Must test with**:
- [ ] mpv (used in `preview` command)
- [ ] VLC
- [ ] MusicBee (Windows)
- [ ] iTunes/Music app (macOS)
- [ ] iPhone Music app
- [ ] Android music player

**Document**: Which players work, which don't, what fallbacks exist.

## Implementation Phases

### Phase 1: Basic MP3 Embedding
1. Create `embed.py` module
2. Implement SYLT embedding
3. Implement USLT embedding (fallback)
4. Add CLI `embed` command
5. Test with MP3 files

### Phase 2: Format Support
1. Add SRT parser
2. Add TTML parser
3. Add LRC parser
4. Test all format conversions

### Phase 3: M4A Support
1. Add M4A static lyrics embedding
2. Document limitations vs MP3

### Phase 4: Integration
1. Add `--embed` flag to `process` command
2. Add LRC export utility
3. Update documentation

### Phase 5: Testing & Validation
1. Test with real players (mpv, VLC, etc.)
2. Document player compatibility
3. Add troubleshooting guide

## Alternative Approaches

### Alternative 1: External LRC Files Only
**Pros**: Universal compatibility, simple implementation
**Cons**: Extra file to manage, not truly "embedded"

### Alternative 2: MP3 + External LRC Hybrid
**Pros**: Best of both worlds
**Cons**: Two outputs for same song

### Alternative 3: TTML as External Standard
**Pros**: Rich metadata, modern format
**Cons**: Limited player support (need to verify)

## Recommendations

**Recommended approach**:
1. **Primary output**: External TTML or LRC files (universal support)
2. **Bonus feature**: SYLT embedding in MP3 (for compatible players)
3. **Always include**: USLT in MP3 (static fallback for all players)
4. **Document clearly**: Player compatibility matrix

**Benefits**:
- Maximum compatibility (external files work everywhere)
- Embedded lyrics for supported players (nice bonus)
- Fallback for unsupported players (USLT)
- User choice (use external or embedded)

**Workflow**:
```bash
# Generate external TTML (universal)
baobao transcribe song.mp3  # → song.ttml

# Enhance with pinyin/translation
baobao enhance song.ttml  # → song.enhanced.ttml

# Bonus: Embed into MP3 for supported players
baobao embed song.mp3 song.enhanced.ttml  # → song.mp3 (with SYLT + USLT)

# Also export LRC for maximum compatibility
baobao export-lrc song.enhanced.ttml song.lrc
```

## Risks and Mitigations

**Risk**: Limited SYLT player support
- **Mitigation**: Keep external files as primary, SYLT as bonus

**Risk**: Mutagen bugs or edge cases
- **Mitigation**: Thorough testing, good error handling

**Risk**: Encoding issues with Chinese text
- **Mitigation**: Always use UTF-8, test with various players

**Risk**: SYLT format complexity
- **Mitigation**: Start simple (one SYLT frame), iterate based on testing

**Risk**: Breaking `preview` command if mpv doesn't support SYLT
- **Mitigation**: Test mpv first, fallback to external .lrc if needed

## Success Criteria

- [ ] MP3 files can have embedded SYLT synchronized lyrics
- [ ] MP3 files have USLT fallback for all players
- [ ] M4A files have static lyrics
- [ ] CLI `embed` command works for all lyric formats
- [ ] Embedded lyrics display correctly in at least one popular player
- [ ] Documentation includes player compatibility matrix
- [ ] Tests verify embedding correctness
- [ ] User can choose between external files or embedded lyrics
