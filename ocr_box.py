import json
from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class OcrBox:
    box_points: List[Tuple[float, float]]
    is_rect: bool
    ocr_text: str
    ocr_prob: float
    accepted_text: str


def load_groups_from_json(file: str) -> Dict[int, List[Tuple[OcrBox, float]]]:
    with open(file, "r") as f:
        json_groups = json.load(f)

    groups: Dict[int, List[Tuple[OcrBox, float]]] = dict()
    for key in json_groups:
        for box_tuple in json_groups[key]:
            json_ocr_box = box_tuple[0]
            dist = box_tuple[1]
            ocr_box = OcrBox(
                json_ocr_box["box_points"],
                json_ocr_box["is_rect"],
                json_ocr_box["ocr_text"],
                json_ocr_box["ocr_prob"],
                json_ocr_box["accepted_text"],
            )
            key = int(key)
            if key not in groups:
                groups[key] = [(ocr_box, dist)]
            else:
                groups[key].append((ocr_box, dist))

    return groups


def save_groups_as_json(groups: Dict[int, List[Tuple[OcrBox, float]]], file: str) -> None:

    def custom_ocr_box(obj):
        if isinstance(obj, OcrBox):
            return obj.__dict__
        return obj

    with open(file, "w") as f:
        json.dump(groups, f, indent=4, default=custom_ocr_box)


def get_box_str(box_pts: List[Tuple[float, float]]) -> str:
    assert len(box_pts) == 4
    return (
        f"{round(box_pts[0][0]):04},{round(box_pts[0][1]):04},"
        f" {round(box_pts[1][0]):04},{round(box_pts[1][1]):04},"
        f" {round(box_pts[2][0]):04},{round(box_pts[2][1]):04},"
        f" {round(box_pts[3][0]):04},{round(box_pts[3][1]):04}"
    )
