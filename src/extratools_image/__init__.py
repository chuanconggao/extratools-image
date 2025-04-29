from __future__ import annotations

import asyncio
from base64 import b64decode, b64encode
from enum import Enum
from http import HTTPStatus
from io import BytesIO

import backoff
import httpx
import truststore
from PIL.Image import Image
from PIL.Image import open as open_image

truststore.inject_into_ssl()

MAX_TRIES: int = 3
MAX_TIMEOUT: int = 60
REQUEST_TIMEOUT: int = 30


@backoff.on_predicate(
    backoff.expo,
    max_tries=MAX_TRIES,
    max_time=MAX_TIMEOUT,
)
async def download_image_async(
    image_url: str,
    *,
    user_agent: str | None = None,
) -> Image | None:
    async with httpx.AsyncClient().stream(
        "GET",
        image_url,
        follow_redirects=True,
        timeout=REQUEST_TIMEOUT,
        headers=(
            {
                "User-Agent": user_agent,
            } if user_agent
            else {}
        ),
    ) as response:
        if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            # It also triggers backoff if necessary
            return None

        response.raise_for_status()

        return bytes_to_image(await response.aread())


def download_image(
    image_url: str,
    *,
    user_agent: str | None = None,
) -> Image | None:
    return asyncio.run(download_image_async(
        image_url,
        user_agent=user_agent,
    ))


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


def image_to_data_url(image: Image, _format: str = "PNG") -> str:
    """
    Following https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data
    """

    return f"data:image/{_format.lower()};base64,{image_to_base64_str(image)}"


def base64_str_to_image(s: str) -> Image:
    return open_image(b64decode(s.encode()))


class CommonSize(Enum):
    """
    https://en.wikipedia.org/wiki/Display_resolution_standards
    """

    # 4:3
    VGA = (640, 480)
    SVGA = (800, 600)
    XGA = (1024, 768)
    SXGA = (1280, 1024)

    # 16:9
    _480p = SD = (854, 480)
    _720p = HD = (1280, 720)
    _2K = _1080p = FULL_HD = (1920, 1080)
    _3K = (2880, 1620)
    _4K = (3840, 2160)
    _5K = (5120, 2880)
    _8K = (7680, 4320)
    _16K = (15360, 8640)

    def __repr__(self) -> str:
        x, y = self.value
        return f"{self.name.rstrip('_').replace('_', '')} ({x}x{y})"
