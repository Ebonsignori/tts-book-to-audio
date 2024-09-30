import argparse
import re
from config import CONFIG
from github_openai_client import GitHubOpenAIClient
from utils import (
    count_tokens,
    split_into_sentences,
    extract_character_tags,
    clean_code_blocks,
    split_text_into_chunks,
    remove_suffix
)
from to_text import extract_text
from datetime import datetime
from errors import error_log_has_new_errors
import json
from tts import generate_mp3_files
from to_m4b import combine_mp3s_with_av, combine_mp3s_with_ffmpeg
import sys


def split_into_blocks(input_text: str) -> list:
    """Splits the input text into manageable blocks based on token limits."""
    paragraphs = re.split(r'\n\s*\n', input_text)

    MODEL_MAX_TOKENS = CONFIG["token_limits"]["MODEL_MAX_TOKENS"]
    MAX_COMPLETION_TOKENS = CONFIG["token_limits"]["MAX_COMPLETION_TOKENS"]
    TOKEN_BUFFER = CONFIG["token_limits"]["TOKEN_BUFFER"]
    TTS_MAX_CHARACTERS = CONFIG["token_limits"]["TTS_MAX_CHARACTERS"]

    MAX_PROMPT_TOKENS = MODEL_MAX_TOKENS - MAX_COMPLETION_TOKENS - TOKEN_BUFFER

    system_message_token_count = count_tokens(CONFIG["system_message"])
    user_message_token_count = count_tokens(
        CONFIG["user_message_prefix"] + CONFIG["user_message_suffix"]
    )

    blocks = []
    current_block = ""
    current_block_token_count = 0

    for paragraph in paragraphs:
        paragraph_token_count = count_tokens(paragraph)

        if (current_block_token_count + paragraph_token_count + system_message_token_count +
                user_message_token_count) <= MAX_PROMPT_TOKENS:
            current_block += ("\n\n" if current_block else "") + paragraph
            current_block_token_count += paragraph_token_count
        else:
            if (paragraph_token_count + system_message_token_count +
                    user_message_token_count) > MAX_PROMPT_TOKENS:
                sentences = split_into_sentences(paragraph)
                for sentence in sentences:
                    sentence_token_count = count_tokens(sentence)
                    if (current_block_token_count + sentence_token_count +
                            system_message_token_count + user_message_token_count) <= MAX_PROMPT_TOKENS:
                        current_block += (" " if current_block else "") + sentence
                        current_block_token_count += sentence_token_count
                    else:
                        if current_block:
                            blocks.append(current_block)
                        current_block = sentence
                        current_block_token_count = sentence_token_count
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = paragraph
                current_block_token_count = paragraph_token_count

    if current_block:
        blocks.append(current_block)

    return blocks

def generate_metadata_json(input_file_name: str, metadata_json_path: str):
    """Generates the metadata.json file based on the input file name."""
    now = datetime.now()
    with open(metadata_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "title": input_file_name.replace(".txt", ""),
            "author": "book-to-audio",
            "album": input_file_name.replace(".txt", ""),
            "genre": "Audiobook",
            "year": now.year,
        }, f, indent=2)

    print(f"Metadata JSON generated and written to {metadata_json_path}")

def generate_characters_json(openai_client, processed_text: str, characters_json_path: str):
    """Generates the characters.json file based on the processed text,
    ensuring that characters sharing first or last names use the same voice identifier."""

    # Step 1: Extract all character tags from processed text
    character_tags = extract_character_tags(processed_text)

    # Step 2: Count speaking frequency for each character
    character_frequency_map = {}
    for tag in character_tags:
        name = tag["name"]
        gender = tag["gender"]
        if name in character_frequency_map:
            character_frequency_map[name]["count"] += 1
        else:
            character_frequency_map[name] = {"gender": gender, "count": 1}

    # Step 3: Convert the map to a sorted list based on speaking frequency
    sorted_characters = sorted(
        character_frequency_map.items(),
        key=lambda item: item[1]["count"],
        reverse=True
    )
    sorted_characters = [
        {"name": name, "gender": data["gender"], "count": data["count"]}
        for name, data in sorted_characters
    ]

    # Step 4: Assign voice identifiers based on gender without name sharing logic
    male_voices = CONFIG["voice_identifiers"]["male_voices"]
    female_voices = CONFIG["voice_identifiers"]["female_voices"]
    narrator_voice = CONFIG["voice_identifiers"]["narrator_voice"]
    default_voice = CONFIG["voice_identifiers"]["default_voice"]

    male_index = 0
    female_index = 0

    characters_json = {
        "narrator": narrator_voice
    }

    for character in sorted_characters:
        name = character["name"]
        gender = character["gender"]

        # Assign a new voice identifier based on gender
        if gender.lower() == "m":
            assigned_voice = male_voices[male_index % len(male_voices)]
            male_index += 1
        elif gender.lower() == "f":
            assigned_voice = female_voices[female_index % len(female_voices)]
            female_index += 1
        else:
            assigned_voice = default_voice

        characters_json[name] = assigned_voice

    # Step 5: Process the characters_json with ChatGPT to enforce voice assignment rules
    processed_characters_json = openai_client.process_characters_json(characters_json)

    # Step 6: Write the processed characters.json file
    with open(characters_json_path, "w", encoding="utf-8") as f:
        json.dump(processed_characters_json, f, indent=2)

    print(f"Characters JSON generated and written to {characters_json_path}")


def split_text_for_tts(processed_text: str, characters_map: dict) -> list:
    """Splits the processed text into segments suitable for TTS API requests."""
    segments = []
    regex = re.compile(r'<([a-z_]+)-(f|m)>(.*?)<\/\1-\2>', re.DOTALL)

    last_index = 0
    for match in regex.finditer(processed_text):
        start, end = match.span()
        name, gender, dialogue = match.groups()

        # Non-dialogue text before this dialogue
        if last_index < start:
            non_dialogue = processed_text[last_index:start]
            if non_dialogue.strip():
                segments.append({
                    "text": non_dialogue.strip(),
                    "voice": characters_map.get("narrator", CONFIG["voice_identifiers"]["narrator_voice"])
                })

        # Dialogue text
        voice = characters_map.get(name, CONFIG["voice_identifiers"]["default_voice"])
        if dialogue.strip():
            segments.append({
                "text": dialogue.strip(),
                "voice": voice
            })

        last_index = end

    # Remaining non-dialogue text after the last dialogue
    if last_index < len(processed_text):
        non_dialogue = processed_text[last_index:]
        if non_dialogue.strip():
            segments.append({
                "text": non_dialogue.strip(),
                "voice": characters_map.get("narrator", CONFIG["voice_identifiers"]["narrator_voice"])
            })

    # Split segments into chunks not exceeding TTS_MAX_CHARACTERS
    tts_chunks = []
    current_chunk = ""
    current_voice = None

    for segment in segments:
        text = segment["text"]
        voice = segment["voice"]

        if current_voice and voice != current_voice:
            if current_chunk.strip():
                tts_chunks.append({"text": current_chunk.strip(), "voice": current_voice})
            current_chunk = text
            current_voice = voice
        else:
            current_chunk += " " + text if current_chunk else text
            current_voice = voice

        # If the current chunk exceeds the max length, split it
        if len(current_chunk) > CONFIG["token_limits"]["TTS_MAX_CHARACTERS"]:
            split_chunks = split_text_into_chunks(current_chunk, CONFIG["token_limits"]["TTS_MAX_CHARACTERS"])
            for split_text in split_chunks:
                tts_chunks.append({"text": split_text, "voice": current_voice})
            current_chunk = ""
            current_voice = None

    if current_chunk.strip():
        tts_chunks.append({"text": current_chunk.strip(), "voice": current_voice})

    return tts_chunks
  
def detect_cover_image(input_file_name):
    # Construct the possible paths for .png and .jpg images
    png_image = CONFIG["inputs_path"] / f"{input_file_name}.png"
    jpg_image = CONFIG["inputs_path"] / f"{input_file_name}.jpg"
    
    # Check if either file exists
    if png_image.exists():
        return png_image
    elif jpg_image.exists():
        return jpg_image
    else:
        return None

def write_output_file(text: str, output_file_path: str):
    """Writes the processed text to the output file."""
    # If directories of the output file do not exist, create them
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(text.strip())
    print(f"Processing complete. Output written to {output_file_path}")


def main():
    parser = argparse.ArgumentParser(description="Process text and generate audio.")
    parser.add_argument(
        "-i", "--input-file", required=True, help="Path to the input file"
    )
    parser.add_argument(
        "-t",
        "--tts-method",
        choices=["local", "remote"],
        default="local",
        help='Text-to-Speech method ("local" or "remote")',
    )
    parser.add_argument(
        "-s",
        "--steps",
        help='Steps of script to run (comma-separated) If not passed will run every step.',
    )
    parser.add_argument(
        "-m",
        "--m4b-method",
        choices=["av", "ffmpeg"],
        default="ffmpeg",
        help='Sometimes the ffmpeg method fails to combine the audio files. In that case, you can try the av method.',
    )
    args = parser.parse_args()

    # Validate that steps is a comma-separated list of integers
    steps = []
    if args.steps:
        try:
            steps = [int(step) for step in args.steps.split(",")]
        except ValueError:
            print("Invalid steps argument. Please provide a comma-separated list of integers.")
            sys.exit(1)
    if len(steps) > 0:
        print(f"Running steps: {steps}")

    # Validate TTS method
    tts_method = args.tts_method.lower()
    if tts_method not in ["local", "remote"]:
        print(f'Invalid TTS method "{args.tts_method}". Allowed values are "local" or "remote".')
        sys.exit(1)

    # Validate input file directory
    CONFIG["inputs_path"].mkdir(parents=True, exist_ok=True)
    CONFIG["outputs_path"].parent.mkdir(parents=True, exist_ok=True)

    # If input file has any suffix, remove it
    book_name = remove_suffix(args.input_file)

    # Validate API Key
    if not CONFIG["api_key"]:
        print("Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)

    # Initialize OpenAI Client
    openai_client = GitHubOpenAIClient()

    # - - - Start Step 1: Process input file into plaintext - - -
    plaintext_output_file_path = CONFIG["outputs_path"] / book_name / f"{book_name}_plaintext.txt"
    if len(steps) == 0 or 1 in steps:
      print("Starting Step 1: Process input file into plaintext")
      input_plaintext = extract_text(CONFIG["inputs_path"] / args.input_file)

      # Write the processed output to {book_name}_plaintext.txt 
      write_output_file(input_plaintext, plaintext_output_file_path)
      
    # - - - Start Step 2: Process input file into output file with dialogue tags - - -
    tagged_output_file_path = CONFIG["outputs_path"] / book_name / f"{book_name}_tagged.txt"
    characters_json_path = CONFIG["outputs_path"] / book_name / "characters.json"
    metadata_json_path = CONFIG["outputs_path"] / book_name / "metadata.json"
    if len(steps) == 0 or 2 in steps:
      print("Starting Step 2: Determine dialogue tags and generate character.json & metadata.json")
      # Read plaintext file
      with open(plaintext_output_file_path, "r", encoding="utf-8") as f:
          input_text = f.read()

      # Split input text into blocks
      blocks = split_into_blocks(input_text)
      print(f"Total input text blocks to process: {len(blocks)}")

      # Process each block and accumulate the final output
      final_output = ""
      for index, block in enumerate(blocks, 1):
          print(f"Processing block {index}/{len(blocks)}...")
          processed_block = openai_client.process_block(block)

          # Clean the processed block by removing any code block wrappers
          processed_block = clean_code_blocks(processed_block)

          final_output += processed_block + "\n\n"

      # Write the processed output to output.txt
      write_output_file(final_output, tagged_output_file_path)
      print(f"Processed output written to {tagged_output_file_path}")

      # Generate characters.json based on the processed output
      generate_characters_json(openai_client, final_output, characters_json_path)

      # Generate metadata.json 
      generate_metadata_json(book_name, metadata_json_path)

    # - - - Start Step 3: Generate TTS audio files from processed text - - -
    audio_files_output_dir = CONFIG["outputs_path"] / book_name / "audio_files"
    if len(steps) == 0 or 3 in steps:
      print("Starting Step 2: Generate TTS audio files from processed text")
      # Read characters.json
      with open(characters_json_path, "r", encoding="utf-8") as f:
          characters_json = json.load(f)

      # Read output.txt
      with open(tagged_output_file_path, "r", encoding="utf-8") as f:
          processed_text = f.read()

      # Split text into TTS-compatible chunks
      tts_chunks = split_text_for_tts(processed_text, characters_json)
      print(f"Total TTS chunks to process: {len(tts_chunks)}")

      # Generate MP3 files from TTS chunks
      generate_mp3_files(tts_chunks, tts_method, audio_files_output_dir)

    # - - - Start Step 4: Combine MP3 files into an m4b - - -
    m4b_output_file = CONFIG["outputs_path"] / book_name / f"{book_name}.m4b"
    if len(steps) == 0 or 4 in steps:
      print("Starting Step 3: Combine MP3 files into an m4b")
      # Read metadata.json
      metadata = {}
      with open(metadata_json_path, "r", encoding="utf-8") as f:
          metadata = json.load(f)

      print("Combining audio files into m4b...")
      cover_image = detect_cover_image(book_name)
      if args.m4b_method == "ffmpeg":
        combine_mp3s_with_ffmpeg(audio_files_output_dir, m4b_output_file, metadata, cover_image)
      elif args.m4b_method == "av":
        combine_mp3s_with_av(audio_files_output_dir, m4b_output_file, metadata, cover_image)
    
    if error_log_has_new_errors():
        print("There were errors during the run. Please check error.log for more details.")


if __name__ == "__main__":
    main()