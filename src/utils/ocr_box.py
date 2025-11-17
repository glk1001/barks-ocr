import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from shapely import MultiPoint

PointList = list[tuple[float, float]]


class OcrBox:
    def __init__(
        self,
        box_points: PointList,
        ocr_text: str,
        ocr_prob: float,
        accepted_text: str,
    ) -> None:
        self._box_points = box_points
        self.ocr_text = ocr_text
        self.ocr_prob = ocr_prob
        self.accepted_text = accepted_text

        min_rotated_rectangle_azimuth = self._get_min_rotated_rectangle_azimuth(
            MultiPoint(self._box_points).minimum_rotated_rectangle
        )
        # print(f"azimuth: {min_rotated_rectangle_azimuth}")
        self.is_approx_rect = (
            abs(min_rotated_rectangle_azimuth) < 5.0  # noqa: PLR2004
            or abs(min_rotated_rectangle_azimuth - 180) < 5.0  # noqa: PLR2004
            or abs(min_rotated_rectangle_azimuth - 90) < 5.0  # noqa: PLR2004
        )
        if self.is_approx_rect:
            self.min_rotated_rectangle = self._get_envelope()
        else:
            self.min_rotated_rectangle = self._get_min_rotated_rectangle()

    def get_state(self) -> dict[str, Any]:
        return {
            "box_points": self._box_points,
            "ocr_text": self.ocr_text,
            "ocr_prob": self.ocr_prob,
            "accepted_text": self.accepted_text,
        }

    def _get_envelope(self) -> PointList:
        rect = MultiPoint(self._box_points).envelope
        coords = rect.exterior.coords
        bottom_left = coords[0]
        top_right = coords[2]
        return [bottom_left, top_right]

    def _get_min_rotated_rectangle(self) -> PointList:
        rect = MultiPoint(self._box_points).minimum_rotated_rectangle
        coords = rect.exterior.coords
        return [coords[0], coords[1], coords[2], coords[3]]

    def _get_min_rotated_rectangle_azimuth(self, rotated_rect):
        bbox = list(rotated_rect.exterior.coords)
        axis1 = self._get_dist_between_points(bbox[0], bbox[3])
        axis2 = self._get_dist_between_points(bbox[0], bbox[1])

        if axis1 <= axis2:
            az = self._get_azimuth_between_points(bbox[0], bbox[1])
        else:
            az = self._get_azimuth_between_points(bbox[0], bbox[3])

        return az

    @staticmethod
    def _get_azimuth_between_points(point1, point2):
        angle = np.arctan2(point2[1] - point1[1], point2[0] - point1[0])
        return np.degrees(angle) if angle > 0 else np.degrees(angle) + 180

    @staticmethod
    def _get_dist_between_points(a, b):
        return math.hypot(b[0] - a[0], b[1] - a[1])


def load_groups_from_json(file: Path) -> dict[int, list[tuple[OcrBox, float]]]:
    with file.open("r") as f:
        json_groups = json.load(f)

    groups: dict[int, list[tuple[OcrBox, float]]] = {}
    for key in json_groups:
        for box_tuple in json_groups[key]:
            json_ocr_box = box_tuple[0]
            dist = box_tuple[1]
            ocr_box = OcrBox(
                json_ocr_box["box_points"],
                json_ocr_box["ocr_text"],
                json_ocr_box["ocr_prob"],
                json_ocr_box["accepted_text"],
            )
            ikey = int(key)
            if ikey not in groups:
                groups[ikey] = [(ocr_box, dist)]
            else:
                groups[ikey].append((ocr_box, dist))

    return groups


def save_groups_as_json(groups: dict[int, list[tuple[OcrBox, float]]], file: Path) -> None:

    def custom_ocr_box(obj):
        if isinstance(obj, OcrBox):
            return obj.get_state()
        return obj

    with file.open("w") as f:
        json.dump(groups, f, indent=4, default=custom_ocr_box)


def get_box_str(box_pts: PointList) -> str:
    assert len(box_pts) == 4  # noqa: PLR2004
    return (
        f"{round(box_pts[0][0]):04},{round(box_pts[0][1]):04},"
        f" {round(box_pts[1][0]):04},{round(box_pts[1][1]):04},"
        f" {round(box_pts[2][0]):04},{round(box_pts[2][1]):04},"
        f" {round(box_pts[3][0]):04},{round(box_pts[3][1]):04}"
    )
