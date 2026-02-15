# logic/smart_import.py - Gemini API-powered smart player import

import json
import logging
import os

from google import genai

logger = logging.getLogger(__name__)


def is_smart_import_available():
    """Check if smart import is available.

    Requires both:
    1. GEMINI_API_KEY environment variable is set
    2. smart_import_enabled DB setting is "true" (default: "false")
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return False

    from db.settings import get_setting

    return get_setting("smart_import_enabled", "false") == "true"


async def smart_parse_signup(signup_text, existing_players):
    """Use Gemini API to extract player names from unstructured text and fuzzy-match them.

    Args:
        signup_text: Raw signup text (WhatsApp messages, emails, etc.)
        existing_players: List of player dicts from the database

    Returns:
        List of dicts with keys: extracted_name, matched_player_id, matched_player_name, confidence
        Returns None on any failure (API error, bad JSON, etc.)
    """
    if not signup_text or not signup_text.strip():
        return None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        # Build a simplified player list for the prompt (only id, name, alias)
        player_list = [
            {
                "id": p["id"],
                "name": p["name"],
                "alias": p.get("alias") or "",
            }
            for p in existing_players
        ]

        prompt = f"""Extract player names from the following signup text. The text may be messy, unstructured, from WhatsApp, email, or other sources. Extract ONLY the player names, ignoring any non-name text like dates, locations, greetings, or instructions.

Then, match each extracted name against this list of existing players. For each match, provide a confidence level:
- "high": Very confident match (exact or near-exact match on name or alias)
- "medium": Likely match but not certain (partial name, nickname, abbreviation)
- "none": No match found in the existing player list

Existing players:
{json.dumps(player_list, ensure_ascii=False)}

Signup text:
{signup_text}

Respond with ONLY a JSON array. Each element should have:
- "extracted_name": the name as extracted from the text
- "matched_player_id": the id of the matched player (null if no match)
- "matched_player_name": the name of the matched player (null if no match)
- "confidence": "high", "medium", or "none"

Example response:
[{{"extracted_name": "Johnny", "matched_player_id": 1, "matched_player_name": "John Doe", "confidence": "high"}}]

Return ONLY the JSON array, no other text."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        response_text = response.text.strip()

        # Strip markdown code fences that Gemini may wrap around JSON
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [line for line in lines[1:] if line.strip() != "```"]
            response_text = "\n".join(lines).strip()

        # Parse JSON response
        results = json.loads(response_text)

        if not isinstance(results, list):
            logger.warning("Smart import: API response is not a list")
            return None

        # Validate each result has the required keys
        validated = []
        for r in results:
            if not isinstance(r, dict) or "extracted_name" not in r:
                continue
            validated.append(
                {
                    "extracted_name": r.get("extracted_name", ""),
                    "matched_player_id": r.get("matched_player_id"),
                    "matched_player_name": r.get("matched_player_name"),
                    "confidence": r.get("confidence", "none"),
                }
            )

        if not validated:
            logger.warning("Smart import: No valid results from API response")
            return None

        return validated

    except Exception:
        logger.exception("Smart import failed")
        return None
