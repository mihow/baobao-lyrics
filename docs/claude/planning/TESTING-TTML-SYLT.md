# TTML and SYLT Player Compatibility Testing Guide

**Created**: 2025-12-31
**Status**: Manual testing required

## Test Files Created

1. **TTML Test File**: `test_output/test_lyrics.ttml`
   - Line-level timing mode
   - Chinese text with pinyin romanization
   - English translations
   - Uses Apple Music TTML extensions

2. **Audio File**: `songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3`

## TTML Compatibility Testing

### Test 1: mpv (Critical - used in preview command)

```bash
# Test basic TTML playback
mpv --sub-file=test_output/test_lyrics.ttml "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"

# Expected behavior:
# - Subtitles should appear in sync with audio
# - Should show Chinese text
# - Ideally shows pinyin and English (depends on mpv TTML support)

# What to check:
# - Does mpv recognize .ttml files?
# - Are subtitles displayed?
# - Does it show only Chinese or also pinyin/English?
# - Any error messages?
```

**Result**: _[NEEDS TESTING]_

### Test 2: VLC Media Player

```bash
# Open VLC
vlc "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"

# Then: Subtitle → Add Subtitle File → select test_output/test_lyrics.ttml

# What to check:
# - Does VLC load the .ttml file?
# - Are subtitles displayed correctly?
# - Does it render Chinese characters properly?
# - Does it show translations/pinyin?
```

**Result**: _[NEEDS TESTING]_

### Test 3: Alternative - Convert TTML to SRT for Testing

If TTML doesn't work, create equivalent SRT:

```bash
# Create test SRT file
cat > test_output/test_lyrics.srt << 'EOF'
1
00:00:01,000 --> 00:00:03,500
你是我陽光
nǐ shì wǒ yáng guāng
(You are my sunlight)

2
00:00:04,000 --> 00:00:06,500
我的小太陽
wǒ de xiǎo tài yáng
(My little sun)

3
00:00:07,000 --> 00:00:09,500
你是我希望
nǐ shì wǒ xī wàng
(You are my hope)

4
00:00:10,000 --> 00:00:12,500
我心中的光
wǒ xīn zhōng de guāng
(The light in my heart)
EOF

# Test with mpv
mpv --sub-file=test_output/test_lyrics.srt "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"
```

**Result**: _[NEEDS TESTING]_

## SYLT (MP3 Embedded Lyrics) Testing

### Prerequisites

Install mutagen:
```bash
pip install mutagen
```

### Create Test MP3 with SYLT

```python
# scripts/test_sylt_embed.py
from mutagen.id3 import ID3, SYLT, USLT, Encoding

# Load MP3
audio_path = "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"
audio = ID3(audio_path)

# Create SYLT synchronized lyrics
lyrics = [
    ("你是我陽光", 1000),
    ("nǐ shì wǒ yáng guāng", 1000),
    ("(You are my sunlight)", 1000),
    ("我的小太陽", 4000),
    ("wǒ de xiǎo tài yáng", 4000),
    ("(My little sun)", 4000),
]

audio.delall("SYLT")
audio.add(SYLT(
    encoding=Encoding.UTF8,
    lang="zho",
    format=2,  # milliseconds
    type=1,    # lyrics
    desc="",
    text=lyrics
))

# Also add unsynchronized fallback
uslt_text = """你是我陽光
nǐ shì wǒ yáng guāng
(You are my sunlight)

我的小太陽
wǒ de xiǎo tài yáng
(My little sun)"""

audio.delall("USLT")
audio.add(USLT(
    encoding=Encoding.UTF8,
    lang="zho",
    desc="",
    text=uslt_text
))

# Save to test file
output = "test_output/test_with_sylt.mp3"
import shutil
shutil.copy(audio_path, output)
audio = ID3(output)
audio.save(v2_version=4)

print(f"Created: {output}")
print("Test with music players that support SYLT")
```

### Test Players

**Desktop Players**:
```bash
# MusicBee (Windows)
# Winamp with lyrics plugin (Windows)
# Lollypop (Linux/GNOME)
lollypop test_output/test_with_sylt.mp3

# kid3 (metadata editor - view SYLT)
kid3 test_output/test_with_sylt.mp3
```

**Mobile Players**:
- iOS: Stage Traxx 3
- Android: Various (check SYLT support)

**What to check**:
- Does player recognize SYLT frame?
- Are lyrics displayed?
- Do they sync with audio?
- Does fallback USLT work if SYLT unsupported?

## Decision Matrix

Based on testing results:

| Scenario | Decision |
|----------|----------|
| mpv supports TTML well | ✅ Use TTML as default |
| mpv doesn't support TTML | ❌ Keep SRT as default, TTML as option |
| SYLT widely supported | ✅ Implement embed feature |
| SYLT poorly supported | ⚠️ Make embed feature optional/bonus |

## Expected Outcomes

### TTML (Likely)
- **mpv**: Probably limited support (may show only text, not metadata)
- **VLC**: Probably limited support
- **Recommendation**: Keep SRT as default, add TTML as `--format ttml` option

### SYLT (Likely)
- **Most players**: Limited support
- **External .lrc files**: Much better compatibility
- **Recommendation**: Implement as bonus feature, emphasize external files

## Testing Commands Summary

```bash
# 1. Test TTML with mpv
mpv --sub-file=test_output/test_lyrics.ttml "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"

# 2. Test SRT with mpv (baseline)
mpv --sub-file=test_output/test_lyrics.srt "songs/01 你是我阳光 You Are My Sunshine - Bao Bao Learns Chinese.mp3"

# 3. Create and test SYLT
python scripts/test_sylt_embed.py
# Then open test_output/test_with_sylt.mp3 in various players

# 4. Check ID3 tags
mid3v2 --list test_output/test_with_sylt.mp3 | grep -A 10 SYLT
```

## Next Steps

1. Run tests above
2. Document results in this file
3. Update Task 3 and Task 5 plans based on findings
4. Decide: TTML as default or SRT?
5. Decide: Implement SYLT or skip?
