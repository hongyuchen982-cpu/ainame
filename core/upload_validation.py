from pathlib import Path, PureWindowsPath


ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
}


def sanitize_upload_filename(raw_name: str | None) -> str:
    """Return a display-only basename for POSIX and Windows upload names."""
    if not raw_name or "\x00" in raw_name:
        raise ValueError("文件名无效")
    filename = PureWindowsPath(raw_name).name
    filename = Path(filename).name.strip()
    if not filename or filename in {".", ".."}:
        raise ValueError("文件名无效")
    return filename


def validate_upload_metadata(
    raw_name: str | None,
    raw_content_type: str | None,
) -> tuple[str, str, str]:
    filename = sanitize_upload_filename(raw_name)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 PDF、TXT 文件")
    content_type = (raw_content_type or "").lower().split(";", 1)[0].strip()
    if content_type not in ALLOWED_MIME_TYPES[extension]:
        raise ValueError("文件 MIME 类型与扩展名不匹配")
    return filename, extension, content_type


def resolve_upload_path(raw_path: str, upload_dir: Path) -> Path:
    """Resolve current and legacy Windows paths strictly inside the upload root."""
    upload_root = upload_dir.resolve()
    direct_path = Path(raw_path).expanduser()
    if direct_path.is_file():
        resolved = direct_path.resolve()
    else:
        filename = PureWindowsPath(raw_path).name if "\\" in raw_path else direct_path.name
        resolved = (upload_root / filename).resolve()
    if upload_root not in resolved.parents:
        raise ValueError("知识库文件路径不安全")
    return resolved
