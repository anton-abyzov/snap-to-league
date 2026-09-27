"""Generate the disclosed product narrator; credentials only from environment."""
from pathlib import Path
import os,json,base64,httpx
P=Path(__file__).resolve().parent
text='Your next result starts with a photo. Snap to League reads a scoresheet with Gemini. Review the teams and scores, then publish through EasyChamp. Another result? Add another photo and review the changes. Built at ShellHacks on the existing EasyChamp platform. Try it at snap dot easychamp dot com.'
out=P/'assets/audio/easychamp-narrator.mp3';timing=out.with_suffix('.json')
if not out.exists():
 key=os.environ['ELEVENLABS_API_KEY']; voice='EXAVITQu4vr4xnSDxMaL'
 r=httpx.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps',headers={'xi-api-key':key},params={'output_format':'mp3_44100_128'},json={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':0.8,'speed':1.0}},timeout=120)
 if r.status_code!=200:raise RuntimeError(f'ElevenLabs HTTP {r.status_code}')
 d=r.json();out.write_bytes(base64.b64decode(d.pop('audio_base64')));d.update(text=text,model='eleven_v3',voice_id=voice,synthetic=True);timing.write_text(json.dumps(d,indent=2)+'\n')
print('Narrator audio and alignment ready')
