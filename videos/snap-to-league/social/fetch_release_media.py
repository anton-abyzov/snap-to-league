"""Restore approved social media from a hash-pinned release; no raw originals needed."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile,shutil
S=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='snap-to-league-social-2026-v1');parser.add_argument('--archive',type=Path,help='Verify a local copy of the exact release archive');args=parser.parse_args()
m=json.loads((S/'reports/release-media.json').read_text());tag=args.tag or m.get('tag')
with tempfile.TemporaryDirectory(prefix='snap-social-approved-') as temp:
 temp=Path(temp);archive=temp/m['asset']
 if args.archive:shutil.copyfile(args.archive,archive)
 else:
  if not tag:raise SystemExit('Pass --tag for the release containing social-editable-media.zip')
  subprocess.run(['gh','release','download',tag,'--repo',m['repository'],'--pattern',m['asset'],'--dir',str(temp)],check=True)
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['zip_sha256'],'Archive hash mismatch'
 with zipfile.ZipFile(archive) as z:
  assert set(z.namelist())==set(m['members']),'Unexpected archive members'
  for name,digest in m['members'].items():
   assert Path(name).name==name,'Only flat archive members allowed'
   data=z.read(name);assert hashlib.sha256(data).hexdigest()==digest,f'Member hash mismatch: {name}'
   (temp/name).write_bytes(data)
 for folder in ('assets/footage','assets/audio','assets/fonts','assets/vendor'):(S/folder).mkdir(parents=True,exist_ok=True)
 for name in ('personal','easychamp'):
  src=temp/f'{name}-editorial.mp4'
  subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-map','0:v:0','-an','-c:v','copy',str(S/'assets/footage'/f'{name}-base.mp4')],check=True)
  subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-map','0:a:0','-vn','-ar','48000','-ac','2',str(S/'assets/audio'/f'{name}-final.wav')],check=True)
  link=S/name/'assets'
  if not link.exists():link.symlink_to('../assets',target_is_directory=True)
 for name in ('9061-phone-safe.mp4','9062-drift-safe-graded.mp4'):shutil.copyfile(temp/name,S/'assets/footage'/name)
 # The parent project tracks fonts and installs its pinned GSAP runtime.
 for name in ('archivo-400.ttf','archivo-700.ttf','archivo-black-400.ttf'):shutil.copyfile(S.parent/'assets/fonts'/name,S/'assets/fonts'/name)
 runtime=S.parent/'assets/vendor/gsap.min.js'
 if not runtime.exists():raise SystemExit('Run the parent npm ci / scripts/setup_runtime.mjs first')
 shutil.copyfile(runtime,S/'assets/vendor/gsap.min.js')
print('Verified approved social picture/sound and safe cutaways restored.')
