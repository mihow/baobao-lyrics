"""
Core transcription module using stable-ts + faster-whisper.

Produces time-synced Chinese lyrics in SRT/LRC format.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class TranscriptionConfig:
    """Configuration for transcription."""

    model_size: str = "large-v3"  # Best for Chinese
    language: str = "zh"
    vad: bool = True  # Voice activity detection (good for music)
    beam_size: int = 5
    refine_timestamps: bool = True  # More precise, slower
    word_level: bool = True  # Word-level timestamps for karaoke

    # Segment grouping - avoids too-granular subtitles
    min_segment_duration: float = 1.0  # Minimum seconds per subtitle
    max_segment_duration: float = 8.0  # Maximum seconds per subtitle


@dataclass
class LyricSegment:
    """A single lyric segment with timing."""

    start: float
    end: float
    text: str
    words: Optional[list] = None  # Word-level timing if available


class Transcriber:
    """Transcribe Chinese audio to time-synced lyrics."""

    def __init__(self, config: Optional[TranscriptionConfig] = None):
        self.config = config or TranscriptionConfig()
        self._model = None

    @property
    def model(self):
        """Lazy-load the whisper model."""
        if self._model is None:
            import stable_whisper

            console.print(
                f"[bold blue]Loading {self.config.model_size} model...[/bold blue]"
            )
            self._model = stable_whisper.load_model(self.config.model_size)
            console.print(f"[green]✓[/green] Model loaded: {self.config.model_size}")
        return self._model

    def transcribe(self, audio_path: str | Path) -> list[LyricSegment]:
        """
        Transcribe audio file to lyric segments.

        Args:
            audio_path: Path to audio file (mp3, wav, etc.)

        Returns:
            List of LyricSegment with timestamps and text
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        console.print(f"\n[bold]Transcribing:[/bold] {audio_path.name}")
        console.print(f"[dim]Model: {self.config.model_size}[/dim]")

        # Transcribe with Chinese language hint
        console.print("[bold blue]Transcribing audio...[/bold blue]")
        result = self.model.transcribe(
            str(audio_path),
            language=self.config.language,
            vad=self.config.vad,
            regroup=True,  # Group words into natural segments
            beam_size=self.config.beam_size,
            best_of=self.config.beam_size,
            condition_on_previous_text=True,
        )

        # Refine timestamps for accuracy
        if self.config.refine_timestamps:
            console.print("[bold blue]Refining timestamps...[/bold blue]")
            self.model.refine(str(audio_path), result)

        console.print("[green]✓[/green] Transcription complete")

        # Convert to LyricSegment list
        segments = []
        for seg in result.segments:
            words = None
            if self.config.word_level and hasattr(seg, "words") and seg.words:
                words = [
                    {"start": w.start, "end": w.end, "word": w.word} for w in seg.words
                ]

            segments.append(
                LyricSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                    words=words,
                )
            )

        console.print(f"[dim]Found {len(segments)} segments[/dim]")
        return segments

    def save_srt(
        self,
        segments: list[LyricSegment],
        output_path: str | Path,
        word_highlight: bool = False,
    ) -> Path:
        """
        Save segments as SRT subtitle file.

        Args:
            segments: List of lyric segments
            output_path: Output file path
            word_highlight: If True, create per-word subtitles with highlighting

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)

        with open(output_path, "w", encoding="utf-8") as f:
            if word_highlight:
                self._write_srt_word_highlight(f, segments)
            else:
                self._write_srt_simple(f, segments)

        console.print(f"[green]✓[/green] Saved: {output_path}")
        return output_path

    def _write_srt_simple(self, f, segments: list[LyricSegment]):
        """Write simple SRT without word highlighting."""
        for i, seg in enumerate(segments, 1):
            start = self._format_srt_time(seg.start)
            end = self._format_srt_time(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{seg.text}\n\n")

    def _write_srt_word_highlight(self, f, segments: list[LyricSegment]):
        """Write SRT with karaoke-style word highlighting."""
        idx = 1
        for seg in segments:
            if not seg.words:
                # No word-level timing, write as simple segment
                start = self._format_srt_time(seg.start)
                end = self._format_srt_time(seg.end)
                f.write(f"{idx}\n{start} --> {end}\n{seg.text}\n\n")
                idx += 1
                continue

            # Create subtitle for each word with highlighting
            full_text = seg.text
            for word_info in seg.words:
                word = word_info["word"].strip()
                if not word:
                    continue

                start = self._format_srt_time(word_info["start"])
                end = self._format_srt_time(word_info["end"])

                # Highlight current word in the full line
                highlighted = full_text.replace(
                    word,
                    f'<font color="#00ff00">{word}</font>',
                    1,  # Only replace first occurrence
                )

                f.write(f"{idx}\n{start} --> {end}\n{highlighted}\n\n")
                idx += 1

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def save_lrc(self, segments: list[LyricSegment], output_path: str | Path) -> Path:
        """
        Save segments as LRC lyrics file.

        Args:
            segments: List of lyric segments
            output_path: Output file path

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)

        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                mins = int(seg.start // 60)
                secs = seg.start % 60
                f.write(f"[{mins:02d}:{secs:05.2f}]{seg.text}\n")

        console.print(f"[green]✓[/green] Saved: {output_path}")
        return output_path


def transcribe_audio(
    audio_path: str | Path,
    output_path: Optional[str | Path] = None,
    model_size: str = "large-v3",
    format: str = "srt",
    word_highlight: bool = False,
) -> Path:
    """
    Convenience function to transcribe audio and save output.

    Args:
        audio_path: Path to audio file
        output_path: Output path (default: same as audio with new extension)
        model_size: Whisper model size
        format: Output format ('srt' or 'lrc')
        word_highlight: Enable karaoke-style word highlighting (SRT only)

    Returns:
        Path to output file
    """
    audio_path = Path(audio_path)

    if output_path is None:
        ext = ".srt" if format == "srt" else ".lrc"
        output_path = audio_path.with_suffix(ext)

    config = TranscriptionConfig(model_size=model_size)
    transcriber = Transcriber(config)

    segments = transcriber.transcribe(audio_path)

    if format == "srt":
        return transcriber.save_srt(
            segments, output_path, word_highlight=word_highlight
        )
    else:
        return transcriber.save_lrc(segments, output_path)
