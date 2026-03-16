from collections.abc import Callable

import spacy.tokens
from barks_fantagraphics.entity_types import EntityType
from barks_fantagraphics.whoosh_barks_terms import (
    BARKSIAN_ENTITY_TYPE_MAP,
    CAPITALIZATION_MAP,
)

# spaCy label → our entity category
SPACY_LABEL_MAP: dict[str, EntityType] = {
    "PERSON": EntityType.PERSON,
    "GPE": EntityType.LOCATION,
    "LOC": EntityType.LOCATION,
    "ORG": EntityType.ORG,
    "WORK_OF_ART": EntityType.WORK,
    "NORP": EntityType.MISC,
    "EVENT": EntityType.MISC,
    "FAC": EntityType.MISC,
    "PRODUCT": EntityType.MISC,
    "LAW": EntityType.MISC,
    "LANGUAGE": EntityType.MISC,
}

type EntityDict = dict[EntityType, set[str]]
type EntityTaggerFn = Callable[[str], EntityDict]


def _build_lower_map(mapping: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in mapping.items()}


class EntityTagger:
    def __init__(self) -> None:
        self._nlp = spacy.load("en_core_web_sm")

        self._single_word_entities: dict[str, EntityType] = {}  # lowercase → entity_type
        self._multi_word_entities: dict[str, EntityType] = {}  # lowercase → entity_type
        for term_set, entity_type in BARKSIAN_ENTITY_TYPE_MAP.items():
            for term in term_set:
                key = term.lower()
                if " " in term:
                    self._multi_word_entities[key] = entity_type
                else:
                    self._single_word_entities[key] = entity_type

        self._capitalization_map = _build_lower_map(CAPITALIZATION_MAP)

    def tag(self, text: str) -> EntityDict:
        result: EntityDict = {t: set() for t in EntityType}
        text_lower = text.lower().replace("\n", " ")
        doc = self._nlp(text)

        self._match_curated_full_names(text_lower, result)
        curated_spans = self._find_curated_spans(text_lower)
        self._match_spacy_entities(doc, curated_spans, result)
        self._match_curated_tokens(doc, result)

        return result

    def _match_curated_full_names(self, text_lower: str, result: EntityDict) -> None:
        for name, category in self._multi_word_entities.items():
            if name in text_lower:
                result[category].add(name.title() if category != EntityType.WORK else name)

    def _find_curated_spans(self, text_lower: str) -> set[tuple[int, int]]:
        spans: set[tuple[int, int]] = set()
        for name in self._multi_word_entities:
            start = 0
            while True:
                idx = text_lower.find(name, start)
                if idx == -1:
                    break
                spans.add((idx, idx + len(name)))
                start = idx + 1
        return spans

    def _match_spacy_entities(
        self,
        doc: spacy.tokens.Doc,
        curated_spans: set[tuple[int, int]],
        result: EntityDict,
    ) -> None:
        for ent in doc.ents:
            if ent.label_ not in SPACY_LABEL_MAP:
                continue
            # Skip if overlapping with a curated multi-word match
            if any(not (ent.end_char <= cs[0] or ent.start_char >= cs[1]) for cs in curated_spans):
                continue
            # Skip if entity text is in any curated single-word list
            ent_lower = ent.text.lower()
            if ent_lower in self._single_word_entities:
                continue
            result[SPACY_LABEL_MAP[ent.label_]].add(ent.text)

    def _match_curated_tokens(self, doc: spacy.tokens.Doc, result: EntityDict) -> None:
        for token in doc:
            token_lower = token.text.lower()
            if token_lower in self._single_word_entities:
                entity_type = self._single_word_entities[token_lower]
                result[entity_type].add(token.text.capitalize())
            if token_lower in self._capitalization_map:
                canonical = self._capitalization_map[token_lower]
                cat = self._classify_capitalization_entry(canonical)
                if cat:
                    result[cat].add(canonical)

    def _classify_capitalization_entry(self, canonical: str) -> EntityType:
        canonical_lower = canonical.lower()
        if canonical_lower in self._multi_word_entities:
            return self._multi_word_entities[canonical_lower]
        if canonical_lower in self._single_word_entities:
            return self._single_word_entities[canonical_lower]
        return EntityType.PERSON
