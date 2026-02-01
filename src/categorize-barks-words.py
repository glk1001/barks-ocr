# ruff: noqa: T201

import json
from argparse import ArgumentParser
from collections import defaultdict
from enum import Enum
from pathlib import Path

import nltk
import pycountry
from barks_fantagraphics.barks_words import BARKSIAN_SPELLING
from spellchecker import SpellChecker


def is_float(value: str) -> bool:
    try:
        float(value)
    except (ValueError, TypeError):
        return False
    else:
        return True


def is_int(value: str) -> bool:
    try:
        int(value)
    except (ValueError, TypeError):
        return False
    else:
        return True


# --- NLTK Setup and Downloads ---
def setup_nltk() -> None:
    """Ensure necessary NLTK data is downloaded."""
    print("Initializing dictionaries (this may take a moment)...")
    try:
        nltk.data.find("corpora/names")
    except LookupError:
        print("Downloading NLTK names corpus...")
        nltk.download("names", quiet=True)


class Categories(Enum):
    EMPTY = "Empty"
    SYMBOL_OR_PUNC = "Symbol/Punctuation"
    ABBREVIATION = "Abbreviation"
    DOT_ABBREVIATION = "Dot Abbreviation"
    NUMBER = "Number"
    DECIMAL = "Decimal"
    CORRECTLY_SPELLED = "Correctly Spelled"
    BARKSIAN_SPELLED = "Barksian Spelled"
    COMMON_SLANG = "Common Slang"
    KNOWN_PLACE_NAMES = "Known Place Names"
    POSSIBLE_PLACE_NAMES = "Possible Place Names"
    KNOWN_PEOPLE_NAMES = "Known People Names"
    POSSIBLE_PEOPLE_NAMES = "Possible People Names"
    POSSIBLE_SLANG = "Possible Slang"
    UNCATEGORIZED = "Uncategorized"


class BarksCategorizer:
    def __init__(self) -> None:
        setup_nltk()

        # English Dictionary
        self.spell = SpellChecker()

        self.spell.word_frequency.load_words(
            [
                "boomtown",
            ]
        )

        # Known People Names (English + manual Spanish/Comic additions)
        self.known_names = set(nltk.corpus.names.words("male.txt")) | set(
            nltk.corpus.names.words("female.txt")
        )
        self.known_names.update(
            [
                "Ana",
                "Antonio",
                "Beagle",
                "Biglook",
                "Bombastro",
                "Bombie",
                "Booneheads",
                "Bosco",
                "Carlos",
                "Diamondtubs",
                "Ellic",
                "Edgars",
                "Fizzlebudget",
                "Flinthide",
                "Gearloose",
                "Gilfinkle",
                "Giltwhiskers",
                "Gladstone",
                "Glomgold",
                "Gnapoleon",
                "Gnatbugg-Mothley",
                "Gnostradamus",
                "Gobblechin",
                "Goldbeak",
                "Goofy",
                "Groanbalm",
                "Gyro",
                "Iglook",
                "Jesus",
                "Jorge",
                "Jose",
                "Juan",
                "Lazy-K",
                "Luis",
                "Magica",
                "Manuel",
                "Maria",
                "Miguel",
                "Morganbilt",
                "Nevvawaza",
                "Pedro",
                "Philo",
                "Sevenchins",
                "Smoogle-Snaghles",
                "Smorgie",
                "Snootsbury",
                "Socrapossi",
                "Squattie",
                "Swansdown-Swoonsudden",
                "Tweeksdale",
                "Wormsley",
            ]
        )
        self.known_names = {n.lower() for n in self.known_names}
        self.known_names -= {
            "bay",
            "canada",
            "derby",
            "derrick",
            "florida",
            "georgia",
            "guy",
            "hagtooth",
            "valencia",
            "venus",
        }

        # Known Place Names (Countries and States)
        self.known_places = set()
        for country in pycountry.countries:
            self.known_places.add(country.name.lower())
            # Add 3-letter codes, like 'USA' or 'GBR' if available
            if hasattr(country, "alpha_3"):
                self.known_places.add(country.alpha_3.lower())
        for place in pycountry.subdivisions:
            self.known_places.add(place.name.lower())
        self.known_places.update(
            [
                "Burma",
                "Calcutta",
                "Floodout",
                "Frozenbear",
                "Scroogeville-on-the-Latex",
                "Timbuctoo",
                "Venus",
                "Volcanovia",
                "Volcanovian",
                "Waha-Go-Gaga",
            ]
        )
        self.known_places = {n.lower() for n in self.known_places}
        self.place_suffixes = (
            "burg",
            "ville",
            "town",
            "land",
            "sota",
            "ia",
            "ford",
            "shire",
            "stan",
        )

        # Common Slang / Exclamations (Carl Barks style)
        self.common_slang = {
            "gosh",
            "gee",
            "jeepers",
            "ya",
            "fer",
            "yer",
            "naw",
            "yep",
            "nope",
            "golly",
            "heck",
            "darn",
            "dang",
            "aw",
            "er",
            "uh",
            "um",
            "shucks",
            "sheesh",
            "swell",
            "feller",
            "kinda",
            "oughta",
            "gonna",
            "wanna",
            "yow",
            "ulp",
            "awk",
            "quack",
        }

    def get_category(self, original_word: str) -> Categories:  # noqa: PLR0911
        """Analyse a single word and return (Category ID, Category Name)."""
        word = original_word.strip()

        is_in_dictionary = len(self.spell.known([word])) > 0

        cat_id = self.check_easy_categories(word, is_in_dictionary)
        if cat_id != Categories.UNCATEGORIZED:
            return cat_id

        if word.lower() in BARKSIAN_SPELLING:
            return Categories.BARKSIAN_SPELLED

        cat_id = self.check_people_names(word, is_in_dictionary)
        if cat_id != Categories.UNCATEGORIZED:
            return cat_id

        cat_id = self.check_places(word, is_in_dictionary)
        if cat_id != Categories.UNCATEGORIZED:
            return cat_id

        cat_id = self.check_slang(word, is_in_dictionary)
        if cat_id != Categories.UNCATEGORIZED:
            return cat_id

        cat_id = self.check_possibilities(word, is_in_dictionary)
        if cat_id != Categories.UNCATEGORIZED:
            return cat_id

        # --- CHECK: Correctly Spelled ---
        if is_in_dictionary:
            return Categories.CORRECTLY_SPELLED

        return Categories.UNCATEGORIZED

    @staticmethod
    def check_easy_categories(word: str, is_in_dictionary: bool) -> Categories:  # noqa: PLR0911
        if is_in_dictionary:
            return Categories.UNCATEGORIZED

        if not word:
            return Categories.EMPTY

        # --- CHECK: Abbreviated ---
        # CHECK Abbreviation: Starts/Ends with apostrophe ('lo, knockin')
        if word.startswith("'") or word.endswith("'"):
            return Categories.ABBREVIATION

        # --- CHECK: Number or decimal ---
        if is_int(word):
            return Categories.NUMBER
        if is_float(word):
            return Categories.DECIMAL

        # CHECK Abbreviation: Contains dots: (a.d., g.i., Mr.)
        if "." in word:
            return Categories.DOT_ABBREVIATION

        return Categories.UNCATEGORIZED

    def check_places(self, word: str, _is_in_dictionary: bool) -> Categories:
        # --- CHECK: Known Place Names ---
        if word.lower() in self.known_places:
            return Categories.KNOWN_PLACE_NAMES

        return Categories.UNCATEGORIZED

    def check_people_names(self, word: str, _is_in_dictionary: bool) -> Categories:
        if word.lower() in self.known_names:
            return Categories.KNOWN_PEOPLE_NAMES

        if word.endswith("'s") and word.removesuffix("'s") in self.known_names:
            return Categories.KNOWN_PEOPLE_NAMES

        return Categories.UNCATEGORIZED

    def check_slang(self, word: str, _is_in_dictionary: bool) -> Categories:
        # --- CHECK: Common Slang ---
        if word.lower() in self.common_slang:
            return Categories.COMMON_SLANG

        return Categories.UNCATEGORIZED

    def check_possibilities(self, word: str, is_in_dictionary: bool) -> Categories:
        # --- CHECK: Possible Place Names ---
        # Has common place suffixes
        if not is_in_dictionary and word.lower().endswith(self.place_suffixes):
            return Categories.POSSIBLE_PLACE_NAMES

        # --- CHECK: Possible People Names ---
        # Capitalized + Not in dictionary + Not a known place
        if not is_in_dictionary and word[0].isupper():
            return Categories.POSSIBLE_PEOPLE_NAMES

        # --- CHECK: Possible Slang ---
        # Lowercase not in dictionary
        if not is_in_dictionary and word[0].islower():
            return Categories.POSSIBLE_SLANG

        return Categories.UNCATEGORIZED


def get_categorized_word_lists(input_path: Path) -> dict[Categories, list[str]]:
    if not input_path.exists():
        msg = f'The file "{input_path}" does not exist.'
        raise FileNotFoundError(msg)

    categorizer = BarksCategorizer()

    print(f'Reading Barks words from: "{input_path}".')
    words: list[str] = json.loads(input_path.read_text(encoding="utf-8"))

    print(f"Processing {len(words)} words...")
    categorized_words_dict = defaultdict(list)
    for w in words:
        if not w.strip():
            continue

        cat_id = categorizer.get_category(w)
        categorized_words_dict[cat_id.value].append(w)

    return categorized_words_dict


if __name__ == "__main__":
    args = ArgumentParser("Barks Word Categorizer.")
    args.add_argument("-i", "--input_file", required=True, type=Path, help="Input file")
    args.add_argument("-o", "--output_file", required=True, type=Path, help="Output file")
    args = args.parse_args()
    input_file = args.input_file
    output_file = args.output_file

    word_lists = get_categorized_word_lists(input_file)
    for cat in word_lists:
        word_lists[cat].sort()

    # Write to JSON file with indentation for readability.
    print(f'Writing word list to JSON file: "{output_file}".')
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(word_lists, f, indent=4, ensure_ascii=False)

    print("Done.")
