# openai_client.py

import os
from errors import write_to_error_log
from openai import OpenAI
import json
from config import CONFIG
from utils import clean_json_code_blocks


class GitHubOpenAIClient:
    def __init__(self):
        self.openai = OpenAI(
            base_url=CONFIG["base_url"],
            api_key=CONFIG["api_key"],
        )

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=os.getenv("GITHUB_TOKEN")
        )

        client

    def process_block(self, block: str) -> str:
        user_message = f"{CONFIG['user_message_prefix']}{block}{CONFIG['user_message_suffix']}"
        prompt = f"{CONFIG['system_message']}\n\n{user_message}"

        try:
            response = self.openai.chat.completions.create(
                model=CONFIG["model"],
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=CONFIG["token_limits"]["MAX_COMPLETION_TOKENS"],
                temperature=.2,
                top_p=.5
            )
            completion = response.choices[0].message.content
            return completion.strip()
        except Exception as e:
            error_message = f"Error processing block: {e}"
            print(error_message)
            write_to_error_log(error_message)
            return ""
        
    def process_characters_json(self, characters_json: str) -> str:
        prompt = f"{CONFIG['characters_json_system_message']}{json.dumps(characters_json, indent=2)}{CONFIG['user_message_suffix']}"

        try:
            response = self.openai.chat.completions.create(
                model=CONFIG["model"],
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=CONFIG["token_limits"]["MAX_COMPLETION_TOKENS"],
                temperature=.2,
                top_p=.8
            )
            # Extract the content
            processed_json_str = clean_json_code_blocks(response.choices[0].message.content.strip())

            # Parse the JSON
            try:
                processed_json = json.loads(processed_json_str)
                return processed_json
            except:
                error_message = f"Error parsing returned character.json. Using unprocessed characters.json.\nReturned: {processed_json_str} \nError: {e}"
                print(error_message)
                write_to_error_log(error_message)
                return characters_json
        except Exception as e:
            error_message = f"Error processing character's JSON: {e}"
            print(error_message)
            write_to_error_log(error_message)
            return ""

