import os
from dataclasses import dataclass
from typing import Optional

import requests



OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # Set in your env/secret store
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")

# GA realtime model (Sep 2025). Choose a voice like "marin" or "cedar".
# See latest docs/models if you need EU data residency or preview variants.
REALTIME_MODEL = os.environ.get("REALTIME_MODEL", "gpt-realtime")
FEMALE_VOICE = os.environ.get("REALTIME_VOICE", "marin")
MALE_VOICE = os.environ.get("REALTIME_VOICE", "cedar")


@dataclass
class CreatedSession:
    id: str
    client_secret: str
    expires_at: int


def create_realtime_session(persona: Optional[str] = None, markdown: Optional[str] = None, gender: Optional[str] = None) -> CreatedSession:
    """
    Server creates a Realtime session and receives a client_secret the browser can use
    to establish WebRTC to the OpenAI Realtime service.
    """
    url = f"{OPENAI_BASE_URL}/v1/realtime/sessions"

    #if gender passed,  then set voice accordingly
    voice_selection=FEMALE_VOICE
    if gender and gender.lower() == "male":
        voice_selection = MALE_VOICE

    INS=f""""
    YOU ARE AN INSURANCE CUSTOMER.

# Core Instructions
<core_capabilities>
YOU ARE AN INSURANCE CUSTOMER. You should assume the personality provided below:
{persona}
Provide answers based on your personality and also the data provided below.
</core_capabilities>

<agent_background>
{markdown}
</agent_background>

<user_information>
User will be Insurance Agent trying to help you with your Insurance needs.
</user_information>

<voice_capabilities>
- Providing answer based on your personality and background
- Keeping your responses brief and only about the question asked
- ALWAYS RESPOND IN ENGLISH
</voice_capabilities>

<communication_preferences>
- Match this communication style and tone:
Keep it formal and concise.
</communication_preferences>

<voice_interaction_guidelines>
- Speak in short, conversational sentences (one or two per reply)
- Use simple words; avoid jargon unless the user uses it first
- Never use lists, markdown, or code blocks—just speak naturally
- If a request is ambiguous, ask a brief clarifying question instead of guessing
</voice_interaction_guidelines>
"""    

    payload = {
        "model": REALTIME_MODEL,
        "voice": voice_selection,
        "modalities": ["audio", "text"],  # speech-in/speech-out; adjust as needed
        "instructions": INS,
        "turn_detection": {"type": "server_vad"}
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI session create failed: {r.status_code} {r.text}")

    data = r.json()
    # Shape: {"id": "...", "client_secret": {"value":"...", "expires_at": 169...}, ...}
    return CreatedSession(
        id=data["id"],
        client_secret=data["client_secret"]["value"],
        expires_at=int(data["client_secret"]["expires_at"]),
    )


