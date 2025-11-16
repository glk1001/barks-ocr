import os

from google import genai
from jinja2 import Template

# create client
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)


# path to the file to upload
file_path = "/home/greg/Downloads/The Duck Man An Interview with Carl Barks 1975.mp3"

# Upload the file to the File API
file = client.files.upload(file=file_path)

# Generate a structured response using the Gemini API
prompt_template = Template(
    """Generate a transcript of the youtube interview. Include timestamps and identify speakers.

Speakers are: 
{% for speaker in speakers %}- {{ speaker }}{% if not loop.last %}\n{% endif %}{% endfor %}

eg:
[00:00] Brady: Hello there.
[00:02] Tim: Hi Brady.

It is important to include the correct speaker names. Use the names you identified earlier.
If you really don't know the speaker's name, identify them with a letter of the alphabet, eg
there may be an unknown speaker 'A' and another unknown speaker 'B'.

If there is music or a short jingle playing, signify like so:
[01:02] [MUSIC] or [01:02] [JINGLE]

If you can identify the name of the music or jingle playing then use that instead, eg:
[01:02] [Firework by Katy Perry] or [01:02] [The Sofa Shop jingle]

If there is some other sound playing try to identify the sound, eg:
[01:02] [Bell ringing]

Each individual caption should be formatted as a single paragraph.

Format the whole transcript using markdown.

Signify the end of the interview with [END].

Don't use any markdown formatting, like bolding or italics.

Only use characters from the English alphabet, unless you genuinely believe foreign 
characters are correct.

It is important that you use the correct words and spell everything correctly. 
Use the context of the interview to help.
If the hosts discuss something like a movie, book or celebrity, make sure the movie, book, 
or celebrity name is spelled correctly."""
)

# Define the speakers and render the prompt
speakers = ["Carl"]
prompt = prompt_template.render(speakers=speakers)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[prompt, file],
)

print(response.text)
