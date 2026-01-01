"""
Baobao CLI - Chinese lyrics transcription and learning tool.

Usage:
    baobao audio.mp3                     # Simple: transcribe to SRT
    baobao play audio.mp3                # Play with synced subtitles (mpv)
    baobao enhance lyrics.srt            # Add pinyin + translations
    baobao batch ./songs/                # Batch transcription
"""

import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .enhance import OutputFormat, enhance_srt
from .transcribe import transcribe_audio

app = typer.Typer(
    name="baobao",
    help="🐼 Chinese lyrics transcription and learning tool",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


class ModelSize(str, Enum):
    """Whisper model sizes."""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large-v3"


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold]baobao[/bold] version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    audio_file: Annotated[
        Optional[Path],
        typer.Argument(
            help="Audio file to transcribe (for simple usage: baobao audio.mp3)",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
):
    """
    🐼 Baobao - Chinese lyrics transcription for language learning.

    Create time-synced subtitles from Chinese audio with optional
    pinyin romanization and English translations.

    Simple usage:
        baobao song.mp3              # Transcribe audio to SRT
        baobao transcribe song.mp3   # Explicit command (same as above)
        baobao enhance song.srt      # Add pinyin + translations
    """
    # If no subcommand and audio file provided, invoke transcribe
    if ctx.invoked_subcommand is None and audio_file:
        ctx.invoke(transcribe, audio_file=audio_file)


@app.command()
def transcribe(
    audio_file: Annotated[
        Path,
        typer.Argument(
            help="Audio file to transcribe (mp3, wav, etc.)",
            exists=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: same name with .srt)",
        ),
    ] = None,
    model: Annotated[
        ModelSize,
        typer.Option(
            "--model",
            "-m",
            help="Whisper model size (larger = more accurate, slower)",
        ),
    ] = ModelSize.LARGE,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: srt or lrc",
        ),
    ] = "srt",
    karaoke: Annotated[
        bool,
        typer.Option(
            "--karaoke",
            "-k",
            help="Enable word-by-word highlighting (karaoke style)",
        ),
    ] = False,
):
    """
    Transcribe Chinese audio to time-synced subtitles.

    Uses Whisper (via stable-ts) for accurate Chinese speech recognition
    with precise word-level timestamps.

    Examples:
        baobao transcribe song.mp3
        baobao transcribe song.mp3 -m base  # Faster, less accurate
        baobao transcribe song.mp3 --karaoke  # Word highlighting
    """
    console.print(
        Panel.fit(
            f"[bold blue]🐼 Baobao Transcription[/bold blue]\n"
            f"Model: {model.value}",
            border_style="blue",
        )
    )

    try:
        output_path = transcribe_audio(
            audio_path=audio_file,
            output_path=output,
            model_size=model.value,
            format=format,
            word_highlight=karaoke,
        )

        console.print("\n[bold green]✓ Done![/bold green]")
        console.print(f"Output: {output_path}")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def enhance(
    srt_file: Annotated[
        Path,
        typer.Argument(
            help="SRT subtitle file to enhance",
            exists=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path",
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format: full, emoji, or learn",
        ),
    ] = OutputFormat.FULL,
    ollama_url: Annotated[
        str,
        typer.Option(
            "--ollama-url",
            help="Ollama API URL",
        ),
    ] = "http://localhost:11434",
    model: Annotated[
        str,
        typer.Option(
            "--llm-model",
            help="LLM model for translations (e.g., qwen3:4b)",
        ),
    ] = "qwen3:4b",
):
    """
    Enhance subtitles with pinyin and English translations.

    Requires Ollama running locally with a Chinese-capable model.

    Output formats:
        full   - Full English translations
        emoji  - Visual emoji + keywords (kid-friendly)
        learn  - Learning mode: pinyin-first with tips

    Examples:
        baobao enhance lyrics.srt
        baobao enhance lyrics.srt --format emoji
        baobao enhance lyrics.srt --format learn
    """
    console.print(
        Panel.fit(
            f"[bold blue]🐼 Baobao Enhancement[/bold blue]\n"
            f"Format: {format.value}, Model: {model}",
            border_style="blue",
        )
    )

    try:
        output_path = enhance_srt(
            srt_path=srt_file,
            output_path=output,
            output_format=format,
            ollama_url=ollama_url,
            model=model,
        )

        console.print("\n[bold green]✓ Done![/bold green]")
        console.print(f"Output: {output_path}")

    except ConnectionError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def batch(
    directory: Annotated[
        Path,
        typer.Argument(
            help="Directory containing audio files",
            exists=True,
            file_okay=False,
        ),
    ],
    pattern: Annotated[
        str,
        typer.Option(
            "--pattern",
            "-p",
            help="File pattern to match (e.g., '*.mp3')",
        ),
    ] = "*.mp3",
    model: Annotated[
        ModelSize,
        typer.Option(
            "--model",
            "-m",
            help="Whisper model size",
        ),
    ] = ModelSize.LARGE,
):
    """
    Transcribe multiple audio files in a directory.

    By default, only transcribes to SRT files. Use 'baobao enhance'
    separately to add pinyin and translations.

    Examples:
        baobao batch ./songs/
        baobao batch ./songs/ --pattern "*.wav"
        baobao batch ./songs/ --model base
    """
    files = list(directory.glob(pattern))

    if not files:
        console.print(
            f"[yellow]No files matching '{pattern}' in {directory}[/yellow]"
        )
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]🐼 Baobao Batch Transcription[/bold blue]\n"
            f"Files: {len(files)}\n"
            f"Model: {model.value}",
            border_style="blue",
        )
    )

    success = 0
    failed = 0

    for i, audio_file in enumerate(files, 1):
        console.print(f"\n[bold]({i}/{len(files)})[/bold] {audio_file.name}")

        try:
            # Transcribe only
            transcribe_audio(
                audio_path=audio_file,
                model_size=model.value,
                format="srt",
            )

            success += 1

        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            failed += 1

    console.print(
        f"\n[bold]Batch complete:[/bold] {success} success, {failed} failed"
    )


@app.command()
def play(
    audio_file: Annotated[
        Path,
        typer.Argument(
            help="Audio file to play with synced subtitles",
            exists=True,
            dir_okay=False,
        ),
    ],
    subtitle: Annotated[
        Optional[Path],
        typer.Option(
            "--subtitle",
            "-s",
            help="Subtitle file (default: auto-detect .srt/.lrc/.ttml)",
        ),
    ] = None,
):
    """
    Play audio with synced subtitles using mpv.

    Automatically finds and loads matching subtitle files.
    Requires mpv to be installed (sudo apt install mpv).

    Examples:
        baobao play song.mp3
        baobao play song.mp3 -s song.enhanced.srt
    """
    # Check if mpv is available
    if not shutil.which("mpv"):
        console.print("[bold red]Error:[/bold red] mpv not found")
        console.print("[dim]Install with: sudo apt install mpv[/dim]")
        raise typer.Exit(1)

    # Find subtitle file if not specified
    if subtitle is None:
        # Look for subtitle files in order of preference
        candidates = [
            audio_file.with_suffix(".enhanced.srt"),
            audio_file.with_suffix(".learn.srt"),
            audio_file.with_suffix(".emoji.srt"),
            audio_file.with_suffix(".srt"),
            audio_file.with_suffix(".lrc"),
            audio_file.with_suffix(".ttml"),
            # Also check for .test.srt pattern
            audio_file.with_suffix("").with_suffix(".test.enhanced.srt"),
            audio_file.with_suffix("").with_suffix(".test.srt"),
        ]

        for candidate in candidates:
            if candidate.exists():
                subtitle = candidate
                break

        if subtitle is None:
            console.print("[bold red]Error:[/bold red] No subtitle file found")
            console.print(
                f"[dim]Looked for: {audio_file.stem}.srt, .lrc, .ttml, etc.[/dim]"
            )
            console.print(
                f"[dim]Run 'baobao {audio_file.name}' first or specify with -s[/dim]"
            )
            raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]🐼 Baobao Player[/bold blue]\n"
            f"Audio: {audio_file.name}\n"
            f"Subtitle: {subtitle.name}",
            border_style="blue",
        )
    )

    console.print("\n[dim]Starting mpv... Press 'q' to quit[/dim]\n")

    # Run mpv with subtitles
    try:
        subprocess.run(
            ["mpv", f"--sub-file={subtitle}", str(audio_file)], check=True
        )
    except subprocess.CalledProcessError as e:
        console.print(
            f"[bold red]Error:[/bold red] mpv exited with code {e.returncode}"
        )
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass  # User quit with Ctrl+C


@app.command()
def preview(
    audio_file: Annotated[
        Path,
        typer.Argument(
            help="Audio file to preview",
            exists=True,
            dir_okay=False,
        ),
    ],
    subtitle: Annotated[
        Optional[Path],
        typer.Option(
            "--subtitle",
            "-s",
            help="Subtitle file (default: looks for .srt/.enhanced.srt)",
        ),
    ] = None,
):
    """
    Preview audio with synced subtitles using mpv.

    Automatically finds matching subtitle files if not specified.
    Requires mpv to be installed (sudo apt install mpv).

    Examples:
        baobao preview song.mp3
        baobao preview song.mp3 -s song.enhanced.srt
    """
    # Check if mpv is available
    if not shutil.which("mpv"):
        console.print("[bold red]Error:[/bold red] mpv not found")
        console.print("[dim]Install with: sudo apt install mpv[/dim]")
        raise typer.Exit(1)

    # Find subtitle file if not specified
    if subtitle is None:
        # Look for subtitle files in order of preference
        candidates = [
            audio_file.with_suffix(".enhanced.srt"),
            audio_file.with_suffix(".learn.srt"),
            audio_file.with_suffix(".emoji.srt"),
            audio_file.with_suffix(".srt"),
            # Also check for .test.srt pattern
            audio_file.with_suffix("").with_suffix(".test.enhanced.srt"),
            audio_file.with_suffix("").with_suffix(".test.srt"),
        ]

        for candidate in candidates:
            if candidate.exists():
                subtitle = candidate
                break

        if subtitle is None:
            console.print("[bold red]Error:[/bold red] No subtitle file found")
            console.print(
                f"[dim]Looked for: {audio_file.stem}.srt, .enhanced.srt, etc.[/dim]"
            )
            console.print(
                "[dim]Run 'baobao transcribe' first or specify with -s[/dim]"
            )
            raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]🐼 Baobao Preview[/bold blue]\n"
            f"Audio: {audio_file.name}\n"
            f"Subtitle: {subtitle.name}",
            border_style="blue",
        )
    )

    console.print("\n[dim]Starting mpv... Press 'q' to quit[/dim]\n")

    # Run mpv with subtitles
    try:
        subprocess.run(
            ["mpv", f"--sub-file={subtitle}", str(audio_file)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(
            f"[bold red]Error:[/bold red] mpv exited with code {e.returncode}"
        )
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass  # User quit with Ctrl+C


if __name__ == "__main__":
    app()
