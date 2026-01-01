"""
Pytest fixtures and configuration for baobao tests.
"""

import asyncio
from pathlib import Path

import pytest

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
SONGS_DIR = Path(__file__).parent.parent / "songs"


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    return TEST_DATA_DIR


@pytest.fixture(scope="session")
def songs_dir():
    """Path to songs directory with real audio files."""
    return SONGS_DIR


@pytest.fixture(scope="session")
def sample_audio_path(songs_dir):
    """Path to a sample audio file for testing."""
    # Use the existing test file
    mp3_files = list(songs_dir.glob("*.mp3"))
    if mp3_files:
        return mp3_files[0]
    pytest.skip("No MP3 files found in songs directory")


@pytest.fixture(scope="session")
def sample_srt_path(songs_dir):
    """Path to a sample SRT file for testing."""
    srt_files = list(songs_dir.glob("*.test.srt"))
    if srt_files:
        return srt_files[0]
    pytest.skip("No test SRT files found in songs directory")


@pytest.fixture
def sample_srt_content():
    """Sample SRT content for unit tests."""
    return """1
00:00:04,970 --> 00:00:08,760
你是我陽光

2
00:00:09,780 --> 00:00:11,780
我唯一陽光

3
00:00:12,864 --> 00:00:14,688
你讓我快樂

4
00:00:15,936 --> 00:00:18,180
當天空會安

5
00:00:19,104 --> 00:00:21,060
你永不知道

6
00:00:22,240 --> 00:00:24,056
我多麼愛你
"""


@pytest.fixture
def temp_srt_file(tmp_path, sample_srt_content):
    """Create a temporary SRT file for testing."""
    srt_path = tmp_path / "test.srt"
    srt_path.write_text(sample_srt_content, encoding="utf-8")
    return srt_path


@pytest.fixture
def word_highlighted_srt_content():
    """Sample SRT with word-level highlighting."""
    return """1
00:00:04,970 --> 00:00:06,820
<font color="#00ff00">你是</font>我陽光

2
00:00:06,820 --> 00:00:07,560
你是<font color="#00ff00">我</font>陽光

3
00:00:07,560 --> 00:00:08,140
你是我<font color="#00ff00">陽</font>光

4
00:00:08,140 --> 00:00:08,760
你是我陽<font color="#00ff00">光</font>
"""


# Test phrases for synthetic audio tests
TEST_PHRASES = [
    ("你好", "nǐ hǎo", ["hello", "hi"]),
    ("謝謝", "xiè xiè", ["thank", "thanks"]),
    ("再見", "zài jiàn", ["goodbye", "bye"]),
    ("我愛你", "wǒ ài nǐ", ["love"]),
    ("中文", "zhōng wén", ["chinese"]),
]


@pytest.fixture
def test_phrases():
    """Test phrases with expected pinyin and English."""
    return TEST_PHRASES


# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
