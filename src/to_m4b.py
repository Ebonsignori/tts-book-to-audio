import os
from pathlib import Path
import re
import subprocess
import tempfile
from errors import write_to_error_log
import av
from pydub import AudioSegment
from mutagen.mp4 import MP4, MP4StreamInfoError, MP4Cover

def get_root_directory():
    """Get the root directory of the project."""
    current_dir = Path(__file__).parent.resolve()  # src
    parent_dir = os.path.dirname(current_dir)      # root of the project
    return parent_dir

def numerical_sort_key(file_name):
    """Extracts the numeric part of the file name for proper sorting."""
    match = re.findall(r'(\d+)', file_name)
    return int(match[-2]) if match else file_name

def combine_mp3s_with_ffmpeg(mp3_directory, output_filename, metadata, cover_image=None):
    """
    Combine MP3 files using ffmpeg and export as an M4B audiobook with metadata.

    Parameters:
    - mp3_directory (str): Path to the directory containing MP3 files.
    - output_filename (str): Path for the output M4B file.
    - metadata (dict): Dictionary containing metadata (e.g., title, author).
    - cover_image (Path, optional): Path to the cover image file.
    """
    try:
        # Get the list of mp3 files and sort them using the custom key
        mp3_files = [f for f in os.listdir(mp3_directory) if f.lower().endswith(".mp3")]
        if not mp3_files:
            raise ValueError("No MP3 files found in the specified directory.")

        sorted_files = sorted(mp3_files, key=numerical_sort_key)

        # Create a temporary file listing the mp3 files for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as list_file:
            for filename in sorted_files:
                file_path = os.path.join(mp3_directory, filename)
                # Escape single quotes by replacing ' with '\'' in the file path
                escaped_path = file_path.replace("'", r"'\''")
                list_file.write(f"file '{escaped_path}'\n")
            list_filename = list_file.name

        # Define the path for the concatenated mp3 (temporary)
        concatenated_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name

        # Build the ffmpeg command to concatenate mp3s
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files without asking
            '-f', 'concat',
            '-safe', '0',
            '-i', list_filename,
            '-c', 'copy',
            concatenated_mp3
        ]

        # Execute the ffmpeg command
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=process.returncode,
                cmd=ffmpeg_cmd,
                output=process.stdout,
                stderr=process.stderr
            )

        # Use pydub to convert the concatenated mp3 to M4B
        combined_audio = AudioSegment.from_mp3(concatenated_mp3)
        combined_audio.export(output_filename, format="mp4", codec="aac")

        # Set metadata on the M4B file
        set_metadata(output_filename, metadata, cover_image)

        print(f"Combined audiobook saved to: {output_filename}")

    except subprocess.CalledProcessError as e:
        error_message = f"FFmpeg error: {e.stderr}\n\If you're seeing this error try running step 4 with the -m av flag."
        write_to_error_log(error_message)
        print(error_message)
    except Exception as e:
        error_message = f"Error processing MP3s with ffmpeg: {e}\nIf you're seeing this error try running step 4 with the -m av flag."
        write_to_error_log(error_message)
        print(error_message)
    finally:
        # Clean up temporary files
        try:
            if 'list_filename' in locals() and os.path.exists(list_filename):
                os.remove(list_filename)
            if 'concatenated_mp3' in locals() and os.path.exists(concatenated_mp3):
                os.remove(concatenated_mp3)
        except Exception as cleanup_error:
            error_message = f"Error during cleanup: {cleanup_error}"
            write_to_error_log(error_message)
            print(error_message)

def combine_mp3s_with_av(mp3_directory, output_filename, metadata, cover_image=None):
    """
    Combine MP3 files using av python liv and export as an M4B audiobook with metadata.

    Alternative to ffmpeg for combining MP3 files. Sometimes this method works when the other doesn't

    Parameters:
    - mp3_directory (str): Path to the directory containing MP3 files.
    - output_filename (str): Path for the output M4B file.
    - metadata (dict): Dictionary containing metadata (e.g., title, author).
    - cover_image (Path, optional): Path to the cover image file.
    """
    combined_audio = AudioSegment.empty()

    # Get the list of mp3 files and sort them using the custom key
    mp3_files = [f for f in os.listdir(mp3_directory) if f.endswith(".mp3")]
    sorted_files = sorted(mp3_files, key=numerical_sort_key)

    for filename in sorted_files:
        file_path = os.path.join(mp3_directory, filename)
        try:
            container = av.open(file_path)
            stream = container.streams.audio[0]
            audio_frames = []

            for frame in container.decode(stream):
                # Convert frame to numpy array
                samples = frame.to_ndarray()
                # Convert to bytes
                samples_bytes = samples.tobytes()

                # Debug: Print frame information
                # print(f"Processing {filename}:")
                # print(f"  Frame rate: {frame.rate}")
                # print(f"  Format bytes: {frame.format.bytes}")
                # print(f"  Channels: {frame.layout.channels}")

                # Ensure 'channels' is an integer
                channels = frame.layout.channels
                if isinstance(channels, tuple) or isinstance(channels, list):
                    # If channels is a tuple/list, get its length
                    channels = len(channels)
                    # print(f"  Adjusted Channels: {channels}")

                # Create AudioSegment
                audio_segment = AudioSegment(
                    data=samples_bytes,
                    sample_width=frame.format.bytes,  # Ensure this is correct
                    frame_rate=frame.rate,
                    channels=channels  # Pass integer
                )
                combined_audio += audio_segment

            # Export the final combined audio as an M4B file
            combined_audio.export(output_filename, format="mp4", codec="aac")

        except Exception as e:
            error_message = f"Error processing {filename} with av: {e}\n\If you're seeing this error try running step 4 with the -m ffmpeg flag."
            write_to_error_log(error_message)
            print(error_message)
            return

    # Set metadata on the M4B file
    set_metadata(output_filename, metadata, cover_image)
    
    print(f"Combined audiobook saved to: {output_filename}")

def set_metadata(file_path, metadata, cover_image=None):
    """Set metadata like title, author, etc., and optionally embed cover art in the M4B file."""
    try:
        audio = MP4(file_path)

        # Set metadata
        if "title" in metadata:
            audio["\xa9nam"] = metadata["title"]
        if "author" in metadata:
            audio["\xa9ART"] = metadata["author"]
        if "album" in metadata:
            audio["\xa9alb"] = metadata["album"]
        if "genre" in metadata:
            audio["\xa9gen"] = metadata["genre"]
        if "year" in metadata:
            audio["\xa9day"] = str(metadata["year"])

        # If a cover image is provided, add it to the file
        if cover_image and cover_image.suffix.lower() in (".jpg", ".jpeg", ".png"):
            with open(cover_image, "rb") as img_file:
                if cover_image.suffix.lower() == ".png":
                    audio["covr"] = [MP4Cover(img_file.read(), imageformat=MP4Cover.FORMAT_PNG)]
                elif cover_image.suffix.lower() in (".jpg", ".jpeg"):
                    audio["covr"] = [MP4Cover(img_file.read(), imageformat=MP4Cover.FORMAT_JPEG)]

        # Save the changes
        audio.save()

    except MP4StreamInfoError:
        error_message = "Error handling the M4B file. Ensure it's in a valid format."
        write_to_error_log(error_message)
        print(error_message)
    except FileNotFoundError:
        error_message = "Cover image file not found."
        write_to_error_log(error_message)
        print(error_message)
    except Exception as e:
        error_message = f"Unexpected error while setting metadata: {e}"
        write_to_error_log(error_message)
        print(error_message)
