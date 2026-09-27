"""Package only approved cutaways and completed editorial works, never isolated music."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,re,shutil
S=Path(__file__).resolve().parent;A=S/'assets';out=S/'renders/release';out.mkdir(exist_ok=True)
files={'personal':'personal-ai-builds-1080x1920.mp4','easychamp':'easychamp-photo-results-1080x1920.mp4'}
def run(args):subprocess.run([str(x) for x in args],check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,final in files.items():
 src=S/'renders'/final;editorial=out/f'{name}-editorial.mp4'
 run(['ffmpeg','-y','-v','error','-i',A/'footage'/f'{name}-base.mp4','-i',src,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',editorial])
 run(['ffmpeg','-y','-v','error','-i',src,'-map','0:a:0','-vn','-ar','48000','-ac','2',A/'audio'/f'{name}-final.wav'])
 p=S/name/'index.html';s=p.read_text();(S/'.private'/f'{name}-production-carve.html').write_text(s)
 audio=re.findall(r'<audio\b[^>]*>.*?</audio>',s,flags=re.S)
 assert len(audio) in (1,2)
 duration=27.5 if name=='personal' else 31
 replacement=f'<audio id="finished-mix" src="assets/audio/{name}-final.wav" data-start="0" data-duration="{duration}" data-track-index="1"></audio>'
 s=s.replace(audio[0],replacement)
 for extra in audio[1:]:s=s.replace(extra,'')
 p.write_text(s)
for n in ['9061-phone-safe.mp4','9062-drift-safe-graded.mp4']:shutil.copyfile(A/'footage'/n,out/n)
license='''Approved editorial media for Snap to League social compositions.\n\nPersonal event imagery and production captures: provided by Anton Abyzov for this campaign. Use the footage within this project and its authorized promotions. The safe muted cutaways exclude unrelated audio and protect the visible badge. No raw originals or archive inventory are included.\n\nThe personal and EasyChamp editorial files are completed, assembled picture-and-sound works. Their soundtracks contain “Deep Urban” by Eugenio Mininni / Mixkit under the Mixkit Stock Music Free License: https://mixkit.co/license/#musicFree . The isolated music track is not included and may not be extracted or redistributed as a standalone stock asset. Reproduce these compositions using the completed editorial work only.\n\nThe EasyChamp editorial work includes a separately generated ElevenLabs promotional narrator, not a clone of Anton. The personal work uses his recorded event speech. Real UI captures are labeled as original event footage, separate demo data or separate published examples in the source compositions.\n'''
(out/'EDITABLE-MEDIA-LICENSE.txt').write_text(license)
names=[f'{x}-editorial.mp4' for x in files]+['9061-phone-safe.mp4','9062-drift-safe-graded.mp4','EDITABLE-MEDIA-LICENSE.txt']
archive=out/'social-editable-media.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in names:z.write(out/name,arcname=name)
manifest={'repository':'anton-abyzov/snap-to-league','tag':'snap-to-league-social-2026-v1','asset':'social-editable-media.zip','zip_sha256':sha(archive),'zip_bytes':archive.stat().st_size,'members':{n:sha(out/n) for n in names},'member_bytes':{n:(out/n).stat().st_size for n in names}}
(S/'reports/release-media.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
