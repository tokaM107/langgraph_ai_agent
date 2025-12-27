

SYSTEM_PROMPT = """
You are an information extraction system.

Extract origin and destination locations from Egyptian Arabic text.

Rules:
- Output ONLY valid JSON
- No explanations
- No markdown
- Do NOT translate names
- If missing, set value to null

JSON schema:
{
  "origin": string | null,
  "destination": string | null
}
"""

import json
import os
from dotenv import load_dotenv
from google.genai import Client
from google.genai import types
from typing import Optional

load_dotenv()

client = Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

print("LLM Client initialized.")
print(client)

def llm_parse(user_input: str) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[user_input],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.0
            )
        )

        parsed = json.loads(response.text)

        return {
            "origin": parsed.get("origin"),
            "destination": parsed.get("destination")
        }

    except Exception as e:
        print(f"[LLM PARSE ERROR] {e}")
        return {
            "origin": None,
            "destination": None
        }


# print(llm_parse("عايز اروح من محطة مصر الى برج العرب"))  # Example usage