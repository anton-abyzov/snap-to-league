"""Fetch only the approved public editorial videos, verify, split local tracks."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,zipfile

P=Path(__file__).resolve().parents[1]
manifest=json.loads((P/'reports/release-media.json').read_text())
with tempfile.TemporaryDirectory(prefix='snap-approved-media-') as temp:
 temp=Path(temp)
 subprocess.run(['gh','release','download',manifest['tag'],'--repo',manifest['repository'],
                 '--pattern','editable-media.zip','--dir',str(temp)],check=True)
 archive=temp/'editable-media.zip'
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['zip_sha256'],'Release archive hash mismatch'
 with zipfile.ZipFile(archive) as z:
  expected=set(manifest['members'])
  assert set(z.namelist())==expected,'Unexpected archive member'
  for name,digest in manifest['members'].items():
   assert Path(name).name==name,'Non-flat archive path'
   data=z.read(name)
   assert hashlib.sha256(data).hexdigest()==digest,f'Hash mismatch: {name}'
   (temp/name).write_bytes(data)
 for aspect in ('landscape','vertical'):
  src=temp/f'{aspect}-editorial.mp4'
  for d in ('assets/footage','assets/audio'):(P/d).mkdir(parents=True,exist_ok=True)
  subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-map','0:v:0','-an','-c:v','copy',
                  str(P/'assets/footage'/f'{aspect}-base.mp4')],check=True)
  subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-map','0:a:0','-vn','-ar','48000','-ac','2',
                  str(P/'assets/audio'/f'{aspect}-final.wav')],check=True)
print('Approved picture and sound tracks restored; private originals not downloaded.')
