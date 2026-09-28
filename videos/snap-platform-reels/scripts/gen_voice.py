"""ElevenLabs narration, one request per line with character timestamps. Key is read from the
environment or the snap-to-league repo's untracked .env and never printed."""
import base64, json, os, sys
from pathlib import Path
import httpx
sys.path.insert(0, str(Path(__file__).parent))
from reels_script import REELS
P = Path(__file__).resolve().parent.parent
VOICE, MODEL = "EXAVITQu4vr4xnSDxMaL", "eleven_v3"

def key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    for line in Path("/Users/antonabyzov/Projects/github/snap-to-league/.env").read_text().splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ELEVENLABS_API_KEY not found")

K = key()
for reel, lines in REELS.items():
    for i, text in enumerate(lines):
        out = P / f"assets/audio/vo/{reel}-{i}.mp3"
        if out.exists() and json.loads(out.with_suffix(".json").read_text()).get("text") == text:
            continue
        r = httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps", headers={"xi-api-key": K},
                       params={"output_format": "mp3_44100_128"},
                       json={"text": text, "model_id": MODEL, "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "speed": 1.0}},
                       timeout=120)
        if r.status_code != 200:
            raise SystemExit(f"ElevenLabs HTTP {r.status_code} on {reel}-{i}")
        d = r.json()
        out.write_bytes(base64.b64decode(d.pop("audio_base64")))
        d.update(text=text, model=MODEL, voice_id=VOICE, synthetic=True, cloned_voice=False)
        out.with_suffix(".json").write_text(json.dumps(d, indent=1) + "\n")
        print(reel, i, "ok", flush=True)
