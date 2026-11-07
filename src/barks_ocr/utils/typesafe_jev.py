"""Minimal client for TypeSafe's Jev (System One API): one image, one yes/no question.

Docs: https://docs.typesafe.ai (images.md, api.md). Image support is marked "Dreamer-ready"
(experimental) by TypeSafe and needs the ``TypeSafe-Danger-Zone-Images`` header. Images
must be PNG/JPEG with each side 280-1568 px; out-of-range images are rejected, never
resized, so :func:`fit_image` does that here. Billing is per input token (an ~900x640
comic panel costs ~1,900 tokens); output tokens are free.

The key is ``TYPESAFE_API_KEY`` in the repo's ``.env.runtime``.
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import httpx
import numpy as np
from dotenv import load_dotenv
from loguru import logger

load_dotenv(Path(__file__).parents[3] / ".env.runtime")

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
MIN_SIDE, MAX_SIDE = 280, 1568
RETRY_STATUSES = {429, 500, 502, 503, 504, 529}
MAX_TRIES = 5
TIMEOUT_S = 60.0


@dataclass(frozen=True)
class NoulAnswer:
    """A yes/no answer: the probability of yes, the model that answered, tokens billed."""

    probability: float
    model: str
    input_tokens: int


class JevError(RuntimeError):
    """A request Jev refused for a reason retrying will not fix (key, credits, format)."""


def fit_image(rgb: np.ndarray) -> np.ndarray:
    """Scale an image so its longer side is at most 1568 px, then pad short sides to 280.

    Padding (white) rather than upscaling keeps a thin banner panel's detail unchanged.
    """
    h, w = rgb.shape[:2]
    if max(h, w) > MAX_SIDE:
        s = MAX_SIDE / max(h, w)
        rgb = cv2.resize(rgb, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
        h, w = rgb.shape[:2]
    pad_h, pad_w = max(0, MIN_SIDE - h), max(0, MIN_SIDE - w)
    if pad_h or pad_w:
        rgb = cv2.copyMakeBorder(
            rgb, pad_h // 2, pad_h - pad_h // 2, pad_w // 2, pad_w - pad_w // 2,
            cv2.BORDER_CONSTANT, value=(255, 255, 255),
        )  # fmt: skip
    return rgb


class JevClient:
    """Ask Jev one yes/no question about one image per request."""

    def __init__(self, api_key: str | None = None) -> None:
        """Create a client.

        Args:
            api_key: The TypeSafe key; defaults to ``TYPESAFE_API_KEY`` from ``.env.runtime``.

        Raises:
            JevError: If no key is available.

        """
        key = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not key:
            msg = "TYPESAFE_API_KEY is not set (add it to the repo's .env.runtime)."
            raise JevError(msg)
        self._headers = {"Authorization": f"Bearer {key}", "TypeSafe-Danger-Zone-Images": "true"}
        self._http = httpx.Client(timeout=TIMEOUT_S)

    def ask_image_noul(self, rgb: np.ndarray, instructions: str) -> NoulAnswer:
        """Ask a yes/no question about an image, which the instructions call `image`.

        Args:
            rgb: The image, RGB uint8; it is fitted to Jev's size limits first.
            instructions: The question; refer to the picture as `image`.

        Returns:
            The answer.

        Raises:
            JevError: On a non-retryable refusal, or when every retry failed.

        """
        ok, png = cv2.imencode(".png", cv2.cvtColor(fit_image(rgb), cv2.COLOR_RGB2BGR))
        if not ok:
            msg = "PNG encoding failed."
            raise JevError(msg)
        request = {
            "model": MODEL,
            "state": {"image": "img"},
            "assets": {"img": {"type": "image", "part": "image-part"}},
            "questions": {"q": {"type": "noul", "instructions": instructions}},
        }
        files = {
            "request": (None, json.dumps(request), "application/json"),
            "image-part": ("image.png", png.tobytes(), "image/png"),
        }
        for attempt in range(1, MAX_TRIES + 1):
            try:
                r = self._http.post(ENDPOINT, headers=self._headers, files=files)
            except httpx.TransportError as exc:
                status, detail = None, str(exc)
            else:
                if r.status_code == httpx.codes.OK:
                    body = r.json()
                    return NoulAnswer(
                        probability=float(body["answers"]["q"]["noul"]),
                        model=str(body["model"]),
                        input_tokens=int(body.get("usage", {}).get("input_tokens", 0)),
                    )
                status, detail = r.status_code, r.text[:300]
                if status not in RETRY_STATUSES:
                    msg = f"Jev refused the request: HTTP {status}: {detail}"
                    raise JevError(msg)
            wait = 2.0**attempt
            logger.warning(f"Jev attempt {attempt} failed ({status}: {detail}); retry in {wait}s.")
            time.sleep(wait)
        msg = f"Jev failed after {MAX_TRIES} attempts."
        raise JevError(msg)
