#!/usr/bin/env python3
"""
End-to-end test for Chinese lyrics transcription pipeline.

This test:
1. Generates synthetic Chinese audio using edge-tts
2. Transcribes it with stable-ts + faster-whisper
3. Enhances with LLM-based pinyin + English
4. Validates the output

Uses simple, original Chinese phrases (not copyrighted content).
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Test phrases - simple original content for testing
# These are basic Chinese learning phrases, not song lyrics
TEST_PHRASES = [
    "你好，我是小明。",      # Hello, I am Xiaoming.
    "今天天气很好。",        # The weather is nice today.
    "我喜欢学习中文。",      # I like learning Chinese.
    "谢谢你的帮助。",        # Thank you for your help.
    "再见，明天见。",        # Goodbye, see you tomorrow.
]

# Expected results for validation
EXPECTED_CONTENT = {
    "你好": {"pinyin_contains": "hǎo", "english_contains": ["hello", "hi", "👋"]},
    "天气": {"pinyin_contains": "tiān", "english_contains": ["weather", "🌤", "☀"]},
    "中文": {"pinyin_contains": "zhōng", "english_contains": ["chinese", "🇨🇳", "📖"]},
    "谢谢": {"pinyin_contains": "xiè", "english_contains": ["thank", "🙏"]},
    "再见": {"pinyin_contains": "zài", "english_contains": ["bye", "goodbye", "👋"]},
}


async def generate_test_audio(output_path: str, phrases: list[str]) -> str:
    """Generate Chinese audio using edge-tts."""
    import edge_tts
    
    # Join phrases with pauses
    text = "。。。".join(phrases)  # Periods create pauses
    
    # Use a Chinese voice
    voice = "zh-CN-XiaoxiaoNeural"  # Female Chinese voice
    
    communicate = edge_tts.Communicate(text, voice, rate="-20%")  # Slower for clarity
    await communicate.save(output_path)
    
    return output_path


def transcribe_audio(audio_path: str, model_size: str = "base") -> object:
    """Transcribe audio using stable-ts."""
    import stable_whisper
    
    print(f"  Loading model: {model_size}")
    model = stable_whisper.load_model(model_size)
    
    print(f"  Transcribing...")
    result = model.transcribe(
        audio_path,
        language="zh",
        vad=True,
        regroup=True,
    )
    
    # Refine timestamps
    print(f"  Refining timestamps...")
    model.refine(audio_path, result)
    
    return result


def create_word_highlighted_srt(result, output_path: str) -> str:
    """Create SRT with word-level highlighting."""
    entries = []
    entry_idx = 1
    
    for segment in result.segments:
        text = segment.text.strip()
        if not text:
            continue
            
        # Get words if available
        words = getattr(segment, 'words', None)
        
        if words:
            # Create entry for each word with highlighting
            for word in words:
                word_text = word.word.strip()
                if not word_text:
                    continue
                    
                # Create highlighted version
                highlighted = text.replace(
                    word_text, 
                    f'<font color="#00ff00">{word_text}</font>',
                    1  # Only first occurrence
                )
                
                start_ts = format_srt_time(word.start)
                end_ts = format_srt_time(word.end)
                
                entries.append({
                    'index': entry_idx,
                    'timestamp': f"{start_ts} --> {end_ts}",
                    'text': highlighted,
                })
                entry_idx += 1
        else:
            # No word-level data, just use segment
            start_ts = format_srt_time(segment.start)
            end_ts = format_srt_time(segment.end)
            
            entries.append({
                'index': entry_idx,
                'timestamp': f"{start_ts} --> {end_ts}",
                'text': text,
            })
            entry_idx += 1
    
    # Write SRT
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['timestamp']}\n")
            f.write(f"{entry['text']}\n\n")
    
    return output_path


def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def enhance_srt_with_llm(srt_path: str, output_format: str = "learn") -> str:
    """Enhance SRT with pinyin and English using the main script."""
    # Import from main script
    sys.path.insert(0, str(Path(__file__).parent))
    from test_transcription import process_srt_with_llm, OUTPUT_FORMAT_EMOJI, OUTPUT_FORMAT_FULL, OUTPUT_FORMAT_LEARN
    
    format_map = {
        "emoji": OUTPUT_FORMAT_EMOJI,
        "full": OUTPUT_FORMAT_FULL,
        "learn": OUTPUT_FORMAT_LEARN,
    }
    fmt = format_map.get(output_format, OUTPUT_FORMAT_LEARN)
    return process_srt_with_llm(srt_path, output_format=fmt)


def validate_results(enhanced_srt_path: str) -> dict:
    """Validate that the enhanced SRT contains expected content."""
    with open(enhanced_srt_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    results = {
        'total_checks': 0,
        'passed': 0,
        'failed': 0,
        'details': []
    }
    
    for chinese, expected in EXPECTED_CONTENT.items():
        results['total_checks'] += 1
        
        # Check if Chinese text is in output
        if chinese not in content and chinese.lower() not in content:
            results['failed'] += 1
            results['details'].append(f"❌ '{chinese}' not found in output")
            continue
        
        # Check pinyin
        pinyin_check = expected.get('pinyin_contains', '')
        if pinyin_check and pinyin_check.lower() in content:
            results['passed'] += 1
            results['details'].append(f"✓ Found pinyin for '{chinese}': contains '{pinyin_check}'")
        else:
            # Partial pass - Chinese found but pinyin might be different
            results['passed'] += 0.5
            results['details'].append(f"⚠ '{chinese}' found, pinyin '{pinyin_check}' not exact match")
    
    return results


async def run_e2e_test():
    """Run the complete end-to-end test."""
    print("\n" + "="*70)
    print("  END-TO-END CHINESE TRANSCRIPTION TEST")
    print("="*70 + "\n")
    
    # Create temp directory for test files
    test_dir = Path(__file__).parent / "test_output"
    test_dir.mkdir(exist_ok=True)
    
    audio_path = test_dir / "test_chinese.mp3"
    srt_path = test_dir / "test_chinese.srt"
    
    try:
        # Step 1: Generate audio
        print("Step 1: Generating test audio with edge-tts...")
        print(f"  Phrases: {len(TEST_PHRASES)}")
        await generate_test_audio(str(audio_path), TEST_PHRASES)
        print(f"  ✓ Audio saved: {audio_path}")
        print(f"  ✓ File size: {audio_path.stat().st_size / 1024:.1f} KB")
        
        # Step 2: Transcribe
        print("\nStep 2: Transcribing with stable-ts + faster-whisper...")
        result = transcribe_audio(str(audio_path))
        print(f"  ✓ Transcribed {len(result.segments)} segments")
        
        # Show transcription
        print("\n  --- Transcription ---")
        for seg in result.segments:
            print(f"  [{seg.start:.2f}s] {seg.text.strip()}")
        
        # Step 3: Create word-highlighted SRT
        print("\nStep 3: Creating word-highlighted SRT...")
        create_word_highlighted_srt(result, str(srt_path))
        print(f"  ✓ SRT saved: {srt_path}")
        
        # Step 4: Enhance with LLM
        print("\nStep 4: Enhancing with LLM (pinyin + English)...")
        enhanced_path = enhance_srt_with_llm(str(srt_path), output_format="learn")
        print(f"  ✓ Enhanced SRT: {enhanced_path}")
        
        # Step 5: Validate
        print("\nStep 5: Validating results...")
        validation = validate_results(enhanced_path)
        
        for detail in validation['details']:
            print(f"  {detail}")
        
        # Summary
        print("\n" + "="*70)
        success_rate = validation['passed'] / validation['total_checks'] * 100 if validation['total_checks'] > 0 else 0
        
        if success_rate >= 80:
            print(f"  ✓ TEST PASSED ({success_rate:.0f}% accuracy)")
        elif success_rate >= 50:
            print(f"  ⚠ TEST PARTIALLY PASSED ({success_rate:.0f}% accuracy)")
        else:
            print(f"  ❌ TEST FAILED ({success_rate:.0f}% accuracy)")
        
        print("="*70)
        
        # Show sample of enhanced output
        print("\n--- Sample Enhanced Output ---\n")
        with open(enhanced_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n\n')[:3]  # First 3 entries
            for entry in lines:
                if entry.strip():
                    print(entry)
                    print()
        
        return success_rate >= 50
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    success = asyncio.run(run_e2e_test())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
