"""Minimal client for TypeSafe's Jev (System One API): one image, yes/no questions.

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
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class NoulAnswers:
    """Answers to several questions about one image, keyed by question id.

    ``boxes`` holds the box questions' answers as (left, top, right, bottom) fractions of
    the image passed in (not of the padded copy sent), with Jev's confidence, which may
    be None. A box is always returned, even for something absent: pair it with a yes/no
    question and ignore the box when that answer is low.
    """

    probabilities: dict[str, float]
    model: str
    input_tokens: int
    boxes: dict[str, tuple[tuple[float, float, float, float], float | None]] = field(
        default_factory=dict
    )


class JevError(RuntimeError):
    """A request Jev refused for a reason retrying will not fix (key, credits, format)."""


def fit_image(rgb: np.ndarray) -> np.ndarray:
    """Scale an image so its longer side is at most 1568 px, then pad short sides to 280.

    Padding (white) rather than upscaling keeps a thin banner panel's detail unchanged.
    """
    return _fit(rgb)[0]


def _fit(rgb: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Fit an image (see :func:`fit_image`), also returning where it sits in the result.

    Returns:
        The fitted image and (left, top, width, height) of the scaled original within it.

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
    return rgb, (pad_w // 2, pad_h // 2, w, h)


def _unfit_box(
    box: dict[str, float], fitted: tuple[int, int], placed: tuple[int, int, int, int]
) -> tuple[float, float, float, float]:
    """Map a box from fractions of the fitted image to fractions of the original."""
    fw, fh = fitted
    left, top, w, h = placed

    def fx(v: float) -> float:
        return min(1.0, max(0.0, (v * fw - left) / w))

    def fy(v: float) -> float:
        return min(1.0, max(0.0, (v * fh - top) / h))

    return fx(box["left"]), fy(box["top"]), fx(box["right"]), fy(box["bottom"])


class JevClient:
    """Ask Jev yes/no questions about one image per request."""

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
        """Ask one yes/no question about an image, which the instructions call `image`.

        Args:
            rgb: The image, RGB uint8; it is fitted to Jev's size limits first.
            instructions: The question; refer to the picture as `image`.

        Returns:
            The answer.

        Raises:
            JevError: On a non-retryable refusal, or when every retry failed.

        """
        answers = self.ask_image_questions(rgb, {"q": instructions})
        return NoulAnswer(answers.probabilities["q"], answers.model, answers.input_tokens)

    def ask_image_questions(
        self, rgb: np.ndarray, questions: dict[str, str], boxes: dict[str, str] | None = None
    ) -> NoulAnswers:
        """Ask several yes/no (and optionally box) questions about one image in one request.

        The image goes in the request's ``state``, which every question shares, rather than
        in each question's instructions (which would send it once per question).

        Args:
            rgb: The image, RGB uint8; it is fitted to Jev's size limits first.
            questions: Question id (an identifier) to instructions; call the picture `image`.
            boxes: Box question id to what to find, e.g. "the camera in `image`"; ids must
                differ from the yes/no ones.

        Returns:
            The answers, keyed by question id.

        Raises:
            JevError: On a non-retryable refusal, or when every retry failed.

        """
        boxes = boxes or {}
        fitted, placed = _fit(rgb)
        ok, png = cv2.imencode(".png", cv2.cvtColor(fitted, cv2.COLOR_RGB2BGR))
        if not ok:
            msg = "PNG encoding failed."
            raise JevError(msg)
        request = {
            "model": MODEL,
            "state": {"image": "img"},
            "assets": {"img": {"type": "image", "part": "image-part"}},
            "questions": {
                **{qid: {"type": "noul", "instructions": text} for qid, text in questions.items()},
                **{qid: {"type": "box", "instructions": text} for qid, text in boxes.items()},
            },
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
                    size = (fitted.shape[1], fitted.shape[0])
                    return NoulAnswers(
                        probabilities={
                            qid: float(body["answers"][qid]["noul"]) for qid in questions
                        },
                        model=str(body["model"]),
                        input_tokens=int(body.get("usage", {}).get("input_tokens", 0)),
                        boxes={
                            qid: (
                                _unfit_box(body["answers"][qid]["box"], size, placed),
                                body["answers"][qid].get("confidence"),
                            )
                            for qid in boxes
                        },
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
