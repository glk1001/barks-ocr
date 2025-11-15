comic_prompt = """
Analyze the comic image, the provided OCR text locations, and the AI text extraction result 
carefully. Your task is to group the OCR-detected word boxes into coherent text bubbles or captions 
within comic panels, while also cleaning and correcting OCR errors. Pay special attention to the 
necessity of including background text and sound effects.

Key Instructions:

1. Word Grouping and Text Cleaning:
   - Group individual text boxes (identified by their IDs) into complete text bubbles or captions.
   - While grouping, clean and correct the OCR text to accurately represent the text in the image.
   - Fix common OCR errors such as misrecognized characters, incorrectly split or joined words, 
     misinterpreted punctuation, and case errors.

2. Panel and Bubble Identification:
   - Assign a unique panel number to each group.
   - Within each panel, assign a unique text bubble or caption number.

3. Text Reconstruction:
   - Provide the complete, cleaned, and corrected text for each group as it should appear in the 
     image.
   - Ensure the text is coherent, grammatically correct, and matches the content visible in the 
     comic.
   - Use escaped newline characters, '\n', to show text breaking to next line.
   - Map individual text boxes (identified by their IDs) to corresponding cleaned text fragments.
     Do not merge the individual text boxes.
   - All text boxes should be used.  

4. Spatial and Visual Analysis:
   - Use the spatial relationships between word boxes to determine groupings.
   - Consider the visual layout of the comic, including panel borders and bubble shapes.

5. Text Types and Styles:
   - Dialogue: Usually in speech bubbles with a pointer to the speaker.
   - Thoughts: Often in cloud-like bubbles or italicized text.
   - Narration: Typically in rectangular boxes, often at the top or bottom of panels.
   - Sound Effects: Can be stylized, vary in size, and placed near the source of the sound.
   - Background Text: Signs, posters, or other environmental text within the comic world that 
     impacts the story.

6. Accuracy Priority:
   - Prioritize accuracy in grouping, text reconstruction, and error correction.
   - If uncertain about a correction or inclusion, provide your best judgment but flag it in the 
     notes.

OCR Text Boxes:
```json
{0}
```

Output Format:
{{
  "groups": [
    {{
      "panel_id": "1",
      "text_bubble_id": "1-1",
      "box_ids": ["1", "2", "3"],
      "split_cleaned_box_texts": {{"1":"cleaned_text1", "2":"cleaned_text2", "3":"cleaned_text3"], 
      "original_text": "The OCR output before cleaning",
      "cleaned_text": "The corrected and cleaned text",
      "type": "dialogue|thought|narration|sound_effect|background",
      "style": "normal|emphasized|angled|split",
      "notes": "Justification for inclusion if background or sound effect, any corrections or uncertainties|none"
    }},
    ...
  ]
}}

Additional Guidelines:
- The output format must be a valid json string. NOTE: single quotes are not valid in json.
- Respect panel boundaries: Never group text from different panels.
- Maintain bubble integrity: Each group should correspond to a single text bubble, caption, or 
  crucial sound effect/background text element.
- Use context clues to resolve ambiguities in text order, bubble assignment, or OCR errors.
- For included sound effects or background text, describe their significance to the story in the 
  "notes" field.
- If you make any corrections to the OCR text, briefly explain your reasoning in the "notes" field.
- Text fragments that match box ids should not contain newlines.

Analyze the image and OCR data thoroughly to produce accurate and contextually appropriate groupings
with cleaned and corrected text that reflects the comic's essential narrative elements.
Properly format the output json.
"""
