"""Generate two disclosed bridge takes; API keys are read only from caller environment."""
from pathlib import Path
import os,json,base64,httpx,subprocess
P=Path(__file__).resolve().parents[1]
LINES={
 'bridge-a':'Gemini reads the photo. A second AI pass checks the extraction. Review the teams and scores before publishing.',
 'bridge-b':'New result? Add another photo and review what changed. Snap to League, built at ShellHacks on the existing EasyChamp platform.'
}
key=os.environ.get('ELEVENLABS_API_KEY');assert key,'ELEVENLABS_API_KEY missing'
voice='EXAVITQu4vr4xnSDxMaL'
for name,line in LINES.items():
 out=P/'assets/audio'/f'{name}.mp3';timings=P/'assets/audio'/f'{name}.json'
 if out.exists() and timings.exists():continue
 r=httpx.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps',headers={'xi-api-key':key},params={'output_format':'mp3_44100_128'},json={'text':line,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':0.8,'speed':1.0}},timeout=120)
 if r.status_code!=200:raise RuntimeError(f'TTS {name} HTTP {r.status_code}: {r.text[:220]}')
 d=r.json();out.write_bytes(base64.b64decode(d.pop('audio_base64')));d.update(text=line,voice_id=voice,model='eleven_v3',synthetic=True);timings.write_text(json.dumps(d,indent=2))
 print(name,subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(out)]).decode().strip(),flush=True)
