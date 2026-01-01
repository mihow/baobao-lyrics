"""
LLM-based enhancement for Chinese lyrics.

Adds pinyin romanization and English translations using Instructor + Ollama.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


# Ollama configuration defaults
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"  # Good for Chinese


class OutputFormat(str, Enum):
    """Output format options for enhanced subtitles."""

    FULL = "full"  # Full English translation
    EMOJI = "emoji"  # Emoji + brief keywords
    LEARN = "learn"  # Learning-optimized: pinyin-first with tips


# Pydantic models for structured LLM output
class WordDetail(BaseModel):
    """Details for a single Chinese character."""

    char: str = Field(description="The Chinese character")
    pinyin: str = Field(description="Pinyin with tone marks (e.g., nǐ, hǎo)")
    english: str = Field(description="Brief English meaning or emoji")


class PhraseInterpretation(BaseModel):
    """Interpretation of a Chinese phrase for language learning."""

    pinyin: str = Field(description="Full pinyin of the phrase with tone marks")
    english: str = Field(
        description="Brief English translation (2-5 words) or emoji + keyword"
    )
    word_details: list[WordDetail] = Field(description="Per-character breakdown")


class LearningLyricLine(BaseModel):
    """Optimized lyric line for language learning."""

    pinyin_spaced: str = Field(
        description="Pinyin with spaces between syllables for clarity"
    )
    literal_gloss: str = Field(
        description="Word-by-word English gloss matching pinyin order"
    )
    natural_english: str = Field(description="Natural English translation")
    sing_along_tip: str = Field(
        description="Brief pronunciation tip or memory hook (emoji welcome)"
    )
    word_details: list[WordDetail] = Field(description="Per-character breakdown")


@dataclass
class EnhanceConfig:
    """Configuration for LLM enhancement."""

    ollama_url: str = DEFAULT_OLLAMA_URL
    model: str = DEFAULT_MODEL
    output_format: OutputFormat = OutputFormat.FULL


class ChineseEnhancer:
    """Enhance Chinese lyrics with pinyin and translations using LLM."""

    def __init__(self, config: Optional[EnhanceConfig] = None):
        self.config = config or EnhanceConfig()
        self._client = None
        self._cache: dict[str, dict] = {}

    @property
    def client(self):
        """Lazy-initialize the instructor client."""
        if self._client is None:
            import instructor

            self._client = instructor.from_provider(
                f"ollama/{self.config.model}",
                mode=instructor.Mode.JSON,
            )
        return self._client

    def check_connection(self) -> bool:
        """Check if Ollama is accessible."""
        import requests

        try:
            resp = requests.get(f"{self.config.ollama_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                model_base = self.config.model.split(":")[0]
                if any(model_base in m for m in models):
                    return True
                console.print(
                    f"[yellow]⚠[/yellow] Model '{self.config.model}' not found"
                )
                console.print(f"[dim]Available: {models[:5]}...[/dim]")
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] Cannot connect to Ollama: {e}")
            return False

    def interpret_phrase(self, chinese_text: str) -> dict:
        """
        Get pinyin and English for a Chinese phrase.

        Uses structured output with Instructor for reliable parsing.
        """
        # Clean text (remove highlighting tags if any)
        clean_text = re.sub(r"<[^>]+>", "", chinese_text).strip()

        if not clean_text:
            return {"pinyin": "", "english": "", "word_details": []}

        # Check cache
        cache_key = f"{self.config.output_format.value}:{clean_text}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Use learning-optimized format
        if self.config.output_format == OutputFormat.LEARN:
            return self._interpret_for_learning(clean_text, cache_key)

        # Build prompt based on output format
        if self.config.output_format == OutputFormat.EMOJI:
            format_instruction = """For english fields: use 1-2 emojis + optional 1-2 word hint.
Examples: "☀️ sunshine", "❤️ love", "😊 happy", "🌧️ rain"
Keep it visual and minimal for children."""
        else:
            format_instruction = """For english fields: use simple 2-5 word translations.
Use simple words appropriate for children learning Chinese."""

        prompt = f"""Analyze this Chinese phrase for a children's learning song.

Chinese: {clean_text}

{format_instruction}

Rules:
- Use standard pinyin with tone marks (ā á ǎ à, ē é ě è, ī í ǐ ì, etc.)
- word_details should have one entry per Chinese character
- Keep translations brief and child-friendly

/no_think"""

        try:
            result = self.client.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=PhraseInterpretation,
                max_retries=2,
                timeout=30.0,
            )

            result_dict = {
                "pinyin": result.pinyin,
                "english": result.english,
                "word_details": [
                    {"char": w.char, "pinyin": w.pinyin, "english": w.english}
                    for w in result.word_details
                ],
            }

            self._cache[cache_key] = result_dict
            return result_dict

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] LLM error for '{clean_text}': {e}")
            fallback = {
                "pinyin": clean_text,
                "english": "?",
                "word_details": [
                    {"char": c, "pinyin": "?", "english": "?"}
                    for c in clean_text
                    if c.strip()
                ],
            }
            self._cache[cache_key] = fallback
            return fallback

    def _interpret_for_learning(self, clean_text: str, cache_key: str) -> dict:
        """Get learning-optimized interpretation with pedagogy focus."""
        prompt = f"""You are a Chinese language teacher creating sing-along lyrics.

Analyze this Chinese phrase and create the BEST learning format:

Chinese: {clean_text}

Design your response to help a child:
1. SING the pinyin correctly (spaced clearly, with tone marks)
2. UNDERSTAND what each word means (literal word-by-word gloss)
3. REMEMBER it (a fun tip, rhyme, or emoji memory hook)

Rules for pinyin_spaced:
- Space between each syllable: "nǐ hǎo" not "nǐhǎo"
- Always use tone marks: ā á ǎ à, ē é ě è, ī í ǐ ì, ū ú ǔ ù, ǖ ǘ ǚ ǜ

Rules for literal_gloss:
- Match the pinyin word order exactly
- Use simple words a child knows

Rules for sing_along_tip:
- Make it memorable! Use emojis, rhymes, or fun associations
- Keep it SHORT (fits on one line)

/no_think"""

        try:
            result = self.client.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=LearningLyricLine,
                max_retries=2,
                timeout=30.0,
            )

            result_dict = {
                "pinyin": result.pinyin_spaced,
                "pinyin_spaced": result.pinyin_spaced,
                "literal_gloss": result.literal_gloss,
                "english": result.natural_english,
                "sing_along_tip": result.sing_along_tip,
                "word_details": [
                    {"char": w.char, "pinyin": w.pinyin, "english": w.english}
                    for w in result.word_details
                ],
            }

            self._cache[cache_key] = result_dict
            return result_dict

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Learning interpret error: {e}")
            fallback = {
                "pinyin": clean_text,
                "pinyin_spaced": clean_text,
                "literal_gloss": "?",
                "english": "?",
                "sing_along_tip": "",
                "word_details": [
                    {"char": c, "pinyin": "?", "english": "?"}
                    for c in clean_text
                    if c.strip()
                ],
            }
            self._cache[cache_key] = fallback
            return fallback

    def format_subtitle_line(
        self, chinese: str, highlight_idx: Optional[int] = None
    ) -> dict:
        """Format a subtitle line with pinyin and English."""
        clean_text = re.sub(r"<[^>]+>", "", chinese).strip()

        # Find highlighted character
        highlight_match = re.search(r"<font[^>]*>([^<]+)</font>", chinese)
        highlighted_char = highlight_match.group(1) if highlight_match else None

        interp = self.interpret_phrase(clean_text)

        pinyin = interp.get("pinyin", "")
        english = interp.get("english", "")
        word_details = interp.get("word_details", [])

        # Build pinyin line with highlighting
        if highlighted_char and word_details:
            pinyin_parts = []
            for detail in word_details:
                char = detail.get("char", "")
                py = detail.get("pinyin", "")
                if char == highlighted_char:
                    pinyin_parts.append(f'<font color="#00ff00">{py}</font>')
                else:
                    pinyin_parts.append(py)
            pinyin_highlighted = " ".join(pinyin_parts)
        else:
            pinyin_highlighted = pinyin

        return {
            "chinese": chinese,
            "pinyin": pinyin_highlighted,
            "pinyin_plain": pinyin,
            "english": english,
            "word_details": word_details,
        }


def enhance_srt(
    srt_path: str | Path,
    output_path: Optional[str | Path] = None,
    output_format: OutputFormat = OutputFormat.FULL,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
) -> Path:
    """
    Enhance an SRT file with pinyin and translations.

    Args:
        srt_path: Path to input SRT file
        output_path: Path for output (default: adds format suffix)
        output_format: Output format (full, emoji, or learn)
        ollama_url: Ollama API URL
        model: LLM model name

    Returns:
        Path to enhanced SRT file
    """
    srt_path = Path(srt_path)

    config = EnhanceConfig(
        ollama_url=ollama_url,
        model=model,
        output_format=output_format,
    )
    enhancer = ChineseEnhancer(config)

    # Check LLM connection
    if not enhancer.check_connection():
        raise ConnectionError("Cannot connect to Ollama. Is it running?")

    console.print(f"\n[bold]Enhancing:[/bold] {srt_path.name}")
    console.print(f"[dim]Format: {output_format.value}, Model: {model}[/dim]")

    # Parse SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = _parse_srt(content)
    console.print(f"[dim]Found {len(entries)} subtitle entries[/dim]")

    # Pre-interpret unique phrases for caching
    unique_phrases = set()
    for entry in entries:
        clean = re.sub(r"<[^>]+>", "", entry.get("text", "")).strip()
        if clean:
            unique_phrases.add(clean)

    console.print(f"[dim]Unique phrases: {len(unique_phrases)}[/dim]")

    with console.status("[bold blue]Interpreting phrases..."):
        for phrase in unique_phrases:
            enhancer.interpret_phrase(phrase)

    # Build enhanced entries
    enhanced_entries = []
    for entry in entries:
        text = entry.get("text", "")
        result = enhancer.format_subtitle_line(text)
        interp = enhancer.interpret_phrase(re.sub(r"<[^>]+>", "", text).strip())

        if output_format == OutputFormat.LEARN:
            lines = [
                result["pinyin"],
                result["chinese"],
                interp.get("sing_along_tip", "")
                or f"({interp.get('literal_gloss', interp.get('english', ''))})",
            ]
        else:
            lines = [
                result["chinese"],
                result["pinyin"],
                f"({result['english']})",
            ]

        enhanced_entries.append(
            {
                "index": entry.get("index", 0),
                "timestamp": entry.get("timestamp", ""),
                "text": "\n".join(lines),
            }
        )

    # Determine output path
    if output_path is None:
        suffixes = {
            OutputFormat.EMOJI: ".emoji.srt",
            OutputFormat.LEARN: ".learn.srt",
            OutputFormat.FULL: ".enhanced.srt",
        }
        suffix = suffixes.get(output_format, ".enhanced.srt")
        output_path = srt_path.with_suffix("").with_suffix(suffix)

    output_path = Path(output_path)

    # Write enhanced SRT
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in enhanced_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['timestamp']}\n")
            f.write(f"{entry['text']}\n\n")

    console.print(f"[green]✓[/green] Saved: {output_path}")
    return output_path


def _parse_srt(content: str) -> list[dict]:
    """Parse SRT content into entries."""
    entries = []
    current_entry = {}

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(current_entry)
                current_entry = {}
        elif line.isdigit() and not current_entry:
            current_entry["index"] = int(line)
        elif "-->" in line:
            current_entry["timestamp"] = line
        elif current_entry:
            current_entry["text"] = current_entry.get("text", "") + line

    if current_entry:
        entries.append(current_entry)

    return entries
