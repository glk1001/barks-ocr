import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from barks_fantagraphics.entity_types import EntityType


def _entity_filename(volume: int) -> str:
    return f"entities-vol-{volume:02d}.json"


def _corrections_filename(volume: int) -> str:
    return f"entity-corrections-vol-{volume:02d}.json"


def save_auto_entities(entities_dir: Path, volume: int, volume_entities: dict) -> None:
    data = {
        "volume": volume,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "groups": volume_entities,
    }
    path = entities_dir / _entity_filename(volume)
    path.write_text(json.dumps(data, indent=4) + "\n")


def load_auto_entities(entities_dir: Path, volume: int) -> dict:
    path = entities_dir / _entity_filename(volume)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("groups", {})


def load_corrections(entities_dir: Path, volume: int) -> dict:
    path = entities_dir / _corrections_filename(volume)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("corrections", {})


def _apply_corrections(
    auto_entities: dict[str, set[str]], corrections: dict
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for entity_type in EntityType:
        auto_set = set(auto_entities.get(entity_type, set()))
        type_corrections = corrections.get(entity_type, {}) if isinstance(corrections, dict) else {}

        if "replace" in type_corrections:
            result[entity_type] = set(type_corrections["replace"])
        else:
            if "add" in type_corrections:
                auto_set |= set(type_corrections["add"])
            if "remove" in type_corrections:
                auto_set -= set(type_corrections["remove"])
            result[entity_type] = auto_set

    return result


def merge_entities(auto: dict[str, set[str]], corrections: dict) -> dict[str, set[str]]:
    if not corrections:
        return auto
    return _apply_corrections(auto, corrections)


def get_merged_entity_provider(
    entities_dir: Path, volumes: list[int]
) -> Callable[[str, str, str], dict[str, set[str]]]:
    cache: dict[int, tuple[dict, dict]] = {}
    for vol in volumes:
        cache[vol] = (load_auto_entities(entities_dir, vol), load_corrections(entities_dir, vol))

    def provider(title: str, fanta_page: str, group_id: str) -> dict[str, set[str]]:
        for auto_groups, corrections in cache.values():
            title_groups = auto_groups.get(title, {})
            page_groups = title_groups.get(fanta_page, {})
            group_entities = page_groups.get(group_id, {})
            if group_entities:
                group_corrections = corrections.get(title, {}).get(fanta_page, {}).get(group_id, {})
                auto_sets = {k: set(v) for k, v in group_entities.items()}
                return merge_entities(auto_sets, group_corrections)

        return {t: set() for t in EntityType}

    return provider
