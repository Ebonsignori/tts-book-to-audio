import os
from dotenv import load_dotenv
from TTS.api import TTS
from errors import write_to_error_log
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from config import get_vits_voice_map, get_openai_voice_map, get_elevenlabs_voice_map

load_dotenv()  # Load environment variables from .env

openai_client = None
elevenlabs_client = None

def get_openai_client():
    global openai_client
    # Validate that the OpenAI API key is set in the environment
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key not found in environment variables. For 'openai' TTS method, set the OPENAI_API_KEY in the .env file.")
    if openai_client is None:
        openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
    return openai_client

def get_elevenlabs_client():
    """
    Initialize and return the ElevenLabs client using the API key from environment variables.
    
    Raises:
        ValueError: If the ElevenLabs API key is not found in environment variables.
    
    Returns:
        ElevenLabs: An instance of the ElevenLabs client.
    """
    global elevenlabs_client
    # Validate that the ElevenLabs API key is set in the environment
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise ValueError("ElevenLabs API key not found in environment variables. For 'elevenlabs' TTS method, set the ELEVENLABS_API_KEY in the .env file.")
    if elevenlabs_client is None:
        elevenlabs_client = ElevenLabs(
            api_key=os.environ.get("ELEVENLABS_API_KEY"),
        )
    return elevenlabs_client

def convert_text_to_speech(text, voice="male_1", method="local", output_file=None):
    """
    Convert text to speech and write the audio data directly to a file.

    Args:
        text (str): The input text to convert to speech.
        voice (str): The voice model to use for conversion.
        method (str): The method to use for conversion, "openai", "local", or "elevenlabs".
        output_file (str): The file path where the audio data will be saved.

    Returns:
        None
    """
    if method == "openai":
        client = get_openai_client()

        # Get the OpenAI voice mapping from config
        openai_voice_map = get_openai_voice_map()
        openai_voice = openai_voice_map.get(voice, "echo")  # Default to "echo" if not found
        try:
            response = client.audio.speech.create(
                model="tts-1-hd",
                input=text,
                voice=openai_voice,
                response_format="mp3",
            )
            # Write the response content directly to the output file
            if output_file:
                with open(output_file, "wb") as f:
                    f.write(response.content)
            else:
                error_message = "Output file path must be provided for openai method."
                write_to_error_log(error_message)
                raise ValueError(error_message)
        except Exception as e:
            error_message = f"Failed to convert text to speech via OpenAI API: {e}"
            write_to_error_log(error_message)
            raise Exception(error_message)

    elif method == "local":
        # Get the VITS voice mapping from config
        vits_voice_map = get_vits_voice_map()
        vits_voice = vits_voice_map.get(voice)
        if not vits_voice:
            raise ValueError(f"Voice '{voice}' not found in VITS voice mapping.")

        try:
            # Initialize TTS model
            tts = TTS(vits_voice["model"])
            
            # Generate speech and save directly to the provided output file path
            if output_file:
                tts.tts_to_file(
                    text=text,
                    speaker=vits_voice["speaker"],
                    file_path=output_file
                )
            else:
                error_message = "Output file path must be provided for local method."
                write_to_error_log(error_message)
                raise ValueError(error_message)
        except Exception as e:
            error_message = f"Failed to convert text to speech locally: {e}"
            write_to_error_log(error_message)
            raise Exception(error_message)

    elif method == "elevenlabs":
        client = get_elevenlabs_client()

        # Get the ElevenLabs voice mapping from config
        elevenlabs_voice_map = get_elevenlabs_voice_map()
        elevenlabs_voice = elevenlabs_voice_map.get(voice)
        if not elevenlabs_voice:
            raise ValueError(f"Voice '{voice}' not found in ElevenLabs voice mapping.")

        try:
            # Generate speech using ElevenLabs API
            audio = client.generate(
                text=text,
                voice=elevenlabs_voice,
                model="eleven_multilingual_v2"
            )

            # Write the audio data directly to the output file
            if output_file:
                save(audio, output_file)
            else:
                error_message = "Output file path must be provided for elevenlabs method."
                write_to_error_log(error_message)
                raise ValueError(error_message)
        except Exception as e:
            error_message = f"Failed to convert text to speech via ElevenLabs API: {e}"
            write_to_error_log(error_message)
            raise Exception(error_message)

    else:
        raise ValueError(f"Invalid TTS method '{method}'. Choose 'local', 'openai', or 'elevenlabs'.")

def generate_mp3_files(tts_chunks: list, method: str, audio_files_dir: str):
    """Generates MP3 files from TTS chunks."""
    os.makedirs(audio_files_dir, exist_ok=True)

    for i, chunk in enumerate(tts_chunks, 1):
        print(f"Generating MP3 file for chunk {i}/{len(tts_chunks)}...")
        text = chunk["text"]
        voice = chunk["voice"]
        file_name = f"{i}.mp3"
        file_path = os.path.join(audio_files_dir, file_name)  # Updated to use os.path.join

        try:
            # Call the TTS conversion and pass the file path directly
            convert_text_to_speech(text, voice, method, output_file=file_path)
            print(f"Generated MP3 file: {file_name}")
        except Exception as e:
            error_message = f"Failed to generate MP3 for chunk {i}: {e}"
            write_to_error_log(error_message)
            print(error_message)

    print(f"All MP3 files have been generated in the '{audio_files_dir}' directory.")
