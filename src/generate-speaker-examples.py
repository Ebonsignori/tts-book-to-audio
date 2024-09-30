import os
import logging
from pathlib import Path
from TTS.api import TTS  # Ensure you have the TTS library installed

def generate_speech_for_speakers(start: int, end: int, output_dir: str, text: str):
    """
    Generates speech files for speaker IDs from p{start} to p{end}.

    Args:
        start (int): Starting number for speaker IDs.
        end (int): Ending number for speaker IDs.
        output_dir (str): Directory where the audio files will be saved.
        text (str): The text to convert to speech.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize logging
    logging.basicConfig(filename='generation.log',
                        level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    # Initialize TTS model once if possible
    model_name = "tts_models/en/vctk/vits"
    try:
        tts = TTS(model_name)
        logging.info(f"Initialized TTS model: {model_name}")
    except Exception as e:
        error_msg = f"Failed to initialize TTS model '{model_name}': {e}"
        logging.error(error_msg)
        return

    for num in range(start, end + 1):
        speaker_id = f"p{num}"
        output_file = os.path.join(output_dir, f"{speaker_id}.wav")
        try:
            # Generate speech and save to file
            tts.tts_to_file(
                text=text,
                speaker=speaker_id,
                file_path=output_file
            )
            logging.info(f"Successfully generated {output_file}")
        except Exception as e:
            error_msg = f"Failed to generate speech for speaker '{speaker_id}': {e}"
            logging.error(error_msg)
            continue  # Proceed with the next speaker

if __name__ == "__main__":
    # Define the range of speaker IDs
    START_SPEAKER_NUM = 225
    END_SPEAKER_NUM = 350

    # Define the output directory
    BASE_DIR = Path(__file__).resolve().parent
    OUTPUT_DIRECTORY = BASE_DIR.parent / "local-voice-examples"

    # Define the text to convert to speech
    EXAMPLE_TEXT = """
    This is a test of the text to speech conversion. 

    "The quick brown fox jumps over the lazy dog." said the narrator. "But why?" asked the fox. "I'm tired of jumping over lazy dogs."
    """

    # Generate speech files
    generate_speech_for_speakers(
        start=START_SPEAKER_NUM,
        end=END_SPEAKER_NUM,
        output_dir=OUTPUT_DIRECTORY,
        text=EXAMPLE_TEXT
    )

    print(f"Speech generation completed. Check the '{OUTPUT_DIRECTORY}' directory for output files.")
