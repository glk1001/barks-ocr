"""A local browser page for reviewing panels: click to label, Save to write the labels.

The page (``resources/panel-review.html``) talks only to the server here, which binds to
127.0.0.1. What it offers and how labels are stored belong to a :class:`ReviewSession`:
a menu of named sets of panels, each panel's caption, scores and label, and its image.
"""

# ruff: noqa: T201

import errno
import json
import threading
import webbrowser
from abc import ABC, abstractmethod
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import parse_qs, urlsplit

import cv2
import numpy as np
import typer
from loguru import logger

LABELS = ("yes", "no", "unsure")
REVIEW_PAGE = Path(__file__).parents[1] / "resources" / "panel-review.html"
REVIEW_THUMB_W = 840
DEFAULT_PORT = 8765
DEFAULT_REVIEW_LIMIT = 300


class ReviewPanel(Protocol):
    """What the server needs of a panel."""

    @property
    def label(self) -> str | None:
        """The panel's reviewed label, if any."""
        ...

    def image(self, width: int | None = None) -> np.ndarray:
        """Return the panel's image as RGB, optionally narrowed."""
        ...


class ReviewSession[P: ReviewPanel](ABC):
    """The panels a review page offers, per named set, and how their labels are written."""

    def __init__(self, panels: dict[str, list[P]]) -> None:
        """Keep the panels on offer: set name to panels, in the order the page shows them."""
        self.panels = panels
        self.lock = threading.Lock()

    def things_data(self) -> list[dict[str, Any]]:
        """Return each set's name, panels shown and how many are labelled."""
        return [
            {"thing": t, "shown": len(ps), "labelled": sum(p.label is not None for p in ps)}
            for t, ps in self.panels.items()
        ]

    @abstractmethod
    def panels_data(self, thing: str) -> dict[str, Any]:
        """Return what the page shows for a set.

        The keys are ``thing``, ``question`` (shown above the panels), ``cutoff`` and
        ``panels``, each with ``caption``, ``score``, ``scores`` (shown beside the caption)
        and ``label``. An unlabelled panel starts as yes when its ``score`` is at or above
        ``cutoff``, otherwise as no. A ``cutoff`` of None hides the Cut-off box and starts
        every unlabelled panel as yes.
        """

    @abstractmethod
    def write_labels(self, panels: list[P], labels: dict[int, str | None]) -> dict[str, int]:
        """Write labels (by position in ``panels``, None clears) and count them by label."""

    def image_jpeg(self, thing: str, k: str) -> bytes | None:
        """Return panel k of a set as a JPEG, or None if there is none."""
        panels = self.panels.get(thing, [])
        if not k.isdigit() or int(k) >= len(panels):
            return None
        rgb = panels[int(k)].image(REVIEW_THUMB_W)
        _, jpg = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        return jpg.tobytes()

    def save(self, thing: str, labels: dict[str, str | None]) -> dict[str, int] | None:
        """Write a set's labels (panel position -> label); None if any is out of range."""
        panels = self.panels.get(thing, [])
        by_index = {int(k): v for k, v in labels.items() if k.isdigit()}
        if len(by_index) != len(labels) or any(
            k >= len(panels) or v not in (*LABELS, None) for k, v in by_index.items()
        ):
            return None
        with self.lock:
            counts = self.write_labels(panels, by_index)
        logger.info(f"Review of {thing}: saved {counts} (source human).")
        print(f"Saved {thing}: {counts}")
        return counts


def _route(path: str) -> tuple[str, dict[str, str]]:
    """Split a request path into its route and query parameters."""
    parts = urlsplit(path)
    return parts.path, {k: v[0] for k, v in parse_qs(parts.query).items()}


class ReviewHandler(BaseHTTPRequestHandler):
    """Requests of the review page; :func:`review_handler` binds a session to it."""

    session: ReviewSession[Any]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, ANN401
        logger.debug(format % args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: object) -> None:
        self._send(HTTPStatus.OK, json.dumps(data).encode(), "application/json")

    def do_GET(self) -> None:
        route, query = _route(self.path)
        thing = query.get("thing", "")
        if route == "/":
            self._send(HTTPStatus.OK, REVIEW_PAGE.read_bytes(), "text/html; charset=utf-8")
        elif route == "/things.json":
            self._json(self.session.things_data())
        elif route == "/panels.json" and thing in self.session.panels:
            self._json(self.session.panels_data(thing))
        elif route == "/img" and (jpg := self.session.image_jpeg(thing, query.get("k", ""))):
            self._send(HTTPStatus.OK, jpg, "image/jpeg")
        else:
            self._send(HTTPStatus.NOT_FOUND, b"", "text/plain")

    def do_POST(self) -> None:
        route, query = _route(self.path)
        if route != "/save":
            self._send(HTTPStatus.NOT_FOUND, b"", "text/plain")
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        counts = self.session.save(query.get("thing", ""), body.get("labels", {}))
        if counts is None:
            self._send(HTTPStatus.BAD_REQUEST, b"bad thing or label", "text/plain")
        else:
            self._json(counts)


def review_handler(session: ReviewSession[Any]) -> type[BaseHTTPRequestHandler]:
    """Return the review page's request handler bound to a session."""
    return type("BoundReviewHandler", (ReviewHandler,), {"session": session})


def run_review(
    session: ReviewSession[Any], port: int, on_stop: Callable[[], None] | None = None
) -> None:
    """Serve the review page on localhost until Ctrl-C.

    Args:
        session: What the page offers.
        port: The local port.
        on_stop: Called when the server stops, not when it could not start.

    Raises:
        typer.Exit: If the port is already in use.

    """
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), review_handler(session))
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        print(f"Port {port} is in use (another review page running?); try --port {port + 1}.")
        raise typer.Exit(code=1) from exc
    url = f"http://127.0.0.1:{port}/"
    shown = sum(len(ps) for ps in session.panels.values())
    sets = "" if len(session.panels) == 1 else f"{len(session.panels)} sets, "
    print(f"Reviewing {sets}{shown} panels at {url} -- Ctrl-C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()
        if on_stop is not None:
            on_stop()
