# TTS Book to Audio

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
  - [Setting up secrets](#setting-up-secrets)
  - [Invoking the Script](#invoking-the-script)
  - [Input Options](#input-options)
- [Processing Steps](#processing-steps)
  - [Running Specific Steps](#running-specific-steps)
- [Example Input & Output Structure](#example-input--output-structure)
- [License](#license)

## Overview

This project converts text files into audiobooks using Text-to-Speech (TTS).

It processes input files, tags dialogues with character names, generates character and metadata files for user's to customize the output, and results in an .m4b audiobook file.

For an illustrative example of the process see:

[inputs/example.txt](./inputs/example.txt) -> [outputs/example/example_tagged.txt](./outputs/example/example_tagged.txt) -> [outputs/example/example.m4b](./outputs/example/example.m4b)


## Installation

If you don't have `pipenv` or `Python 3.9` installed, please install it.

Then,

```bash
git clone https://github.com/ebonsignori/tts-book-to-audio.git
cd tts-book-to-audio
pipenv install
```

## Usage


### Setting up secrets

See [.env.example](./.env.example) and rename it to `.env` with the respective keys.

This project uses a [GitHub PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) with any level of permissions set via `GITHUB_TOKEN` to access OpenAI's 4o model via [GitHub Models](https://docs.github.com/en/github-models).

- The `OPENAI_API_KEY` is only needed if you are using the `--tts-method openai` option. This is NOT a free API, however the resulting audio quality may be higher if you choose to use this method.

- The `ELEVENLABS_API_KEY` is only needed if you are using the `--tts-method elevenlabs` option. This is NOT a free API, however the resulting audio quality may be higher if you choose to use this method.

### Invoking the Script

`bash
pipenv run python src/main.py -i <input_book_name> [options]
`

Example:

`bash
pipenv run python src/main.py -i my_book.epub
`

### Input Options

- `-i`, `--input-file`: (Required) The name of the book file in the `inputs/` directory. Should include the file extension (e.g., `my_book.epub`).

  Supported Formats:
    - `.txt`
    - `.epub`
    - `.mobi`
    - `.pdf`

- `--tts-method`, `-t`: (Optional) Text-to-Speech method to use. Choices are:
  - `local`: (default) Free and fast, but not as high quality as paid APIs.
  - `openai`: Requires an `OPENAI_API_KEY` in `.env`. Costs money to use the OpenAPI TTS API.
  - `elevenlabs`: Requires an `ELEVENLABS_API_KEY` in `.env`. Costs money to use the ElevenLabs TTS API.

- `--steps`, `-s`: (Optional) Comma-separated list of processing steps to execute. If not provided, all steps will run. See [Processing Steps](#processing-steps)

- `--m4b-method`, `-m`: (Optional) Method to combine audio files into .m4b.

  Supported methods
    - `av`
    - `ffmpeg`

- `-p`, `--write-processed-blocks` (Optional): Write intermediate text processing blocks to `output/<input_book_name>/processed_blocks/processed_#.txt` returned from the GPT. Useful for debugging.

**Note**: Ensure the input file is placed inside the `inputs/` directory.

## Processing Steps

The conversion process is divided into four main steps. You can execute all steps at once or specify individual steps for manual intervention or customization.

**Step 1**: Process Input File into Plaintext.
  - Converts the input book file into a plaintext file.
  - **Output**: `outputs/<input_book_name>/<input_book_name>_plaintext.txt`

**Step 2**: Tag Dialogues and Generate JSON Files
   - Transforms plaintext by surrounding dialogues with `<character_name>` tags.
   - Generates `characters.json` with character names and their corresponding voices.
   - Creates `metadata.json` for audiobook metadata customization.
  - **Outputs**:
   - `outputs/<input_book_name>/<input_book_name>_tagged.txt`
   - `outputs/<input_book_name>/characters.json`
   - `outputs/<input_book_name>/metadata.json`
   - `output/<input_book_name>/processed_blocks/processed_#.txt` (if `-p` flag is passed)

**Step 3**: Generate TTS Audio Files
  - Converts the tagged text into audio files using the specified TTS method.
  - **Output**: `outputs/<input_book_name>/audio_files/<file_number>.mp3`

**Step 4**: Combine Audio Files into an .m4b Audiobook
  - Merges all generated audio files into a single .m4b file using the chosen method (av or ffmpeg).
  - **Output**: `outputs/<input_book_name>/<input_book_name>.m4b`

### Running Specific Steps

To run specific steps, use the `-s` or `--steps` option followed by a comma-separated list of step numbers.

Example:

`bash
pipenv run python src/main.py -i my_book.epub -s 1,2
`

This command will execute Step 1 and Step 2 only.

**Note**: After running certain steps, you may manually edit the generated files (e.g., characters.json, metadata.json, or \_plaintext.txt) before proceeding to the next steps.

## Example input / output structure

```
book-to-audio-converter/
├── inputs/
│   └── my_book.epub
│   └── my_book.jpg
├── outputs/
│   └── my_book/
│       ├── my_book_plaintext.txt
│       ├── my_book_tagged.txt
│       ├── characters.json
│       ├── metadata.json
│       ├── audio_files/
│       │   ├── 1.mp3
│       │   ├── 2.mp3
│       │   └── ...
│       └── my_book.m4b
```

## More local voice options

1. Run `pipenv run python src/generate-voice-examples.py` 
2. Browse the resulting `local-voice-examples` directory and play audio files to hear the speaker's voice
3. Adjust `vits_voice_mapping` and the gendered voices in `CONFIG.voice_identifiers` in the [src/config.py](./src/config.py) file. 

For example, if you listened to `p237` in `local-voice-examples` and want to add it as another female voice option, append the following to `vits_voice_mapping`:

```
"female_3": {
    "model": "tts_models/en/vctk/vits",
    "speaker": "p237"
},
```

Then in `CONFIG.voice_identifiers.female_voices`, add the new voice as an auto-map option so that it shows up in auto-generated `characters.json`:

```
"female_voices": ["female_1", "female_2", "female_3"],
```

## License

This project is licensed under the MIT License.
