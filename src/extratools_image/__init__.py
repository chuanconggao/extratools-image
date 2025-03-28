from base64 import b64decode, b64encode
from io import BytesIO

from PIL.Image import Image
from PIL.Image import open as open_image


def image_to_bytes(image: Image, _format: str = "PNG") -> bytes:
    bio = BytesIO()
    image.save(bio, format=_format)
    return bio.getvalue()


def bytes_to_image(b: bytes, _format: str | None = None) -> Image:
    return open_image(
        BytesIO(b),
        formats=((_format,) if _format else None),
    )


def image_to_base64_str(image: Image, _format: str = "PNG") -> str:
    return b64encode(image_to_bytes(image, _format)).decode()


def base64_str_to_image(s: str) -> Image:
    return open_image(b64decode(s.encode()))
