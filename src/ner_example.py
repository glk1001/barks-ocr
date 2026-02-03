import spacy

# Load the pre-trained English model
nlp = spacy.load("en_core_web_md")

# Process the text
text = (
    "When Sebastian Thrun started working on self-driving cars at "
    "Google in 2007, few people outside of the company took him "
    "seriously. He said this in an interview with Recode earlier this week."
)
doc = nlp(text)

# Find named entities, phrases and concepts
print("Named Entities:")
for entity in doc.ents:
    print(f"- {entity.text}: {entity.label_}")
