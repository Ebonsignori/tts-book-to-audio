# config.py

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Configuration and Constants
CONFIG = {
    "api_key": os.getenv("GITHUB_TOKEN"),
    "inputs_path": BASE_DIR.parent / "inputs",
    "outputs_path": BASE_DIR.parent / "outputs",
    "base_url": "https://models.inference.ai.azure.com",
    "model": "gpt-4o",
    "system_message": """You are given a block of text that may contain dialogue. Your task is to identify the dialogue spoken by characters and wrap each spoken line with a tag labeled with the speaker’s name in snake_case, appending '-m' if the character is male or '-f' if the character is female.

Important Rules:

1. Do not alter the content or wording of the input text, including punctuation, capitalization, or spacing.
2. Only wrap dialogue with the character's name tag, including the gender suffix. Do not include narrative descriptions or speaker attributions (e.g., "said Bob") inside the tags.
3. Do not remove narrative descriptions (e.g., "said Bob").
4. Character names should always be in snake_case and consistent with how they appear in the text.
5. Do not modify any text that is not dialogue (e.g., character actions, narrative descriptions).
6. If dialogue is interrupted by a description or action, apply the tag to each individual segment of dialogue.
7. Determine the gender of each character based on the context and append '-m' for male or '-f' for female to the character name tag.

For example:

Input:

\`\`\`
"Hi, how are you?" said Bob. "I'm good, thanks!" replied Alice.
\`\`\`

Output:

\`\`\`
<bob-m>"Hi, how are you?"</bob-m> said Bob. <alice-f>"I'm good, thanks!"</alice-f> replied Alice.
\`\`\`

Input:

\`\`\`
"Wait," John hesitated, "what do you mean?"
\`\`\`

Output

\`\`\`
<john-m>"Wait,"</john-m> John hesitated, <john-m>"what do you mean?"</john-m>
\`\`\`

Do not change any of the text or summarize it in any way other than surrounding dialogue in character tags with appropriate gender suffixes.""",
    "characters_json_system_message": """
You are an assistant that processes a JSON object containing character names and their associated voice identifiers.
Please perform the following tasks:

1. **Output Only JSON:** Your response should be strictly a JSON object without any additional text or explanations.

2. **Preserve All Keys:** Do not alter any of the keys in the JSON.

3. **Synchronize Voice Identifiers for Identical Names:**
   - If a key is a base name (e.g., "hermione") and another key is a variation of that name (e.g., "hermione_granger"), assume they refer to the same character.
   - Assign the same voice identifier to such keys based on the first occurrence.
   
4. **Handle Titles Appropriately:**
   - If a key includes a title (e.g., "professor_mcgonagall" or "professor_dumbledore"), treat them as distinct characters regardless of any shared name parts.
   - Do not synchronize voice identifiers based on title prefixes.

5. **Avoid Altering Unique Names:**
   - If a name could be someone else's last name or is unique enough, do not alter its voice identifier.

**Examples:**

- Given:
```
{
"hermione_granger": "female_1",
"hermione": "female_2"
}
```
Output:
```
{
"hermione_granger": "female_1",
"hermione": "female_1"
}
```

- Given:
```
{
  "professor_mcgonagall": "female_1",
  "professor_dumbledore": "male_1"
}
```
Output:
```
{
  "professor_mcgonagall": "female_1",
  "professor_dumbledore": "male_1"
}
```

- Given:
```
{
  "bob": "male_1",
  "evan": "male_2",
  "bob_evan": "male_3"
}
```
Output:
```
{
  "bob": "male_1",
  "evan": "male_2",
  "bob_evan": "male_3"
}
```

Please ensure your response adheres strictly to these rules.

User input:\n\n```\n""",
    "user_message_prefix": "Actual input:\n\n```",
    "user_message_suffix": "\n```",
    "token_limits": {
        "MODEL_MAX_TOKENS": 8192,  # For GPT-4
        "MAX_COMPLETION_TOKENS": 2048,
        "TOKEN_BUFFER": 100,  # Buffer to account for additional tag characters
        "TTS_MAX_CHARACTERS": 4096,  # Max characters per TTS request
    },
    "voice_identifiers": {
        "male_voices": ["male_2", "male_3", "male_4"],
        "female_voices": ["female_1", "female_2"],
        "narrator_voice": "male_1",
        "default_voice": "female_1",
    },
    "tts_server_url": "http://localhost:8000/tts",
}

vits_voice_mapping = {
    "male_1": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p231"
    },
    "male_2": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p232"
    },
    "male_3": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p241"
    },
    "male_4": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p251"
    },
    "female_1": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p343"
    },
    "female_2": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p310"
    },
}

openai_voice_mapping = {
  "male_1": "alloy",
  "male_2": "echo",
  "male_3": "fable",
  "male_4": "onyx",
  "female_1": "nova",
  "female_2": "shimmer",
}

elevenlabs_voice_mapping = {
  "male_1": "Bill",
  "male_2": "George",
  "male_3": "Callum",
  "male_4": "Daniel",
  "female_1": "Lily",
  "female_2": "Aria"
}

def get_vits_voice_map():
  global vits_voice_mapping
  return vits_voice_mapping

def get_openai_voice_map():
  global openai_voice_mapping
  return openai_voice_mapping

def get_elevenlabs_voice_map():
  global elevenlabs_voice_mapping
  return elevenlabs_voice_mapping