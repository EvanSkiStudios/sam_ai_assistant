import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play, VoiceSettings

# Load Env
load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")

client = ElevenLabs(
    api_key=f"{API_KEY}"
)

audio = client.text_to_speech.convert(
    text="let's keep this little chat between us, shall we?",
    voice_id="FGY2WhTYpPnrIDTdsKH5",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
    voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
)

# Collect into bytes
audio_bytes = b"".join(audio)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)

print("✅ Audio saved as output.mp3")

# Optional: play it too
play(audio_bytes)

