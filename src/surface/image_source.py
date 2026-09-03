# Qt-free by design.
from pathlib import Path

from surface.protocol import ProtocolError

ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024

_BLOCKED_PREFIXES = ("http://", "https://", "data:", "file:")


def interpret_image_source(source: str) -> Path:
    """Prefiks, UNC, suffiks. Ingen filesystem-I/O.

    Raises:
        ProtocolError: empty_field | invalid_field
    """
    if not isinstance(source, str) or not source.strip():
        raise ProtocolError("empty_field", "empty field 'source'")
    stripped = source.strip()
    lowered = stripped.lower()
    # Prefix/UNC must be rejected before any is_file/stat so a network path
    # cannot hang the GUI thread.
    if lowered.startswith(_BLOCKED_PREFIXES):
        raise ProtocolError("invalid_field", "invalid field 'source'")
    if stripped.startswith("\\\\") or stripped.startswith("//"):
        raise ProtocolError("invalid_field", "invalid field 'source'")
    if Path(stripped).suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
        raise ProtocolError("invalid_field", "invalid field 'source'")
    return Path(stripped)


def resolve_image_file(source: str) -> Path:
    """interpret_image_source + cwd-resolve + is_file + størrelse.

    Raises:
        ProtocolError: som over, plus not-a-file / limit_exceeded
    """
    path = interpret_image_source(source)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.is_file():
        raise ProtocolError("invalid_field", "not a file")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ProtocolError(
            "limit_exceeded",
            f"field 'source' exceeds limit of {MAX_IMAGE_BYTES}",
        )
    return path
