"""Directory archiver utility with live progress tracking.

Compresses a folder tree into a .zip archive, preserving relative paths
and displaying interactive progress in the terminal.
"""

from pathlib import Path
import zipfile
import click


def zip_folder(
    folder_path: Path | str,
    output_path: Path | str | None = None,
) -> Path:
    """Zip a directory into an archive file with live terminal progress.

    Args:
        folder_path: Source directory to archive.
        output_path: Destination .zip path (defaults to <folder_path>.zip).

    Returns:
        Path to the generated .zip archive.
    """
    source = Path(folder_path).resolve()
    if not source.is_dir():
        raise ValueError(f"Path is not a valid directory: {source}")

    target = Path(output_path).resolve() if output_path else source.parent / f"{source.name}.zip"

    # Collect all files first
    files: list[Path] = [p for p in source.rglob("*") if p.is_file() and p.resolve() != target]
    total_files = len(files)

    click.echo(f"  {click.style('📦', fg='cyan')} Zipping directory: {source}")
    click.echo(f"  {click.style('📁', fg='cyan')} Output archive:   {target}")
    click.echo(f"  {click.style('📄', fg='cyan')} Total files:      {total_files}")

    target.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for idx, file in enumerate(files, start=1):
            rel_name = file.relative_to(source.parent).as_posix()
            zipf.write(file, rel_name)

            percent = int((idx / total_files) * 100) if total_files else 100
            bar_len = 25
            filled = int(bar_len * (idx / total_files)) if total_files else bar_len
            bar = "█" * filled + "-" * (bar_len - filled)

            click.echo(f"\r  [{bar}] {percent:3d}% ({idx}/{total_files}) - {file.name[:30]:<30}", nl=False)

    click.echo("\n  " + click.style("✅ ZIP created successfully!", fg="green", bold=True))
    return target
