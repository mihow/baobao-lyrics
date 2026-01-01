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

**Result**: ❌ **TTML NOT SUPPORTED**
```
Tested: 2025-12-31
Command: baobao play "songs/01 你是我阳光..." -s test_output/test_lyrics.ttml
Error: "Can not open external file test_output/test_lyrics.ttml"
Behavior: mpv automatically fell back to .srt file
Conclusion: mpv does not recognize TTML format
```

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

## Testing Results Summary

### TTML Compatibility
**Status**: ❌ **NOT RECOMMENDED** for default format

**Test Results**:
- mpv: Does not support TTML (tested 2025-12-31)
- VLC: Not tested (likely similar lack of support)
- Mobile players: Unknown, but likely poor support

**Conclusion**:
- TTML is not widely supported by common media players
- Keep **SRT as default format** for maximum compatibility
- TTML can be added as **optional output format** if needed for specific use cases (Apple Music, etc.)

### SYLT Compatibility
**Status**: ⏸️ **TESTING DEFERRED**

Based on TTML results and research showing limited SYLT support:
- Most players prefer external .lrc files over embedded SYLT
- External files have better compatibility
- Recommend focusing on external file formats (SRT, LRC) first

## Final Decisions

### Task 3 (TTML Support)
**Decision**: ✅ **Implement as OPTIONAL format only**
- Keep SRT as default (proven compatibility)
- Add TTML as `--format ttml` option
- Useful for Apple Music submissions
- Document limited player support in README

### Task 5 (Embedded Lyrics)
**Decision**: ⏸️ **DEFER** or make low priority
- External .srt/.lrc files work universally
- SYLT has limited player support
- Better to focus on improving existing formats
- Can revisit if user demand exists

## Next Steps

1. ✅ TTML tested - mpv does not support
2. ✅ Decision made - keep SRT as default
3. ⏭️ Proceed with Task 3 implementation (TTML as optional format)
4. ⏭️ Skip or defer Task 5 (embedded lyrics)
5. ⏭️ Update task-3 plan to reflect "optional format" approach
