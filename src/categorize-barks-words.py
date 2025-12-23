import csv
import re

import nltk
import pycountry
from spellchecker import SpellChecker

# --- Download NLTK data (Names corpus) ---
try:
    nltk.data.find("corpora/names")
except LookupError:
    print("Downloading name datasets...")
    nltk.download("names")

from nltk.corpus import names


class WordCategorizer:
    def __init__(self) -> None:
        print("Initializing dictionaries and databases...")

        # 1. English Dictionary
        self.spell = SpellChecker()

        # 2. Known People Names (English)
        # We combine male and female names from NLTK
        self.known_names = set(names.words("male.txt")) | set(names.words("female.txt"))
        # Add some common Spanish names manually or load a file here if needed
        self.known_names.update(["Juan", "Jose", "Maria", "Carlos", "Luis", "Ana", "Pedro"])

        # 3. Known Place Names (Countries and Subdivisions)
        self.known_places = set()
        for country in pycountry.countries:
            self.known_places.add(country.name)
        for sub in pycountry.subdivisions:
            self.known_places.add(sub.name)

        # 4. Common Slang (Carl Barks / Comic Book Specifics)
        # You should expand this list based on what you see in the results
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
        }

    def get_category(self, word):
        """Analyzes a single word and returns a category ID and Name.
        Priority is important here.
        """  # noqa: D205
        clean_word = word.strip()

        # --- CHECK 4: Abbreviated ---
        # Starts or ends with apostrophe (e.g., 'lo, knockin')
        if clean_word.startswith("'") or clean_word.endswith("'"):
            return 4, "Abbreviated"

        # Remove punctuation for the remaining checks (so "Hello?" becomes "Hello")
        # We keep internal apostrophes for names like O'Hara
        stripped_word = re.sub(r"[^\w\']", "", clean_word)

        if not stripped_word:
            return 0, "Symbol/Empty"

        # --- CHECK 5: Known Place Names ---
        if stripped_word in self.known_places:
            return 5, "Known Place Name"

        # --- CHECK 7: Known People Names ---
        if stripped_word in self.known_names:
            return 7, "Known People Name"

        # --- CHECK 2: Common Slang ---
        if stripped_word.lower() in self.common_slang:
            return 2, "Common Slang"

        # --- CHECK 1: Correctly Spelled (Standard English) ---
        # known() returns a set of words that are found in the dictionary
        if self.spell.known([stripped_word]):
            # If it's capitalized, it might be a name (like "Baker"),
            # but if it's in the dictionary, we usually classify as Correctly Spelled
            # unless we want to prioritize names. Here we prioritize Dictionary.
            return 1, "Correctly Spelled"

        # --- HEURISTICS FOR "POSSIBLE" CATEGORIES ---

        # --- CHECK 6: Possible Place Names ---
        # Logic: Capitalized + Suffixes common in comics (Duckburg, etc)
        place_suffixes = ("burg", "ville", "town", "land", "sota", "ia", "ford", "shire")
        if stripped_word[0].isupper() and stripped_word.lower().endswith(place_suffixes):
            return 6, "Possible Place Name"

        # --- CHECK 8: Possible People Names ---
        # Logic: Capitalized, not in dictionary, not a known place
        if stripped_word[0].isupper():
            return 8, "Possible People Name"

        # --- CHECK 3: Possible Slang ---
        # Logic: Lowercase, not in dictionary, usually phonetic spellings
        if stripped_word[0].islower():
            return 3, "Possible Slang"

        # Fallback
        return 9, "Uncategorized"


def process_file(input_file, output_file):
    categorizer = WordCategorizer()

    results = []

    print(f"Reading {input_file}...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            words = f.read().splitlines()
    except FileNotFoundError:
        print("Error: Input file not found.")
        return

    print(f"Categorizing {len(words)} words...")

    for word in words:
        if not word.strip():
            continue  # Skip empty lines

        cat_id, cat_name = categorizer.get_category(word)
        results.append([word, cat_id, cat_name])

    # Write to CSV
    print(f"Writing results to {output_file}...")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Word", "Category ID", "Category Name"])
        writer.writerows(results)

    print("Done!")


# --- EXECUTION ---
# Create a dummy file for testing if you don't have one ready
# remove this block if you have your own 'words.txt'
if __name__ == "__main__":
    # Example usage:
    # 1. Create a text file named 'words.txt' with your 15,000 words (one per line)
    # 2. Run this script

    # Just for demonstration, let's create a dummy input file
    sample_data = """Hello
'lo
Duckburg
Scrooge
Donald
runnin'
gosh
flibberflabber
Paris
Mickey
Calisota
bork
Spain"""

    with open("words_input.txt", "w") as f:
        f.write(sample_data)

    # Run the processor
    process_file("words_input.txt", "categorized_words.csv")
