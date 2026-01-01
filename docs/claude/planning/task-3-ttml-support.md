# Task 3: Add TTML Support as Default Lyrics Format

**Status**: Needs research and validation
**Complexity**: High
**Dependencies**: Task 2 (simplified defaults)

## Objective

Replace SRT with TTML as the default time-synced lyrics format, leveraging TTML's superior structure for multi-language lyrics, metadata, and word-level timing.

## Background

**TTML Advantages over SRT**:
- Native support for translations and romanization (pinyin)
- Word-level timing for karaoke highlighting
- Rich metadata (performers, song structure, language codes)
- Standardized W3C format with Apple Music extensions
- Better structure for educational features

**Reference Documentation**:
- `/home/michael/Projects/Leon/baobao/docs/reference/ttml-specification-en.md` (591 lines - primary spec)
- `/home/michael/Projects/Leon/baobao/docs/reference/Overview of TTML for Lyrics - Apple Video and Audio Asset Guide.html`
- Apple Music examples for line-by-line and beat-by-beat timing

## Implementation Plan

### 1. Create TTML Module

**New file**: `/home/michael/Projects/Leon/baobao/baobao/ttml.py`

**Key components**:
```python
from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ET

class TtmlTimingMode(Enum):
    LINE = "Line"  # Line-by-line timing
    WORD = "Word"  # Word-by-word timing

@dataclass
class TtmlConfig:
    """TTML generation configuration."""
    timing_mode: TtmlTimingMode = TtmlTimingMode.LINE
    include_translations: bool = True
    include_romanization: bool = True  # Pinyin for Chinese
    language: str = "zh"  # BCP-47 code
    metadata: dict | None = None

class TtmlWriter:
    """Generate TTML lyrics from LyricSegment data."""

    def __init__(self, config: TtmlConfig):
        self.config = config

    def create_ttml(self, segments: list[LyricSegment],
                    metadata: dict | None = None) -> str:
        """Generate TTML XML from lyric segments."""
        # Build XML tree with proper namespaces
        # Add metadata if available
        # Create <p> elements with timing
        # Add translations/romanization as <span> elements
        pass

    def save_ttml(self, segments: list[LyricSegment],
                  output_path: str, metadata: dict | None = None):
        """Save TTML to file with proper formatting."""
        pass
```

**Structure to generate**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttm="http://www.w3.org/ns/ttml#metadata"
    xmlns:itunes="http://itunes.apple.com/lyric-ttml-extensions"
    xml:lang="zh"
    itunes:timing="Line">

    <head>
        <metadata>
            <ttm:title>Song Title</ttm:title>
            <!-- Add from metadata dict -->
        </metadata>
    </head>

    <body dur="TOTAL_DURATION">
        <div>
            <!-- Each segment becomes a <p> -->
            <p begin="00:00:01.000" end="00:00:03.500">
                你是我陽光
                <span ttm:role="x-roman" xml:lang="zh-Latn">nǐ shì wǒ yáng guāng</span>
                <span ttm:role="x-translation" xml:lang="en">You are my sunlight</span>
            </p>
        </div>
    </body>
</tt>
```

### 2. Integrate with Transcriber

**File**: `/home/michael/Projects/Leon/baobao/baobao/transcribe.py`

**Changes**:
```python
from baobao.ttml import TtmlWriter, TtmlConfig

class Transcriber:
    def save_ttml(self, output_path: str, config: TtmlConfig | None = None):
        """Save transcription as TTML file."""
        config = config or TtmlConfig()
        writer = TtmlWriter(config)
        writer.save_ttml(self.segments, output_path)
```

**Add to line ~120**: New method alongside `save_srt()` and `save_lrc()`.

### 3. Update CLI to Use TTML by Default

**File**: `/home/michael/Projects/Leon/baobao/baobao/cli.py`

**Changes to `transcribe` command** (lines 74-151):
```python
@app.command()
def transcribe(
    audio: str,
    output: str | None = None,
    model: ModelSize = ModelSize.LARGE,
    format: str = "ttml",  # Changed from "srt" to "ttml"
    karaoke: bool = False,
):
    """Transcribe audio to time-synced lyrics (TTML by default)."""

    # Generate output filename
    if output is None:
        base = Path(audio).stem
        ext = ".ttml" if format == "ttml" else f".{format}"
        output = str(Path(audio).parent / f"{base}{ext}")

    # ... transcription logic ...

    # Save based on format
    if format == "ttml":
        transcriber.save_ttml(output)
    elif format == "srt":
        transcriber.save_srt(output, karaoke=karaoke)
    elif format == "lrc":
        transcriber.save_lrc(output)
```

**Add format choices**: `format: str = typer.Option("ttml", "--format", "-f", help="Output format (ttml, srt, lrc)")`

### 4. TTML Enhancement Support

**File**: `/home/michael/Projects/Leon/baobao/baobao/enhance.py`

**New function**:
```python
def enhance_ttml(
    ttml_path: str,
    output_path: str | None = None,
    config: EnhanceConfig | None = None
) -> str:
    """
    Enhance TTML file with pinyin and translations.

    TTML already has structure for translations/romanization,
    so we parse, enhance, and write back in proper format.
    """
    # Parse TTML XML
    # Extract Chinese text from <p> elements
    # Call LLM to get pinyin + translations
    # Add as <span ttm:role="x-roman"> and <span ttm:role="x-translation">
    # Save enhanced TTML
```

**Challenge**: TTML structure is different from SRT's line-based format. Need to:
- Parse XML properly
- Preserve timing attributes
- Add enhancement as structured spans, not text lines
- Handle word-level timing if using Word mode

### 5. Word-Level Timing (Future Enhancement)

**Current limitation**: `stable-ts` provides word-level timestamps, but current code only uses line-level.

**For TTML Word mode**:
```xml
<p begin="00:01.000" end="00:03.500">
    <span begin="00:01.000" end="00:01.500">你</span>
    <span begin="00:01.500" end="00:02.000">是</span>
    <span begin="00:02.000" end="00:02.500">我</span>
    <span begin="00:02.500" end="00:03.500">陽光</span>
</p>
```

**Implementation**:
- Extract word-level data from `LyricSegment.words` (already available in transcribe.py:40)
- Create nested `<span>` elements for each word
- Set `itunes:timing="Word"` in root `<tt>` element

**Recommendation**: Start with Line mode, add Word mode as optional feature.

## Critical Files to Create/Modify

**New files**:
- `/home/michael/Projects/Leon/baobao/baobao/ttml.py` (~300 lines estimated)

**Modified files**:
- `/home/michael/Projects/Leon/baobao/baobao/transcribe.py`:
  - Add `save_ttml()` method (line ~120)
- `/home/michael/Projects/Leon/baobao/baobao/cli.py`:
  - Change default format to TTML (line 106)
  - Add format option (line 100)
- `/home/michael/Projects/Leon/baobao/baobao/enhance.py`:
  - Add `enhance_ttml()` function (~150 lines)
  - Add TTML parser

**New tests**:
- `/home/michael/Projects/Leon/baobao/tests/test_ttml.py` (unit tests)
- Update `/home/michael/Projects/Leon/baobao/tests/test_e2e.py` (E2E with TTML)

## Dependencies

**Python packages** (add to pyproject.toml):
```toml
# XML handling (stdlib sufficient)
# No additional dependencies needed for basic TTML

# Optional: XML validation
lxml>=4.9.0  # For better XML handling and validation
```

## Questions Needing Research

### 1. **XML Library Choice**
- Use `xml.etree.ElementTree` (stdlib)?
- Or `lxml` for better namespace handling and validation?
- **Recommendation**: Start with stdlib, add lxml if needed

### 2. **TTML Validation**
- Should we validate against W3C TTML schema?
- How to handle Apple Music-specific extensions?
- **Recommendation**: Basic validation, ensure well-formed XML

### 3. **Backward Compatibility**
- Keep SRT support indefinitely?
- How long to maintain SRT as option?
- **Recommendation**: Keep SRT as option (`--format srt`), TTML as default

### 4. **Enhancement Integration**
- Should `enhance` command auto-detect TTML vs SRT?
- Or require separate `enhance-ttml` command?
- **Recommendation**: Auto-detect based on file extension

### 5. **Karaoke Mode in TTML**
- How to handle karaoke highlighting?
- Use Word timing mode?
- Or custom styling attributes?
- **Recommendation**: Word timing mode is natural fit for karaoke

### 6. **File Extension**
- Use `.ttml` or `.xml`?
- Apple Music uses `.ttml`
- **Recommendation**: `.ttml` for clarity

## Testing Requirements

- [ ] Generate valid TTML from LyricSegment data
- [ ] TTML validates against W3C spec
- [ ] Proper namespace declarations
- [ ] Translations embedded correctly
- [ ] Romanization (pinyin) embedded correctly
- [ ] Timing format correct (HH:MM:SS.fff)
- [ ] Total duration calculated properly
- [ ] CLI format flag works (`--format ttml`)
- [ ] Enhancement works with TTML files
- [ ] Line-level timing mode works
- [ ] Word-level timing mode works (if implemented)
- [ ] Backward compat: SRT format still available

## Implementation Phases

### Phase 1: Basic TTML Generation (MVP)
1. Create `ttml.py` module with `TtmlWriter` class
2. Implement line-level timing mode
3. Add basic metadata support
4. Integrate with `Transcriber.save_ttml()`
5. Update CLI to support `--format ttml`
6. Write unit tests

### Phase 2: Enhancement Integration
1. Parse TTML XML in `enhance.py`
2. Add translations as `<span ttm:role="x-translation">`
3. Add pinyin as `<span ttm:role="x-roman">`
4. Update CLI `enhance` command to handle TTML
5. Write integration tests

### Phase 3: Advanced Features
1. Word-level timing mode (karaoke)
2. Rich metadata (performers, song structure)
3. Multiple language translations
4. Validation against TTML schema

### Phase 4: Make TTML Default
1. Change CLI default format from SRT to TTML
2. Update documentation
3. Update README examples
4. Migration guide for SRT users

## Risks and Mitigations

**Risk**: TTML complexity vs SRT simplicity
- **Mitigation**: Keep SRT as option, clear docs

**Risk**: Limited player support for TTML
- **Mitigation**: Research player compatibility first, provide fallback

**Risk**: XML parsing/generation bugs
- **Mitigation**: Thorough testing, use established libraries

**Risk**: Enhancement pipeline complexity with XML
- **Mitigation**: Clean separation between TTML parsing and LLM calls

## Player Compatibility Research Needed

**Must verify**:
- Does mpv support TTML? (used in `preview` command)
- Does VLC support TTML?
- Mobile player support?
- Apple Music / iTunes compatibility?

**Fallback strategy**:
- Always generate both TTML and SRT?
- Or provide easy conversion: `baobao convert song.ttml song.srt`?

## Recommendations

1. **Start with Line mode** - Simpler, works for most use cases
2. **Keep SRT as option** - Don't break existing workflows
3. **Use stdlib XML** - Avoid new dependencies initially
4. **Test with real players** - Validate TTML output works in mpv/VLC
5. **Document TTML structure** - Help users understand format
6. **Add conversion utility** - Easy TTML ↔ SRT conversion

## Success Criteria

- [ ] TTML generation works for transcription
- [ ] Enhancement adds translations/romanization to TTML
- [ ] TTML files play correctly in mpv (preview command)
- [ ] CLI defaults to TTML for new transcriptions
- [ ] SRT still available as option
- [ ] Documentation updated with TTML examples
- [ ] All tests pass
