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


def create_realtime_session(instructions: Optional[str] = None, markdown: Optional[str] = None, gender: Optional[str] = None) -> CreatedSession:
    """
    Server creates a Realtime session and receives a client_secret the browser can use
    to establish WebRTC to the OpenAI Realtime service.
    """
    url = f"{OPENAI_BASE_URL}/v1/realtime/sessions"

    #if gender passed,  then set voice accordingly
    voice_selection=FEMALE_VOICE
    if gender and gender.lower() == "male":
        voice_selection = MALE_VOICE

    payload = {
        "model": REALTIME_MODEL,
        "voice": voice_selection,
        "modalities": ["audio", "text"],  # speech-in/speech-out; adjust as needed
        "instructions": instructions or "You are an Insurance Customer.",
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


