"""
Upload paths and validators.

Two rules from CLAUDE.md section 10, applied to every file field on the site:
uploads are validated by type and size, and a client-supplied filename is
never trusted.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image, UnidentifiedImageError

# Extensions we are willing to store. SVG is excluded on purpose: it is an
# XML document that can carry script, and it would be served from our own
# media origin.
ALLOWED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"})
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".pdf"})
ALLOWED_VIDEO_EXTENSIONS = frozenset({".mp4", ".webm"})


def validate_media_file(value):
    """Check the actual container/image format, never the browser MIME claim."""
    extension = Path(value.name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError("Upload a supported image, MP4 or WebM file.")
    value.open("rb")
    position = value.tell()
    try:
        header = value.read(64)
        value.seek(0)
        if extension in ALLOWED_IMAGE_EXTENSIONS:
            try:
                image = Image.open(value)
                expected = {
                    ".jpg": "JPEG",
                    ".jpeg": "JPEG",
                    ".png": "PNG",
                    ".gif": "GIF",
                    ".webp": "WEBP",
                    ".avif": "AVIF",
                }
                if image.format != expected[extension]:
                    raise ValidationError("Image contents do not match its extension.")
                image.verify()
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
                raise ValidationError("The uploaded image is invalid.") from exc
        elif extension == ".mp4":
            if header[4:8] != b"ftyp" or header[8:12] not in (
                b"isom",
                b"iso2",
                b"mp41",
                b"mp42",
                b"avc1",
                b"M4V ",
                b"dash",
            ):
                raise ValidationError("The uploaded file is not a supported MP4 container.")
        elif not (header.startswith(b"\x1a\x45\xdf\xa3") and b"webm" in header):
            raise ValidationError("The uploaded file is not a WebM container.")
    finally:
        value.seek(position)


def validate_image_file(value):
    if Path(value.name).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Upload a JPEG, PNG, WebP, AVIF or GIF image.")
    validate_media_file(value)


def validate_video_file(value):
    if Path(value.name).suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError("Upload an MP4 or WebM video.")
    validate_media_file(value)


def validate_upload_size(value) -> None:
    """Reject anything over MAX_UPLOAD_SIZE_BYTES."""
    limit = settings.MAX_UPLOAD_SIZE_BYTES
    if value.size > limit:
        raise ValidationError(
            f"File is {value.size // 1024} KB. The limit is {limit // 1024} KB.",
            code="upload_too_large",
        )


@deconstructible
class UploadTo:
    """
    Generates the stored path for an upload, discarding the client's filename.

    The original name is used only to read an extension, which is then checked
    against an allowlist. The stored name is a fresh UUID, so a caller cannot
    choose where the file lands, overwrite someone else's upload, or smuggle
    a path separator or a double extension through.

    Deconstructible so it can be referenced from a migration.
    """

    def __init__(self, prefix: str, allowed: frozenset[str] = ALLOWED_IMAGE_EXTENSIONS):
        self.prefix = prefix.strip("/")
        self.allowed = allowed

    def __call__(self, _instance, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in self.allowed:
            permitted = ", ".join(sorted(self.allowed))
            raise ValidationError(
                f"{extension or 'That file type'} is not allowed. Permitted: {permitted}.",
                code="upload_type_not_allowed",
            )

        return f"{self.prefix}/{uuid.uuid4().hex}{extension}"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, UploadTo)
            and other.prefix == self.prefix
            and other.allowed == self.allowed
        )

    def __hash__(self) -> int:
        return hash((self.prefix, self.allowed))
