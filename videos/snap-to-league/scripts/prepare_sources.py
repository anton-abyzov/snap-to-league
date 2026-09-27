"""Make color-managed SDR editorial proxies. Originals remain on SanDisk untouched."""
from pathlib import Path
import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
PROJECT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(os.environ['SNAP_MEDIA_ARCHIVE'])
OUT=PROJECT/'assets/footage';OUT.mkdir(parents=True,exist_ok=True)
TAKES={'9043':('2026-09-27',0,12),'9045':('2026-09-27',28,17),'9049':('2026-09-27',0,95.5),'9051':('2026-09-27',5,12),'9056':('2026-09-27',16,8),'9060':('2026-09-27',0,38),'9062':('2026-09-27',0,7.4),'9028':('2026-09-26',0,4),'9034':('2026-09-26',1,5)}
def run(item):
 n,(day,start,dur)=item; src=ARCHIVE/day/f'139APPLE_IMG_{n}.MOV';out=OUT/f'{n}-sdr.mp4'
 if not out.exists():
  p=subprocess.run(['avconvert','--source',str(src),'--preset','Preset1920x1080','--output',str(out),'--start',str(start),'--duration',str(dur)],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(n+': '+p.stderr[-300:])
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,color_space,color_transfer,color_primaries,width,height,r_frame_rate:format=duration','-of','json',str(out)]))
 v=next(s for s in meta['streams'] if s['codec_type']=='video');assert v.get('color_transfer')=='bt709',(n,v)
 print(n,'SDR verified',flush=True);return {'take':n,'source_filename':src.name,'source_start':start,'source_duration':dur,'proxy':str(out.relative_to(PROJECT)),'metadata':meta}
with ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(run,TAKES.items()))
(PROJECT/'reports/source-proxies.json').write_text(json.dumps(r,indent=2)+'\n')
